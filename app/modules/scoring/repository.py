from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.repository import JurisdictionRepository
from app.modules.engine.types import Flag
from app.modules.recommender.models import Scorecard, ScoringRun, WeightSet
from app.modules.scoring.types import ENGINE_VERSION, ScoreCard, ScoringProfile


def _dec(v: Decimal | None) -> str | None:
    return None if v is None else str(v)


def _flags(flags: tuple[Flag, ...]) -> list[dict[str, Any]]:
    return [
        {"code": f.code, "message": f.message, "interpretation_required": f.interpretation_required}
        for f in flags
    ]


def card_to_dict(card: ScoreCard) -> dict[str, Any]:
    """JSON form of a ScoreCard (spec §3), used for storage and the API."""
    return {
        "jurisdiction": card.jurisdiction,
        "rank": card.rank,
        "overall_score": _dec(card.overall_score),
        "complete": card.complete,
        "weight_set": card.weight_set,
        "data_asof": card.data_asof.isoformat(),
        "engine_version": card.engine_version,
        "factors": {
            name: {
                "score": _dec(fs.score),
                "weight": _dec(fs.weight),
                "citations": list(fs.citations),
                "flags": _flags(fs.flags),
                "detail": fs.detail,
            }
            for name, fs in card.factors.items()
        },
        "flow_breakdown": [
            {
                "flow": line.flow,
                "leg": line.leg,
                "kind": line.kind,
                "rate": _dec(line.rate),
                "tax_per_100": _dec(line.tax_per_100),
                "citations": list(line.citations),
            }
            for line in card.flow_breakdown
        ],
        "guardrail_flags": _flags(card.guardrail_flags),
        "citations": list(card.citations),
    }


class WeightSetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, name: str) -> WeightSet | None:
        return self.session.scalar(select(WeightSet).where(WeightSet.name == name))

    def default(self) -> WeightSet | None:
        return self.session.scalar(select(WeightSet).where(WeightSet.is_default.is_(True)))


class ScoringRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        *,
        org_id: int,
        profile: ScoringProfile,
        profile_id: int | None,
        weight_set: WeightSet | None,
        weights: dict[str, Decimal],
        data_asof: date,
        cards: list[ScoreCard],
    ) -> ScoringRun:
        run = ScoringRun(
            org_id=org_id,
            profile_id=profile_id,
            profile_snapshot=profile.to_json(),
            weight_set_id=weight_set.id if weight_set else None,
            weights={k: str(v) for k, v in weights.items()},
            engine_version=ENGINE_VERSION,
            data_asof=data_asof,
        )
        self.session.add(run)
        self.session.flush()
        jurisdictions = JurisdictionRepository(self.session)
        for card in cards:
            j = jurisdictions.get_by_code(card.jurisdiction)
            assert j is not None
            data = card_to_dict(card)
            self.session.add(
                Scorecard(
                    scoring_run_id=run.id,
                    jurisdiction_id=j.id,
                    rank=card.rank,
                    overall_score=card.overall_score,
                    complete=card.complete,
                    factor_scores=data["factors"],
                    flow_breakdown=data["flow_breakdown"],
                    guardrail_flags=data["guardrail_flags"],
                    citations=data["citations"],
                )
            )
        self.session.flush()
        return run
