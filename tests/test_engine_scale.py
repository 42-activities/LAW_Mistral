"""P8 mechanics on synthetic data: group exemptions, tiered treaty rates, consequences per type."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.dialects.postgresql import Range

from app.modules.core.reference import JurisdictionGroup, JurisdictionGroupMember
from app.modules.core.reference_repo import ReferenceRepository
from app.modules.core.repository import JurisdictionRepository
from app.modules.engine.withholding import WithholdingEngine
from app.modules.risk.models import ListMembership, RegulatoryConsequence
from app.modules.risk.repository import ListDefinitionRepository
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.tax.models import WhtExemption
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyParty, TreatyRate

D = date(2026, 6, 30)
ALWAYS = Range(date(2000, 1, 1), None, bounds="[)")


@pytest.fixture
def world(seeded_session):
    s = seeded_session
    doc = SourceDocument(
        title="t", url="https://example.test/s", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    s.add(doc)
    s.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    s.add(ev)
    s.flush()
    jr = JurisdictionRepository(s)
    zl = jr.create("ZL", "Zedland")
    fr = jr.get_by_code("FR")
    eu = JurisdictionGroup(code="EU_TEST", name="test union")
    s.add(eu)
    s.flush()
    for j in (fr, zl):
        s.add(JurisdictionGroupMember(group_id=eu.id, jurisdiction_id=j.id,
                                      source_evidence_id=ev.id, valid_period=ALWAYS))
    ref = ReferenceRepository(s)
    div, roy = ref.income_category("DIVIDEND"), ref.income_category("ROYALTY")
    s.add(WhtExemption(jurisdiction_id=fr.id, income_category_id=div.id,
                       recipient_group_id=eu.id, min_holding_pct=Decimal("10"),
                       min_holding_months=24, legal_ref="TEST art. 1",
                       description="parent-subsidiary relief", source_evidence_id=ev.id,
                       valid_period=ALWAYS))
    treaty = Treaty(name="FR-ZL test treaty", signature_date=date(2010, 1, 1),
                    entry_into_force_date=date(2011, 1, 1), source_evidence_id=ev.id)
    s.add(treaty)
    s.flush()
    s.add_all([TreatyParty(treaty_id=treaty.id, jurisdiction_id=fr.id),
               TreatyParty(treaty_id=treaty.id, jurisdiction_id=zl.id)])
    art = TreatyArticle(treaty_id=treaty.id, article_category="ROYALTIES", article_ref="Art. 12")
    s.add(art)
    s.flush()
    for cap, threshold, days in ((Decimal("15"), None, None), (Decimal("5"), Decimal("10"), 365)):
        s.add(TreatyRate(treaty_id=treaty.id, treaty_article_id=art.id, income_category_id=roy.id,
                         max_rate=cap, ownership_threshold=threshold, min_holding_days=days,
                         relief_mechanism="at_source", source_evidence_id=ev.id,
                         valid_period=ALWAYS))
    s.flush()
    return s, ev, zl


def codes(r):
    return {f.code for f in r.flags}


def test_group_exemption_applies_when_conditions_met(world):
    s, *_ = world
    r = WithholdingEngine(s).compute("FR", "ZL", "DIVIDEND", D, Decimal("10"), 730)
    assert r.domestic_rate == Decimal("25.000") and r.effective_domestic_rate == Decimal("0.000")
    assert r.final_rate == Decimal("0.000")
    assert {"directive_exemption", "exemption_anti_abuse"} <= codes(r)


@pytest.mark.parametrize(
    ("pct", "days"), [(Decimal("9.9"), 730), (Decimal("50"), 300), (None, 730)]
)
def test_group_exemption_conditions_not_met(world, pct, days):
    s, *_ = world
    r = WithholdingEngine(s).compute("FR", "ZL", "DIVIDEND", D, pct, days)
    assert r.domestic_rate == Decimal("25.000")
    assert "exemption_conditions_not_met" in codes(r)


def test_non_member_gets_no_exemption(world):
    s, *_ = world
    r = WithholdingEngine(s).compute("FR", "AE", "ROYALTY", D, Decimal("100"), 730)
    assert "directive_exemption" not in codes(r)


@pytest.mark.parametrize(
    ("pct", "days", "cap", "flag"),
    [
        (Decimal("20"), 400, "5.000", None),
        (Decimal("20"), 100, "15.000", "treaty_holding_period_not_met"),
        (Decimal("5"), 400, "15.000", "treaty_threshold_not_met"),
        (None, None, "15.000", "treaty_threshold_not_met"),
    ],
)
def test_tiered_treaty_rates(world, pct, days, cap, flag):
    s, *_ = world
    r = WithholdingEngine(s).compute("FR", "ZL", "ROYALTY", D, pct, days)
    assert str(r.treaty_cap) == cap and str(r.final_rate) == cap
    if flag:
        assert flag in codes(r)


def test_consequence_limited_to_one_income_category(world):
    s, ev, zl = world
    fr = JurisdictionRepository(s).get_by_code("FR")
    defs = ListDefinitionRepository(s)
    s.add(ListMembership(list_definition_id=defs.get("EU_TAX_ANNEX_I").id, jurisdiction_id=zl.id,
                         classification="listed", source_evidence_id=ev.id, valid_period=ALWAYS))
    s.add(RegulatoryConsequence(
        applying_jurisdiction_id=fr.id, list_definition_id=defs.get("EU_TAX_ANNEX_I").id,
        consequence_type="withholding_tax",
        income_category_id=ReferenceRepository(s).income_category("ROYALTY").id,
        rate=Decimal("40"), legal_ref="TEST art. 2", source_evidence_id=ev.id,
        valid_period=ALWAYS,
    ))
    s.flush()
    engine = WithholdingEngine(s)
    royalty = engine.compute("FR", "ZL", "ROYALTY", D)
    assert royalty.effective_domestic_rate == Decimal("40.000")
    dividend = engine.compute("FR", "ZL", "DIVIDEND", D)
    assert dividend.consequences == ()
