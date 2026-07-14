import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.daily_recommendations import build_daily_recommendations
from app.domain.daily_risk import evaluate_daily_risks
from app.domain.daily_scoring import SCORING_VERSION, calculate_daily_scores
from app.models import (
    AssessmentStatus,
    DailyCheckIn,
    DailyScoreComponent,
    DailyScoreSnapshot,
    OnboardingAssessment,
    RiskAlert,
    TraineeProfile,
    User,
)
from app.schemas import DailyCheckInData


def trainee_timezone(db: Session, trainee_id: uuid.UUID) -> ZoneInfo:
    timezone_name = db.scalar(
        select(TraineeProfile.timezone).where(TraineeProfile.user_id == trainee_id)
    ) or "UTC"
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "invalid_profile_timezone",
                "message": "Update the trainee profile with a valid IANA timezone",
            },
        ) from exc


def local_today(
    db: Session, trainee_id: uuid.UUID, now: datetime | None = None
) -> tuple[date, str]:
    timezone = trainee_timezone(db, trainee_id)
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(timezone).date(), timezone.key


def baseline_context(db: Session, trainee_id: uuid.UUID) -> dict | None:
    assessment = db.scalar(
        select(OnboardingAssessment)
        .where(
            OnboardingAssessment.trainee_id == trainee_id,
            OnboardingAssessment.status == AssessmentStatus.SUBMITTED,
        )
        .order_by(OnboardingAssessment.submitted_at.desc())
        .limit(1)
    )
    if assessment:
        return assessment.responses
    profile = db.scalar(select(TraineeProfile).where(TraineeProfile.user_id == trainee_id))
    if profile and profile.weight_kg and profile.selected_goal:
        return {
            "weight_kg": profile.weight_kg,
            "selected_goal": profile.selected_goal,
            "protein_target_g": None,
        }
    return None


def _check_in_dict(item: DailyCheckIn) -> dict:
    return {
        "local_date": item.local_date,
        "sleep_hours": item.sleep_hours,
        "sleep_quality": item.sleep_quality,
        "wake_refreshed": item.wake_refreshed,
        "soreness": item.soreness,
        "fatigue": item.fatigue,
        "stress": item.stress,
        "steps": item.steps,
        "exercised": item.exercised,
        "exercise_minutes": item.exercise_minutes,
        "session_rpe": item.session_rpe,
        "activity_types": item.activity_types,
        "water_liters": item.water_liters,
        "protein_grams": item.protein_grams,
    }


def get_check_in(db: Session, trainee_id: uuid.UUID, local_date: date) -> DailyCheckIn | None:
    return db.scalar(
        select(DailyCheckIn).where(
            DailyCheckIn.trainee_id == trainee_id, DailyCheckIn.local_date == local_date
        )
    )


def _history_records(
    db: Session,
    trainee_id: uuid.UUID,
    end_date: date,
    baseline: dict | None,
    days: int = 30,
) -> list[dict]:
    check_ins = db.scalars(
        select(DailyCheckIn)
        .where(
            DailyCheckIn.trainee_id == trainee_id,
            DailyCheckIn.local_date >= end_date - timedelta(days=days - 1),
            DailyCheckIn.local_date <= end_date,
        )
        .order_by(DailyCheckIn.local_date)
    ).all()
    snapshots = {
        item.local_date: item
        for item in db.scalars(
            select(DailyScoreSnapshot).where(
                DailyScoreSnapshot.trainee_id == trainee_id,
                DailyScoreSnapshot.local_date >= end_date - timedelta(days=days - 1),
                DailyScoreSnapshot.local_date <= end_date,
                DailyScoreSnapshot.scoring_version == SCORING_VERSION,
            )
        ).all()
    }
    target_liters = None
    protein_target = (baseline or {}).get("protein_target_g")
    if (baseline or {}).get("weight_kg") and (baseline or {}).get("selected_goal"):
        from app.domain.scoring import hydration_target_ml

        target_liters = hydration_target_ml(
            baseline["weight_kg"], baseline["selected_goal"]
        ) / 1000
    records = []
    for item in check_ins:
        record = _check_in_dict(item)
        record["hydration_ratio"] = (
            item.water_liters / target_liters if target_liters else None
        )
        record["protein_ratio"] = (
            item.protein_grams / protein_target
            if protein_target and item.protein_grams is not None
            else None
        )
        record["recovery_score"] = (
            snapshots[item.local_date].recovery_score if item.local_date in snapshots else None
        )
        records.append(record)
    return records


