from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import String, cast, select

from .models import (
    Course,
    Quiz,
    QuizAnswer,
    QuizListResponse,
    QuizOption,
    QuizOptionRequest,
    QuizOptionResponse,
    QuizQuestion,
    QuizQuestionRequest,
    QuizQuestionResponse,
    QuizUserRecord,
)
from .session import get_db


def _to_iso(value: Optional[Any]) -> Optional[str]:
    """把 datetime 转成 isoformat 字符串，便于 JSON 返回。"""
    return value.isoformat() if value is not None else None


def _record_payload(record: QuizUserRecord) -> Dict[str, Any]:
    return {
        "id": record.id,
        "quiz_id": record.quiz_id,
        "user_id": record.user_id,
        "start_at": _to_iso(record.start_at),
        "submit_at": _to_iso(record.submit_at),
    }


def _quiz_payload(quiz: Quiz) -> Dict[str, Any]:
    return {
        "id": quiz.id,
        "title": quiz.title,
        "question_count": quiz.question_count,
        "course_id": quiz.course_id,
        "status": quiz.status,
        "total_score": quiz.total_score,
        "created_at": _to_iso(quiz.created_at),
        "updated_at": _to_iso(quiz.updated_at),
    }


async def list_all_quizzes() -> List[QuizListResponse]:
    """查询全部测验，并关联课程表补全课程名称，返回 QuizListResponse 列表。"""
    async with get_db as db:
        stmt = (
            select(
                Quiz.id,
                Quiz.title,
                Course.course_name,
                Quiz.question_count,
                Quiz.status,
                Quiz.total_score,
                Quiz.created_at,
                Quiz.updated_at,
            )
            .outerjoin(Course, Quiz.course_id == Course.course_id)
            .order_by(Quiz.id.desc())
        )
        result = await db.execute(stmt)
        rows = result.all()
        return [
            QuizListResponse(
                id=row.id,
                title=str(row.title) if row.title is not None else "",
                course_name=row.course_name or "",
                question_count=row.question_count,
                status=row.status,
                total_score=row.total_score,
                created_at=_to_iso(row.created_at),
                updated_at=_to_iso(row.updated_at),
            )
            for row in rows
        ]


