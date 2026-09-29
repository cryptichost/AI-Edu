from typing import List, Optional

from pydantic import BaseModel, Field


class QuizOptionResponse(BaseModel):
    id: int
    content: str
    is_correct: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class QuizQuestionResponse(BaseModel):
    id: int
    question_type: int
    content: Optional[str] = None
    score: int = 0
    analysis: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    options: List[QuizOptionResponse] = Field(default_factory=list)
