import os
import pathlib
import uuid

from dotenv import load_dotenv
from sqlalchemy import CHAR, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

DEFAULT_SQLITE_PATH = os.path.abspath(
    pathlib.Path(__file__).parent.parent / "app.db"
)

if not DATABASE_URL:
    print(
        "WARNING: DATABASE_URL is not set. Falling back to local SQLite database.")
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        if dialect.name == "postgresql":
            return str(value) if isinstance(value, uuid.UUID) else value

        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return uuid.UUID(value) if isinstance(value, str) else value


connect_args = {
    "check_same_thread": False
} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()