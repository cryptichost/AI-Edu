import json
import logging
import time
from typing import Any, AsyncGenerator, List, Optional

from google.adk import Runner
from google.genai import types

from .models import ChatRequest, ChatResponse, Course, ChatHistory, ChatEventData, CourseNode
from . import rag
from .session import get_db, get_agent_db, session_service
from .model import CHROMA_PERSIST_DIRACTORY,DEFAULT_RESOURCE_DIRECTORY
from .agents import engagement_agent, exploration_agent, explanation_agent, elaboration_agent, evaluation_agent, orchestrator_agent, EntranceAgent

from sqlalchemy import select

logger = logging.getLogger(__name__)

agent_runner = Runner(
    agent = EntranceAgent(
        name="agents",
        engagement_agent=engagement_agent,
        exploration_agent=exploration_agent,
        explanation_agent=explanation_agent,
        elaboration_agent=elaboration_agent,
        evaluation_agent=evaluation_agent,
        orchestrator_agent=orchestrator_agent
    ),
    app_name="agents",
    session_service=session_service,
    auto_create_session=True
)

async def get_history_by_student_and_course(student_id: str, course_id: str) -> List[ChatResponse]:
    async with get_agent_db as db:
        stmt = select(ChatHistory).filter(
            ChatHistory.user_id == student_id,
            ChatHistory.session_id == course_id
        ).order_by(ChatHistory.timestamp.asc())

        result = await db.execute(stmt)
        rows = result.scalars().all()

        results = []
        for row in rows:
            if row.event_data:
                try:
                    data = json.loads(row.event_data)
                    event_data = ChatEventData(**data)
                except Exception as e:
                    print(f"[service.py] json.loads(row.event_data) 解析失败: {e}")
                    print(f"[service.py] event_data 内容: {row.event_data}")
                    continue

                if event_data.content.parts[0].function_call:
                    continue

                if event_data.author=='user':
                    results.append(ChatResponse(
                        role='user',
                        content=event_data.content.parts[0].text,
                        buttons=[],
                        resources=[],
                        tests=[],
                        timestamp=event_data.timestamp
                    ))
                else:
                    part = event_data.content.parts[0]
                    try:
                        part_data = json.loads(part.text)
                    except Exception as e:
                        print(f"[service.py] json.loads(part.text) 解析失败: {e}")
                        print(f"[service.py] part.text 内容: {part.text}")
                        continue
                    # Map ChatEventData to ChatResponse with flattened content and action items
                    results.append(ChatResponse(
                        role=event_data.author,
                        content=part_data.get('content'),
                        buttons=part_data.get('buttons', []),
                        resources=part_data.get('resources', []),
                        tests=part_data.get('tests', []),
                        timestamp=event_data.timestamp
                    ))

        return results


async def chat_message_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    user_id = request.user_id
    course_id = request.course_id
    content = types.Content(
        role='user',
        parts=[
            types.Part(text=request.content)
        ]
    )

    events = agent_runner.run_async(user_id=user_id, session_id=course_id, new_message=content)
    async for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    yield part.text
        elif event.actions and event.actions.escalate:
            yield f"Agent escalated: {event.error_message or 'No specific message'}"


async def get_course_id_by_name(course_name: str) -> Optional[str]:    
    async with get_db as db:
        stmt = select(CourseNode.node_detail_id).where(CourseNode.node_name == course_name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

async def init_rag() -> None:
    rag.prepare_chroma_db_from_directory(
        directory_path=DEFAULT_RESOURCE_DIRECTORY,
        persist_directory=CHROMA_PERSIST_DIRACTORY
    )
