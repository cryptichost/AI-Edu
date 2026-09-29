from typing import Optional

from pydantic import BaseModel


class QuizListResponse(BaseModel):
    id: int
    title: str
    course_name: str
    question_count: int
    status: int
    total_score: int
    created_at: Optional[str]
    updated_at: Optional[str]

