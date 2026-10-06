"""Read-only, as-of views for the browse / compare / evidence pages (spec §7)."""

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory, JurisdictionGroup, TaxType
from app.modules.engine.risk import RiskEngine
from app.modules.risk.models import ListDefinition, ListMembership
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.tax.models import DomesticTaxRule, WhtExemption
from app.modules.tax.repository import AntiAbuseRepository, HoldingRegimeRepository
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyParty, TreatyRate


def _d(v: Decimal | None) -> str | None:
    return None if v is None else str(v)


def _period(p: Any) -> dict[str, str | None]:
    return {
        "from": p.lower.isoformat() if p.lower else None,
        "to": p.upper.isoformat() if p.upper else None,
    }


class BrowseService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def evidence(self, evidence_id: int) -> dict[str, Any] | None:
        ev = self.session.get(SourceEvidence, evidence_id)
        if ev is None:
            return None
        doc = self.session.get(SourceDocument, ev.document_id)
        assert doc is not None  # FK-enforced
        return {
            "id": ev.id,
            "document_title": doc.title,
            "document_url": doc.url,
            "retrieved_at": doc.retrieved_at.isoformat(),
            "article": ev.article,
            "page": ev.page,
            "quoted_text": ev.quoted_text,
            "review_status": ev.review_status,
        }

    def corporate_tax(self, on: date) -> list[dict[str, Any]]:
        """Headline corporate income tax per jurisdiction for the map: the flat rate, or for a
        bracketed rule the top (open-ended) bracket, with the lowest bracket as ``min_rate``."""
        stmt = (
            select(Jurisdiction.code, Jurisdiction.name, DomesticTaxRule)
            .join(DomesticTaxRule, DomesticTaxRule.jurisdiction_id == Jurisdiction.id)
            .join(TaxType, DomesticTaxRule.tax_type_id == TaxType.id)
            .join(IncomeCategory, DomesticTaxRule.income_category_id == IncomeCategory.id)
            .where(
                TaxType.code == "CIT",
                IncomeCategory.code == "CORPORATE_PROFIT",
                DomesticTaxRule.valid_period.contains(on),
            )
        )
        found: dict[str, dict[str, Any]] = {}
        for code, name, rule in self.session.execute(stmt):
            rates = [b.rate for b in sorted(rule.brackets, key=lambda b: b.position)]
            top = rates[-1] if rates else rule.rate
            if top is None or (code in found and Decimal(found[code]["rate"]) >= top):
                continue
            found[code] = {
                "code": code,
                "name": name,
                "rate": _d(top),
                "min_rate": _d(min(rates)) if rates else None,
                "bracketed": bool(rates),
                "citation": rule.source_evidence_id,
            }
        wht = self._wht_ranges(on)
        treaties = self._treaty_counts(on)
        out = []
        for c, n in self.session.execute(select(Jurisdiction.code, Jurisdiction.name)):
            row = found.get(c) or {"code": c, "name": n, "rate": None, "min_rate": None,
                                   "bracketed": False, "citation": None}
            regime = HoldingRegimeRepository(self.session).get(c, on)
            row["summary"] = {
                "wht": wht.get(c, {}),
                "participation_exemption": None if regime is None else {
                    "dividends": regime.participation_exemption_dividends,
                    "capital_gains": regime.participation_exemption_capgains,
                    "min_holding_pct": _d(regime.min_holding_pct),
                    "exempt_share_pct": _d(regime.exempt_share_pct),
                },
                "lists": [
                    {"code": h.list_code, "classification": h.classification}
                    for h in RiskEngine(self.session).profile(c, on).memberships
                ],
                "treaties_in_force": treaties.get(c, 0),
            }
            out.append(row)
        return sorted(out, key=lambda r: r["code"])

    def _wht_ranges(self, on: date) -> dict[str, dict[str, dict[str, str]]]:
        """Lowest and highest domestic withholding rate per jurisdiction and income category."""
        stmt = (
            select(Jurisdiction.code, IncomeCategory.code, DomesticTaxRule.rate)
            .join(DomesticTaxRule, DomesticTaxRule.jurisdiction_id == Jurisdiction.id)
            .join(TaxType, DomesticTaxRule.tax_type_id == TaxType.id)
            .join(IncomeCategory, DomesticTaxRule.income_category_id == IncomeCategory.id)
            .where(
                TaxType.code.like("WHT%"),
                IncomeCategory.code.in_(("DIVIDEND", "INTEREST", "ROYALTY")),
                DomesticTaxRule.valid_period.contains(on),
                DomesticTaxRule.rate.is_not(None),
            )
        )
        seen: dict[str, dict[str, list[Decimal]]] = {}
        for code, category, rate in self.session.execute(stmt):
            if rate is None:
                continue
            seen.setdefault(code, {}).setdefault(category, []).append(rate)
        return {
            code: {cat: {"min": str(min(rs)), "max": str(max(rs))} for cat, rs in cats.items()}
            for code, cats in seen.items()
        }

    def _treaty_counts(self, on: date) -> dict[str, int]:
        stmt = (
            select(Jurisdiction.code, func.count(Treaty.id))
            .join(TreatyParty, TreatyParty.jurisdiction_id == Jurisdiction.id)
            .join(Treaty, Treaty.id == TreatyParty.treaty_id)
            .where(Treaty.entry_into_force_date <= on)
            .group_by(Jurisdiction.code)
        )
        return {code: n for code, n in self.session.execute(stmt)}

    def jurisdiction(self, code: str, on: date) -> dict[str, Any] | None:
        j = self.session.scalar(select(Jurisdiction).where(Jurisdiction.code == code))
        if j is None:
            return None
        return {
            "code": j.code,
            "name": j.name,
            "on_date": on.isoformat(),
            "domestic_rules": self._rules(j.id, on),
            "wht_exemptions": self._exemptions(j.id, on),
            "holding_regime": self._regime(code, on),
            "cfc_rule": self._cfc(code, on),
            "substance_rules": [
                {
                    "regime": r.regime,
                    "requirement_band": r.requirement_band,
                    "activity_scope": r.activity_scope,
                    "citation": r.source_evidence_id,
                }
                for r in AntiAbuseRepository(self.session).substance_rules(code, on)
            ],
            "lists": [
                {
                    "list_code": h.list_code,
                    "family": h.family,
                    "classification": h.classification,
                    "citation": h.citation,
                }
                for h in RiskEngine(self.session).profile(code, on).memberships
            ],
            "treaties": self._treaties(j.id, on),
        }

    def _rules(self, jurisdiction_id: int, on: date) -> list[dict[str, Any]]:
        stmt = (
            select(DomesticTaxRule, TaxType.code, IncomeCategory.code)
            .join(TaxType, DomesticTaxRule.tax_type_id == TaxType.id)
            .join(IncomeCategory, DomesticTaxRule.income_category_id == IncomeCategory.id)
            .where(
                DomesticTaxRule.jurisdiction_id == jurisdiction_id,
                DomesticTaxRule.valid_period.contains(on),
            )
            .order_by(TaxType.code, DomesticTaxRule.taxpayer_type)
        )
        out = []
        for rule, tax_type, category in self.session.execute(stmt):
            out.append(
                {
                    "tax_type": tax_type,
                    "income_category": category,
                    "taxpayer_type": rule.taxpayer_type,
                    "rate": _d(rule.rate),
                    "brackets": [
                        {
                            "lower": _d(b.lower_bound),
                            "upper": _d(b.upper_bound),
                            "rate": _d(b.rate),
                        }
                        for b in rule.brackets
                    ],
                    "valid": _period(rule.valid_period),
                    "citation": rule.source_evidence_id,
                }
            )
        return out

    def _exemptions(self, jurisdiction_id: int, on: date) -> list[dict[str, Any]]:
        stmt = (
            select(WhtExemption, IncomeCategory.code, JurisdictionGroup.code)
            .join(IncomeCategory, WhtExemption.income_category_id == IncomeCategory.id)
            .join(JurisdictionGroup, WhtExemption.recipient_group_id == JurisdictionGroup.id)
            .where(
                WhtExemption.jurisdiction_id == jurisdiction_id,
                WhtExemption.valid_period.contains(on),
            )
            .order_by(IncomeCategory.code)
        )
        return [
            {
                "income_category": category,
                "recipient_group": group,
                "min_holding_pct": _d(e.min_holding_pct),
                "min_holding_months": e.min_holding_months,
                "legal_ref": e.legal_ref,
                "description": e.description,
                "citation": e.source_evidence_id,
            }
            for e, category, group in self.session.execute(stmt)
        ]

    def _regime(self, code: str, on: date) -> dict[str, Any] | None:
        r = HoldingRegimeRepository(self.session).get(code, on)
        if r is None:
            return None
        return {
            "dividends_exempt": r.participation_exemption_dividends,
            "capital_gains_exempt": r.participation_exemption_capgains,
            "min_holding_pct": _d(r.min_holding_pct),
            "min_holding_period_months": r.min_holding_period_months,
            "min_subject_to_tax_rate": _d(r.min_subject_to_tax_rate),
            "exempt_share_pct": _d(r.exempt_share_pct),
            "notes": r.notes,
            "valid": _period(r.valid_period),
            "citation": r.source_evidence_id,
        }

    def _cfc(self, code: str, on: date) -> dict[str, Any] | None:
        c = AntiAbuseRepository(self.session).cfc_rule(code, on)
        if c is None:
            return None
        return {
            "control_threshold_pct": _d(c.control_threshold_pct),
            "low_tax_relative_pct": _d(c.low_tax_relative_pct),
            "effect": c.effect,
            "legal_ref": c.legal_ref,
            "citation": c.source_evidence_id,
        }

    def _treaties(self, jurisdiction_id: int, on: date) -> list[dict[str, Any]]:
        treaty_ids = select(TreatyParty.treaty_id).where(
            TreatyParty.jurisdiction_id == jurisdiction_id
        )
        out = []
        for t in self.session.scalars(
            select(Treaty).where(Treaty.id.in_(treaty_ids)).order_by(Treaty.name)
        ):
            others = self.session.scalars(
                select(Jurisdiction.code)
                .join(TreatyParty, TreatyParty.jurisdiction_id == Jurisdiction.id)
                .where(TreatyParty.treaty_id == t.id, Jurisdiction.id != jurisdiction_id)
            )
            rates = self.session.execute(
                select(TreatyRate, IncomeCategory.code, TreatyArticle.article_ref)
                .join(IncomeCategory, TreatyRate.income_category_id == IncomeCategory.id)
                .join(TreatyArticle, TreatyRate.treaty_article_id == TreatyArticle.id)
                .where(TreatyRate.treaty_id == t.id, TreatyRate.valid_period.contains(on))
                .order_by(IncomeCategory.code, TreatyRate.ownership_threshold.nulls_first())
            )
            out.append(
                {
                    "name": t.name,
                    "counterparties": sorted(others),
                    "signature_date": t.signature_date.isoformat(),
                    "entry_into_force_date": t.entry_into_force_date.isoformat()
                    if t.entry_into_force_date
                    else None,
                    "in_force": t.entry_into_force_date is not None
                    and t.entry_into_force_date <= on,
                    "citation": t.source_evidence_id,
                    "rates": [
                        {
                            "income_category": category,
                            "article": article,
                            "max_rate": _d(r.max_rate),
                            "exclusive_residence_taxation": r.exclusive_residence_taxation,
                            "relief_mechanism": r.relief_mechanism,
                            "beneficial_owner_required": r.beneficial_owner_required,
                            "ownership_threshold": _d(r.ownership_threshold),
                            "min_holding_days": r.min_holding_days,
                            "citation": r.source_evidence_id,
                        }
                        for r, category, article in rates
                    ],
                }
            )
        return out

    def lists(self, on: date) -> list[dict[str, Any]]:
        out = []
        for d in self.session.scalars(select(ListDefinition).order_by(ListDefinition.code)):
            members = self.session.execute(
                select(ListMembership, Jurisdiction.code)
                .join(Jurisdiction, ListMembership.jurisdiction_id == Jurisdiction.id)
                .where(
                    ListMembership.list_definition_id == d.id,
                    ListMembership.valid_period.contains(on),
                )
                .order_by(Jurisdiction.code)
            )
            out.append(
                {
                    "code": d.code,
                    "name": d.name,
                    "family": d.family,
                    "publisher": d.publisher,
                    "update_cadence": d.update_cadence,
                    "citation": d.source_evidence_id,
                    "members": [
                        {
                            "jurisdiction": code,
                            "classification": m.classification,
                            "valid": _period(m.valid_period),
                            "citation": m.source_evidence_id,
                        }
                        for m, code in members
                    ],
                }
            )
        return out
