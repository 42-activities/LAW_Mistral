from datetime import date
from decimal import Decimal

from app.modules.risk.models import ListMembership, RegulatoryConsequence
from app.modules.risk.repository import ConsequenceRepository, ListRepository
from app.modules.seed.france_uae import seed


def test_seed_lists_idempotent_and_resolves(db_session):
    seed(db_session)
    seed(db_session)  # idempotent
    db_session.flush()

    lists = ListRepository(db_session)
    # UAE FATF grey: listed during the window, not after removal
    assert lists.is_listed("AE", "FATF_GREY", date(2023, 1, 1)) is not None
    assert lists.is_listed("AE", "FATF_GREY", date(2024, 6, 1)) is None
    # UAE EU AML high-risk window
    assert lists.is_listed("AE", "EU_AML_HIGH_RISK", date(2024, 1, 1)) is not None
    assert lists.is_listed("AE", "EU_AML_HIGH_RISK", date(2026, 1, 1)) is None
    # Vanuatu currently on FR ETNC (full measures)
    vu = lists.is_listed("VU", "FR_ETNC", date(2026, 1, 1))
    assert vu is not None and vu.classification == "full_measures"

    cons = ConsequenceRepository(db_session)
    etnc = cons.triggered_by("FR_ETNC", "full_measures", date(2026, 1, 1))
    assert len(etnc) == 1 and etnc[0].rate == Decimal("75")


def test_every_list_row_has_evidence(db_session):
    seed(db_session)
    db_session.flush()
    for model in (ListMembership, RegulatoryConsequence):
        rows = db_session.query(model).all()
        assert rows and all(r.source_evidence_id is not None for r in rows)
