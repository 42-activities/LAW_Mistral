from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.reference import Currency, IncomeCategory, TaxType


class ReferenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def currency(self, code: str) -> Currency | None:
        return self.session.scalar(select(Currency).where(Currency.code == code))

    def tax_type(self, code: str) -> TaxType | None:
        return self.session.scalar(select(TaxType).where(TaxType.code == code))

    def income_category(self, code: str) -> IncomeCategory | None:
        return self.session.scalar(select(IncomeCategory).where(IncomeCategory.code == code))

    def get_or_create_currency(self, code: str, name: str) -> Currency:
        row = self.currency(code)
        if row is None:
            row = Currency(code=code, name=name)
            self.session.add(row)
        return row

    def get_or_create_tax_type(self, code: str, name: str) -> TaxType:
        row = self.tax_type(code)
        if row is None:
            row = TaxType(code=code, name=name)
            self.session.add(row)
        return row

    def get_or_create_income_category(self, code: str, name: str) -> IncomeCategory:
        row = self.income_category(code)
        if row is None:
            row = IncomeCategory(code=code, name=name)
            self.session.add(row)
        return row
