from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.engine.types import ZERO, merge_citations
from app.modules.scoring.factors import GUARDRAIL_CAP, FactorCalculator
from app.modules.scoring.types import (
    ENGINE_VERSION,
    FACTORS,
    FactorScore,
    ScoreCard,
    ScoringProfile,
    q2,
)

DEFAULT_WEIGHTS = {
    "tax_efficiency": Decimal("0.45"),
    "compliance": Decimal("0.20"),
    "treaty_breadth": Decimal("0.20"),
    "substance_burden": Decimal("0.15"),
}


def normalise_weights(raw: dict[str, Decimal]) -> dict[str, Decimal]:
    unknown = set(raw) - set(FACTORS)
    if unknown:
        raise ValueError(f"unknown factors: {sorted(unknown)}")
    weights = {k: Decimal(str(raw.get(k, ZERO))) for k in FACTORS}
    if any(w < ZERO for w in weights.values()):
        raise ValueError("weights must be non-negative")
    total = sum(weights.values(), ZERO)
    if total == ZERO:
        raise ValueError("weights must not all be zero")
    return {k: (w / total).quantize(Decimal("0.0001")) for k, w in weights.items()}


class Scorer:
    """Ranks candidate holding jurisdictions for a profile (spec §3). Deterministic."""

    def __init__(self, session: Session) -> None:
        self.factors = FactorCalculator(session)

    def score(
        self,
        profile: ScoringProfile,
        holding: str,
        on: date,
        weights: dict[str, Decimal],
        weight_set: str,
    ) -> ScoreCard:
        f = self.factors
        results = f.flow_results(profile, holding, on)
        risk = f.risk.profile(holding, on)

        tax_score, tax_cites, tax_flags, tax_detail = f.tax_efficiency(profile, results)
        comp_score, comp_flags, comp_detail = f.compliance(profile, risk)
        treaty_score, treaty_cites, treaty_detail = f.treaty_breadth(profile, holding, on)
        sub_score, sub_cites, sub_flags, sub_detail = f.substance_burden(
            profile, holding, on, results
        )
        factors = {
            "tax_efficiency": FactorScore(
                tax_score, weights["tax_efficiency"], tax_cites, tax_flags, tax_detail
            ),
            "compliance": FactorScore(
                comp_score, weights["compliance"], risk.citations, comp_flags, comp_detail
            ),
            "treaty_breadth": FactorScore(
                treaty_score, weights["treaty_breadth"], treaty_cites, (), treaty_detail
            ),
            "substance_burden": FactorScore(
                sub_score, weights["substance_burden"], sub_cites, sub_flags, sub_detail
            ),
        }

        guardrails = f.guardrails(profile, risk)
        complete = all(fs.score is not None for fs in factors.values())
        overall: Decimal | None = None
        if complete:
            overall = q2(sum(((fs.score or ZERO) * fs.weight for fs in factors.values()), ZERO))
            if guardrails:
                overall = min(overall, GUARDRAIL_CAP)

        return ScoreCard(
            jurisdiction=holding,
            rank=0,  # assigned by rank()
            overall_score=overall,
            complete=complete,
            weight_set=weight_set,
            data_asof=on,
            engine_version=ENGINE_VERSION,
            factors=factors,
            flow_breakdown=f.flow_lines(profile, results),
            guardrail_flags=guardrails,
            citations=merge_citations(*(fs.citations for fs in factors.values())),
        )

    def rank(
        self,
        profile: ScoringProfile,
        candidates: list[str],
        on: date,
        weights: dict[str, Decimal] | None = None,
        weight_set: str = "default-v1",
    ) -> list[ScoreCard]:
        w = normalise_weights(weights or DEFAULT_WEIGHTS)
        cards = [self.score(profile, c, on, w, weight_set) for c in sorted(set(candidates))]
        # Complete cards first by score (desc), then incomplete; ties broken by code.
        cards.sort(
            key=lambda c: (
                not c.complete,
                -(c.overall_score or ZERO),
                c.jurisdiction,
            )
        )
        return [
            ScoreCard(**{**card.__dict__, "rank": i}) for i, card in enumerate(cards, start=1)
        ]
