from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.daily_services import (
    bounded_dates,
    build_trends,
    daily_score_out,
    daily_score_summary,
    latest_daily_score,
    local_today,
    score_history,
)
from app.database import get_db
from app.models import User
from app.schemas import DailyScoreOut, DailyScoreSummaryOut, DailyTrendsOut
from app.security import require_trainee

router = APIRouter(prefix="/daily-scores", tags=["daily intelligence"])


@router.get("/today", response_model=DailyScoreOut)
def today_score(
    trainee: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> dict:
    today, _ = local_today(db, trainee.id)
    snapshot = latest_daily_score(db, trainee.id, today)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "daily_score_missing",
                "message": "Submit today's check-in to calculate daily intelligence",
            },
        )
    return daily_score_out(snapshot)


@router.get("/trends", response_model=DailyTrendsOut)
def trends(
    days: int = Query(default=7),
    end_date: date | None = Query(default=None),
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    start, end = bounded_dates(db, trainee.id, days, end_date)
    return build_trends(db, trainee.id, start, end)


@router.get("", response_model=list[DailyScoreSummaryOut])
def daily_scores(
    days: int = Query(default=7),
    end_date: date | None = Query(default=None),
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> list[dict]:
    start, end = bounded_dates(db, trainee.id, days, end_date)
    return [daily_score_summary(item) for item in score_history(db, trainee.id, start, end)]
