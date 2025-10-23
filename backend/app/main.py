from fastapi import FastAPI

from app.api import register_routes
from app.logging import configure_logging

configure_logging()

app = FastAPI()


register_routes(app)