async def get_record_by_user(user_id: int, course_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """按用户查询测验，返回该用户全部作答记录，仅包含 id 与 submit_at。

    传入 course_id 时，仅返回该课程下的作答记录（通过 quiz.course_id 关联过滤）。
    """
    async with get_db as db:
        stmt = (
            select(QuizUserRecord.id, QuizUserRecord.submit_at)
            .where(QuizUserRecord.user_id == user_id)
            .order_by(QuizUserRecord.id.desc())
        )
        if course_id is not None:
            stmt = (
                stmt.join(Quiz, QuizUserRecord.quiz_id == Quiz.id)
                .where(Quiz.course_id == course_id)
            )
        result = await db.execute(stmt)
        rows = result.all()
        return [
            {
                "id": row.id,
                "updated_at": _to_iso(row.submit_at),
            }
            for row in rows
        ]


async def get_quiz_detail_by_record(record_id: int) -> Optional[Dict[str, Any]]:
    """根据作答记录 id 查询测验详情。

    返回作答记录 + 对应测验 + 题目列表(含选项与作答)；记录不存在时返回 None。
    """
    async with get_db as db:
        record = (
            await db.execute(select(QuizUserRecord).where(QuizUserRecord.id == record_id))
        ).scalar_one_or_none()
        if record is None:
            return None

        quiz = None
        if record.quiz_id is not None:
            quiz = (
                await db.execute(select(Quiz).where(Quiz.id == record.quiz_id))
            ).scalar_one_or_none()

        questions: List[Dict[str, Any]] = []
        if quiz is not None:
            question_rows = (
                await db.execute(
                    select(QuizQuestion)
                    .where(QuizQuestion.quiz_id == quiz.id)
                    .order_by(QuizQuestion.id)
                )
            ).scalars().all()

            question_ids = [q.id for q in question_rows]
            option_map: Dict[int, List[Dict[str, Any]]] = {}
            answer_map: Dict[int, List[Dict[str, Any]]] = {}

            if question_ids:
                options = (
                    await db.execute(
                        select(QuizOption)
                        .where(QuizOption.question_id.in_(question_ids))
                        .order_by(QuizOption.id)
                    )
                ).scalars().all()
                for option in options:
                    option_map.setdefault(option.question_id, []).append({
                        "id": option.id,
                        "question_id": option.question_id,
                        "content": option.content,
                        "is_correct": option.is_correct,
                        "created_at": _to_iso(option.created_at),
                        "updated_at": _to_iso(option.updated_at),
                    })

                answers = (
                    await db.execute(
                        select(QuizAnswer)
                        .where(QuizAnswer.question_id.in_(question_ids))
                        .order_by(QuizAnswer.id)
                    )
                ).scalars().all()
                for answer in answers:
                    answer_map.setdefault(answer.question_id, []).append({
                        "id": answer.id,
                        "question_id": answer.question_id,
                        "user_answer": answer.user_answer,
                        "is_correct": answer.is_correct,
                        "created_at": _to_iso(answer.created_at),
                        "updated_at": _to_iso(answer.updated_at),
                    })

            for question in question_rows:
                questions.append({
                    "id": question.id,
                    "quiz_id": question.quiz_id,
                    "question_type": question.question_type,
                    "content": question.content,
                    "score": question.score,
                    "analysis": question.analysis,
                    "created_at": _to_iso(question.created_at),
                    "updated_at": _to_iso(question.updated_at),
                    "options": option_map.get(question.id, []),
                    "answers": answer_map.get(question.id, []),
                })

        return {
            "record": _record_payload(record),
            "quiz": _quiz_payload(quiz) if quiz is not None else None,
            "questions": questions,
        }


async def get_questions_by_quiz(quiz_id: int) -> Optional[List[QuizQuestionResponse]]:
    """按 quiz id 查询该测验的全部题目及选项。

    返回 QuizQuestionResponse 列表；quiz 不存在时返回 None。
    """
    async with get_db as db:
        quiz = (
            await db.execute(select(Quiz).where(Quiz.id == quiz_id))
        ).scalar_one_or_none()
        if quiz is None:
            return None

        question_rows = (
            await db.execute(
                select(QuizQuestion)
                .where(QuizQuestion.quiz_id == quiz_id)
                .order_by(QuizQuestion.id)
            )
        ).scalars().all()

        question_ids = [q.id for q in question_rows]
        option_map: Dict[int, List[QuizOption]] = {}
        if question_ids:
            options = (
                await db.execute(
                    select(QuizOption)
                    .where(QuizOption.question_id.in_(question_ids))
                    .order_by(QuizOption.id)
                )
            ).scalars().all()
            for option in options:
                option_map.setdefault(option.question_id, []).append(option)

        return [
            QuizQuestionResponse(
                id=q.id,
                question_type=q.question_type,
                content=q.content,
                score=q.score,
                analysis=q.analysis,
                created_at=_to_iso(q.created_at),
                updated_at=_to_iso(q.updated_at),
                options=[
                    QuizOptionResponse(
                        id=o.id,
                        content=o.content,
                        is_correct=o.is_correct,
                        created_at=_to_iso(o.created_at),
                        updated_at=_to_iso(o.updated_at),
                    )
                    for o in option_map.get(q.id, [])
                ],
            )
            for q in question_rows
        ]


async def update_question_by_id(
    question_id: int, payload: QuizQuestionRequest
) -> Optional[QuizQuestionResponse]:
    """整题保存（含选项）：更新题目字段，并按 payload.options 同步该题全部选项。

    题目不存在时返回 None。
    options 同步规则：
    - 不传（None）：不改动选项；
    - 传 []：清空该题全部选项；
    - 已提交带 id 的选项：原地更新 content / is_correct；
    - 未带 id 的选项：作为新增选项插入；
    - 未在本次提交中的旧选项：删除。
    """
    async with get_db as db:
        question = (
            await db.execute(
                select(QuizQuestion).where(QuizQuestion.id == question_id)
            )
        ).scalar_one_or_none()
        if question is None:
            return None

        now = datetime.now()

        # 更新题目本身的字段（未传的字段保持原样）
        if payload.question_type is not None:
            question.question_type = payload.question_type
        if payload.content is not None:
            question.content = payload.content
        if payload.score is not None:
            question.score = payload.score
        if payload.analysis is not None:
            question.analysis = payload.analysis
        question.updated_at = now

        if payload.options is not None:
            existing_options = (
                await db.execute(
                    select(QuizOption)
                    .where(QuizOption.question_id == question_id)
                    .order_by(QuizOption.id)
                )
            ).scalars().all()
            existing_by_id = {option.id: option for option in existing_options}

            submit_ids = {
                item.id for item in payload.options if item.id is not None and item.id > 0
            }

            # 1) 删除本次未提交的旧选项
            for option in existing_options:
                if option.id not in submit_ids:
                    await db.delete(option)

            # 2) 更新已有选项 / 新增选项
            for item in payload.options:
                if item.id is not None and item.id in existing_by_id:
                    option = existing_by_id[item.id]
                    option.content = item.content
                    option.is_correct = item.is_correct
                    option.updated_at = now
                else:
                    db.add(
                        QuizOption(
                            question_id=question_id,
                            content=item.content,
                            is_correct=item.is_correct,
                            created_at=now,
                            updated_at=now,
                        )
                    )

        await db.commit()

        # 提交后重新读取题目与选项，返回最新 QuizQuestionResponse
        updated_question = (
            await db.execute(
                select(QuizQuestion).where(QuizQuestion.id == question_id)
            )
        ).scalar_one()
        updated_options = (
            await db.execute(
                select(QuizOption)
                .where(QuizOption.question_id == question_id)
                .order_by(QuizOption.id)
            )
        ).scalars().all()

        return QuizQuestionResponse(
            id=updated_question.id,
            question_type=updated_question.question_type,
            content=updated_question.content,
            score=updated_question.score,
            analysis=updated_question.analysis,
            created_at=_to_iso(updated_question.created_at),
            updated_at=_to_iso(updated_question.updated_at),
            options=[
                QuizOptionResponse(
                    id=o.id,
                    content=o.content,
                    is_correct=o.is_correct,
                    created_at=_to_iso(o.created_at),
                    updated_at=_to_iso(o.updated_at),
                )
                for o in updated_options
            ],
        )


async def create_question_by_quiz(
    quiz_id: int, payload: QuizQuestionRequest
) -> Optional[QuizQuestionResponse]:
    """在指定测验下新增一道题目（含选项）。

    测验不存在时返回 None。
    - question_type / score 未传时使用兜底值（1 = 单选题，0 分）；
    - payload.options 全部作为新增选项插入；
    - 同步 quiz.question_count / quiz.total_score，保证列表数量与总分正确。
    """
    async with get_db as db:
        quiz = (
            await db.execute(select(Quiz).where(Quiz.id == quiz_id))
        ).scalar_one_or_none()
        if quiz is None:
            return None

        now = datetime.now()

        question = QuizQuestion(
            quiz_id=quiz_id,
            question_type=payload.question_type if payload.question_type is not None else 1,
            content=payload.content,
            score=payload.score if payload.score is not None else 0,
            analysis=payload.analysis,
            created_at=now,
            updated_at=now,
        )
        db.add(question)
        await db.flush()  # 先拿到自增 id，供选项外键使用

        for item in payload.options or []:
            db.add(
                QuizOption(
                    question_id=question.id,
                    content=item.content,
                    is_correct=item.is_correct,
                    created_at=now,
                    updated_at=now,
                )
            )

        # 同步 quiz 聚合字段，保持「测验列表」展示的数量/总分一致
        quiz.question_count = (quiz.question_count or 0) + 1
        quiz.total_score = (quiz.total_score or 0) + (question.score or 0)
        quiz.updated_at = now

        await db.commit()

        # 提交后重新读取题目与选项，返回最新 QuizQuestionResponse
        created_question = (
            await db.execute(
                select(QuizQuestion).where(QuizQuestion.id == question.id)
            )
        ).scalar_one()
        created_options = (
            await db.execute(
                select(QuizOption)
                .where(QuizOption.question_id == question.id)
                .order_by(QuizOption.id)
            )
        ).scalars().all()

        return QuizQuestionResponse(
            id=created_question.id,
            question_type=created_question.question_type,
            content=created_question.content,
            score=created_question.score,
            analysis=created_question.analysis,
            created_at=_to_iso(created_question.created_at),
            updated_at=_to_iso(created_question.updated_at),
            options=[
                QuizOptionResponse(
                    id=o.id,
                    content=o.content,
                    is_correct=o.is_correct,
                    created_at=_to_iso(o.created_at),
                    updated_at=_to_iso(o.updated_at),
                )
                for o in created_options
            ],
        )