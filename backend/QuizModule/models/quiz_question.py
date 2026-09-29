from sqlalchemy import BigInteger, Column, DateTime, Integer, SmallInteger, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quiz_id = Column(BigInteger, nullable=False)
    question_type = Column(SmallInteger, nullable=False)
    content = Column(Text, nullable=True)
    score = Column(Integer, nullable=False)
    analysis = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
