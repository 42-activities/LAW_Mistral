from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.modules.saas.models import ApiKey
from app.modules.saas.security import hash_api_key


def require_api_key(
    x_api_key: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> int:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    key = session.scalar(
        select(ApiKey).where(ApiKey.key_hash == hash_api_key(x_api_key), ApiKey.active.is_(True))
    )
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return key.org_id
