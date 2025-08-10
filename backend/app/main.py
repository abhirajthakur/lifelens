from fastapi import FastAPI
from sqlalchemy import create_engine

from app.models.base import Base
from app.routers import media

app = FastAPI()
engine = create_engine(
    "postgresql://postgres:password@localhost:5432/lifelens_db", echo=True
)
Base.metadata.create_all(engine)

app.include_router(media.router)
