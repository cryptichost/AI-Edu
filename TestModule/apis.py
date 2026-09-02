from typing import List

from fastapi import HTTPException, APIRouter, Cookie
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/test")
test_router = router

@router.get("/{user_id}/{course_id}", response_model=List[ChatResponse])
async def get_course_test(user_id: str, course_id: str):
    return await service.get_history_by_student_and_course(user_id, course_id)