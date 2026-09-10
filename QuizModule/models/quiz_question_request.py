"""题目 / 选项修改请求数据类型。"""

from typing import List, Optional

from pydantic import BaseModel, Field


class QuizOptionRequest(BaseModel):
    """单个选项的修改数据（对应 quiz_option 可编辑字段）。

    id 为空（或 <=0）表示这是一个待新增的选项。
    """

    id: Optional[int] = Field(default=None, description="已有选项 id；为空表示新增")
    content: str
    is_correct: bool


class QuizQuestionRequest(BaseModel):
    """整题保存（含选项）的请求体。

    题目字段用于更新 quiz_question；options 用于同步该题的全部选项：
    options 不传（None）表示不改动选项，传 [] 表示清空全部选项。
    """

    question_type: Optional[int] = None
    content: Optional[str] = None
    score: Optional[int] = None
    analysis: Optional[str] = None
    options: Optional[List[QuizOptionRequest]] = Field(
        default=None, description="该题全部选项（缺省表示不改动选项）"
    )
