from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import require_api_key
from app.errors import NotFoundError
from app.modules.core.repository import JurisdictionRepository
from app.modules.engine.flow import Flow, FlowCalculator
from app.modules.engine.risk import RiskEngine
from app.modules.engine.withholding import WithholdingEngine

router = APIRouter(prefix="/v1/analyze", tags=["analyze"])

IncomeCategory = Literal["DIVIDEND", "INTEREST", "ROYALTY"]
JurisdictionCode = Field(min_length=2, max_length=8, examples=["FR"])


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FlagOut(_Out):
    code: str
    message: str
    interpretation_required: bool


class ConsequenceOut(_Out):
    list_code: str
    classification: str
    consequence_type: str
    rate: Decimal | None
    legal_ref: str
    citations: list[int]


class WhtOut(_Out):
    source: str
    recipient: str
    income_category: str
    on_date: date
    complete: bool
    domestic_rate: Decimal | None
    effective_domestic_rate: Decimal | None
    treaty_cap: Decimal | None
    withheld_at_payment: Decimal | None
    final_rate: Decimal | None
    relief_mechanism: str | None
    treaty_name: str | None
    consequences: list[ConsequenceOut]
    citations: list[int]
    flags: list[FlagOut]


class ListHitOut(_Out):
    list_code: str
    family: str
    classification: str
    citation: int


class RiskOut(_Out):
    jurisdiction: str
    on_date: date
    memberships: list[ListHitOut]


class FlowLegOut(_Out):
    leg: str
    kind: str
    rate: Decimal | None
    tax_per_100: Decimal | None
    citations: list[int]
    flags: list[FlagOut]
    detail: dict[str, str]


class FlowOut(_Out):
    income_category: str
    source: str
    holding: str
    parent: str
    on_date: date
    complete: bool
    total_leakage_pct: Decimal | None
    legs: list[FlowLegOut]
    citations: list[int]
    flags: list[FlagOut]


class WhtIn(BaseModel):
    source: str = JurisdictionCode
    recipient: str = JurisdictionCode
    income_category: IncomeCategory
    on_date: date
    holding_pct: Decimal | None = Field(default=None, ge=0, le=100)
    holding_days: int | None = Field(default=None, ge=0)


class FlowIn(BaseModel):
    income_category: IncomeCategory
    source: str = JurisdictionCode
    holding: str = JurisdictionCode
    parent: str = JurisdictionCode
    on_date: date
    holding_pct: Decimal | None = Field(default=None, ge=0, le=100)
    holding_months: int | None = Field(default=None, ge=0)
    amount: Decimal | None = Field(default=None, gt=0)


def _require(session: Session, *codes: str) -> None:
    repo = JurisdictionRepository(session)
    for code in codes:
        if repo.get_by_code(code) is None:
            raise NotFoundError(f"jurisdiction {code} not found")


@router.post("/withholding-tax", response_model=WhtOut)
def withholding_tax(
    body: WhtIn,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> WhtOut:
    _require(session, body.source, body.recipient)
    r = WithholdingEngine(session).compute(
        body.source,
        body.recipient,
        body.income_category,
        body.on_date,
        body.holding_pct,
        body.holding_days,
    )
    return WhtOut.model_validate(r)


@router.get("/jurisdiction-risk", response_model=RiskOut)
def jurisdiction_risk(
    jurisdiction: str,
    on_date: date,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> RiskOut:
    _require(session, jurisdiction)
    return RiskOut.model_validate(RiskEngine(session).profile(jurisdiction, on_date))


@router.post("/flow", response_model=FlowOut)
def flow(
    body: FlowIn,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> FlowOut:
    _require(session, body.source, body.holding, body.parent)
    f = Flow(
        body.income_category,
        body.source,
        body.holding,
        body.parent,
        body.holding_pct,
        body.holding_months,
        body.amount,
    )
    return FlowOut.model_validate(FlowCalculator(session).compute(f, body.on_date))
