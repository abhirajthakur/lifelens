from fastapi import FastAPI

from app.routes import auth, media, query


def register_routes(app: FastAPI):
    app.include_router(media.router)
    app.include_router(auth.router)
    app.include_router(query.router)
