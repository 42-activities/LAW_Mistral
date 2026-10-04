from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

HUNDRED = Decimal("100")
ZERO = Decimal("0")


def q(value: Decimal) -> Decimal:
    """Quantize a percentage to 3 dp, the storage precision of every rate."""
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Flag:
    code: str
    message: str
    interpretation_required: bool = False


@dataclass(frozen=True)
class SourcedRate:
    """A rate and the evidence it came from."""

    rate: Decimal
    citations: tuple[int, ...]
    rule: str


@dataclass(frozen=True)
class CitResult:
    jurisdiction: str
    on_date: date
    rate: Decimal | None
    citations: tuple[int, ...] = ()
    flags: tuple[Flag, ...] = ()

    @property
    def complete(self) -> bool:
        return self.rate is not None


@dataclass(frozen=True)
class ExemptionResult:
    applies: bool
    exempt_share_pct: Decimal
    citations: tuple[int, ...] = ()
    reasons: tuple[str, ...] = ()
    flags: tuple[Flag, ...] = ()


@dataclass(frozen=True)
class TreatyTerms:
    treaty_id: int
    treaty_name: str
    article_ref: str | None
    cap: Decimal
    exclusive_residence_taxation: bool
    relief_mechanism: str | None
    citations: tuple[int, ...]
    flags: tuple[Flag, ...] = ()


@dataclass(frozen=True)
class ListHit:
    list_code: str
    family: str
    classification: str
    citation: int


@dataclass(frozen=True)
class RiskProfile:
    jurisdiction: str
    on_date: date
    memberships: tuple[ListHit, ...]

    def on_list(self, list_code: str) -> ListHit | None:
        return next((m for m in self.memberships if m.list_code == list_code), None)

    @property
    def citations(self) -> tuple[int, ...]:
        return tuple(m.citation for m in self.memberships)


@dataclass(frozen=True)
class AppliedConsequence:
    list_code: str
    classification: str
    consequence_type: str
    rate: Decimal | None
    legal_ref: str
    citations: tuple[int, ...]


@dataclass(frozen=True)
class WhtResult:
    """Withholding on one payment. Kept apart on purpose (spec core principle):
    domestic rate ≠ treaty cap ≠ amount withheld at payment ≠ final rate after relief."""

    source: str
    recipient: str
    income_category: str
    on_date: date
    domestic_rate: Decimal | None
    effective_domestic_rate: Decimal | None
    treaty_cap: Decimal | None
    withheld_at_payment: Decimal | None
    final_rate: Decimal | None
    relief_mechanism: str | None
    treaty_name: str | None
    consequences: tuple[AppliedConsequence, ...]
    citations: tuple[int, ...]
    flags: tuple[Flag, ...]

    @property
    def complete(self) -> bool:
        return self.final_rate is not None


@dataclass(frozen=True)
class FlowLeg:
    leg: str
    kind: str  # "wht" | "cit"
    rate: Decimal | None
    tax_per_100: Decimal | None
    citations: tuple[int, ...]
    flags: tuple[Flag, ...] = ()
    detail: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class FlowResult:
    income_category: str
    source: str
    holding: str
    parent: str
    on_date: date
    legs: tuple[FlowLeg, ...]
    total_leakage_pct: Decimal | None
    citations: tuple[int, ...]
    flags: tuple[Flag, ...]

    @property
    def complete(self) -> bool:
        return self.total_leakage_pct is not None


def merge_citations(*groups: tuple[int, ...]) -> tuple[int, ...]:
    """Stable de-duplicated union, so outputs are reproducible."""
    seen: dict[int, None] = {}
    for group in groups:
        for cid in group:
            seen.setdefault(cid, None)
    return tuple(seen)
