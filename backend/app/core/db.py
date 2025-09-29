from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/lifelens_db"
engine = create_engine(DATABASE_URL, echo=True)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
