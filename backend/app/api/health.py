import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import HealthIndexSnapshot, User
from app.schemas import HealthIndexOut
from app.security import require_trainee
from app.services import current_snapshot, health_out

router = APIRouter(prefix="/health-index", tags=["health index"])


@router.get("/current", response_model=HealthIndexOut)
def get_current(user: User = Depends(require_trainee), db: Session = Depends(get_db)) -> dict:
    snapshot = current_snapshot(db, user.id)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "baseline_missing",
                "message": "Submit onboarding to create a baseline",
            },
        )
    return health_out(db, snapshot)


@router.get("/history", response_model=list[HealthIndexOut])
def get_history(user: User = Depends(require_trainee), db: Session = Depends(get_db)) -> list[dict]:
    snapshots = db.scalars(
        select(HealthIndexSnapshot)
        .where(HealthIndexSnapshot.trainee_id == user.id)
        .order_by(desc(HealthIndexSnapshot.calculated_at))
    ).all()
    return [health_out(db, item) for item in snapshots]


@router.get("/{snapshot_id}", response_model=HealthIndexOut)
def get_snapshot(
    snapshot_id: uuid.UUID, user: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> dict:
    snapshot = db.get(HealthIndexSnapshot, snapshot_id)
    if snapshot is None or snapshot.trainee_id != user.id:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Health index snapshot not found"},
        )
    return health_out(db, snapshot)
