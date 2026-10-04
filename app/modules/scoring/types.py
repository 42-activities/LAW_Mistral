from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.modules.engine.types import Flag

ENGINE_VERSION = "1.0.0"
FACTORS = ("tax_efficiency", "compliance", "treaty_breadth", "substance_burden")
BANDS = ("low", "medium", "high")


def q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class ProfileFlow:
    income_category: str
    source: str
    annual_amount: Decimal | None = None


@dataclass(frozen=True)
class ScoringProfile:
    """The structured profile the scorer ranks against (spec §6 `derived`)."""

    parent: str
    flows: tuple[ProfileFlow, ...]
    holding_pct: Decimal = Decimal("100")
    holding_months: int = 24
    substance_capacity: str = "medium"
    activity: str | None = None
    size: str | None = None

    def __post_init__(self) -> None:
        if self.substance_capacity not in BANDS:
            raise ValueError(f"substance_capacity must be one of {BANDS}")
        if not self.flows:
            raise ValueError("a profile needs at least one flow")

    def counterparties(self) -> tuple[str, ...]:
        return tuple(sorted({f.source for f in self.flows} | {self.parent}))

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ScoringProfile":
        return cls(
            parent=data["parent"],
            flows=tuple(
                ProfileFlow(
                    f["income_category"],
                    f["source"],
                    None if f.get("annual_amount") is None else Decimal(f["annual_amount"]),
                )
                for f in data["flows"]
            ),
            holding_pct=Decimal(data.get("holding_pct", "100")),
            holding_months=int(data.get("holding_months", 24)),
            substance_capacity=data.get("substance_capacity", "medium"),
            activity=data.get("activity"),
            size=data.get("size"),
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "parent": self.parent,
            "flows": [
                {
                    "income_category": f.income_category,
                    "source": f.source,
                    "annual_amount": None if f.annual_amount is None else str(f.annual_amount),
                }
                for f in self.flows
            ],
            "holding_pct": str(self.holding_pct),
            "holding_months": self.holding_months,
            "substance_capacity": self.substance_capacity,
            "activity": self.activity,
            "size": self.size,
        }


@dataclass(frozen=True)
class FactorScore:
    score: Decimal | None
    weight: Decimal
    citations: tuple[int, ...] = ()
    flags: tuple[Flag, ...] = ()
    detail: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class FlowLine:
    flow: str
    leg: str
    kind: str
    rate: Decimal | None
    tax_per_100: Decimal | None
    citations: tuple[int, ...]


@dataclass(frozen=True)
class ScoreCard:
    jurisdiction: str
    rank: int
    overall_score: Decimal | None
    complete: bool
    weight_set: str
    data_asof: date
    engine_version: str
    factors: dict[str, FactorScore]
    flow_breakdown: tuple[FlowLine, ...]
    guardrail_flags: tuple[Flag, ...]
    citations: tuple[int, ...]
