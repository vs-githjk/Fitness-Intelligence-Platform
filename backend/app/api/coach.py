import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.avatar_services import avatar_url_for
from app.daily_services import (
    bounded_dates,
    build_trends,
    check_in_history,
    daily_score_out,
    daily_score_summary,
    latest_daily_score,
    score_history,
)
from app.database import get_db
from app.models import RiskAlert, TraineeProfile, User
from app.schemas import (
    CoachTraineeDetail,
    CoachTraineeSummary,
    DailyCheckInOut,
    DailyScoreOut,
    DailyScoreSummaryOut,
    DailyTrendsOut,
    HealthIndexOut,
)
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
        "avatar_url": avatar_url_for(db, trainee_id),
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
        select(RiskAlert).where(
            RiskAlert.trainee_id.in_(trainee_ids),
            RiskAlert.health_index_snapshot_id.is_not(None),
            RiskAlert.status == "open",
        )
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


@router.get(
    "/trainees/{trainee_id}/check-ins", response_model=list[DailyCheckInOut]
)
def trainee_check_ins(
    trainee_id: uuid.UUID,
    days: int = Query(default=7),
    end_date: date | None = Query(default=None),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> list:
    assert_assignment(db, coach.id, trainee_id)
    start, end = bounded_dates(db, trainee_id, days, end_date)
    return check_in_history(db, trainee_id, start, end)


@router.get(
    "/trainees/{trainee_id}/daily-scores", response_model=list[DailyScoreSummaryOut]
)
def trainee_daily_scores(
    trainee_id: uuid.UUID,
    days: int = Query(default=7),
    end_date: date | None = Query(default=None),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> list[dict]:
    assert_assignment(db, coach.id, trainee_id)
    start, end = bounded_dates(db, trainee_id, days, end_date)
    return [daily_score_summary(item) for item in score_history(db, trainee_id, start, end)]


@router.get("/trainees/{trainee_id}/daily-score-latest", response_model=DailyScoreOut)
def trainee_latest_daily_score(
    trainee_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    assert_assignment(db, coach.id, trainee_id)
    snapshot = latest_daily_score(db, trainee_id)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "daily_score_missing", "message": "The trainee has no daily score"},
        )
    return daily_score_out(snapshot)


@router.get("/trainees/{trainee_id}/trends", response_model=DailyTrendsOut)
def trainee_trends(
    trainee_id: uuid.UUID,
    days: int = Query(default=7),
    end_date: date | None = Query(default=None),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    assert_assignment(db, coach.id, trainee_id)
    start, end = bounded_dates(db, trainee_id, days, end_date)
    return build_trends(db, trainee_id, start, end)


@router.get("/daily-alerts")
def daily_alerts(
    coach: User = Depends(require_coach), db: Session = Depends(get_db)
) -> list[dict]:
    trainee_ids = [item["trainee_id"] for item in coach_trainee_summaries(db, coach.id)]
    if not trainee_ids:
        return []
    alerts = db.scalars(
        select(RiskAlert).where(
            RiskAlert.trainee_id.in_(trainee_ids),
            RiskAlert.daily_score_snapshot_id.is_not(None),
            RiskAlert.status == "open",
        )
    ).all()
    return [
        {
            "id": item.id,
            "trainee_id": item.trainee_id,
            "daily_score_snapshot_id": item.daily_score_snapshot_id,
            "rule_key": item.rule_key,
            "rule_version": item.rule_version,
            "severity": item.severity,
            "status": item.status,
            "title": item.title,
            "explanation": item.explanation,
            "recommended_action": item.recommended_action,
            "triggering_inputs": item.input_snapshot,
            "triggered_at": item.triggered_at,
            "resolved_at": item.resolved_at,
        }
        for item in alerts
    ]