def save_today_check_in(
    db: Session,
    trainee: User,
    validated: DailyCheckInData,
    now: datetime | None = None,
) -> tuple[DailyCheckIn, DailyScoreSnapshot]:
    current_time = now or datetime.now(UTC)
    today, timezone_name = local_today(db, trainee.id, current_time)
    check_in = get_check_in(db, trainee.id, today)
    if check_in is None:
        check_in = DailyCheckIn(
            trainee_id=trainee.id,
            local_date=today,
            timezone=timezone_name,
            submitted_at=current_time,
        )
        db.add(check_in)
    for key, value in validated.model_dump(mode="json").items():
        setattr(check_in, key, value)
    check_in.timezone = timezone_name
    check_in.updated_at = current_time
    try:
        db.flush()
        snapshot = calculate_and_store_daily_score(db, trainee.id, check_in, current_time)
        db.commit()
        db.refresh(check_in)
        db.refresh(snapshot)
        return check_in, snapshot
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "daily_check_in_conflict",
                "message": "A check-in already exists for this trainee-local date; reload and edit it",
            },
        ) from exc
    except Exception:
        db.rollback()
        raise


def calculate_and_store_daily_score(
    db: Session,
    trainee_id: uuid.UUID,
    check_in: DailyCheckIn,
    calculated_at: datetime | None = None,
) -> DailyScoreSnapshot:
    baseline = baseline_context(db, trainee_id)
    recent_items = db.scalars(
        select(DailyCheckIn)
        .where(
            DailyCheckIn.trainee_id == trainee_id,
            DailyCheckIn.local_date >= check_in.local_date - timedelta(days=6),
            DailyCheckIn.local_date <= check_in.local_date,
        )
        .order_by(DailyCheckIn.local_date)
    ).all()
    score = calculate_daily_scores(
        _check_in_dict(check_in), baseline, [_check_in_dict(item) for item in recent_items]
    )
    history = _history_records(db, trainee_id, check_in.local_date, baseline)
    for item in history:
        if item["local_date"] == check_in.local_date:
            item["recovery_score"] = score["recovery_score"]
    risks = evaluate_daily_risks(history, score)
    recommendations = build_daily_recommendations(score, risks)
    now = calculated_at or datetime.now(UTC)
    payload = {
        **score,
        "risk_flags": [{**item, "triggered_at": now.isoformat()} for item in risks],
        "recommendations": recommendations,
    }
    snapshot = db.scalar(
        select(DailyScoreSnapshot).where(
            DailyScoreSnapshot.daily_check_in_id == check_in.id,
            DailyScoreSnapshot.scoring_version == SCORING_VERSION,
        )
    )
    if snapshot is None:
        snapshot = DailyScoreSnapshot(
            trainee_id=trainee_id,
            daily_check_in_id=check_in.id,
            local_date=check_in.local_date,
            scoring_version=SCORING_VERSION,
        )
        db.add(snapshot)
    snapshot.recovery_score = score["recovery_score"]
    snapshot.activity_score = score["activity_score"]
    snapshot.nutrition_score = score["nutrition_score"]
    snapshot.readiness_score = score["readiness_score"]
    snapshot.readiness_state = score["readiness_state"]
    snapshot.calculation_payload = payload
    snapshot.calculated_at = now
    db.flush()
    db.execute(
        delete(DailyScoreComponent).where(
            DailyScoreComponent.daily_score_snapshot_id == snapshot.id
        )
    )
    for item in score["components"]:
        db.add(
            DailyScoreComponent(
                daily_score_snapshot_id=snapshot.id,
                component_key=item["key"],
                normalized_score=item["normalized_score"],
                weight=item["weight"],
                contribution=item["contribution"],
                status=item["status"],
                explanation=item["explanation"],
                input_snapshot=item["raw_inputs"],
            )
        )
    triggered_keys = {item["rule_key"] for item in risks}
    open_daily_alerts = db.scalars(
        select(RiskAlert).where(
            RiskAlert.trainee_id == trainee_id,
            RiskAlert.health_index_snapshot_id.is_(None),
            RiskAlert.status == "open",
        )
    ).all()
    by_rule = {item.rule_key: item for item in open_daily_alerts}
    for alert in open_daily_alerts:
        if alert.rule_key not in triggered_keys:
            alert.status = "resolved"
            alert.resolved_at = now
    for item in risks:
        alert = by_rule.get(item["rule_key"])
        if alert is None:
            alert = RiskAlert(
                trainee_id=trainee_id,
                rule_key=item["rule_key"],
                triggered_at=now,
            )
            db.add(alert)
        alert.daily_score_snapshot_id = snapshot.id
        alert.severity = item["severity"]
        alert.status = "open"
        alert.title = item["title"]
        alert.explanation = item["explanation"]
        alert.recommended_action = item["recommended_action"]
        alert.input_snapshot = item["triggering_inputs"]
        alert.rule_version = item["rule_version"]
        alert.resolved_at = None
    db.flush()
    return snapshot


