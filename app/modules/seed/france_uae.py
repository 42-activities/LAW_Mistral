from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference_repo import ReferenceRepository
from app.modules.core.repository import JurisdictionRepository
from app.modules.seed.lists import seed_lists
from app.modules.seed.scoring import seed_scoring
from app.modules.seed.sources import upsert_source
from app.modules.source.models import SourceDocument, SourceEvidence
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
# The P1 URL (.../convention-france-emirats-arabes-unis.pdf) returns 404 since 2026-10;
# this is the consolidated official text (convention + 1993 avenant) on impots.gouv.fr.
OLD_TREATY_URL = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/"
    "emirats_arabes_unis/convention-france-emirats-arabes-unis.pdf"
)
TREATY_URL = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/emirats_arabes_unis/"
    "emirats-arabes-unis_convention-avec-les-emirats-arabes-unis_fd_2138.pdf"
)
BOFIP_IS_URL = "https://bofip.impots.gouv.fr/bofip/2066-PGP"
UAE_PE_URL = "https://afridi-angell.com/the-participation-exemption-dividends-and-capital-gains/"
TREATY_EIF = date(1990, 7, 1)
AVENANT_EIF = date(1995, 6, 1)


def _period(start: date) -> Range[date]:
    return Range(start, None, bounds="[)")


