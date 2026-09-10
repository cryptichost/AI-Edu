from typing import Optional

from pydantic import BaseModel


class QuizRecordResponse(BaseModel):
    id: int
    updated_at: Optional[str]
