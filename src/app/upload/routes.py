from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.jwt_middleware import get_current_user
from app.db.models import User, get_db
from app.gamification.service import record_scan
from app.ml.service import infer
from app.upload.validation import validate_upload

router = APIRouter(prefix="/api", tags=["upload"])


class ScanResult(BaseModel):
    predicted_class: str
    confidence: float
    is_recyclable: bool
    points_awarded: int
    total_points: int
    model_loaded: bool


@router.post("/upload", response_model=ScanResult)
async def upload_image(
    file: UploadFile | None = File(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScanResult:
    raw = await file.read() if file is not None else b""
    validate_upload(file, raw)
    result = infer(raw, file.filename or "")
    log = record_scan(db, user, result)
    return ScanResult(
        predicted_class=result.predicted_class,
        confidence=result.confidence,
        is_recyclable=result.is_recyclable,
        points_awarded=log.points_awarded,
        total_points=user.points,
        model_loaded=result.model_loaded,
    )
