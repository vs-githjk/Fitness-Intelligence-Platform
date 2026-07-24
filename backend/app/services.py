import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.domain.recommendations import build_recommendations
from app.domain.risk import evaluate_risks
from app.domain.scoring import calculate_health_index
from app.models import (
    AssessmentStatus,
    CoachTraineeAssignment,
    DailyCheckIn,
    DailyScoreSnapshot,
    HealthIndexSnapshot,
    OnboardingAssessment,
    RiskAlert,
    ScoreComponentSnapshot,
    TraineeProfile,
    User,
)
from app.schemas import REQUIRED_ASSESSMENT_FIELDS, AssessmentData


def missing_required(data: dict) -> list[str]:
    return [key for key in REQUIRED_ASSESSMENT_FIELDS if data.get(key) is None]


def assessment_out(assessment: OnboardingAssessment) -> dict:
    return {
        "id": assessment.id,
        "status": assessment.status.value,
        "schema_version": assessment.schema_version,
        "responses": assessment.responses,
        "missing_required_fields": missing_required(assessment.responses),
        "submitted_at": assessment.submitted_at,
        "updated_at": assessment.updated_at,
    }


def current_assessment(db: Session, trainee_id: uuid.UUID) -> OnboardingAssessment | None:
    return db.scalar(
        select(OnboardingAssessment)
        .where(OnboardingAssessment.trainee_id == trainee_id)
        .order_by(desc(OnboardingAssessment.created_at))
        .limit(1)
    )


def current_snapshot(db: Session, trainee_id: uuid.UUID) -> HealthIndexSnapshot | None:
    return db.scalar(
        select(HealthIndexSnapshot)
        .where(HealthIndexSnapshot.trainee_id == trainee_id)
        .order_by(desc(HealthIndexSnapshot.calculated_at))
        .limit(1)
    )


def assert_assignment(db: Session, coach_id: uuid.UUID, trainee_id: uuid.UUID) -> None:
    assigned = db.scalar(
        select(CoachTraineeAssignment.id).where(
            CoachTraineeAssignment.coach_id == coach_id,
            CoachTraineeAssignment.trainee_id == trainee_id,
            CoachTraineeAssignment.status == "active",
        )
    )
    if not assigned:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "not_assigned",
                "message": "This trainee is not assigned to the current coach",
            },
        )


def save_assessment(db: Session, trainee: User, validated: AssessmentData) -> OnboardingAssessment:
    assessment = current_assessment(db, trainee.id)
    if assessment is None or assessment.status == AssessmentStatus.SUBMITTED:
        assessment = OnboardingAssessment(trainee_id=trainee.id, responses={})
        db.add(assessment)
    assessment.responses = validated.model_dump(mode="json")
    profile = db.scalar(select(TraineeProfile).where(TraineeProfile.user_id == trainee.id))
    if profile:
        for key in ("age", "height_cm", "weight_kg", "selected_goal", "target_weight_kg"):
            setattr(profile, key, getattr(validated, key))
    db.commit()
    db.refresh(assessment)
    return assessment


def submit_assessment(db: Session, trainee: User) -> HealthIndexSnapshot:
    assessment = current_assessment(db, trainee.id)
    if assessment is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "assessment_missing",
                "message": "Save an onboarding draft before submitting",
            },
        )
    existing = db.scalar(
        select(HealthIndexSnapshot).where(HealthIndexSnapshot.assessment_id == assessment.id)
    )
    if existing:
        return existing
    missing = missing_required(assessment.responses)
    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "assessment_incomplete",
                "message": "Complete all required onboarding fields",
                "fields": {key: "Required" for key in missing},
            },
        )
    data = AssessmentData.model_validate(assessment.responses).model_dump(mode="json")
    score = calculate_health_index(data, REQUIRED_ASSESSMENT_FIELDS)
    risks = evaluate_risks(data)
    recommendations = build_recommendations(score, risks)
    now = datetime.now(UTC)
    payload = {
        **score,
        "risk_flags": [
            {**risk, "triggered_at": risk["triggered_at"].isoformat()} for risk in risks
        ],
        "recommendations": recommendations,
    }
    snapshot = HealthIndexSnapshot(
        trainee_id=trainee.id,
        assessment_id=assessment.id,
        overall_score=score["overall_score"],
        interpretation_band=score["band"],
        scoring_version=score["scoring_version"],
        calculation_payload=payload,
        calculated_at=now,
    )
    db.add(snapshot)
    db.flush()
    for item in score["components"]:
        db.add(
            ScoreComponentSnapshot(
                health_index_snapshot_id=snapshot.id,
                component_key=item["key"],
                normalized_score=item["normalized_score"],
                weight=item["weight"],
                weighted_contribution=item["weighted_contribution"],
                status=item["status"],
                explanation=item["explanation"],
                input_snapshot=item["raw_inputs"],
            )
        )
    for item in risks:
        db.add(
            RiskAlert(
                trainee_id=trainee.id,
                health_index_snapshot_id=snapshot.id,
                rule_key=item["rule_key"],
                severity=item["severity"],
                title=item["title"],
                explanation=item["explanation"],
                recommended_action=item["recommended_action"],
                input_snapshot=item["triggering_inputs"],
                rule_version=item["rule_version"],
                triggered_at=item["triggered_at"],
            )
        )
    assessment.status = AssessmentStatus.SUBMITTED
    assessment.submitted_at = now
    db.commit()
    db.refresh(snapshot)
    return snapshot