def daily_score_summary(snapshot: DailyScoreSnapshot) -> dict:
    return {
        "id": snapshot.id,
        "trainee_id": snapshot.trainee_id,
        "daily_check_in_id": snapshot.daily_check_in_id,
        "local_date": snapshot.local_date,
        "recovery_score": snapshot.recovery_score,
        "activity_score": snapshot.activity_score,
        "nutrition_score": snapshot.nutrition_score,
        "readiness_score": snapshot.readiness_score,
        "readiness_state": snapshot.readiness_state,
        "scoring_version": snapshot.scoring_version,
        "calculated_at": snapshot.calculated_at,
    }


def daily_score_out(snapshot: DailyScoreSnapshot) -> dict:
    return {**daily_score_summary(snapshot), **snapshot.calculation_payload}


def latest_daily_score(
    db: Session, trainee_id: uuid.UUID, local_date: date | None = None
) -> DailyScoreSnapshot | None:
    query = select(DailyScoreSnapshot).where(
        DailyScoreSnapshot.trainee_id == trainee_id,
        DailyScoreSnapshot.scoring_version == SCORING_VERSION,
    )
    if local_date is not None:
        query = query.where(DailyScoreSnapshot.local_date == local_date)
    return db.scalar(query.order_by(DailyScoreSnapshot.local_date.desc()).limit(1))


def check_in_history(
    db: Session, trainee_id: uuid.UUID, start_date: date, end_date: date
) -> list[DailyCheckIn]:
    return list(
        db.scalars(
            select(DailyCheckIn)
            .where(
                DailyCheckIn.trainee_id == trainee_id,
                DailyCheckIn.local_date >= start_date,
                DailyCheckIn.local_date <= end_date,
            )
            .order_by(DailyCheckIn.local_date.desc())
        ).all()
    )


def score_history(
    db: Session, trainee_id: uuid.UUID, start_date: date, end_date: date
) -> list[DailyScoreSnapshot]:
    return list(
        db.scalars(
            select(DailyScoreSnapshot)
            .where(
                DailyScoreSnapshot.trainee_id == trainee_id,
                DailyScoreSnapshot.local_date >= start_date,
                DailyScoreSnapshot.local_date <= end_date,
                DailyScoreSnapshot.scoring_version == SCORING_VERSION,
            )
            .order_by(DailyScoreSnapshot.local_date.desc())
        ).all()
    )


def build_trends(
    db: Session, trainee_id: uuid.UUID, start_date: date, end_date: date
) -> dict:
    timezone_name = trainee_timezone(db, trainee_id).key
    check_ins = {
        item.local_date: item for item in check_in_history(db, trainee_id, start_date, end_date)
    }
    scores = {
        item.local_date: item for item in score_history(db, trainee_id, start_date, end_date)
    }
    definitions = [
        ("recovery_score", "Recovery Score", "points", scores),
        ("activity_score", "Activity Score", "points", scores),
        ("nutrition_score", "Nutrition Score", "points", scores),
        ("readiness_score", "Training Readiness", "points", scores),
        ("sleep_hours", "Sleep duration", "hours", check_ins),
        ("stress", "Stress", "0–10", check_ins),
        ("steps", "Steps", "steps", check_ins),
    ]
    day_count = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=offset) for offset in range(day_count)]
    series = []
    for key, label, unit, source in definitions:
        points = []
        recorded: list[float] = []
        previous: float | None = None
        for current_date in dates:
            record = source.get(current_date)
            value = getattr(record, key) if record is not None else None
            numeric = float(value) if value is not None else None
            difference = round(numeric - previous, 1) if numeric is not None and previous is not None else None
            if numeric is not None:
                recorded.append(numeric)
                previous = numeric
            rolling = round(sum(recorded[-7:]) / len(recorded[-7:]), 1) if recorded else None
            points.append(
                {
                    "date": current_date,
                    "value": numeric,
                    "missing": numeric is None,
                    "rolling_average": rolling if numeric is not None else None,
                    "difference_from_previous": difference,
                }
            )
        series.append({"key": key, "label": label, "unit": unit, "points": points})
    return {
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone_name,
        "series": series,
    }


def bounded_dates(
    db: Session,
    trainee_id: uuid.UUID,
    days: int,
    end_date: date | None = None,
) -> tuple[date, date]:
    if days not in {7, 14, 30}:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_range", "message": "Range must be 7, 14, or 30 days"},
        )
    today, _ = local_today(db, trainee_id)
    end = min(end_date or today, today)
    return end - timedelta(days=days - 1), end
