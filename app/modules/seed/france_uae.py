from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference_repo import ReferenceRepository
from app.modules.core.repository import JurisdictionRepository
from app.modules.seed.sources import upsert_source
from app.modules.source.models import SourceEvidence
from app.modules.tax.models import DomesticTaxRule, HoldingRegime, TaxBracket
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyParty, TreatyProtocol, TreatyRate
from app.modules.treaty.repository import TreatyRepository

RETRIEVED_AT = datetime(2026, 10, 4, tzinfo=UTC)
UAE_CT_FROM = date(2023, 6, 1)
FR_FROM = date(2023, 1, 1)

MOF_URL = "https://mof.gov.ae/corporate-tax/"
PWC_UAE_URL = "https://taxsummaries.pwc.com/united-arab-emirates/corporate/withholding-taxes"
PWC_FR_URL = "https://taxsummaries.pwc.com/france/corporate/withholding-taxes"
LEGIFRANCE_URL = "https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006069577/"
TREATY_URL = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/"
    "emirats_arabes_unis/convention-france-emirats-arabes-unis.pdf"
)


def _period(start: date) -> Range[date]:
    return Range(start, None, bounds="[)")


def _src(session: Session, title: str, url: str, article: str | None, quote: str) -> SourceEvidence:
    return upsert_source(
        session,
        title=title,
        url=url,
        retrieved_at=RETRIEVED_AT,
        content_hash="fixture-v1",
        article=article,
        quoted_text=quote,
    )


def _jurisdiction(session: Session, code: str, name: str) -> Jurisdiction:
    repo = JurisdictionRepository(session)
    row = repo.get_by_code(code)
    if row is None:
        row = repo.create(code, name)
    return row


def _rule_exists(
    session: Session, j: int, tt: int, ic: int, taxpayer_type: str, start: date
) -> bool:
    stmt = select(DomesticTaxRule.id).where(
        DomesticTaxRule.jurisdiction_id == j,
        DomesticTaxRule.tax_type_id == tt,
        DomesticTaxRule.income_category_id == ic,
        DomesticTaxRule.taxpayer_type == taxpayer_type,
        DomesticTaxRule.valid_period.contains(start),
    )
    return session.scalar(stmt) is not None


