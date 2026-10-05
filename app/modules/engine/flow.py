from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.engine.tax import PARTICIPATION_INCOME, TaxEngine
from app.modules.engine.types import (
    HUNDRED,
    ZERO,
    Flag,
    FlowLeg,
    FlowResult,
    WhtResult,
    merge_citations,
    q,
)
from app.modules.engine.withholding import WithholdingEngine
from app.modules.tax.repository import cit_refund

SUPPORTED = {"DIVIDEND", "INTEREST", "ROYALTY"}


@dataclass(frozen=True)
class Flow:
    """One expected income stream: source S pays the holding H, which distributes to parent U."""

    income_category: str
    source: str
    holding: str
    parent: str
    holding_pct: Decimal | None = None
    holding_months: int | None = None
    amount: Decimal | None = None


def _days(months: int | None) -> int | None:
    return None if months is None else months * 365 // 12


def _wht_leg(label: str, r: WhtResult) -> FlowLeg:
    detail = {
        k: str(v)
        for k, v in (
            ("domestic_rate", r.domestic_rate),
            ("effective_domestic_rate", r.effective_domestic_rate),
            ("treaty_cap", r.treaty_cap),
            ("withheld_at_payment", r.withheld_at_payment),
            ("relief_mechanism", r.relief_mechanism),
            ("treaty", r.treaty_name),
        )
        if v is not None
    }
    return FlowLeg(label, "wht", r.final_rate, r.final_rate, r.citations, r.flags, detail)


class FlowCalculator:
    """Total tax leakage per 100 of gross income along S → H → U."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.tax = TaxEngine(session)
        self.wht = WithholdingEngine(session)

    def compute(self, flow: Flow, on_date: date) -> FlowResult:
        cat, s, h, u = flow.income_category, flow.source, flow.holding, flow.parent

        def done(legs: list[FlowLeg], total: Decimal | None, extra: list[Flag]) -> FlowResult:
            return FlowResult(
                income_category=cat,
                source=s,
                holding=h,
                parent=u,
                on_date=on_date,
                legs=tuple(legs),
                total_leakage_pct=None if total is None else q(total),
                citations=merge_citations(*(leg.citations for leg in legs)),
                flags=tuple(extra) + tuple(f for leg in legs for f in leg.flags),
            )

        if cat not in SUPPORTED:
            return done(
                [], None, [Flag("unsupported_flow", f"{cat} flows are not modelled in v1")]
            )

        legs: list[FlowLeg] = []
        flags: list[Flag] = []

        # Leg 1: source-state withholding S → H.
        if s == h:
            legs.append(FlowLeg(f"{s}→{h} {cat.lower()}", "wht", q(ZERO), q(ZERO), ()))
        else:
            r1 = self.wht.compute(s, h, cat, on_date, flow.holding_pct, _days(flow.holding_months))
            legs.append(_wht_leg(f"{s}→{h} {cat.lower()}", r1))
            if not r1.complete:
                return done(legs, None, flags)
        w1 = legs[0].rate or ZERO

        # Leg 2: CIT in H, after its participation exemption.
        cit = self.tax.cit(h, on_date, flow.amount, income_category=cat)
        if cit.rate is None:
            legs.append(FlowLeg(f"{h} corporate tax", "cit", None, None, cit.citations, cit.flags))
            return done(legs, None, flags)
        taxable_share = HUNDRED
        cites = cit.citations
        leg2_flags = list(cit.flags)
        detail = {"cit_rate": str(cit.rate)}
        if cat in PARTICIPATION_INCOME:
            payer_cit = self.tax.cit(s, on_date).rate
            ex = self.tax.participation_exemption(
                h, cat, on_date, flow.holding_pct, flow.holding_months, payer_cit
            )
            cites = merge_citations(cites, ex.citations)
            leg2_flags.extend(ex.flags)
            detail["participation_exemption"] = "applies" if ex.applies else "not applied"
            if ex.reasons:
                detail["exemption_reasons"] = "; ".join(ex.reasons)
            if ex.applies:
                taxable_share = HUNDRED - ex.exempt_share_pct
                detail["exempt_share_pct"] = str(ex.exempt_share_pct)
        h_rate = q(cit.rate * taxable_share / HUNDRED)
        refund = cit_refund(self.session, h, cat, on_date) if h != u else None
        if refund is not None and h_rate > ZERO:
            # The parent recovers part of H's tax when H distributes (e.g. Malta 6/7).
            net = q(h_rate * (HUNDRED - refund.refund_pct) / HUNDRED)
            detail["cit_before_refund"] = str(h_rate)
            detail["shareholder_refund_pct"] = str(refund.refund_pct)
            cites = merge_citations(cites, (refund.source_evidence_id,))
            leg2_flags.append(
                Flag(
                    "shareholder_refund",
                    f"{refund.legal_ref}: {refund.description}; {h_rate}% is paid by {h} and "
                    f"{h_rate - net}% refunded to the shareholder on distribution "
                    "(cash-flow cost; conditions apply)",
                    interpretation_required=True,
                )
            )
            h_rate = net
        if h_rate > ZERO and w1 > ZERO:
            leg2_flags.append(
                Flag(
                    "foreign_tax_credit_not_modelled",
                    f"{h} may credit the {w1}% withheld in {s}; not modelled (conservative)",
                )
            )
        legs.append(
            FlowLeg(f"{h} corporate tax", "cit", h_rate, h_rate, cites, tuple(leg2_flags), detail)
        )

        # Leg 3: onward dividend H → U, on what is left after legs 1 and 2.
        net = max(HUNDRED - w1 - h_rate, ZERO)
        if h == u:
            legs.append(FlowLeg(f"{h}→{u} dividend", "wht", q(ZERO), q(ZERO), ()))
        else:
            flags.append(
                Flag(
                    "parent_holding_assumed",
                    f"{u} assumed to hold 100% of the {h} holding company",
                )
            )
            r3 = self.wht.compute(
                h, u, "DIVIDEND", on_date, HUNDRED, _days(flow.holding_months)
            )
            leg3 = _wht_leg(f"{h}→{u} dividend", r3)
            if not r3.complete or r3.final_rate is None:
                legs.append(leg3)
                return done(legs, None, flags)
            tax3 = q(net * r3.final_rate / HUNDRED)
            legs.append(
                FlowLeg(
                    leg3.leg, leg3.kind, leg3.rate, tax3, leg3.citations, leg3.flags, leg3.detail
                )
            )

        total = sum((leg.tax_per_100 or ZERO for leg in legs), ZERO)
        return done(legs, total, flags)
