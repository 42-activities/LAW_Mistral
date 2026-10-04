from app.modules.core.reference import Currency, IncomeCategory, TaxType
from app.modules.core.reference_repo import ReferenceRepository


def test_lookup_by_code(db_session):
    db_session.add_all([
        Currency(code="EUR", name="Euro"),
        TaxType(code="CIT", name="Corporate income tax"),
        IncomeCategory(code="DIVIDEND", name="Dividend"),
    ])
    db_session.flush()
    repo = ReferenceRepository(db_session)
    assert repo.currency("EUR").name == "Euro"
    assert repo.tax_type("CIT").name == "Corporate income tax"
    assert repo.income_category("DIVIDEND").code == "DIVIDEND"
    assert repo.currency("USD") is None


def test_get_or_create_is_idempotent(db_session):
    repo = ReferenceRepository(db_session)
    a = repo.get_or_create_tax_type("VAT", "Value added tax")
    db_session.flush()
    b = repo.get_or_create_tax_type("VAT", "Value added tax")
    db_session.flush()
    assert a.id == b.id
