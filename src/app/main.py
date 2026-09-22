from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth.routes import router as auth_router
from app.gamification.routes import router as gamification_router
from app.upload.routes import router as upload_router
from app.db.models import get_db

app = FastAPI(title="RecycleSort", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:43180"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

""" init_db() is not needed anymore because Alembic is used for migrations. 
The database will be initialized automatically when the application starts.
@app.on_event("startup")
def on_startup() -> None:
    init_db()
"""

@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Health check for API + DB.
    Load balancer will use this endpoint to check if the API is healthy and ready to serve requests.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return {"status": "error", "db": "unreachable"}


app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(gamification_router)
