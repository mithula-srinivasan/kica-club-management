from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import setting


def sqlalchemy_url(url: str) -> str:
    """Render gives "postgresql://..." (older services: "postgres://...").
    SQLAlchemy needs "postgresql+psycopg://..." to use psycopg 3, which we installed."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]

    return url


DATABASE_URL = sqlalchemy_url(
    setting("DATABASE_URL", "postgresql+psycopg:///kica_club_management")
)

# pool_pre_ping: check a connection still works before using it,
# because the database server can close idle connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass