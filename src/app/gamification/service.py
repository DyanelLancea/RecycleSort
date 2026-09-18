from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import ScanLog, User
from app.ml.service import InferenceResult

POINTS_PER_SCAN = 1
POINTS_RECYCLABLE_BONUS = 4


def award_points(is_recyclable: bool) -> int:
    total = POINTS_PER_SCAN
    if is_recyclable:
        total += POINTS_RECYCLABLE_BONUS
    return total


def record_scan(db: Session, user: User, result: InferenceResult) -> ScanLog:
    points = award_points(result.is_recyclable)
    log = ScanLog(
        user_id=user.id,
        predicted_class=result.predicted_class,
        confidence=result.confidence,
        is_recyclable=result.is_recyclable,
        points_awarded=points,
        created_at=datetime.now(timezone.utc),
    )
    user.points += points
    db.add(log)
    db.commit()
    db.refresh(log)
    db.refresh(user)
    return log