def health_out(db: Session, snapshot: HealthIndexSnapshot) -> dict:
    payload = snapshot.calculation_payload
    alerts = db.scalars(
        select(RiskAlert).where(RiskAlert.health_index_snapshot_id == snapshot.id)
    ).all()
    return {
        "id": snapshot.id,
        "trainee_id": snapshot.trainee_id,
        "assessment_id": snapshot.assessment_id,
        "overall_score": snapshot.overall_score,
        "band": snapshot.interpretation_band,
        "scoring_version": snapshot.scoring_version,
        "calculated_at": snapshot.calculated_at,
        "components": payload["components"],
        "missing_fields": payload["missing_fields"],
        "risk_flags": [
            {
                "rule_key": a.rule_key,
                "severity": a.severity,
                "status": a.status,
                "title": a.title,
                "explanation": a.explanation,
                "recommended_action": a.recommended_action,
                "triggering_inputs": a.input_snapshot,
                "rule_version": a.rule_version,
                "triggered_at": a.triggered_at,
            }
            for a in alerts
        ],
        "recommendations": payload["recommendations"],
    }


def coach_trainee_summaries(db: Session, coach_id: uuid.UUID) -> list[dict]:
    from app.avatar_services import avatar_url_for
    from app.daily_services import local_today

    trainees = db.scalars(
        select(User)
        .join(CoachTraineeAssignment, CoachTraineeAssignment.trainee_id == User.id)
        .where(
            CoachTraineeAssignment.coach_id == coach_id, CoachTraineeAssignment.status == "active"
        )
        .order_by(User.first_name)
    ).all()
    results = []
    for trainee in trainees:
        profile = db.scalar(select(TraineeProfile).where(TraineeProfile.user_id == trainee.id))
        assessment = current_assessment(db, trainee.id)
        snapshot = current_snapshot(db, trainee.id)
        baseline_alerts = (
            db.scalar(
                select(func.count(RiskAlert.id)).where(
                    RiskAlert.trainee_id == trainee.id,
                    RiskAlert.health_index_snapshot_id.is_not(None),
                    RiskAlert.status == "open",
                )
            )
            or 0
        )
        today, _timezone = local_today(db, trainee.id)
        latest_check_in = db.scalar(
            select(DailyCheckIn)
            .where(DailyCheckIn.trainee_id == trainee.id)
            .order_by(DailyCheckIn.local_date.desc())
            .limit(1)
        )
        latest_daily_score = db.scalar(
            select(DailyScoreSnapshot)
            .where(DailyScoreSnapshot.trainee_id == trainee.id)
            .order_by(DailyScoreSnapshot.local_date.desc())
            .limit(1)
        )
        daily_alerts = (
            db.scalar(
                select(func.count(RiskAlert.id)).where(
                    RiskAlert.trainee_id == trainee.id,
                    RiskAlert.daily_score_snapshot_id.is_not(None),
                    RiskAlert.status == "open",
                )
            )
            or 0
        )
        results.append(
            {
                "trainee_id": trainee.id,
                "name": f"{trainee.first_name} {trainee.last_name}",
                "email": trainee.email,
                "selected_goal": profile.selected_goal if profile else None,
                "assessment_status": assessment.status.value if assessment else "not_started",
                "assessment_updated_at": assessment.updated_at if assessment else None,
                "current_score": snapshot.overall_score if snapshot else None,
                "band": snapshot.interpretation_band if snapshot else None,
                "baseline_calculated_at": snapshot.calculated_at if snapshot else None,
                "open_alerts": baseline_alerts,
                "latest_check_in_date": latest_check_in.local_date if latest_check_in else None,
                "latest_check_in_at": latest_check_in.updated_at if latest_check_in else None,
                "latest_readiness_score": (
                    latest_daily_score.readiness_score if latest_daily_score else None
                ),
                "latest_readiness_state": (
                    latest_daily_score.readiness_state if latest_daily_score else None
                ),
                "checked_in_today": bool(
                    latest_check_in and latest_check_in.local_date == today
                ),
                "open_daily_alerts": daily_alerts,
                "avatar_url": avatar_url_for(db, trainee.id),
            }
        )
    return results
