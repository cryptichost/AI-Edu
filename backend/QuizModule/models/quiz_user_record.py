from sqlalchemy import BigInteger, Column, DateTime, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class QuizUserRecord(Base):
    __tablename__ = 'quiz_user_records'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    start_at = Column(DateTime, nullable=False)
    submit_at = Column(DateTime, nullable=True)
