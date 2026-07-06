from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.config import settings

# SQLite URL config
database_url = f"sqlite:///{settings.database_path}"

# SQLite specific connect args: disable check_same_thread for multiple threads
engine = create_engine(
    database_url, connect_args={"check_same_thread": False}, echo=False
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
