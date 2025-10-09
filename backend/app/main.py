from fastapi import FastAPI
from dotenv import load_dotenv
from app.api import register_routes
from app.logging import configure_logging

configure_logging()
load_dotenv()

app = FastAPI()


register_routes(app)
