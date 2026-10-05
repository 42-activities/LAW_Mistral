from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.analyze import WhtOut
from app.db import get_session
from app.deps import get_llm_provider, require_api_key
from app.modules.llm.ask import AskError, AskService
from app.modules.llm.provider import LlmProvider

router = APIRouter(prefix="/v1", tags=["ask"])


class AskIn(BaseModel):
    question: str = Field(min_length=5, max_length=1000)
    on_date: date | None = None


@router.post("/ask")
def ask(
    body: AskIn,
    org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
    provider: LlmProvider | None = Depends(get_llm_provider),
) -> dict[str, Any]:
    if provider is None:
        raise HTTPException(status_code=503, detail="natural-language questions are not enabled")
    try:
        intent, result, answer = AskService(session, provider).ask(
            body.question, org_id=org_id, default_date=body.on_date or date.today()
        )
    except AskError as exc:
        session.commit()  # keep the audit row
        raise HTTPException(status_code=422, detail=str(exc)) from exc
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
