from sqlalchemy import BigInteger, Boolean, Column, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class QuizOption(Base):
    __tablename__ = 'quiz_options'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    question_id = Column(BigInteger, nullable=False)
    content = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
