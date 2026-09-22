from app.db.models import SessionLocal, get_db

# init_db not called anymore cause alembic migrations are used 
# to create the database schema instead of creating it on startup. 
# This is to avoid issues with multiple instances of the app trying 
# to create the database at the same time, which can cause race conditions and errors.
__all__ = ["SessionLocal", "get_db"]


