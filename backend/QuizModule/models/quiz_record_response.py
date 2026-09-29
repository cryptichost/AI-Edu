from typing import Optional

from pydantic import BaseModel


class QuizRecordResponse(BaseModel):
    """作答记录；submit_at 为空表示「进行中」（已进入测验但尚未提交）。"""

    id: int
    quiz_id: Optional[int] = None
    user_id: Optional[int] = None
    start_at: Optional[str] = None
    submit_at: Optional[str] = None
    # 兼容旧字段：提交时间优先，进行中回退到进入时间。
    updated_at: Optional[str] = None
