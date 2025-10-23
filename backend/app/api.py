import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, chat, media

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL") or "http://localhost:5173"
origins = [
    FRONTEND_URL,
]


def register_routes(app: FastAPI):
    app.include_router(media.router)
    app.include_router(auth.router)
    app.include_router(chat.router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
