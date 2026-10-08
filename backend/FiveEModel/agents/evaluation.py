from google.adk import Runner
from google.adk.agents.llm_agent import Agent

from ..model import deepseek
from ..session import session_service
from ..prompts import evaluation

evaluation_agent = Agent(
    model=deepseek,
    name='evaluation_agent',
    description='',
    instruction=evaluation
)

runner = Runner(
    agent=evaluation_agent,
    app_name='evaluation',
    session_service=session_service,
    auto_create_session=True
)
