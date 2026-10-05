from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory
from app.modules.treaty.models import (
    MfnClause,
    MliApplication,
    Treaty,
    TreatyArticle,
    TreatyParty,
    TreatyRate,
)


class TreatyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_parties(self, code_a: str, code_b: str) -> Treaty | None:
        stmt = select(Treaty).where(
            Treaty.id.in_(
                select(TreatyParty.treaty_id)
                .join(Jurisdiction, TreatyParty.jurisdiction_id == Jurisdiction.id)
                .where(Jurisdiction.code == code_a)
            ),
            Treaty.id.in_(
                select(TreatyParty.treaty_id)
                .join(Jurisdiction, TreatyParty.jurisdiction_id == Jurisdiction.id)
                .where(Jurisdiction.code == code_b)
            ),
        )
        return self.session.scalar(stmt)

    def get_rate(
        self, treaty_id: int, income_category_code: str, on_date: date
    ) -> TreatyRate | None:
        stmt = (
            select(TreatyRate)
            .join(IncomeCategory, TreatyRate.income_category_id == IncomeCategory.id)
            .where(
                TreatyRate.treaty_id == treaty_id,
                IncomeCategory.code == income_category_code,
                TreatyRate.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)

    def get_article(self, treaty_id: int, article_category: str) -> TreatyArticle | None:
        stmt = select(TreatyArticle).where(
            TreatyArticle.treaty_id == treaty_id,
            TreatyArticle.article_category == article_category,
        )
        return self.session.scalar(stmt)

    def get_mli(self, treaty_id: int, on_date: date) -> MliApplication | None:
        stmt = select(MliApplication).where(
            MliApplication.treaty_id == treaty_id, MliApplication.valid_period.contains(on_date)
        )
        return self.session.scalar(stmt)

    def get_mfn(
        self, treaty_id: int, income_category_code: str, on_date: date
    ) -> MfnClause | None:
        stmt = (
            select(MfnClause)
            .join(IncomeCategory, MfnClause.income_category_id == IncomeCategory.id)
            .where(
                MfnClause.treaty_id == treaty_id,
                IncomeCategory.code == income_category_code,
                MfnClause.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)

    def get_rates(
        self, treaty_id: int, income_category_code: str, on_date: date
    ) -> list[TreatyRate]:
        """Every ownership tier valid on the date (one row when the treaty has a single rate)."""
        stmt = (
            select(TreatyRate)
            .join(IncomeCategory, TreatyRate.income_category_id == IncomeCategory.id)
            .where(
                TreatyRate.treaty_id == treaty_id,
                IncomeCategory.code == income_category_code,
                TreatyRate.valid_period.contains(on_date),
            )
            .order_by(TreatyRate.id)
        )
        return list(self.session.scalars(stmt))
