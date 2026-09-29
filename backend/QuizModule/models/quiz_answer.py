from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class QuizAnswer(Base):
    __tablename__ = 'quiz_answers'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    question_id = Column(Integer, nullable=False)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
