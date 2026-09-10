from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from . import services
from .models import (
    QuizListResponse,
    QuizQuestionRequest,
    QuizQuestionResponse,
    QuizRecordResponse,
)

router = APIRouter(prefix="/api/quiz", tags=["quiz"])
quiz_router = router


@router.get("/list", response_model=List[QuizListResponse])
async def quiz_list_all():
    """返回所有测验。"""
    return await services.list_all_quizzes()


@router.get("/records/user/{user_id}", response_model=List[QuizRecordResponse])
async def quiz_records_by_user(
    user_id: int,
    course_id: Optional[int] = Query(default=None, description="按课程过滤（quiz.course_id）"),
):
    """按用户查询测验，返回该用户的作答记录（id 与 updated_at），可选 course_id 按课程过滤。"""
    return await services.get_record_by_user(user_id, course_id=course_id)


@router.get("/records/{record_id}")
async def quiz_detail_by_record(record_id: int):
    """根据作答记录 id 查询测验详情。"""
    detail = await services.get_quiz_detail_by_record(record_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"作答记录不存在: {record_id}")
    return detail


@router.get("/questions/{quiz_id}", response_model=List[QuizQuestionResponse])
async def quiz_questions_by_quiz(quiz_id: int):
    """按 quiz id 查询该测验的全部题目及选项。"""
    questions = await services.get_questions_by_quiz(quiz_id)
    if questions is None:
        raise HTTPException(status_code=404, detail=f"测验不存在: {quiz_id}")
    return questions


@router.post("/questions/{question_id}", response_model=QuizQuestionResponse)
async def quiz_question_update(question_id: int, payload: QuizQuestionRequest):
    """整题保存（含选项）：按 question_id 更新题目字段，并按 body 中的 options 同步该题全部选项。"""
    question = await services.update_question_by_id(question_id, payload)
    if question is None:
        raise HTTPException(status_code=404, detail=f"题目不存在: {question_id}")
    return question


@router.post("/questions/new/{quiz_id}", response_model=QuizQuestionResponse)
async def quiz_question_create(
    quiz_id: int,
    payload: QuizQuestionRequest
):
    """在指定测验下新增一道题目（含选项）。

    - quiz_id 通过查询参数传入（该测验必须存在）；
    - body 中的 options 全部作为该题的新增选项插入。
    """
    question = await services.create_question_by_quiz(quiz_id, payload)
    if question is None:
        raise HTTPException(status_code=404, detail=f"测验不存在: {quiz_id}")
    return question