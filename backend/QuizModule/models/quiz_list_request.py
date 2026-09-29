from typing import Optional

from pydantic import BaseModel

class QuizListRequest(BaseModel):
    course_id: Optional[int]