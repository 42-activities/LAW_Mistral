from collections.abc import Callable
from datetime import timedelta

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.modules.llm.provider import LlmProvider, default_provider
from app.modules.saas.models import ApiKey
from app.modules.saas.service import (
    Principal,
    now,
    principal_from_api_key,
    principal_from_session,
)

UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED


def get_principal(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> Principal:
    """Authenticate an `X-API-Key` (machines) or a `Bearer` session token (people)."""
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=UNAUTHORIZED, detail="Invalid authorization header")
        p = principal_from_session(session, token.strip())
        if p is None:
            raise HTTPException(status_code=UNAUTHORIZED, detail="Session expired or invalid")
        return p
    if not x_api_key:
        raise HTTPException(status_code=UNAUTHORIZED, detail="API key required")
    key_principal = principal_from_api_key(session, x_api_key)
    if key_principal is None:
        raise HTTPException(status_code=UNAUTHORIZED, detail="Invalid API key")
    key = session.get(ApiKey, key_principal.api_key_id)
    # Record use at most once a minute, so reads do not turn into a write per request.
    if key is not None and (
        key.last_used_at is None or key.last_used_at < now() - timedelta(minutes=1)
    ):
        key.last_used_at = now()
        session.commit()
    return key_principal


def require_api_key(principal: Principal = Depends(get_principal)) -> int:
    """Any authenticated caller; returns the organisation id."""
    return principal.org_id


def require_role(role: str) -> Callable[..., Principal]:
    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.at_least(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"requires the {role} role"
            )
        return principal

    return dependency


def get_llm_provider() -> LlmProvider | None:
    return default_provider()


require_analyst = require_role("analyst")
require_admin = require_role("admin")
