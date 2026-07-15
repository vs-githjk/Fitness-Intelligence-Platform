import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.invitations import generate_invite_token, hash_invite_token, invite_out, invite_status
from app.models import CoachInvite, User
from app.schemas import CoachInviteCreate, CoachInviteCreatedOut, CoachInviteOut
from app.security import ensure_not_demo, require_coach

router = APIRouter(prefix="/coach/invites", tags=["coach invitations"])


@router.get("", response_model=list[CoachInviteOut])
def list_invites(
    coach: User = Depends(require_coach), db: Session = Depends(get_db)
) -> list[dict]:
    invites = db.scalars(
        select(CoachInvite)
        .where(CoachInvite.coach_id == coach.id)
        .order_by(CoachInvite.created_at.desc())
    ).all()
    return [invite_out(item) for item in invites]


@router.post("", response_model=CoachInviteCreatedOut, status_code=201)
def create_invite(
    body: CoachInviteCreate,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    token = generate_invite_token()
    now = datetime.now(UTC)
    invite = CoachInvite(
        coach_id=coach.id,
        token_hash=hash_invite_token(token),
        intended_email=body.intended_email.lower() if body.intended_email else None,
        expires_at=now + timedelta(days=body.expires_in_days),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return {**invite_out(invite), "token": token}


@router.post("/{invite_id}/revoke", response_model=CoachInviteOut)
def revoke_invite(
    invite_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    invite = db.scalar(
        select(CoachInvite)
        .where(CoachInvite.id == invite_id, CoachInvite.coach_id == coach.id)
        .with_for_update()
    )
    if invite is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Invitation not found"},
        )
    if invite_status(invite) != "active":
        raise HTTPException(
            status_code=409,
            detail={"code": "invite_inactive", "message": "Only active invitations can be revoked"},
        )
    invite.revoked_at = datetime.now(UTC)
    db.commit()
    db.refresh(invite)
    return invite_out(invite)
