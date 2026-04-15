"""Database connection and session management."""

import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

logger = logging.getLogger(__name__)

# Create engine with connection pooling
# For SQLite: disable connection pooling and set check_same_thread=False
# For PostgreSQL: use normal connection pool
engine_kwargs = {
    "echo": (settings.LOG_LEVEL == "DEBUG"),
    "pool_pre_ping": True,  # Verify connections before using
}

if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        **engine_kwargs
    )
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        **engine_kwargs
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI to inject database session.
    Usage: @app.get("/endpoint")
           def endpoint(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables (create if not exist)."""
    try:
        logger.info("Initializing database...")
        logger.info(f"Database URL: {settings.DATABASE_URL[:50]}...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def check_db_connection():
    """Test database connection and return status."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False
