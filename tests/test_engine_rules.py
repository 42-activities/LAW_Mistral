from datetime import UTC, date, datetime
from decimal import Decimal
from itertools import product

import pytest
from sqlalchemy.dialects.postgresql import Range

from app.modules.core.reference_repo import ReferenceRepository
from app.modules.engine.tax import TaxEngine
from app.modules.engine.treaty import TreatyEngine
from app.modules.engine.withholding import WithholdingEngine
from app.modules.seed.france_uae import OLD_TREATY_URL, TREATY_URL, seed
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.treaty.models import MfnClause, MliApplication
from app.modules.treaty.repository import TreatyRepository

D = date(2024, 6, 30)


@pytest.fixture
def seeded(seeded_session):
    return seeded_session


def _evidence(session) -> int:
    doc = SourceDocument(
        title="t", url="https://example.test/t", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    session.add(doc)
    session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    session.add(ev)
    session.flush()
    return ev.id


def _treaty(session):
    return TreatyRepository(session).find_by_parties("FR", "AE")


def codes(flags):
    return {f.code for f in flags}


# --- TaxEngine -------------------------------------------------------------------------------


def test_cit_bracket_boundary_and_average(seeded):
    tax = TaxEngine(seeded)
    assert tax.cit("AE", D, Decimal("375000")).rate == Decimal("0.000")
    assert tax.cit("AE", D, Decimal("750000")).rate == Decimal("4.500")
    assert tax.cit("FR", D).rate == Decimal("25")


def test_cit_missing_rule(seeded):
    r = TaxEngine(seeded).cit("VU", D)
    assert r.rate is None and "missing_cit_rule" in codes(r.flags)


def test_cit_before_validity(seeded):
    assert TaxEngine(seeded).cit("AE", date(2022, 1, 1)).rate is None


@pytest.mark.parametrize(
    ("pct", "months", "payer_cit", "applies"),
    [
        (Decimal("5"), 12, Decimal("25"), True),
        (Decimal("4.999"), 12, Decimal("25"), False),
        (Decimal("5"), 11, Decimal("25"), False),
        (Decimal("5"), 12, Decimal("8.999"), False),
        (Decimal("5"), 12, None, False),
        (None, 12, Decimal("25"), False),
    ],
)
def test_uae_participation_exemption_conditions(seeded, pct, months, payer_cit, applies):
    ex = TaxEngine(seeded).participation_exemption("AE", "DIVIDEND", D, pct, months, payer_cit)
    assert ex.applies is applies
    assert ex.exempt_share_pct == (Decimal("100") if applies else Decimal("0"))
    assert ex.citations


def test_france_exemption_share_is_95(seeded):
    ex = TaxEngine(seeded).participation_exemption(
        "FR", "DIVIDEND", D, Decimal("10"), 24, Decimal("0")
    )
    assert ex.applies and ex.exempt_share_pct == Decimal("95")


def test_exemption_not_for_royalties(seeded):
    assert not TaxEngine(seeded).participation_exemption(
        "AE", "ROYALTY", D, Decimal("100"), 24, Decimal("25")
    ).applies


# --- TreatyEngine ----------------------------------------------------------------------------


def test_treaty_not_in_force_before_entry(seeded):
    terms, flags = TreatyEngine(seeded).terms("FR", "AE", "DIVIDEND", date(1990, 6, 30))
    assert terms is None and "treaty_not_in_force" in codes(flags)


def test_treaty_threshold(seeded):
    rate = TreatyRepository(seeded).get_rate(_treaty(seeded).id, "DIVIDEND", D)
    rate.ownership_threshold = Decimal("10")
    seeded.flush()
    engine = TreatyEngine(seeded)
    terms, flags = engine.terms("FR", "AE", "DIVIDEND", D, Decimal("9"))
    assert terms is None and "treaty_threshold_not_met" in codes(flags)
    terms, _ = engine.terms("FR", "AE", "DIVIDEND", D, Decimal("10"))
    assert terms is not None


def test_mli_ppt_and_holding_period(seeded):
    treaty = _treaty(seeded)
    rate = TreatyRepository(seeded).get_rate(treaty.id, "DIVIDEND", D)
    rate.ownership_threshold = Decimal("10")
    seeded.add(
        MliApplication(
            treaty_id=treaty.id,
            ppt_applies=True,
            dividend_min_holding_days=365,
            source_evidence_id=_evidence(seeded),
            valid_period=Range(date(2019, 1, 1), None, bounds="[)"),
        )
    )
    seeded.flush()
    engine = TreatyEngine(seeded)
    terms, flags = engine.terms("FR", "AE", "DIVIDEND", D, Decimal("50"), 200)
    assert terms is None and {"mli_ppt", "mli_holding_period_not_met"} <= codes(flags)
    terms, flags = engine.terms("FR", "AE", "DIVIDEND", D, Decimal("50"), 365)
    assert terms is not None and "mli_ppt" in codes(flags)


def test_mfn_clause_flags_interpretation(seeded):
    treaty = _treaty(seeded)
    seeded.add(
        MfnClause(
            treaty_id=treaty.id,
            income_category_id=ReferenceRepository(seeded).income_category("ROYALTY").id,
            description="test clause",
            source_evidence_id=_evidence(seeded),
            valid_period=Range(date(2000, 1, 1), None, bounds="[)"),
        )
    )
    seeded.flush()
    r = WithholdingEngine(seeded).compute("FR", "AE", "ROYALTY", D)
    mfn = [f for f in r.flags if f.code == "mfn_clause"]
    assert mfn and mfn[0].interpretation_required
    assert r.final_rate == Decimal("0")  # never auto-applied


def test_no_treaty(seeded):
    terms, flags = TreatyEngine(seeded).terms("FR", "VU", "DIVIDEND", D)
    assert terms is None and "no_treaty" in codes(flags)


# --- WithholdingEngine properties ------------------------------------------------------------


def test_withholding_invariants_over_seeded_corridors(seeded):
    engine = WithholdingEngine(seeded)
    jurisdictions = ["FR", "AE", "VU", "PA"]
    dates = [date(2023, 6, 1), D, date(2025, 6, 1), date(2026, 10, 1)]
    categories = ["DIVIDEND", "INTEREST", "ROYALTY"]
    for s, r, cat, d in product(jurisdictions, jurisdictions, categories, dates):
        res = engine.compute(s, r, cat, d, Decimal("100"), 730)
        if not res.complete:
            continue
        assert res.final_rate <= res.effective_domestic_rate
        assert res.withheld_at_payment >= res.final_rate
        if res.treaty_cap is not None:
            assert res.final_rate <= res.treaty_cap
        assert res.citations, (s, r, cat, d)


def test_same_jurisdiction_payment(seeded):
    r = WithholdingEngine(seeded).compute("FR", "FR", "DIVIDEND", D)
    assert not r.complete and "domestic_payment" in codes(r.flags)


# --- Seed corrections ------------------------------------------------------------------------


def test_seed_corrects_p1_rows(seeded):
    treaty = _treaty(seeded)
    repo = TreatyRepository(seeded)
    # Recreate the P1 state, then re-seed.
    treaty.entry_into_force_date = None
    for p in treaty.protocols:
        p.entry_into_force_date = date(1994, 1, 1)
    repo.get_rate(treaty.id, "DIVIDEND", D).valid_period = Range(
        date(1994, 1, 1), None, bounds="[)"
    )
    doc = seeded.query(SourceDocument).filter_by(url=TREATY_URL).one()
    doc.url = OLD_TREATY_URL
    seeded.flush()

    seed(seeded)
    seeded.flush()
    seeded.refresh(treaty)
    assert treaty.entry_into_force_date == date(1990, 7, 1)
    assert all(p.entry_into_force_date == date(1995, 6, 1) for p in treaty.protocols)
    assert repo.get_rate(treaty.id, "DIVIDEND", D).valid_period.lower == date(1995, 6, 1)
    assert seeded.query(SourceDocument).filter_by(url=OLD_TREATY_URL).count() == 0
