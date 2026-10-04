from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory, TaxType
from app.modules.tax.models import CfcRule, DomesticTaxRule, HoldingRegime, SubstanceRule


class TaxRuleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_rule(
        self,
        jurisdiction_code: str,
        tax_type_code: str,
        income_category_code: str,
        on_date: date,
        taxpayer_type: str = "any",
    ) -> DomesticTaxRule | None:
        stmt = (
            select(DomesticTaxRule)
            .join(Jurisdiction, DomesticTaxRule.jurisdiction_id == Jurisdiction.id)
            .join(TaxType, DomesticTaxRule.tax_type_id == TaxType.id)
            .join(IncomeCategory, DomesticTaxRule.income_category_id == IncomeCategory.id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                TaxType.code == tax_type_code,
                IncomeCategory.code == income_category_code,
                DomesticTaxRule.taxpayer_type == taxpayer_type,
                DomesticTaxRule.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)


def resolve_bracket_rate(rule: DomesticTaxRule, amount: Decimal) -> Decimal:
    if not rule.is_bracketed:
        if rule.rate is None:
            raise ValueError("flat rule has no rate")
        return rule.rate
    for bracket in rule.brackets:
        upper_ok = bracket.upper_bound is None or amount < bracket.upper_bound
        if amount >= bracket.lower_bound and upper_ok:
            return bracket.rate
    raise ValueError(f"no bracket covers amount {amount}")


class HoldingRegimeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, jurisdiction_code: str, on_date: date) -> HoldingRegime | None:
        stmt = (
            select(HoldingRegime)
            .join(Jurisdiction, HoldingRegime.jurisdiction_id == Jurisdiction.id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                HoldingRegime.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)


class AntiAbuseRepository:
    """CFC and substance rules (coarse, spec §3 factor 4)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def cfc_rule(self, jurisdiction_code: str, on_date: date) -> CfcRule | None:
        stmt = (
            select(CfcRule)
            .join(Jurisdiction, CfcRule.jurisdiction_id == Jurisdiction.id)
            .where(Jurisdiction.code == jurisdiction_code, CfcRule.valid_period.contains(on_date))
        )
        return self.session.scalar(stmt)

    def substance_rules(self, jurisdiction_code: str, on_date: date) -> list[SubstanceRule]:
        stmt = (
            select(SubstanceRule)
            .join(Jurisdiction, SubstanceRule.jurisdiction_id == Jurisdiction.id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                SubstanceRule.valid_period.contains(on_date),
            )
            .order_by(SubstanceRule.regime)
        )
        return list(self.session.scalars(stmt))
