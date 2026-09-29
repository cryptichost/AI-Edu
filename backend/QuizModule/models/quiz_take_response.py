from typing import List, Optional

from pydantic import BaseModel, Field


class QuizTakeOptionResponse(BaseModel):
    """学生作答时的选项：只包含展示所需字段，不含 is_correct。"""

    id: int
    content: str


class QuizTakeQuestionResponse(BaseModel):
    """学生作答时的题目：不含正确答案与解析，避免答案泄露。"""

    id: int
    question_type: int
    content: Optional[str] = None
    score: int = 0
    options: List[QuizTakeOptionResponse] = Field(default_factory=list)