def seed(session: Session) -> None:
    ref = ReferenceRepository(session)
    fr = _jurisdiction(session, "FR", "France")
    ae = _jurisdiction(session, "AE", "United Arab Emirates")
    ref.get_or_create_currency("EUR", "Euro")
    ref.get_or_create_currency("AED", "UAE Dirham")
    tt = {
        code: ref.get_or_create_tax_type(code, name)
        for code, name in [
            ("WHT_DIVIDEND", "Withholding tax on dividends"),
            ("WHT_INTEREST", "Withholding tax on interest"),
            ("WHT_ROYALTY", "Withholding tax on royalties"),
            ("CIT", "Corporate income tax"),
        ]
    }
    ic = {
        code: ref.get_or_create_income_category(code, name)
        for code, name in [
            ("DIVIDEND", "Dividends"),
            ("INTEREST", "Interest"),
            ("ROYALTY", "Royalties"),
            ("CORPORATE_PROFIT", "Corporate profit"),
        ]
    }
    session.flush()

    uae_wht = _src(
        session,
        "UAE Corporate Tax Law (Federal Decree-Law No. 47 of 2022) / PwC UAE WHT",
        PWC_UAE_URL,
        "FDL No. 47 of 2022",
        "UAE withholding tax rate on dividends, interest and royalties "
        "paid to non-residents is 0%.",
    )
    uae_cit = _src(
        session,
        "UAE Corporate Tax (Ministry of Finance)",
        MOF_URL,
        "FDL No. 47 of 2022",
        "Corporate tax 0% on taxable income up to AED 375,000 and 9% above.",
    )
    fr_div_src = _src(
        session,
        "France withholding taxes (PwC) / CGI art. 119 bis 2, 187",
        PWC_FR_URL,
        "CGI art. 119 bis 2 / 187",
        "France withholding tax on dividends paid to non-resident companies is 25%.",
    )
    fr_roy_src = _src(
        session,
        "CGI art. 182 B / 219",
        LEGIFRANCE_URL,
        "CGI art. 182 B / 219",
        "France withholding tax on royalties paid to non-resident companies is 25%.",
    )
    fr_int_src = _src(
        session,
        "CGI interest to non-residents (exempt since 2018, ETNC excepted)",
        LEGIFRANCE_URL,
        "CGI art. 125 A III / 119 bis",
        "Interest paid to non-residents is exempt from withholding since 2018, "
        "except to non-cooperative states.",
    )
    fr_hold_src = _src(
        session,
        "CGI art. 145 / 216 (regime mere-fille)",
        LEGIFRANCE_URL,
        "CGI art. 145 / 216",
        "Parent-subsidiary regime: dividends exempt (95%) for holdings of at least 5% "
        "held 2 years.",
    )
    treaty_src = _src(
        session,
        "Convention France - United Arab Emirates (impots.gouv.fr)",
        TREATY_URL,
        None,
        "Convention signed 19 July 1989; protocol of 6 December 1993 (verified dates). "
        "Entry-into-force date not asserted.",
    )
    art8_src = _src(
        session,
        "Convention France - United Arab Emirates (impots.gouv.fr)",
        TREATY_URL,
        "Article 8",
        "Dividends are taxable only in the State of residence of the beneficial owner; "
        "refund mechanism per CGI art. 119 bis A II.",
    )

    # (jurisdiction, tax_type, income_category, taxpayer_type, rate, start, evidence)
    flat_rules = [
        (ae, "WHT_DIVIDEND", "DIVIDEND", "any", "0", UAE_CT_FROM, uae_wht),
        (ae, "WHT_INTEREST", "INTEREST", "any", "0", UAE_CT_FROM, uae_wht),
        (ae, "WHT_ROYALTY", "ROYALTY", "any", "0", UAE_CT_FROM, uae_wht),
        (fr, "WHT_DIVIDEND", "DIVIDEND", "company", "25", FR_FROM, fr_div_src),
        (fr, "WHT_ROYALTY", "ROYALTY", "company", "25", FR_FROM, fr_roy_src),
        (fr, "WHT_INTEREST", "INTEREST", "company", "0", FR_FROM, fr_int_src),
    ]
    for j, tcode, icode, ttype, rate, start, ev in flat_rules:
        if _rule_exists(session, j.id, tt[tcode].id, ic[icode].id, ttype, start):
            continue
        session.add(
            DomesticTaxRule(
                jurisdiction_id=j.id,
                tax_type_id=tt[tcode].id,
                income_category_id=ic[icode].id,
                taxpayer_type=ttype,
                rate=Decimal(rate),
                is_bracketed=False,
                source_evidence_id=ev.id,
                valid_period=_period(start),
            )
        )
    session.flush()

    if not _rule_exists(
        session, ae.id, tt["CIT"].id, ic["CORPORATE_PROFIT"].id, "company", UAE_CT_FROM
    ):
        cit = DomesticTaxRule(
            jurisdiction_id=ae.id,
            tax_type_id=tt["CIT"].id,
            income_category_id=ic["CORPORATE_PROFIT"].id,
            taxpayer_type="company",
            rate=None,
            is_bracketed=True,
            source_evidence_id=uae_cit.id,
            valid_period=_period(UAE_CT_FROM),
        )
        session.add(cit)
        session.flush()
        session.add_all(
            [
                TaxBracket(
                    domestic_tax_rule_id=cit.id,
                    lower_bound=Decimal("0"),
                    upper_bound=Decimal("375000"),
                    rate=Decimal("0"),
                    position=1,
                ),
                TaxBracket(
                    domestic_tax_rule_id=cit.id,
                    lower_bound=Decimal("375000"),
                    upper_bound=None,
                    rate=Decimal("9"),
                    position=2,
                ),
            ]
        )
        session.flush()

    holding_start = date(2020, 1, 1)
    if (
        session.scalar(
            select(HoldingRegime.id).where(
                HoldingRegime.jurisdiction_id == fr.id,
                HoldingRegime.valid_period.contains(holding_start),
            )
        )
        is None
    ):
        session.add(
            HoldingRegime(
                jurisdiction_id=fr.id,
                participation_exemption_dividends=True,
                participation_exemption_capgains=True,
                min_holding_pct=Decimal("5"),
                min_holding_period_months=24,
                subject_to_tax_condition=False,
                notes="Regime mere-fille (CGI art. 145 / 216)",
                source_evidence_id=fr_hold_src.id,
                valid_period=_period(holding_start),
            )
        )
        session.flush()

    treaty = TreatyRepository(session).find_by_parties("FR", "AE")
    if treaty is None:
        treaty = Treaty(
            name="Convention between France and the United Arab Emirates",
            signature_date=date(1989, 7, 19),
            entry_into_force_date=None,  # not verified against an official source
            source_evidence_id=treaty_src.id,
        )
        session.add(treaty)
        session.flush()
        session.add_all(
            [
                TreatyParty(treaty_id=treaty.id, jurisdiction_id=fr.id),
                TreatyParty(treaty_id=treaty.id, jurisdiction_id=ae.id),
            ]
        )
        session.flush()
    if not any(p.signature_date == date(1993, 12, 6) for p in _protocols(session, treaty.id)):
        session.add(
            TreatyProtocol(
                treaty_id=treaty.id,
                signature_date=date(1993, 12, 6),
                entry_into_force_date=date(1994, 1, 1),
                description="Protocol of 6 December 1993",
                source_evidence_id=treaty_src.id,
            )
        )
        session.flush()

    article = TreatyRepository(session).get_article(treaty.id, "DIVIDENDS")
    if article is None:
        article = TreatyArticle(
            treaty_id=treaty.id, article_category="DIVIDENDS", article_ref="Article 8"
        )
        session.add(article)
        session.flush()

    rate_start = date(1994, 1, 1)
    if TreatyRepository(session).get_rate(treaty.id, "DIVIDEND", rate_start) is None:
        session.add(
            TreatyRate(
                treaty_id=treaty.id,
                treaty_article_id=article.id,
                income_category_id=ic["DIVIDEND"].id,
                max_rate=Decimal("0"),
                exclusive_residence_taxation=True,
                relief_mechanism="refund",
                beneficial_owner_required=True,
                source_evidence_id=art8_src.id,
                valid_period=_period(rate_start),
            )
        )
        session.flush()


def _protocols(session: Session, treaty_id: int) -> list[TreatyProtocol]:
    return list(
        session.scalars(select(TreatyProtocol).where(TreatyProtocol.treaty_id == treaty_id))
    )
