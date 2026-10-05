from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.saas.models import (
    ROLES,
    ApiKey,
    AuditEvent,
    OrganisationAccount,
    Plan,
    UsageEvent,
    User,
    UserSession,
)
from app.modules.saas.security import (
    generate_api_key,
    generate_session_token,
    hash_api_key,
    hash_password,
    hash_session_token,
    password_problem,
    verify_password,
)

SESSION_TTL = timedelta(days=7)
LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_MAX_FAILURES = 5
DEFAULT_PLAN = "standard"


def now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Principal:
    """Who is calling: an API key or a signed-in user, always within one organisation."""

    org_id: int
    role: str
    user_id: int | None = None
    api_key_id: int | None = None

    def at_least(self, role: str) -> bool:
        return ROLES.index(self.role) >= ROLES.index(role)


class AuthError(Exception):
    pass


class TooManyAttempts(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after


class LimitExceeded(Exception):
    def __init__(self, detail: str, retry_after: int) -> None:
        self.detail = detail
        self.retry_after = retry_after


def audit(
    session: Session,
    action: str,
    *,
    org_id: int | None = None,
    user_id: int | None = None,
    target: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditEvent(org_id=org_id, user_id=user_id, action=action, target=target,
                   detail=detail or {})
    )


# --- authentication ----------------------------------------------------------------------------


def principal_from_api_key(session: Session, raw: str) -> Principal | None:
    key = session.scalar(
        select(ApiKey).where(ApiKey.key_hash == hash_api_key(raw), ApiKey.active.is_(True))
    )
    if key is None:
        return None
    return Principal(org_id=key.org_id, role=key.role, api_key_id=key.id)


def principal_from_session(session: Session, token: str) -> Principal | None:
    row = session.execute(
        select(UserSession, User)
        .join(User, UserSession.user_id == User.id)
        .where(
            UserSession.token_hash == hash_session_token(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now(),
            User.active.is_(True),
        )
    ).first()
    if row is None:
        return None
    _, user = row
    return Principal(org_id=user.org_id, role=user.role, user_id=user.id)


def login(session: Session, email: str, password: str) -> tuple[str, datetime, User]:
    email = email.strip().lower()
    failures = session.scalar(
        select(func.count())
        .select_from(AuditEvent)
        .where(
            AuditEvent.action == "login_failed",
            AuditEvent.target == email,
            AuditEvent.created_at > now() - LOGIN_WINDOW,
        )
    )
    if (failures or 0) >= LOGIN_MAX_FAILURES:
        raise TooManyAttempts(int(LOGIN_WINDOW.total_seconds()))
    user = session.scalar(select(User).where(func.lower(User.email) == email))
    if user is None or not user.active or not verify_password(password, user.password_hash):
        audit(session, "login_failed", org_id=user.org_id if user else None, target=email)
        raise AuthError("invalid email or password")
    token, token_hash = generate_session_token()
    expires = now() + SESSION_TTL
    session.add(UserSession(user_id=user.id, token_hash=token_hash, expires_at=expires))
    user.last_login_at = now()
    audit(session, "login", org_id=user.org_id, user_id=user.id, target=email)
    return token, expires, user


def logout(session: Session, token: str) -> None:
    row = session.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(token))
    )
    if row is not None and row.revoked_at is None:
        row.revoked_at = now()
        user = session.get(User, row.user_id)
        audit(session, "logout", org_id=user.org_id if user else None, user_id=row.user_id)


