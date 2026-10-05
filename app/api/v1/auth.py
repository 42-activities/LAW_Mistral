from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import get_principal, require_admin
from app.errors import NotFoundError
from app.modules.saas import service
from app.modules.saas.models import ApiKey, AuditEvent, OrganisationAccount, User
from app.modules.saas.service import AuthError, Principal

router = APIRouter(prefix="/v1", tags=["accounts"])
Role = Literal["viewer", "analyst", "admin"]


def _user_out(u: User) -> dict[str, Any]:
    return {
        "id": u.id,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "active": u.active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
    }


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=200)


@router.post("/auth/login")
def login(body: LoginIn, session: Session = Depends(get_session)) -> dict[str, Any]:
    try:
        token, expires, user = service.login(session, body.email, body.password)
    except AuthError as exc:
        session.commit()  # keep the failed attempt for brute-force limiting
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    session.commit()
    return {"token": token, "expires_at": expires.isoformat(), "user": _user_out(user)}


@router.post("/auth/logout", status_code=204)
def logout(
    authorization: str | None = Header(default=None), session: Session = Depends(get_session)
) -> None:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() == "bearer" and token:
        service.logout(session, token.strip())
        session.commit()


@router.get("/auth/me")
def me(
    p: Principal = Depends(get_principal), session: Session = Depends(get_session)
) -> dict[str, Any]:
    org = session.get(OrganisationAccount, p.org_id)
    user = session.get(User, p.user_id) if p.user_id else None
    return {
        "organisation": {"id": p.org_id, "name": org.name if org else None},
        "role": p.role,
        "user": _user_out(user) if user else None,
        "api_key_id": p.api_key_id,
        "plan": service.usage_summary(session, p.org_id, 1)["plan"],
    }


class PasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=1, max_length=200)


@router.post("/auth/password", status_code=204)
def change_password(
    body: PasswordIn,
    p: Principal = Depends(get_principal),
    session: Session = Depends(get_session),
) -> None:
    if p.user_id is None:
        raise HTTPException(status_code=400, detail="API keys have no password")
    try:
        service.change_password(session, p.user_id, body.current_password, body.new_password)
    except AuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.commit()


# --- admin -------------------------------------------------------------------------------------

admin = require_admin


@router.get("/admin/users")
def list_users(
    p: Principal = Depends(admin), session: Session = Depends(get_session)
) -> list[dict[str, Any]]:
    rows = session.scalars(select(User).where(User.org_id == p.org_id).order_by(User.email))
    return [_user_out(u) for u in rows]


class UserIn(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: str | None = Field(default=None, max_length=200)
    role: Role = "analyst"
    password: str = Field(min_length=1, max_length=200)


@router.post("/admin/users", status_code=201)
def create_user(
    body: UserIn, p: Principal = Depends(admin), session: Session = Depends(get_session)
) -> dict[str, Any]:
    try:
        user = service.create_user(
            session, org_id=p.org_id, email=body.email, name=body.name, role=body.role,
            password=body.password, actor_id=p.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.commit()
    return _user_out(user)


class UserPatch(BaseModel):
    role: Role | None = None
    active: bool | None = None


@router.patch("/admin/users/{user_id}")
def update_user(
    user_id: int,
    body: UserPatch,
    p: Principal = Depends(admin),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    try:
        user = service.update_user(
            session, org_id=p.org_id, user_id=user_id, role=body.role, active=body.active,
            actor_id=p.user_id,
        )
    except LookupError as exc:
        raise NotFoundError(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.commit()
    return _user_out(user)


def _key_out(k: ApiKey) -> dict[str, Any]:
    return {
        "id": k.id,
        "name": k.name,
        "role": k.role,
        "active": k.active,
        "created_at": k.created_at.isoformat() if k.created_at else None,
        "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
    }


@router.get("/admin/api-keys")
def list_keys(
    p: Principal = Depends(admin), session: Session = Depends(get_session)
) -> list[dict[str, Any]]:
    rows = session.scalars(
        select(ApiKey).where(ApiKey.org_id == p.org_id).order_by(ApiKey.id.desc())
    )
    return [_key_out(k) for k in rows]


class KeyIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: Role = "analyst"


@router.post("/admin/api-keys", status_code=201)
def create_key(
    body: KeyIn, p: Principal = Depends(admin), session: Session = Depends(get_session)
) -> dict[str, Any]:
    raw, key = service.create_api_key(
        session, org_id=p.org_id, name=body.name, role=body.role, actor_id=p.user_id
    )
    session.commit()
    return {**_key_out(key), "key": raw, "note": "shown once; store it now"}


@router.delete("/admin/api-keys/{key_id}", status_code=204)
def revoke_key(
    key_id: int, p: Principal = Depends(admin), session: Session = Depends(get_session)
) -> None:
    if key_id == p.api_key_id:
        raise HTTPException(status_code=422, detail="a key cannot revoke itself")
    try:
        service.revoke_api_key(session, org_id=p.org_id, key_id=key_id, actor_id=p.user_id)
    except LookupError as exc:
        raise NotFoundError(str(exc)) from exc
    session.commit()


@router.get("/admin/usage")
def usage(
    days: int = 30, p: Principal = Depends(admin), session: Session = Depends(get_session)
) -> dict[str, Any]:
    return service.usage_summary(session, p.org_id, min(max(days, 1), 366))


@router.get("/admin/audit")
def audit_log(
    limit: int = 100, p: Principal = Depends(admin), session: Session = Depends(get_session)
) -> list[dict[str, Any]]:
    rows = session.execute(
        select(AuditEvent, User.email)
        .outerjoin(User, AuditEvent.user_id == User.id)
        .where(AuditEvent.org_id == p.org_id)
        .order_by(AuditEvent.id.desc())
        .limit(min(max(limit, 1), 500))
    )
    return [
        {
            "action": e.action,
            "actor": email,
            "target": e.target,
            "detail": e.detail,
            "created_at": e.created_at.isoformat(),
        }
        for e, email in rows
    ]
