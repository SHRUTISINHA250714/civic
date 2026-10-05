from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

import time
import logging
from sqlalchemy import event

logger = logging.getLogger(__name__)

# For PostgreSQL connection (Local or Neon Cloud serverless pooler)
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    # pool_pre_ping checks connection health before executing commands (critical for serverless DBs like Neon)
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=60,  # Recycle connections every 60s to prevent stale serverless pooler drops
    connect_args={
        "connect_timeout": 15,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)

@event.listens_for(engine, "do_connect")
def receive_do_connect(dialect, conn_rec, cargs, cparams):
    """
    Automatic retry with backoff for transient serverless connection drops
    (such as Neon compute wakeup or pooler reset).
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return dialect.connect(*cargs, **cparams)
        except Exception as exc:
            err_str = str(exc).lower()
            transient_triggers = [
                "closed the connection",
                "terminated abnormally",
                "connection reset",
                "terminat",
                "could not connect",
                "timeout",
                "refused"
            ]
            if attempt < max_retries - 1 and any(msg in err_str for msg in transient_triggers):
                sleep_secs = 0.6 * (attempt + 1)
                logger.warning(
                    "Database connection attempt %d/%d encountered transient error: %s. Retrying in %.1fs...",
                    attempt + 1, max_retries, exc, sleep_secs
                )
                time.sleep(sleep_secs)
            else:
                raise exc


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
