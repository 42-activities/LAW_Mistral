from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.modules.core.repository import JurisdictionRepository
from app.modules.recommender.models import WeightSet
from app.modules.scoring.repository import WeightSetRepository
from app.modules.scoring.scorer import DEFAULT_WEIGHTS
from app.modules.seed.sources import upsert_source
from app.modules.tax.models import CfcRule
from app.modules.tax.repository import AntiAbuseRepository

RETRIEVED_AT = datetime(2026, 10, 4, tzinfo=UTC)
CGI_238A_URL = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037526846"
FR_CFC_FROM = date(2020, 1, 1)


def seed_scoring(session: Session) -> None:
    if WeightSetRepository(session).get("default-v1") is None:
        session.add(
            WeightSet(
                name="default-v1",
                weights={k: str(v) for k, v in DEFAULT_WEIGHTS.items()},
                is_default=True,
            )
        )
        session.flush()

    fr = JurisdictionRepository(session).get_by_code("FR")
    if fr is None:
        return
    existing = AntiAbuseRepository(session).cfc_rule("FR", FR_CFC_FROM)
    if existing is not None:
        existing.threshold_inclusive = True  # CGI 238 A: "inférieur de 40 % ou plus"
        session.flush()
        return
    ev = upsert_source(
        session,
        title="CGI art. 238 A (régime fiscal privilégié), applied by CGI art. 209 B",
        url=CGI_238A_URL,
        retrieved_at=RETRIEVED_AT,
        content_hash="fixture-v1",
        article="CGI art. 238 A (version en vigueur depuis le 01/01/2020); art. 209 B I",
        quoted_text=(
            "les personnes sont regardées comme soumises à un régime fiscal privilégié [...] si "
            "elles n'y sont pas imposables ou si elles y sont assujetties à des impôts sur les "
            "bénéfices ou les revenus dont le montant est inférieur de 40 % ou plus à celui de "
            "l'impôt [...] dont elles auraient été redevables dans les conditions de droit "
            "commun en France"
        ),
        review_status="unreviewed",
    )
    session.add(
        CfcRule(
            jurisdiction_id=fr.id,
            control_threshold_pct=Decimal("50"),
            low_tax_relative_pct=Decimal("60"),
            threshold_inclusive=True,
            effect="Profits of a >50%-held entity under a privileged tax regime are taxed in "
            "France (CGI 209 B I); safe harbour for genuine activity (209 B III) needs review.",
            legal_ref="CGI art. 209 B / 238 A",
            source_evidence_id=ev.id,
            valid_period=Range(FR_CFC_FROM, None, bounds="[)"),
        )
    )
    session.flush()
