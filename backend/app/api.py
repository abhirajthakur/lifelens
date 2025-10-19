from fastapi import FastAPI

from app.routes import auth, chat, media


def register_routes(app: FastAPI):
    app.include_router(media.router)
    app.include_router(auth.router)
    app.include_router(chat.router)
