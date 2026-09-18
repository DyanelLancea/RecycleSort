from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.jwt_middleware import get_current_user
from app.db.models import ScanLog, User, get_db
from app.secrets import admin_api_key

router = APIRouter(prefix="/api", tags=["gamification"])


class ProfileOut(BaseModel):
    id: int
    email: str
    points: int


class LogOut(BaseModel):
    id: int
    user_id: int
    user_email: str | None = None
    predicted_class: str
    confidence: float
    is_recyclable: bool
    points_awarded: int
    created_at: str


class LeaderboardRow(BaseModel):
    email: str
    points: int


@router.get("/profile", response_model=ProfileOut)
def profile(user: User = Depends(get_current_user)) -> ProfileOut:
    return ProfileOut(id=user.id, email=user.email, points=user.points)


@router.get("/logs/me", response_model=list[LogOut])
def my_logs(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[LogOut]:
    rows = (
        db.query(ScanLog)
        .filter(ScanLog.user_id == user.id)
        .order_by(ScanLog.created_at.desc())
        .limit(50)
        .all()
    )
    return [_log_out(row, user.email) for row in rows]


def _require_admin(x_admin_key: str | None) -> None:
    expected = admin_api_key()
    if not x_admin_key or x_admin_key != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin API key required")


@router.get("/admin/logs", response_model=list[LogOut])
def admin_logs(
    db: Session = Depends(get_db),
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> list[LogOut]:
    _require_admin(x_admin_key)
    rows = db.query(ScanLog).order_by(ScanLog.created_at.desc()).limit(200).all()
    users = {u.id: u.email for u in db.query(User).all()}
    return [_log_out(row, users.get(row.user_id)) for row in rows]


@router.get("/admin/leaderboard", response_model=list[LeaderboardRow])
def admin_leaderboard(
    db: Session = Depends(get_db),
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> list[LeaderboardRow]:
    _require_admin(x_admin_key)
    rows = db.query(User).order_by(User.points.desc(), User.email.asc()).limit(50).all()
    return [LeaderboardRow(email=u.email, points=u.points) for u in rows]


def _log_out(row: ScanLog, email: str | None) -> LogOut:
    return LogOut(
        id=row.id,
        user_id=row.user_id,
        user_email=email,
        predicted_class=row.predicted_class,
        confidence=row.confidence,
        is_recyclable=row.is_recyclable,
        points_awarded=row.points_awarded,
        created_at=row.created_at.isoformat(),
    )