def _src(
    session: Session,
    title: str,
    url: str,
    article: str | None,
    quote: str,
    review_status: str = "human_verified",
) -> SourceEvidence:
    return upsert_source(
        session,
        title=title,
        url=url,
        retrieved_at=RETRIEVED_AT,
        content_hash="fixture-v1",
        article=article,
        quoted_text=quote,
        review_status=review_status,
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
    old_doc = session.scalar(select(SourceDocument).where(SourceDocument.url == OLD_TREATY_URL))
    if old_doc is not None:
        old_doc.url = TREATY_URL
        session.flush()
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
                entry_into_force_date=AVENANT_EIF,
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

    rate_start = AVENANT_EIF
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

    seed_lists(session)
    seed_engine_data(session, treaty, article)
    seed_scoring(session)


def _protocols(session: Session, treaty_id: int) -> list[TreatyProtocol]:
    return list(
        session.scalars(select(TreatyProtocol).where(TreatyProtocol.treaty_id == treaty_id))
    )


def seed_engine_data(session: Session, treaty: Treaty, dividend_article: TreatyArticle) -> None:
    """P3 corrections and additions, checked against official texts on 2026-10-04.

    Evidence added here is `unreviewed`: it was checked by the assistant, not by a named human
    reviewer (spec §10).
    """
    ref = ReferenceRepository(session)
    fr = _jurisdiction(session, "FR", "France")
    ae = _jurisdiction(session, "AE", "United Arab Emirates")

    eif_src = _src(
        session,
        "Convention France - United Arab Emirates (impots.gouv.fr)",
        TREATY_URL,
        "Cover page",
        "signée à Abou Dhabi le 19 juillet 1989 [...] entrée en vigueur le 1er juillet 1990 [...] "
        "modifiée par l'Avenant signé à Abou Dhabi le 6 décembre 1993 [...] entré en vigueur "
        "le 1er juin 1995",
        review_status="unreviewed",
    )
    # Corrections to P1 rows (P1 left entry into force blank and dated the avenant 1994-01-01).
    if treaty.entry_into_force_date is None:
        treaty.entry_into_force_date = TREATY_EIF
        treaty.source_evidence_id = eif_src.id
    for protocol in _protocols(session, treaty.id):
        if protocol.signature_date == date(1993, 12, 6) and protocol.entry_into_force_date != (
            AVENANT_EIF
        ):
            protocol.entry_into_force_date = AVENANT_EIF
            protocol.source_evidence_id = eif_src.id
    div_rate = TreatyRepository(session).get_rate(treaty.id, "DIVIDEND", AVENANT_EIF)
    if div_rate is not None and div_rate.valid_period.lower != AVENANT_EIF:
        div_rate.valid_period = _period(AVENANT_EIF)
    session.flush()

    # Interest (art. 9) and royalties (art. 10): exclusive residence taxation.
    articles = [
        (
            "INTEREST",
            "INTEREST",
            "Article 9",
            "Les revenus de créances provenant d'un Etat et payés à un résident de l'autre Etat "
            "ne sont imposables que dans cet autre Etat, si ce résident en est le bénéficiaire "
            "effectif.",
        ),
        (
            "ROYALTIES",
            "ROYALTY",
            "Article 10",
            "Les redevances provenant d'un Etat et payées à un résident de l'autre Etat ne sont "
            "imposables que dans cet autre Etat, si ce résident en est le bénéficiaire effectif.",
        ),
    ]
    repo = TreatyRepository(session)
    for category, income_code, article_ref, quote in articles:
        ev = _src(
            session,
            "Convention France - United Arab Emirates (impots.gouv.fr)",
            TREATY_URL,
            f"{article_ref}, para. 1",
            quote,
            review_status="unreviewed",
        )
        article = repo.get_article(treaty.id, category)
        if article is None:
            article = TreatyArticle(
                treaty_id=treaty.id, article_category=category, article_ref=article_ref
            )
            session.add(article)
            session.flush()
        if repo.get_rate(treaty.id, income_code, AVENANT_EIF) is None:
            income = ref.income_category(income_code)
            assert income is not None
            session.add(
                TreatyRate(
                    treaty_id=treaty.id,
                    treaty_article_id=article.id,
                    income_category_id=income.id,
                    max_rate=Decimal("0"),
                    exclusive_residence_taxation=True,
                    relief_mechanism=None,  # the treaty text does not set the procedure
                    beneficial_owner_required=True,
                    source_evidence_id=ev.id,
                    valid_period=_period(AVENANT_EIF),
                )
            )
            session.flush()

    # France CIT 25% from fiscal years opened on or after 2022-01-01 (CGI art. 219 I).
    fr_cit_src = _src(
        session,
        "BOI-IS-LIQ-10 - IS - Taux normal (BOFiP)",
        BOFIP_IS_URL,
        "CGI art. 219 I",
        "Exercices ouverts à compter du 01/01/2022 : 25 %",
        review_status="unreviewed",
    )
    cit_type = ref.tax_type("CIT")
    profit = ref.income_category("CORPORATE_PROFIT")
    assert cit_type is not None and profit is not None
    fr_cit_from = date(2022, 1, 1)
    if not _rule_exists(session, fr.id, cit_type.id, profit.id, "company", fr_cit_from):
        session.add(
            DomesticTaxRule(
                jurisdiction_id=fr.id,
                tax_type_id=cit_type.id,
                income_category_id=profit.id,
                taxpayer_type="company",
                rate=Decimal("25"),
                is_bracketed=False,
                source_evidence_id=fr_cit_src.id,
                valid_period=_period(fr_cit_from),
            )
        )
        session.flush()

    # France: 95% of qualifying dividends exempt (5% quote-part), per the P1 CGI 145/216 evidence.
    fr_regime = session.scalar(
        select(HoldingRegime).where(
            HoldingRegime.jurisdiction_id == fr.id,
            HoldingRegime.valid_period.contains(date(2020, 1, 1)),
        )
    )
    if fr_regime is not None and fr_regime.exempt_share_pct != Decimal("95"):
        fr_regime.exempt_share_pct = Decimal("95")

    # UAE participation exemption, FDL No. 47 of 2022 art. 23.
    ae_pe_src = _src(
        session,
        "UAE Participation Exemption (FDL No. 47 of 2022, art. 23; Ministerial Decision 116/2023)",
        UAE_PE_URL,
        "FDL No. 47 of 2022 art. 23",
        "5% (five percent) or greater ownership interest [...] held, or has the intention to "
        "hold, the Participating Interest for an uninterrupted period of at least (12) twelve "
        "months [...] subject to Corporate Tax [...] at a rate not less than [9%] [...] Income "
        "from a Participating Interest shall be exempt from Corporate Tax",
        review_status="unreviewed",
    )
    if (
        session.scalar(
            select(HoldingRegime.id).where(
                HoldingRegime.jurisdiction_id == ae.id,
                HoldingRegime.valid_period.contains(UAE_CT_FROM),
            )
        )
        is None
    ):
        session.add(
            HoldingRegime(
                jurisdiction_id=ae.id,
                participation_exemption_dividends=True,
                participation_exemption_capgains=True,
                min_holding_pct=Decimal("5"),
                min_holding_period_months=12,
                subject_to_tax_condition=True,
                min_subject_to_tax_rate=Decimal("9"),
                exempt_share_pct=Decimal("100"),
                notes="Participation exemption (FDL No. 47 of 2022 art. 23); also requires "
                "the 50% asset test, not modelled",
                source_evidence_id=ae_pe_src.id,
                valid_period=_period(UAE_CT_FROM),
            )
        )
    session.flush()
