from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import require_api_key
from app.errors import NotFoundError
from app.modules.core.repository import JurisdictionRepository

router = APIRouter(prefix="/v1/jurisdictions", tags=["jurisdictions"])


class JurisdictionOut(BaseModel):
    id: int
    code: str
    name: str


@router.get("", response_model=list[JurisdictionOut])
def list_jurisdictions(
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> list[JurisdictionOut]:
    repo = JurisdictionRepository(session)
    return [JurisdictionOut(id=j.id, code=j.code, name=j.name) for j in repo.list()]


@router.get("/{jurisdiction_id}", response_model=JurisdictionOut)
def get_jurisdiction(
    jurisdiction_id: int,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> JurisdictionOut:
    repo = JurisdictionRepository(session)
    j = repo.get(jurisdiction_id)
    if j is None:
        raise NotFoundError("jurisdiction not found")
    return JurisdictionOut(id=j.id, code=j.code, name=j.name)
