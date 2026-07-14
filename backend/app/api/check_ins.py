from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.daily_services import (
    bounded_dates,
    check_in_history,
    get_check_in,
    local_today,
    save_today_check_in,
)
from app.database import get_db
from app.models import User
from app.schemas import DailyCheckInData, DailyCheckInOut
from app.security import require_trainee

router = APIRouter(prefix="/check-ins", tags=["daily check-ins"])


def _missing() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "code": "check_in_missing",
            "message": "No check-in has been submitted for this local date",
        },
    )


@router.get("/today", response_model=DailyCheckInOut)
def today_check_in(
    trainee: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> DailyCheckInOut:
    today, _ = local_today(db, trainee.id)
    item = get_check_in(db, trainee.id, today)
    if item is None:
        raise _missing()
    return item


@router.put("/today", response_model=DailyCheckInOut)
def put_today_check_in(
    body: DailyCheckInData,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> DailyCheckInOut:
    item, _score = save_today_check_in(db, trainee, body)
    return item


@router.get("", response_model=list[DailyCheckInOut])
def check_ins(
    days: int = Query(default=7),
    end_date: date | None = Query(default=None),
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> list[DailyCheckInOut]:
    start, end = bounded_dates(db, trainee.id, days, end_date)
    return check_in_history(db, trainee.id, start, end)


@router.get("/{local_date}", response_model=DailyCheckInOut)
def check_in_by_date(
    local_date: date,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> DailyCheckInOut:
    today, _ = local_today(db, trainee.id)
    if local_date > today:
        raise HTTPException(
            status_code=422,
            detail={"code": "future_date", "message": "Future check-ins are not available"},
        )
    item = get_check_in(db, trainee.id, local_date)
    if item is None:
        raise _missing()
    return item
