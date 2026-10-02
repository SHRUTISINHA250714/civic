from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# For PostgreSQL connection (Local or Neon Cloud)
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    # pool_pre_ping checks connection health before executing commands (critical for serverless DBs like Neon)
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=300,  # Recycle connections every 5 minutes to prevent stale idle disconnects
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
