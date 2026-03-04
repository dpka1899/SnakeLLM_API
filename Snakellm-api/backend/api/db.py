from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from api.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def ensure_db():
    # create tables if they don't exist
    from api.models import Job  # noqa: F401
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()