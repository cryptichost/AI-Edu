from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ChatSession(Base):
    __tablename__="sessions"

    app_name = Column(String(length=128), primary_key=True, index=True)
    user_id = Column(String(length=128), primary_key=True, index=True)
    id = Column(String(length=128), primary_key=True, index=True)
    state = Column(Text, nullable=False)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)