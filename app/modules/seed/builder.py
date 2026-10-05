"""Idempotent helpers for seeding verified jurisdiction data (P8 batches).

Each helper inserts a row only when no row with the same logical key is valid on the start
date, so re-running a seed never duplicates and never violates the exclusion constraints.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup, JurisdictionGroupMember
from app.modules.core.reference_repo import ReferenceRepository
from app.modules.core.repository import JurisdictionRepository
from app.modules.risk.models import ListMembership, RegulatoryConsequence
from app.modules.risk.repository import ListDefinitionRepository, ListRepository
from app.modules.seed.sources import upsert_source
from app.modules.tax.models import (
    CfcRule,
    CitRefund,
    DomesticTaxRule,
    HoldingRegime,
    TaxBracket,
    WhtExemption,
)
from app.modules.treaty.models import (
    MliApplication,
    Treaty,
    TreatyArticle,
    TreatyParty,
    TreatyRate,
)
from app.modules.treaty.repository import TreatyRepository

RETRIEVED_AT = datetime(2026, 10, 5, tzinfo=UTC)

TAX_TYPES = {
    "CIT": "Corporate income tax",
    "WHT_DIVIDEND": "Withholding tax on dividends",
    "WHT_INTEREST": "Withholding tax on interest",
    "WHT_ROYALTY": "Withholding tax on royalties",
}
CATEGORIES = {
    "DIVIDEND": "Dividends",
    "INTEREST": "Interest",
    "ROYALTY": "Royalties",
    "CORPORATE_PROFIT": "Corporate profit",
}
WHT_FOR = {"DIVIDEND": "WHT_DIVIDEND", "INTEREST": "WHT_INTEREST", "ROYALTY": "WHT_ROYALTY"}
ARTICLE_CATEGORY = {"DIVIDEND": "DIVIDENDS", "INTEREST": "INTEREST", "ROYALTY": "ROYALTIES"}


@dataclass(frozen=True)
class Src:
    """A verified extract: where it is and what it says."""

    title: str
    url: str
    article: str | None
    quote: str
    review_status: str = "unreviewed"


def period(start: date, end: date | None = None) -> Range[date]:
    return Range(start, end, bounds="[)")


class Seeder:
    def __init__(self, session: Session) -> None:
        self.s = session
        self.ref = ReferenceRepository(session)
        for code, name in TAX_TYPES.items():
            self.ref.get_or_create_tax_type(code, name)
        for code, name in CATEGORIES.items():
            self.ref.get_or_create_income_category(code, name)
        session.flush()

    def ev(self, src: Src) -> int:
        return upsert_source(
            self.s,
            title=src.title,
            url=src.url,
            retrieved_at=RETRIEVED_AT,
            content_hash="fixture-v1",
            article=src.article,
            quoted_text=src.quote,
            review_status=src.review_status,
        ).id

    def jurisdiction(self, code: str, name: str) -> Jurisdiction:
        repo = JurisdictionRepository(self.s)
        return repo.get_by_code(code) or repo.create(code, name)

    def _id(self, kind: str, code: str) -> int:
        row = self.ref.tax_type(code) if kind == "tax" else self.ref.income_category(code)
        assert row is not None, code
        return row.id

    def _rule_exists(self, j: int, tt: int, ic: int, taxpayer: str, start: date) -> bool:
        return (
            self.s.scalar(
                select(DomesticTaxRule.id).where(
                    DomesticTaxRule.jurisdiction_id == j,
                    DomesticTaxRule.tax_type_id == tt,
                    DomesticTaxRule.income_category_id == ic,
                    DomesticTaxRule.taxpayer_type == taxpayer,
                    DomesticTaxRule.valid_period.contains(start),
                )
            )
            is not None
        )

    def wht(
        self, j: Jurisdiction, category: str, rate: str, start: date, src: Src,
        taxpayer: str = "company",
    ) -> None:
        tt, ic = self._id("tax", WHT_FOR[category]), self._id("cat", category)
        if self._rule_exists(j.id, tt, ic, taxpayer, start):
            return
        self.s.add(
            DomesticTaxRule(
                jurisdiction_id=j.id, tax_type_id=tt, income_category_id=ic,
                taxpayer_type=taxpayer, rate=Decimal(rate), is_bracketed=False,
                source_evidence_id=self.ev(src), valid_period=period(start),
            )
        )
        self.s.flush()

    def cit(
        self,
        j: Jurisdiction,
        start: date,
        src: Src,
        rate: str | None = None,
        brackets: list[tuple[str, str | None, str]] | None = None,
        end: date | None = None,
        category: str = "CORPORATE_PROFIT",
    ) -> None:
        """General CIT, or CIT for one income category (e.g. passive royalties)."""
        tt, ic = self._id("tax", "CIT"), self._id("cat", category)
        if self._rule_exists(j.id, tt, ic, "company", start):
            return
        rule = DomesticTaxRule(
            jurisdiction_id=j.id, tax_type_id=tt, income_category_id=ic, taxpayer_type="company",
            rate=None if brackets else Decimal(str(rate)), is_bracketed=bool(brackets),
            source_evidence_id=self.ev(src), valid_period=period(start, end),
        )
        self.s.add(rule)
        self.s.flush()
        for i, (lower, upper, r) in enumerate(brackets or [], start=1):
            self.s.add(
                TaxBracket(
                    domestic_tax_rule_id=rule.id, lower_bound=Decimal(lower),
                    upper_bound=None if upper is None else Decimal(upper), rate=Decimal(r),
                    position=i,
                )
            )
        self.s.flush()

    def regime(
        self, j: Jurisdiction, start: date, src: Src, end: date | None = None, **fields: object
    ) -> None:
        exists = self.s.scalar(
            select(HoldingRegime.id).where(
                HoldingRegime.jurisdiction_id == j.id, HoldingRegime.valid_period.contains(start)
            )
        )
        if exists is None:
            self.s.add(
                HoldingRegime(
                    jurisdiction_id=j.id, source_evidence_id=self.ev(src),
                    valid_period=period(start, end), **fields,
                )
            )
            self.s.flush()

    def cfc(self, j: Jurisdiction, start: date, src: Src, **fields: object) -> None:
        exists = self.s.scalar(
            select(CfcRule.id).where(
                CfcRule.jurisdiction_id == j.id, CfcRule.valid_period.contains(start)
            )
        )
        if exists is None:
            self.s.add(
                CfcRule(jurisdiction_id=j.id, source_evidence_id=self.ev(src),
                        valid_period=period(start), **fields)
            )
            self.s.flush()

    def group(self, code: str, name: str) -> JurisdictionGroup:
        g = self.s.scalar(select(JurisdictionGroup).where(JurisdictionGroup.code == code))
        if g is None:
            g = JurisdictionGroup(code=code, name=name)
            self.s.add(g)
            self.s.flush()
        return g

    def member(self, g: JurisdictionGroup, j: Jurisdiction, start: date, src: Src) -> None:
        exists = self.s.scalar(
            select(JurisdictionGroupMember.id).where(
                JurisdictionGroupMember.group_id == g.id,
                JurisdictionGroupMember.jurisdiction_id == j.id,
                JurisdictionGroupMember.valid_period.contains(start),
            )
        )
        if exists is None:
            self.s.add(
                JurisdictionGroupMember(
                    group_id=g.id, jurisdiction_id=j.id, source_evidence_id=self.ev(src),
                    valid_period=period(start),
                )
            )
            self.s.flush()

    def exemption(
        self, j: Jurisdiction, category: str, g: JurisdictionGroup, start: date, src: Src, *,
        min_holding_pct: str | None, min_holding_months: int | None, legal_ref: str,
        description: str, reduced_rate: str | None = None,
    ) -> None:
        ic = self._id("cat", category)
        threshold = None if min_holding_pct is None else Decimal(min_holding_pct)
        exists = self.s.scalar(
            select(WhtExemption.id).where(
                WhtExemption.jurisdiction_id == j.id,
                WhtExemption.income_category_id == ic,
                WhtExemption.recipient_group_id == g.id,
                WhtExemption.min_holding_pct.is_(None)
                if threshold is None
                else WhtExemption.min_holding_pct == threshold,
                WhtExemption.valid_period.contains(start),
            )
        )
        if exists is None:
            self.s.add(
                WhtExemption(
                    jurisdiction_id=j.id, income_category_id=ic, recipient_group_id=g.id,
                    min_holding_pct=threshold,
                    reduced_rate=None if reduced_rate is None else Decimal(reduced_rate),
                    min_holding_months=min_holding_months, legal_ref=legal_ref,
                    description=description, source_evidence_id=self.ev(src),
                    valid_period=period(start),
                )
            )
            self.s.flush()

    def consequence(
        self, applier: Jurisdiction, list_code: str, category: str | None, rate: str,
        start: date, src: Src, *, legal_ref: str, description: str,
        classification: str = "",
    ) -> None:
        definition = ListDefinitionRepository(self.s).get(list_code)
        assert definition is not None, list_code
        ic = None if category is None else self._id("cat", category)
        exists = self.s.scalar(
            select(RegulatoryConsequence.id).where(
                RegulatoryConsequence.applying_jurisdiction_id == applier.id,
                RegulatoryConsequence.list_definition_id == definition.id,
                RegulatoryConsequence.classification_trigger == classification,
                RegulatoryConsequence.consequence_type == "withholding_tax",
                RegulatoryConsequence.income_category_id.is_(None)
                if ic is None
                else RegulatoryConsequence.income_category_id == ic,
                RegulatoryConsequence.valid_period.contains(start),
            )
        )
        if exists is None:
            self.s.add(
                RegulatoryConsequence(
                    applying_jurisdiction_id=applier.id, list_definition_id=definition.id,
                    classification_trigger=classification, consequence_type="withholding_tax",
                    income_category_id=ic, rate=Decimal(rate), legal_ref=legal_ref,
                    description=description, source_evidence_id=self.ev(src),
                    valid_period=period(start),
                )
            )
            self.s.flush()

    def treaty(
        self, a: Jurisdiction, b: Jurisdiction, *, name: str, signed: date,
        in_force: date | None, src: Src,
    ) -> Treaty:
        t = TreatyRepository(self.s).find_by_parties(a.code, b.code)
        if t is None:
            t = Treaty(name=name, signature_date=signed, entry_into_force_date=in_force,
                       source_evidence_id=self.ev(src))
            self.s.add(t)
            self.s.flush()
            self.s.add_all([TreatyParty(treaty_id=t.id, jurisdiction_id=a.id),
                            TreatyParty(treaty_id=t.id, jurisdiction_id=b.id)])
            self.s.flush()
        return t

    def treaty_rate(
        self, t: Treaty, category: str, article_ref: str, start: date, src: Src, *,
        max_rate: str | None = None, exclusive: bool = False,
        ownership_threshold: str | None = None, min_holding_days: int | None = None,
        relief: str | None = None, beneficial_owner: bool = True,
        source: Jurisdiction | None = None,
    ) -> None:
        repo = TreatyRepository(self.s)
        article = repo.get_article(t.id, ARTICLE_CATEGORY[category])
        if article is None:
            article = TreatyArticle(
                treaty_id=t.id, article_category=ARTICLE_CATEGORY[category],
                article_ref=article_ref,
            )
            self.s.add(article)
            self.s.flush()
        threshold = None if ownership_threshold is None else Decimal(ownership_threshold)
        source_id = None if source is None else source.id
        if any(
            r.ownership_threshold == threshold and r.source_jurisdiction_id == source_id
            for r in repo.get_rates(t.id, category, start)
        ):
            return
        self.s.add(
            TreatyRate(
                treaty_id=t.id, treaty_article_id=article.id,
                income_category_id=self._id("cat", category),
                max_rate=None if max_rate is None else Decimal(max_rate),
                exclusive_residence_taxation=exclusive, relief_mechanism=relief,
                beneficial_owner_required=beneficial_owner, ownership_threshold=threshold,
                min_holding_days=min_holding_days, source_jurisdiction_id=source_id,
                source_evidence_id=self.ev(src),
                valid_period=period(start),
            )
        )
        self.s.flush()

    def ppt(
        self, t: Treaty, start: date, src: Src, *, dividend_min_holding_days: int | None = None
    ) -> None:
        """Principal purpose test from the MLI or the treaty's own clause."""
        if TreatyRepository(self.s).get_mli(t.id, start) is None:
            self.s.add(
                MliApplication(
                    treaty_id=t.id, ppt_applies=True,
                    dividend_min_holding_days=dividend_min_holding_days,
                    source_evidence_id=self.ev(src), valid_period=period(start),
                )
            )
            self.s.flush()

    def listing(
        self, j: Jurisdiction, list_code: str, classification: str, start: date,
        end: date | None, src: Src,
    ) -> None:
        definition = ListDefinitionRepository(self.s).get(list_code)
        assert definition is not None, list_code
        if ListRepository(self.s).is_listed(j.code, list_code, start) is None:
            self.s.add(
                ListMembership(
                    list_definition_id=definition.id, jurisdiction_id=j.id,
                    classification=classification, announcement_date=start,
                    source_evidence_id=self.ev(src), valid_period=period(start, end),
                )
            )
            self.s.flush()

    def refund(
        self, j: Jurisdiction, category: str, refund_pct: str, start: date, src: Src, *,
        legal_ref: str, description: str,
    ) -> None:
        ic = self._id("cat", category)
        exists = self.s.scalar(
            select(CitRefund.id).where(
                CitRefund.jurisdiction_id == j.id,
                CitRefund.income_category_id == ic,
                CitRefund.valid_period.contains(start),
            )
        )
        if exists is None:
            self.s.add(
                CitRefund(
                    jurisdiction_id=j.id, income_category_id=ic,
                    refund_pct=Decimal(refund_pct), legal_ref=legal_ref,
                    description=description, source_evidence_id=self.ev(src),
                    valid_period=period(start),
                )
            )
            self.s.flush()