def change_password(session: Session, user_id: int, current: str, new: str) -> None:
    user = session.get(User, user_id)
    if user is None or not verify_password(current, user.password_hash):
        raise AuthError("current password is incorrect")
    problem = password_problem(new)
    if problem:
        raise ValueError(problem)
    user.password_hash = hash_password(new)
    # Other sessions of this user end; the caller signs in again elsewhere.
    for s in session.scalars(
        select(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
    ):
        s.revoked_at = now()
    audit(session, "password_changed", org_id=user.org_id, user_id=user.id)


# --- organisation administration ---------------------------------------------------------------


def create_user(
    session: Session,
    *,
    org_id: int,
    email: str,
    name: str | None,
    role: str,
    password: str,
    actor_id: int | None,
) -> User:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    problem = password_problem(password)
    if problem:
        raise ValueError(problem)
    email = email.strip().lower()
    if session.scalar(select(User.id).where(func.lower(User.email) == email)) is not None:
        raise ValueError("a user with this email already exists")
    user = User(
        org_id=org_id, email=email, name=name, role=role, password_hash=hash_password(password)
    )
    session.add(user)
    session.flush()
    audit(session, "user_created", org_id=org_id, user_id=actor_id, target=email,
          detail={"role": role})
    return user


def update_user(
    session: Session, *, org_id: int, user_id: int, role: str | None, active: bool | None,
    actor_id: int | None,
) -> User:
    user = session.get(User, user_id)
    if user is None or user.org_id != org_id:
        raise LookupError("user not found")
    if role is not None and role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    demoting_admin = user.role == "admin" and (
        (role is not None and role != "admin") or active is False
    )
    if demoting_admin:
        admins = session.scalar(
            select(func.count()).select_from(User).where(
                User.org_id == org_id, User.role == "admin", User.active.is_(True)
            )
        )
        if (admins or 0) <= 1:
            raise ValueError("an organisation must keep at least one active admin")
    changes: dict[str, Any] = {}
    if role is not None and role != user.role:
        changes["role"] = [user.role, role]
        user.role = role
    if active is not None and active != user.active:
        changes["active"] = [user.active, active]
        user.active = active
        if not active:
            for s in session.scalars(
                select(UserSession).where(
                    UserSession.user_id == user.id, UserSession.revoked_at.is_(None)
                )
            ):
                s.revoked_at = now()
    if changes:
        audit(session, "user_updated", org_id=org_id, user_id=actor_id, target=user.email,
              detail=changes)
    return user


def create_api_key(
    session: Session, *, org_id: int, name: str, role: str, actor_id: int | None
) -> tuple[str, ApiKey]:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    raw, key_hash = generate_api_key()
    key = ApiKey(org_id=org_id, key_hash=key_hash, name=name, role=role, created_by=actor_id)
    session.add(key)
    session.flush()
    audit(session, "api_key_created", org_id=org_id, user_id=actor_id, target=name,
          detail={"key_id": key.id, "role": role})
    return raw, key


def revoke_api_key(session: Session, *, org_id: int, key_id: int, actor_id: int | None) -> None:
    key = session.get(ApiKey, key_id)
    if key is None or key.org_id != org_id:
        raise LookupError("API key not found")
    if key.active:
        key.active = False
        audit(session, "api_key_revoked", org_id=org_id, user_id=actor_id, target=key.name,
              detail={"key_id": key.id})


# --- metering and limits -----------------------------------------------------------------------


def plan_for(session: Session, org_id: int) -> Plan:
    org = session.get(OrganisationAccount, org_id)
    plan = session.get(Plan, org.plan_id) if org and org.plan_id else None
    plan = plan or session.scalar(select(Plan).where(Plan.code == DEFAULT_PLAN))
    if plan is None:  # migration 0017 seeds it; defensive for hand-built databases
        raise RuntimeError("default plan missing")
    return plan


def _count(session: Session, org_id: int, kinds: tuple[str, ...], since: datetime) -> int:
    return session.scalar(
        select(func.count())
        .select_from(UsageEvent)
        .where(
            UsageEvent.org_id == org_id,
            UsageEvent.kind.in_(kinds),
            UsageEvent.created_at > since,
        )
    ) or 0


def enforce_analysis_limit(session: Session, p: Principal) -> None:
    plan = plan_for(session, p.org_id)
    t = now()
    kinds = ("analysis", "ask")
    if _count(session, p.org_id, kinds, t - timedelta(minutes=1)) >= plan.analyses_per_minute:
        raise LimitExceeded(
            f"rate limit: {plan.analyses_per_minute} analyses per minute on the {plan.name} plan",
            60,
        )
    midnight = t.replace(hour=0, minute=0, second=0, microsecond=0)
    if _count(session, p.org_id, kinds, midnight) >= plan.analyses_per_day:
        raise LimitExceeded(
            f"daily limit: {plan.analyses_per_day} analyses per day on the {plan.name} plan",
            int((midnight + timedelta(days=1) - t).total_seconds()),
        )


def llm_allowed(session: Session, org_id: int) -> bool:
    plan = plan_for(session, org_id)
    midnight = now().replace(hour=0, minute=0, second=0, microsecond=0)
    return _count(session, org_id, ("llm_call",), midnight) < plan.llm_calls_per_day


def meter(
    session: Session, p: Principal, kind: str, *, units: int = 1, ref: str | None = None
) -> None:
    session.add(
        UsageEvent(org_id=p.org_id, user_id=p.user_id, api_key_id=p.api_key_id, kind=kind,
                   units=units, ref=ref)
    )


def usage_summary(session: Session, org_id: int, days: int) -> dict[str, Any]:
    since = now() - timedelta(days=days)
    rows = session.execute(
        select(UsageEvent.kind, func.count(), func.coalesce(func.sum(UsageEvent.units), 0))
        .where(UsageEvent.org_id == org_id, UsageEvent.created_at > since)
        .group_by(UsageEvent.kind)
    ).all()
    plan = plan_for(session, org_id)
    return {
        "days": days,
        "plan": {
            "code": plan.code,
            "name": plan.name,
            "analyses_per_day": plan.analyses_per_day,
            "analyses_per_minute": plan.analyses_per_minute,
            "llm_calls_per_day": plan.llm_calls_per_day,
        },
        "usage": {kind: {"events": n, "units": int(u)} for kind, n, u in rows},
    }
