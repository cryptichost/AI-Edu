import os
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.sessions.database_session_service import DatabaseSessionService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")

if not all([host, port, user, password, database]):
    raise RuntimeError("5E database config missing: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD and DB_NAME are required")

DB1_URL = "mysql+aiomysql://{}:{}@{}:{}/{}".format(user, password, host, port, database)
engine1 = create_async_engine(DB1_URL, pool_pre_ping=True)
SessionLocal1 = async_sessionmaker(autocommit=False, autoflush=False, bind=engine1)

get_db = SessionLocal1()
