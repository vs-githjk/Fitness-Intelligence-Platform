from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import AssessmentOut, AssessmentSaveRequest, HealthIndexOut
from app.security import ensure_not_demo, require_trainee
from app.services import (
    assessment_out,
    current_assessment,
    health_out,
    save_assessment,
    submit_assessment,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/onboarding", response_model=AssessmentOut)
def get_onboarding(user: User = Depends(require_trainee), db: Session = Depends(get_db)) -> dict:
    assessment = current_assessment(db, user.id)
    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_started", "message": "No onboarding assessment has been started"},
        )
    return assessment_out(assessment)


@router.put("/onboarding", response_model=AssessmentOut)
def put_onboarding(
    body: AssessmentSaveRequest,
    user: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(user)
    return assessment_out(save_assessment(db, user, body.responses))


@router.post("/onboarding/submit", response_model=HealthIndexOut)
def submit_onboarding(user: User = Depends(require_trainee), db: Session = Depends(get_db)) -> dict:
    ensure_not_demo(user)
    return health_out(db, submit_assessment(db, user))
