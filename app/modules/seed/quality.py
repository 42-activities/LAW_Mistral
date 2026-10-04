from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.tax.models import DomesticTaxRule
from app.modules.treaty.models import Treaty, TreatyParty, TreatyRate


def run_checks(session: Session) -> list[str]:
    violations: list[str] = []

    # 1. treaties need >= 2 parties
    for treaty in session.scalars(select(Treaty)):
        count = session.scalar(
            select(func.count()).select_from(TreatyParty).where(TreatyParty.treaty_id == treaty.id)
        )
        if (count or 0) < 2:
            violations.append(f"treaty {treaty.id} ({treaty.name}) has {count} party rows (< 2)")

    # 3. flat rules need a rate; bracketed rules need brackets
    for rule in session.scalars(select(DomesticTaxRule)):
        if rule.is_bracketed and not rule.brackets:
            violations.append(f"bracketed domestic_tax_rule {rule.id} has no brackets")
        if not rule.is_bracketed and rule.rate is None:
            violations.append(f"flat domestic_tax_rule {rule.id} has no rate")

    # 4. relief_mechanism within the allowed set
    allowed = {None, "at_source", "refund", "credit"}
    for tr in session.scalars(select(TreatyRate)):
        if tr.relief_mechanism not in allowed:
            msg = (
                f"treaty_rate {tr.id} has invalid relief_mechanism "
                f"{tr.relief_mechanism!r}"
            )
            violations.append(msg)

    return violations
