from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import require_analyst, require_api_key
from app.errors import NotFoundError
from app.modules.browse.overview import BrowseService
from app.modules.core.repository import JurisdictionRepository
from app.modules.recommender.builder import InvalidAnswers, build_profile, questions
from app.modules.recommender.models import Profile
from app.modules.saas.service import Principal

router = APIRouter(prefix="/v1", tags=["product"])


@router.get("/onboarding/questions")
def onboarding_questions(
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    return {
        "questions": [
            {
                "code": q.code,
                "text": q.text,
                "help": q.help,
                "kind": q.kind,
                "maps_to": q.maps_to,
                "options": q.options,
            }
            for q in questions(session)
        ],
        "jurisdictions": [
            {"code": j.code, "name": j.name}
            for j in sorted(JurisdictionRepository(session).list(), key=lambda j: j.name)
        ],
    }


class ProfileIn(BaseModel):
    answers: dict[str, Any]


def _profile_out(p: Profile) -> dict[str, Any]:
    return {"id": p.id, "answers": p.answers, "derived": p.derived}


@router.get("/profiles")
def list_profiles(
    limit: int = 50,
    org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    rows = session.scalars(
        select(Profile)
        .where(Profile.org_id == org_id)
        .order_by(Profile.id.desc())
        .limit(min(max(limit, 1), 200))
    )
    return [{**_profile_out(p), "created_at": p.created_at.isoformat()} for p in rows]


@router.post("/profiles", status_code=201)
def create_profile(
    body: ProfileIn,
    principal: Principal = Depends(require_analyst),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    org_id = principal.org_id
    try:
        answers, profile = build_profile(session, body.answers)
    except InvalidAnswers as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    row = Profile(org_id=org_id, answers=answers.to_json(), derived=profile.to_json())
    session.add(row)
    session.commit()
    return _profile_out(row)


def load_profile(session: Session, org_id: int, profile_id: int) -> Profile:
    row = session.get(Profile, profile_id)
    if row is None or row.org_id != org_id:
        raise NotFoundError("profile not found")
    return row


@router.get("/profiles/{profile_id}")
def get_profile(
    profile_id: int,
    org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    return _profile_out(load_profile(session, org_id, profile_id))


@router.get("/browse/corporate-tax")
def browse_corporate_tax(
    on_date: date | None = None,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    on = on_date or date.today()
    return {"on_date": on.isoformat(), "jurisdictions": BrowseService(session).corporate_tax(on)}


@router.get("/browse/jurisdictions/{code}")
def browse_jurisdiction(
    code: str,
    on_date: date | None = None,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    data = BrowseService(session).jurisdiction(code.upper(), on_date or date.today())
    if data is None:
        raise NotFoundError(f"jurisdiction {code} not found")
    return data


@router.get("/lists")
def lists(
    on_date: date | None = None,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    return BrowseService(session).lists(on_date or date.today())


@router.get("/evidence/{evidence_id}")
def evidence(
    evidence_id: int,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    data = BrowseService(session).evidence(evidence_id)
    if data is None:
        raise NotFoundError("evidence not found")
    return data
