from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import WorkoutImportRequest
from app.security import require_coach
from app.workout_import_services import preview_workout_import

router = APIRouter(prefix="/coach/workout-imports", tags=["workout import"])


@router.post("/preview")
def preview(
    body: WorkoutImportRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    # Read-only: parses and matches against the coach's library and returns a preview.
    # Nothing is created here, so no demo guard is needed — a demo coach may preview.
    # The coach resolves matches in the UI, then the normal workout-template create
    # endpoint (demo-protected) builds the draft.
    return preview_workout_import(db, coach, body.content, body.template_name, body.format)
