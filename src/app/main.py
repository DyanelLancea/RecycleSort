from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.db.models import init_db
from app.gamification.routes import router as gamification_router
from app.upload.routes import router as upload_router

app = FastAPI(title="RecycleSort", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    """AWS Application Load Balancer health check."""
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(gamification_router)
