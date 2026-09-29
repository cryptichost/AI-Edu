from sqlalchemy import BigInteger, Column, DateTime, Integer, SmallInteger, Text, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Quiz(Base):
    __tablename__ = 'quiz'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=True)
    question_count = Column(Integer, nullable=False)
    course_id = Column(String(length=100), nullable=False)
    status = Column(SmallInteger, nullable=False)
    total_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
