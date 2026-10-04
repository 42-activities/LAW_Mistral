from datetime import date
from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import require_api_key
from app.errors import NotFoundError
from app.modules.core.repository import JurisdictionRepository
from app.modules.scoring.repository import (
    ScoringRunRepository,
    WeightSetRepository,
    card_to_dict,
)
from app.modules.scoring.scorer import DEFAULT_WEIGHTS, Scorer, normalise_weights
from app.modules.scoring.types import ENGINE_VERSION, ProfileFlow, ScoringProfile

router = APIRouter(prefix="/v1/analyze", tags=["recommendation"])

Code = Field(min_length=2, max_length=8)


class FlowIn(BaseModel):
    income_category: Literal["DIVIDEND", "INTEREST", "ROYALTY"]
    source: str = Code
    annual_amount: Decimal | None = Field(default=None, gt=0)


class ProfileIn(BaseModel):
    parent: str = Code
    flows: list[FlowIn] = Field(min_length=1)
    holding_pct: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    holding_months: int = Field(default=24, ge=0)
    substance_capacity: Literal["low", "medium", "high"] = "medium"
    activity: str | None = None
    size: str | None = None

    def to_profile(self) -> ScoringProfile:
        return ScoringProfile(
            parent=self.parent,
            flows=tuple(
                ProfileFlow(f.income_category, f.source, f.annual_amount) for f in self.flows
            ),
            holding_pct=self.holding_pct,
            holding_months=self.holding_months,
            substance_capacity=self.substance_capacity,
            activity=self.activity,
            size=self.size,
        )


class RecommendationIn(BaseModel):
    profile: ProfileIn
    on_date: date
    candidates: list[str] | None = Field(
        default=None, description="Candidate holding jurisdictions; default: all known."
    )
    weight_set: str | None = Field(default=None, description="Named weight set; default: default")
    weights: dict[str, Decimal] | None = Field(
        default=None, description="Custom weights; overrides weight_set"
    )


@router.post("/holding-recommendation")
def holding_recommendation(
    body: RecommendationIn,
    org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    jurisdictions = JurisdictionRepository(session)
    profile = body.profile.to_profile()
    candidates = body.candidates or [j.code for j in jurisdictions.list()]
    for code in {*candidates, *profile.counterparties()}:
        if jurisdictions.get_by_code(code) is None:
            raise NotFoundError(f"jurisdiction {code} not found")

    sets = WeightSetRepository(session)
    weight_set = sets.get(body.weight_set) if body.weight_set else sets.default()
    if body.weight_set and weight_set is None:
        raise NotFoundError(f"weight set {body.weight_set} not found")
    if body.weights is not None:
        raw, name = body.weights, "custom"
    elif weight_set is not None:
        raw = {k: Decimal(v) for k, v in weight_set.weights.items()}
        name = weight_set.name
    else:
        raw, name = DEFAULT_WEIGHTS, "default-v1"
    try:
        weights = normalise_weights(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    cards = Scorer(session).rank(profile, candidates, body.on_date, weights, name)
    run = ScoringRunRepository(session).save(
        org_id=org_id,
        profile=profile,
        profile_id=None,
        weight_set=weight_set if body.weights is None else None,
        weights=weights,
        data_asof=body.on_date,
        cards=cards,
    )
    session.commit()
    return {
        "scoring_run_id": run.id,
        "weight_set": name,
        "weights": {k: str(v) for k, v in weights.items()},
        "engine_version": ENGINE_VERSION,
        "data_asof": body.on_date.isoformat(),
        "scorecards": [card_to_dict(c) for c in cards],
    }
