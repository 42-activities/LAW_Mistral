"""The four ScoreCard factors (spec §3). Constants here are part of ENGINE_VERSION."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.engine.flow import Flow, FlowCalculator
from app.modules.engine.risk import RiskEngine
from app.modules.engine.tax import PARTICIPATION_INCOME, TaxEngine
from app.modules.engine.treaty import TreatyEngine
from app.modules.engine.types import HUNDRED, ZERO, Flag, FlowResult, RiskProfile, merge_citations
from app.modules.scoring.types import BANDS, FlowLine, ScoringProfile, q2
from app.modules.tax.repository import AntiAbuseRepository, cit_refund

LEAKAGE_SLOPE = Decimal("2")  # score = 100 − 2 × leakage %

LIST_PENALTY = {
    "FATF_BLACK": Decimal("100"),
    "FATF_GREY": Decimal("40"),
    "EU_TAX_ANNEX_I": Decimal("50"),
    "EU_TAX_ANNEX_II": Decimal("10"),
    "EU_AML_HIGH_RISK": Decimal("30"),
}
GLOBAL_FORUM_PENALTY = {"non_compliant": Decimal("40"), "partially_compliant": Decimal("20")}
# National non-cooperative lists → the state that publishes them.
NATIONAL_ETNC = {"FR_ETNC": "FR"}
ETNC_COUNTERPARTY_PENALTY = Decimal("50")
ETNC_OTHER_PENALTY = Decimal("10")

SUBSTANCE_GAP_PENALTY = Decimal("30")
SUBSTANCE_UNKNOWN_PENALTY = Decimal("30")
CFC_PENALTY = Decimal("40")
PPT_PENALTY = Decimal("10")

GUARDRAIL_CAP = Decimal("20")


def _clamp(value: Decimal) -> Decimal:
    return q2(min(max(value, ZERO), HUNDRED))


class FactorCalculator:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.flows = FlowCalculator(session)
        self.risk = RiskEngine(session)
        self.tax = TaxEngine(session)
        self.treaties = TreatyEngine(session)
        self.anti_abuse = AntiAbuseRepository(session)

    # Factor 1 ------------------------------------------------------------------------------

    def flow_results(self, profile: ScoringProfile, holding: str, on: date) -> list[FlowResult]:
        return [
            self.flows.compute(
                Flow(
                    f.income_category,
                    f.source,
                    holding,
                    profile.parent,
                    profile.holding_pct,
                    profile.holding_months,
                    f.annual_amount,
                ),
                on,
            )
            for f in profile.flows
        ]

    def tax_efficiency(
        self, profile: ScoringProfile, results: list[FlowResult]
    ) -> tuple[Decimal | None, tuple[int, ...], tuple[Flag, ...], dict[str, str]]:
        cites = merge_citations(*(r.citations for r in results))
        flags = tuple(f for r in results for f in r.flags)
        if any(r.total_leakage_pct is None for r in results):
            return None, cites, flags, {"reason": "at least one flow could not be computed"}
        amounts = [f.annual_amount for f in profile.flows]
        if all(a is not None for a in amounts):
            weights = [a for a in amounts if a is not None]
        else:
            weights = [Decimal("1")] * len(results)
        total_w = sum(weights, ZERO)
        leakage = sum(
            ((r.total_leakage_pct or ZERO) * w for r, w in zip(results, weights, strict=True)),
            ZERO,
        ) / total_w
        detail = {"weighted_leakage_pct": str(q2(leakage))}
        return _clamp(HUNDRED - LEAKAGE_SLOPE * leakage), cites, flags, detail

    @staticmethod
    def flow_lines(profile: ScoringProfile, results: list[FlowResult]) -> tuple[FlowLine, ...]:
        lines = []
        for f, r in zip(profile.flows, results, strict=True):
            label = f"{f.income_category.lower()} from {f.source}"
            for leg in r.legs:
                lines.append(
                    FlowLine(label, leg.leg, leg.kind, leg.rate, leg.tax_per_100, leg.citations)
                )
        return tuple(lines)

    # Factor 2 ------------------------------------------------------------------------------

    def compliance(
        self, profile: ScoringProfile, risk: RiskProfile
    ) -> tuple[Decimal, tuple[Flag, ...], dict[str, str]]:
        penalty = ZERO
        flags: list[Flag] = []
        counterparties = set(profile.counterparties())
        for hit in risk.memberships:
            p = LIST_PENALTY.get(hit.list_code, ZERO)
            if hit.list_code == "GLOBAL_FORUM_RATING":
                p = GLOBAL_FORUM_PENALTY.get(hit.classification, ZERO)
            owner = NATIONAL_ETNC.get(hit.list_code)
            if owner is not None:
                p = ETNC_COUNTERPARTY_PENALTY if owner in counterparties else ETNC_OTHER_PENALTY
            if p > ZERO:
                penalty += p
                flags.append(
                    Flag(
                        f"listed_{hit.list_code.lower()}",
                        f"{risk.jurisdiction} on {hit.list_code} ({hit.classification}): −{p}",
                    )
                )
        return _clamp(HUNDRED - penalty), tuple(flags), {"penalty": str(penalty)}

    @staticmethod
    def guardrails(profile: ScoringProfile, risk: RiskProfile) -> tuple[Flag, ...]:
        flags = []
        if risk.on_list("FATF_BLACK"):
            flags.append(
                Flag(
                    "guardrail_fatf_black",
                    f"{risk.jurisdiction} is on the FATF call-for-action list; "
                    f"score capped at {GUARDRAIL_CAP}",
                )
            )
        for code, owner in NATIONAL_ETNC.items():
            if risk.on_list(code) and owner in profile.counterparties():
                flags.append(
                    Flag(
                        "guardrail_etnc_counterparty",
                        f"{risk.jurisdiction} is non-cooperative for counterparty {owner} "
                        f"({code}); score capped at {GUARDRAIL_CAP}",
                    )
                )
        return tuple(flags)

    # Factor 3 ------------------------------------------------------------------------------

    def treaty_breadth(
        self, profile: ScoringProfile, holding: str, on: date
    ) -> tuple[Decimal, tuple[int, ...], dict[str, str]]:
        others = [c for c in profile.counterparties() if c != holding]
        if not others:
            return q2(HUNDRED), (), {"counterparties": "none besides the holding jurisdiction"}
        covered = []
        cites: list[int] = []
        for c in others:
            treaty = self.treaties.in_force(holding, c, on)
            if treaty is not None:
                covered.append(c)
                cites.append(treaty.source_evidence_id)
        score = _clamp(HUNDRED * Decimal(len(covered)) / Decimal(len(others)))
        detail = {"with_treaty": ",".join(covered) or "none", "counterparties": ",".join(others)}
        return score, tuple(cites), detail

    # Factor 4 ------------------------------------------------------------------------------

    def _effective_cit(self, profile: ScoringProfile, holding: str, on: date) -> Decimal | None:
        """Lowest corporate tax the holding bears on the profile's taxable income, after
        shareholder refunds (Malta) — what a CFC "privileged regime" test compares."""
        general = self.tax.cit(holding, on).rate
        if general is None:
            return None
        rates = [general]
        for cat in {f.income_category for f in profile.flows} - PARTICIPATION_INCOME:
            rate = self.tax.cit(holding, on, income_category=cat).rate
            if rate is None:
                continue
            refund = cit_refund(self.session, holding, cat, on)
            if refund is not None:
                rate = rate * (HUNDRED - refund.refund_pct) / HUNDRED
            rates.append(q2(rate))
        return min(rates)

    def substance_burden(
        self, profile: ScoringProfile, holding: str, on: date, results: list[FlowResult]
    ) -> tuple[Decimal, tuple[int, ...], tuple[Flag, ...], dict[str, str]]:
        score = HUNDRED
        cites: list[int] = []
        flags: list[Flag] = []
        detail: dict[str, str] = {"capacity": profile.substance_capacity}

        rules = self.anti_abuse.substance_rules(holding, on)
        if rules:
            required = max(BANDS.index(r.requirement_band) for r in rules)
            gap = max(required - BANDS.index(profile.substance_capacity), 0)
            score -= SUBSTANCE_GAP_PENALTY * gap
            cites.extend(r.source_evidence_id for r in rules)
            detail["requirement"] = BANDS[required]
        else:
            score -= SUBSTANCE_UNKNOWN_PENALTY
            detail["requirement"] = "not recorded"
            flags.append(
                Flag(
                    "substance_not_recorded",
                    f"no structured substance-rule data is recorded for {holding}; the substance "
                    f"score treats the burden as unknown — this is not evidence that no "
                    f"substance requirements apply",
                )
            )

        if holding != profile.parent:
            cfc = self.anti_abuse.cfc_rule(profile.parent, on)
            if cfc is not None and profile.holding_pct > cfc.control_threshold_pct:
                h_cit = self._effective_cit(profile, holding, on)
                u_cit = self.tax.cit(profile.parent, on).rate
                if h_cit is None or u_cit is None:
                    flags.append(
                        Flag(
                            "cfc_unknown",
                            f"{profile.parent} CFC rule applies to controlled entities but a "
                            f"CIT rate is missing; exposure not evaluated",
                            interpretation_required=True,
                        )
                    )
                else:
                    limit = u_cit * cfc.low_tax_relative_pct / HUNDRED
                    caught = h_cit <= limit if cfc.threshold_inclusive else h_cit < limit
                    if caught:
                        score -= CFC_PENALTY
                        cites.append(cfc.source_evidence_id)
                        detail["cfc"] = f"{holding} CIT {h_cit}% < {q2(limit)}% ({cfc.legal_ref})"
                        flags.append(
                            Flag(
                                "cfc_exposure",
                                f"{profile.parent} CFC rule ({cfc.legal_ref}) may attribute "
                                f"{holding} profits to the parent: {h_cit}% < {q2(limit)}% "
                                f"threshold. {cfc.effect}",
                                interpretation_required=True,
                            )
                        )

        if any(f.code == "mli_ppt" for r in results for f in r.flags):
            score -= PPT_PENALTY
            flags.append(
                Flag("ppt_exposure", "a treaty used by the flows carries the MLI PPT")
            )
        return _clamp(score), tuple(cites), tuple(flags), detail
