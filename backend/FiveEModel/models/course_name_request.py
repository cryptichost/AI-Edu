from pydantic import BaseModel


class CourseNameRequest(BaseModel):
    course:str
    course_name:str