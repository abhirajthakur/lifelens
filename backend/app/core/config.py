from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or "postgresql://postgres:mysecretpassword@localhost:5432/lifelens_db"
)
SECRET_KEY = os.getenv("SECRET_KEY") or "supersecretjwtkey"
API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL") or "redis://localhost:6379"
