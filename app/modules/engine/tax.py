from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.engine.types import (
    HUNDRED,
    ZERO,
    CitResult,
    ExemptionResult,
    Flag,
    SourcedRate,
    q,
)
from app.modules.tax.models import DomesticTaxRule
from app.modules.tax.repository import (
    HoldingRegimeRepository,
    TaxRuleRepository,
    WhtExemptionRepository,
)

WHT_TAX_TYPE = {
    "DIVIDEND": "WHT_DIVIDEND",
    "INTEREST": "WHT_INTEREST",
    "ROYALTY": "WHT_ROYALTY",
}
PARTICIPATION_INCOME = {"DIVIDEND", "CAPITAL_GAIN"}


class TaxEngine:
    """Domestic law only: WHT rates, CIT and participation exemptions."""

    def __init__(self, session: Session) -> None:
        self.rules = TaxRuleRepository(session)
        self.regimes = HoldingRegimeRepository(session)
        self.exemptions = WhtExemptionRepository(session)

    def _rule(
        self, jurisdiction: str, tax_type: str, category: str, on_date: date, taxpayer: str
    ) -> DomesticTaxRule | None:
        # A rule for the specific taxpayer type wins over the generic "any" rule.
        return self.rules.get_rule(
            jurisdiction, tax_type, category, on_date, taxpayer_type=taxpayer
        ) or self.rules.get_rule(jurisdiction, tax_type, category, on_date, taxpayer_type="any")

    def domestic_wht(
        self,
        jurisdiction: str,
        category: str,
        on_date: date,
        recipient_type: str = "company",
        recipient: str | None = None,
        holding_pct: Decimal | None = None,
        holding_months: int | None = None,
    ) -> SourcedRate | None:
        tax_type = WHT_TAX_TYPE.get(category)
        if tax_type is None:
            return None
        rule = self._rule(jurisdiction, tax_type, category, on_date, recipient_type)
        if rule is None or rule.rate is None:
            return None
        base = SourcedRate(
            rate=rule.rate,
            citations=(rule.source_evidence_id,),
            rule=f"{jurisdiction} domestic {tax_type} ({rule.taxpayer_type})",
        )
        if recipient is None or rule.rate == ZERO or recipient_type != "company":
            return base
        return self._apply_exemptions(
            base, jurisdiction, category, on_date, recipient, holding_pct, holding_months
        )

    def _apply_exemptions(
        self,
        base: SourcedRate,
        jurisdiction: str,
        category: str,
        on_date: date,
        recipient: str,
        holding_pct: Decimal | None,
        holding_months: int | None,
    ) -> SourcedRate:
        """Domestic exemptions for recipients in a group, e.g. EU directive reliefs."""
        flags: list[Flag] = []
        for ex, group, member in self.exemptions.applicable(
            jurisdiction, category, recipient, on_date
        ):
            missing = []
            if ex.min_holding_pct is not None and (
                holding_pct is None or holding_pct < ex.min_holding_pct
            ):
                missing.append(f"holding ≥{ex.min_holding_pct}% (given: {holding_pct})")
            if ex.min_holding_months is not None and (
                holding_months is None or holding_months < ex.min_holding_months
            ):
                missing.append(
                    f"held ≥{ex.min_holding_months} months (given: {holding_months})"
                )
            if missing:
                flags.append(
                    Flag(
                        "exemption_conditions_not_met",
                        f"{ex.legal_ref} exemption for {group.code} recipients not applied: "
                        + "; ".join(missing),
                    )
                )
                continue
            return SourcedRate(
                rate=ZERO,
                citations=(*base.citations, ex.source_evidence_id, member.source_evidence_id),
                rule=f"{base.rule}, exempt under {ex.legal_ref}",
                statutory_rate=base.rate,
                flags=(
                    Flag(
                        "directive_exemption",
                        f"{jurisdiction} {category.lower()} withholding exempt for a "
                        f"{group.code} recipient: {ex.description}",
                    ),
                    Flag(
                        "exemption_anti_abuse",
                        f"{ex.legal_ref}: the exemption is subject to anti-abuse conditions "
                        "(genuine arrangement, beneficial ownership)",
                        interpretation_required=True,
                    ),
                ),
            )
        return SourcedRate(base.rate, base.citations, base.rule, tuple(flags))

    def cit(self, jurisdiction: str, on_date: date, amount: Decimal | None = None) -> CitResult:
        rule = self._rule(jurisdiction, "CIT", "CORPORATE_PROFIT", on_date, "company")
        if rule is None:
            return CitResult(
                jurisdiction,
                on_date,
                None,
                flags=(Flag("missing_cit_rule", f"no CIT rule for {jurisdiction} on {on_date}"),),
            )
        cites = (rule.source_evidence_id,)
        if not rule.is_bracketed:
            if rule.rate is None:
                return CitResult(
                    jurisdiction,
                    on_date,
                    None,
                    flags=(Flag("missing_cit_rule", f"flat CIT rule {rule.id} has no rate"),),
                )
            return CitResult(jurisdiction, on_date, rule.rate, cites)
        if not rule.brackets:
            return CitResult(
                jurisdiction,
                on_date,
                None,
                flags=(Flag("missing_cit_rule", f"bracketed CIT rule {rule.id} has no brackets"),),
            )
        if amount is None or amount <= ZERO:
            top = max(rule.brackets, key=lambda b: b.position)
            return CitResult(
                jurisdiction,
                on_date,
                top.rate,
                cites,
                (
                    Flag(
                        "cit_top_bracket_assumed",
                        f"no taxable amount given; {jurisdiction} top CIT bracket "
                        f"{top.rate}% used (conservative)",
                    ),
                ),
            )
        tax = ZERO
        for b in rule.brackets:
            upper = amount if b.upper_bound is None else min(amount, b.upper_bound)
            if upper > b.lower_bound:
                tax += (upper - b.lower_bound) * b.rate / HUNDRED
        return CitResult(
            jurisdiction,
            on_date,
            q(tax / amount * HUNDRED),
            cites,
            (Flag("cit_average_rate", f"average CIT rate on {amount} across brackets"),),
        )

    def participation_exemption(
        self,
        holding: str,
        category: str,
        on_date: date,
        holding_pct: Decimal | None,
        holding_months: int | None,
        payer_cit_rate: Decimal | None,
    ) -> ExemptionResult:
        if category not in PARTICIPATION_INCOME:
            reason = f"{category} is not participation income"
            return ExemptionResult(False, ZERO, reasons=(reason,))
        regime = self.regimes.get(holding, on_date)
        if regime is None:
            return ExemptionResult(
                False,
                ZERO,
                flags=(
                    Flag(
                        "holding_regime_not_recorded",
                        f"no participation-exemption regime recorded for {holding}; "
                        "income treated as fully taxable",
                    ),
                ),
            )
        cites = (regime.source_evidence_id,)
        covered = (
            regime.participation_exemption_dividends
            if category == "DIVIDEND"
            else regime.participation_exemption_capgains
        )
        if not covered:
            return ExemptionResult(
                False, ZERO, cites, (f"{holding} regime does not exempt {category}",)
            )

        reasons: list[str] = []
        flags: list[Flag] = []
        if regime.min_holding_pct is not None:
            if holding_pct is None:
                reasons.append("holding % not given")
            elif holding_pct < regime.min_holding_pct:
                reasons.append(f"holding {holding_pct}% < minimum {regime.min_holding_pct}%")
        if regime.min_holding_period_months is not None:
            if holding_months is None:
                reasons.append("holding period not given")
            elif holding_months < regime.min_holding_period_months:
                reasons.append(
                    f"held {holding_months} months < minimum {regime.min_holding_period_months}"
                )
        if regime.min_subject_to_tax_rate is not None:
            if payer_cit_rate is None:
                reasons.append("payer's CIT rate unknown (subject-to-tax test)")
                flags.append(
                    Flag("payer_cit_unknown", "subject-to-tax test could not be evaluated")
                )
            elif payer_cit_rate < regime.min_subject_to_tax_rate:
                reasons.append(
                    f"payer taxed at {payer_cit_rate}% < minimum {regime.min_subject_to_tax_rate}%"
                )
        elif regime.subject_to_tax_condition:
            if payer_cit_rate is None or payer_cit_rate == ZERO:
                reasons.append("payer not shown to be subject to tax")
            else:
                flags.append(
                    Flag(
                        "subject_to_tax_review",
                        "regime has a subject-to-tax condition without a recorded rate floor",
                        interpretation_required=True,
                    )
                )

        if reasons:
            return ExemptionResult(False, ZERO, cites, tuple(reasons), tuple(flags))
        return ExemptionResult(True, regime.exempt_share_pct, cites, (), tuple(flags))
