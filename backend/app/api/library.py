"""Curated starter-library API: browse, preview, and clone-to-edit.

Read endpoints are coach-only and expose only the read-only, system-owned library.
The single mutation clones a starter Program into a coach-owned draft; it is
demo-protected and registered in the central demo-mutation inventory. There are no
update or delete routes for system content.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.library_services import (
    clone_library_program,
    get_library_program,
    list_library_programs,
)
from app.models import User
from app.schemas import (
    LibraryProgramDetailOut,
    LibraryProgramListOut,
    TrainingProgramDetailOut,
)
from app.security import ensure_not_demo, require_coach

router = APIRouter(prefix="/program-library", tags=["program library"])


@router.get("", response_model=LibraryProgramListOut)
def browse(
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return list_library_programs(db)


@router.get("/{program_id}", response_model=LibraryProgramDetailOut)
def detail(
    program_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return get_library_program(db, program_id)


@router.post("/{program_id}/clone", response_model=TrainingProgramDetailOut, status_code=201)
def clone(
    program_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return clone_library_program(db, coach, program_id)
