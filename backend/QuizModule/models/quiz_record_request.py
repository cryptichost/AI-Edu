from typing import Optional

from pydantic import BaseModel


class QuizRecordRequest(BaseModel):
    user_id: int
    course_id: Optional[int] = None


class QuizRecordStartRequest(BaseModel):
    """进入测验：为学生在指定测验下创建一条作答记录。"""

    quiz_id: int
    user_id: int