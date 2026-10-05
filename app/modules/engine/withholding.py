from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.engine.risk import RiskEngine
from app.modules.engine.tax import TaxEngine
from app.modules.engine.treaty import TreatyEngine
from app.modules.engine.types import ZERO, Flag, WhtResult, merge_citations, q

RATE_FIELDS = (
    "domestic_rate",
    "effective_domestic_rate",
    "treaty_cap",
    "withheld_at_payment",
    "final_rate",
)


class WithholdingEngine:
    """Source-state withholding on one cross-border payment.

    Order of precedence (see docs/superpowers/plans/2026-10-04-p3-engines.md):
    domestic rate → replaced by a list-triggered WHT consequence → capped by an applicable
    treaty → split into withheld-at-payment vs final by the relief mechanism.
    """

    def __init__(self, session: Session) -> None:
        self.tax = TaxEngine(session)
        self.treaty = TreatyEngine(session)
        self.risk = RiskEngine(session)

    def compute(
        self,
        source: str,
        recipient: str,
        category: str,
        on_date: date,
        holding_pct: Decimal | None = None,
        holding_days: int | None = None,
        recipient_type: str = "company",
    ) -> WhtResult:
        def result(**kw: object) -> WhtResult:
            base: dict[str, object] = dict(
                source=source,
                recipient=recipient,
                income_category=category,
                on_date=on_date,
                domestic_rate=None,
                effective_domestic_rate=None,
                treaty_cap=None,
                withheld_at_payment=None,
                final_rate=None,
                relief_mechanism=None,
                treaty_name=None,
                consequences=(),
                citations=(),
                flags=(),
            )
            base.update(kw)
            for key in RATE_FIELDS:
                if isinstance(base[key], Decimal):
                    base[key] = q(base[key])  # type: ignore[arg-type]
            return WhtResult(**base)  # type: ignore[arg-type]

        if source == recipient:
            return result(
                flags=(Flag("domestic_payment", "payer and recipient in the same jurisdiction"),)
            )

        domestic = self.tax.domestic_wht(
            source,
            category,
            on_date,
            recipient_type,
            recipient=recipient,
            holding_pct=holding_pct,
            holding_months=None if holding_days is None else holding_days * 12 // 365,
        )
        if domestic is None:
            return result(
                flags=(
                    Flag(
                        "missing_domestic_rule",
                        f"no {source} withholding rule for {category} on {on_date}",
                    ),
                )
            )

        flags: list[Flag] = list(domestic.flags)
        # The statutory rate is reported as `domestic_rate`; an exemption lowers `effective`.
        statutory = domestic.rate if domestic.statutory_rate is None else domestic.statutory_rate
        effective = domestic.rate
        consequences = self.risk.applied_consequences(
            source, recipient, on_date, consequence_type="withholding_tax", category=category
        )
        rated = [c for c in consequences if c.rate is not None]
        if rated:
            # Several triggering lists: the highest rate is the one the payer must withhold.
            top = max(rated, key=lambda c: c.rate or ZERO)
            assert top.rate is not None
            effective = top.rate
            flags.append(
                Flag(
                    "consequence_applied",
                    f"{recipient} on {top.list_code} ({top.classification}): {source} applies "
                    f"{top.rate}% under {top.legal_ref} instead of {effective}%",
                )
            )

        terms, treaty_flags = self.treaty.terms(
            source, recipient, category, on_date, holding_pct, holding_days
        )
        flags.extend(treaty_flags)
        cites = merge_citations(domestic.citations, *(c.citations for c in consequences))

        if terms is None:
            return result(
                domestic_rate=statutory,
                effective_domestic_rate=effective,
                withheld_at_payment=effective,
                final_rate=effective,
                consequences=consequences,
                citations=cites,
                flags=tuple(flags),
            )

        cites = merge_citations(cites, terms.citations)
        final = min(effective, terms.cap)
        if rated and terms.cap < effective:
            flags.append(
                Flag(
                    "consequence_vs_treaty",
                    "a list-triggered domestic rate and a treaty cap both apply; the treaty cap "
                    "is used — confirm the treaty is not overridden for listed jurisdictions",
                    interpretation_required=True,
                )
            )

        relief = terms.relief_mechanism
        if final == effective or relief in ("at_source", "credit"):
            withheld = final
        elif relief == "refund":
            withheld = effective
            flags.append(
                Flag(
                    "refund_cash_flow",
                    f"{effective}% withheld at payment; reduced to {final}% by refund claim",
                )
            )
        else:
            withheld = effective
            flags.append(
                Flag(
                    "relief_mechanism_unknown",
                    f"treaty relief procedure not recorded; {effective}% assumed withheld at "
                    f"payment until relief is obtained",
                )
            )

        return result(
            domestic_rate=statutory,
            effective_domestic_rate=effective,
            treaty_cap=terms.cap,
            withheld_at_payment=withheld,
            final_rate=final,
            relief_mechanism=relief,
            treaty_name=f"{terms.treaty_name}"
            + (f", {terms.article_ref}" if terms.article_ref else ""),
            consequences=consequences,
            citations=cites,
            flags=tuple(flags),
        )
