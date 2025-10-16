from dotenv import load_dotenv
import os

load_dotenv()

API_V1_STR = "/api/v1"
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or "postgresql://postgres:mysecretpassword@localhost:5432/lifelens_db"
)
SECRET_KEY = os.getenv("SECRET_KEY") or "supersecretjwtkey"
API_KEY = os.getenv("GEMINI_API_KEY")
