from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.analyze import WhtOut
from app.db import get_session
from app.deps import get_llm_provider, require_analyst
from app.modules.llm.ask import AskError, AskService
from app.modules.llm.provider import LlmProvider
from app.modules.saas.service import (
    LimitExceeded,
    Principal,
    enforce_analysis_limit,
    llm_allowed,
    meter,
)

router = APIRouter(prefix="/v1", tags=["ask"])


class AskIn(BaseModel):
    question: str = Field(min_length=5, max_length=1000)
    on_date: date | None = None


@router.post("/ask")
def ask(
    body: AskIn,
    principal: Principal = Depends(require_analyst),
    session: Session = Depends(get_session),
    provider: LlmProvider | None = Depends(get_llm_provider),
) -> dict[str, Any]:
    if provider is None:
        raise HTTPException(status_code=503, detail="natural-language questions are not enabled")
    enforce_analysis_limit(session, principal)
    if not llm_allowed(session, principal.org_id):
        raise LimitExceeded("daily AI call limit reached for your plan", 3600)
    service = AskService(session, provider)
    try:
        intent, result, answer = service.ask(
            body.question, org_id=principal.org_id, default_date=body.on_date or date.today()
        )
    except AskError as exc:
        meter(session, principal, "llm_call", units=service.tokens, ref="ask")
        session.commit()  # keep the audit row and the metered call
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    meter(session, principal, "ask", ref="ask")
    meter(session, principal, "llm_call", units=service.tokens, ref="ask")
    session.commit()
    return {
        "query": {
            "source": intent.source,
            "recipient": intent.recipient,
            "income_category": intent.income_category,
            "holding_pct": None if intent.holding_pct is None else str(intent.holding_pct),
            "on_date": intent.on_date.isoformat(),
        },
        "result": WhtOut.model_validate(result).model_dump(mode="json"),
        "answer": answer,
        "answer_kind": "template",
    }
