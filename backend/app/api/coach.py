import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RiskAlert, TraineeProfile, User
from app.schemas import CoachTraineeDetail, CoachTraineeSummary, HealthIndexOut
from app.security import require_coach
from app.services import (
    assert_assignment,
    assessment_out,
    coach_trainee_summaries,
    current_assessment,
    current_snapshot,
    health_out,
)

router = APIRouter(prefix="/coach", tags=["coach"])


@router.get("/trainees", response_model=list[CoachTraineeSummary])
def trainees(coach: User = Depends(require_coach), db: Session = Depends(get_db)) -> list[dict]:
    return coach_trainee_summaries(db, coach.id)


@router.get("/trainees/{trainee_id}", response_model=CoachTraineeDetail)
def trainee_detail(
    trainee_id: uuid.UUID, coach: User = Depends(require_coach), db: Session = Depends(get_db)
) -> dict:
    assert_assignment(db, coach.id, trainee_id)
    trainee = db.get(User, trainee_id)
    if trainee is None:
        raise HTTPException(
            status_code=404, detail={"code": "not_found", "message": "Trainee not found"}
        )
    profile = db.scalar(select(TraineeProfile).where(TraineeProfile.user_id == trainee_id))
    assessment = current_assessment(db, trainee_id)
    snapshot = current_snapshot(db, trainee_id)
    return {
        "trainee": trainee,
        "profile": profile,
        "assessment_status": assessment.status.value if assessment else "not_started",
        "assessment": assessment_out(assessment) if assessment else None,
        "health_index": health_out(db, snapshot) if snapshot else None,
    }


@router.get("/trainees/{trainee_id}/health-index", response_model=HealthIndexOut)
def trainee_health(
    trainee_id: uuid.UUID, coach: User = Depends(require_coach), db: Session = Depends(get_db)
) -> dict:
    assert_assignment(db, coach.id, trainee_id)
    snapshot = current_snapshot(db, trainee_id)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "baseline_missing", "message": "The trainee has no baseline yet"},
        )
    return health_out(db, snapshot)


@router.get("/risk-alerts")
def risk_alerts(coach: User = Depends(require_coach), db: Session = Depends(get_db)) -> list[dict]:
    trainee_ids = [item["trainee_id"] for item in coach_trainee_summaries(db, coach.id)]
    if not trainee_ids:
        return []
    alerts = db.scalars(
        select(RiskAlert).where(RiskAlert.trainee_id.in_(trainee_ids), RiskAlert.status == "open")
    ).all()
    return [
        {
            "id": a.id,
            "trainee_id": a.trainee_id,
            "rule_key": a.rule_key,
            "severity": a.severity,
            "title": a.title,
            "explanation": a.explanation,
            "recommended_action": a.recommended_action,
            "triggered_at": a.triggered_at,
        }
        for a in alerts
    ]
