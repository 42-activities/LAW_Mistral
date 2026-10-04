from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.repository import JurisdictionRepository
from app.modules.risk.models import ListMembership, RegulatoryConsequence
from app.modules.risk.repository import (
    ConsequenceRepository,
    ListDefinitionRepository,
    ListRepository,
)
from app.modules.seed.sources import upsert_source
from app.modules.source.models import SourceEvidence

RETRIEVED_AT = datetime(2026, 10, 4, tzinfo=UTC)

FATF_URL = "https://www.fatf-gafi.org/en/countries/black-and-grey-lists.html"
CONSILIUM_URL = "https://www.consilium.europa.eu/en/policies/eu-list-of-non-cooperative-jurisdictions/"
EC_AML_URL = "https://finance.ec.europa.eu/financial-crime/high-risk-third-countries-and-international-context-content-anti-money-laundering-and-countering_en"
OECD_URL = "https://www.oecd.org/tax/transparency/exchange-of-information-on-request/ratings/"
LEGIFRANCE_ETNC_URL = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000041464260"
LEGIFRANCE_ARRETE_URL = "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051571516"


def _period(start: date, end: date | None) -> Range[date]:
    return Range(start, end, bounds="[)")


def _src(
    session: Session, title: str, url: str, article: str | None, quote: str
) -> SourceEvidence:
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


def seed_lists(session: Session) -> None:
    fatf = _src(
        session, "FATF black and grey lists", FATF_URL, None,
        "FATF publishes jurisdictions under increased monitoring and high-risk "
        "jurisdictions subject to a call for action after each plenary.",
    )
    fatf_ae = _src(
        session, "FATF black and grey lists", FATF_URL, "Plenary statements 2022-2024",
        "UAE added to FATF increased monitoring in March 2022; removed on 23 February 2024.",
    )
    consilium = _src(
        session, "EU list of non-cooperative jurisdictions for tax purposes", CONSILIUM_URL,
        "Annex I / Annex II",
        "The Council reviews the EU list of non-cooperative jurisdictions twice a year.",
    )
    ec_aml = _src(
        session, "EU high-risk third countries (Reg (EU) 2016/1675)", EC_AML_URL,
        "Reg (EU) 2016/1675",
        "The Commission identifies high-risk third countries by delegated acts.",
    )
    ec_aml_ae = _src(
        session, "EU high-risk third countries (Reg (EU) 2016/1675)", EC_AML_URL,
        "Del. Reg (EU) 2023/410; Del. Reg (EU) 2025/1184",
        "UAE added to the EU AML high-risk list on 16 March 2023; removed by "
        "Delegated Regulation (EU) 2025/1184 of 10 June 2025.",
    )
    oecd = _src(
        session, "OECD Global Forum EOIR ratings", OECD_URL, None,
        "The Global Forum rates jurisdictions on exchange of information on request "
        "per peer review.",
    )
    fr_def = _src(
        session, "CGI art. 238-0 A (ETNC)", LEGIFRANCE_ETNC_URL, "CGI art. 238-0 A",
        "France publishes by arrete the list of non-cooperative states and territories (ETNC).",
    )
    fr_arrete = _src(
        session, "Arrete du 18 avril 2025 (ETNC list)", LEGIFRANCE_ARRETE_URL,
        "Arrete of 18 April 2025 (JO 7 May 2025)",
        "Vanuatu (full measures) and Panama (certain measures) on the French ETNC list, "
        "effective 8 May 2025.",
    )
    fr_cons = _src(
        session, "CGI art. 238-0 A (ETNC)", LEGIFRANCE_ETNC_URL, "CGI art. 238-0 A",
        "75% withholding tax applies to certain payments to ETNC (full measures).",
    )

    defs = ListDefinitionRepository(session)
    definitions = [
        ("FATF_GREY", "FATF jurisdictions under increased monitoring", "aml_cft", "FATF",
         "after each plenary (Feb/Jun/Oct)", fatf),
        ("FATF_BLACK", "FATF high-risk jurisdictions subject to a call for action", "aml_cft",
         "FATF", "after each plenary", fatf),
        ("EU_TAX_ANNEX_I", "EU list of non-cooperative jurisdictions (Annex I)",
         "tax_governance", "Council of the EU", "twice a year", consilium),
        ("EU_TAX_ANNEX_II", "EU list state of play (Annex II)", "tax_governance",
         "Council of the EU", "twice a year", consilium),
        ("EU_AML_HIGH_RISK", "EU AML high-risk third countries (Reg (EU) 2016/1675)", "aml_cft",
         "European Commission", "ad hoc delegated acts", ec_aml),
        ("GLOBAL_FORUM_RATING", "OECD Global Forum EOIR ratings", "tax_governance",
         "OECD Global Forum", "per peer review", oecd),
        ("FR_ETNC", "France non-cooperative states and territories (ETNC)", "tax_governance",
         "France", "per national law", fr_def),
    ]
    rows = {}
    for code, name, family, publisher, cadence, ev in definitions:
        rows[code] = defs.get_or_create(
            code, name=name, family=family, publisher=publisher,
            update_cadence=cadence, source_evidence_id=ev.id,
        )
    session.flush()

    fr = _jurisdiction(session, "FR", "France")
    ae = _jurisdiction(session, "AE", "United Arab Emirates")
    vu = _jurisdiction(session, "VU", "Vanuatu")
    pa = _jurisdiction(session, "PA", "Panama")
    session.flush()

    lists = ListRepository(session)
    # (jurisdiction, list, classification, announcement, start, end, evidence)
    memberships = [
        (ae, "FATF_GREY", "increased_monitoring", date(2022, 3, 4),
         date(2022, 3, 4), date(2024, 2, 23), fatf_ae),
        (ae, "EU_AML_HIGH_RISK", "high_risk", date(2023, 3, 16),
         date(2023, 3, 16), date(2025, 6, 10), ec_aml_ae),
        (vu, "FR_ETNC", "full_measures", date(2025, 5, 8),
         date(2025, 5, 8), None, fr_arrete),
        (pa, "FR_ETNC", "certain_measures", date(2025, 5, 8),
         date(2025, 5, 8), None, fr_arrete),
    ]
    for j, list_code, classification, announced, start, end, ev in memberships:
        if lists.is_listed(j.code, list_code, start) is not None:
            continue
        session.add(
            ListMembership(
                list_definition_id=rows[list_code].id,
                jurisdiction_id=j.id,
                classification=classification,
                announcement_date=announced,
                source_evidence_id=ev.id,
                valid_period=_period(start, end),
            )
        )
        session.flush()

    cons_start = date(2010, 2, 12)
    if not ConsequenceRepository(session).triggered_by("FR_ETNC", "full_measures", cons_start):
        session.add(
            RegulatoryConsequence(
                applying_jurisdiction_id=fr.id,
                list_definition_id=rows["FR_ETNC"].id,
                classification_trigger="full_measures",
                consequence_type="withholding_tax",
                rate=Decimal("75"),
                legal_ref="CGI art. 238-0 A",
                description="75% withholding tax on certain payments to ETNC (full measures)",
                source_evidence_id=fr_cons.id,
                valid_period=_period(cons_start, None),
            )
        )
        session.flush()
