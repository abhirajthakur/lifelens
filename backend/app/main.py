from fastapi import FastAPI

from app.routes import auth, media

app = FastAPI()

app.include_router(media.router)
app.include_router(auth.router)
