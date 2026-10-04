import pytest

from app.modules.core.repository import DuplicateCodeError, JurisdictionRepository


def test_create_and_get_by_code(db_session):
    repo = JurisdictionRepository(db_session)
    created = repo.create(code="AE", name="United Arab Emirates")
    db_session.flush()
    assert created.id is not None
    assert repo.get_by_code("AE").name == "United Arab Emirates"


def test_duplicate_code_raises(db_session):
    repo = JurisdictionRepository(db_session)
    repo.create(code="FR", name="France")
    db_session.flush()
    with pytest.raises(DuplicateCodeError):
        repo.create(code="FR", name="France Again")
        db_session.flush()
