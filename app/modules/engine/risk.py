from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.repository import JurisdictionRepository
from app.modules.engine.types import AppliedConsequence, ListHit, RiskProfile
from app.modules.risk.models import ListDefinition
from app.modules.risk.repository import ConsequenceRepository, ListRepository


class RiskEngine:
    """List memberships of a jurisdiction and the consequences other states attach to them."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.lists = ListRepository(session)
        self.consequences = ConsequenceRepository(session)
        self.jurisdictions = JurisdictionRepository(session)

    def profile(self, jurisdiction: str, on_date: date) -> RiskProfile:
        hits = []
        for m in self.lists.lists_for(jurisdiction, on_date):
            definition = self.session.get(ListDefinition, m.list_definition_id)
            assert definition is not None  # FK-enforced
            hits.append(
                ListHit(definition.code, definition.family, m.classification, m.source_evidence_id)
            )
        hits.sort(key=lambda h: h.list_code)
        return RiskProfile(jurisdiction, on_date, tuple(hits))

    def applied_consequences(
        self,
        applying: str,
        target: str,
        on_date: date,
        consequence_type: str | None = None,
    ) -> tuple[AppliedConsequence, ...]:
        """Consequences `applying` imposes because `target` is listed on `on_date`."""
        applier = self.jurisdictions.get_by_code(applying)
        if applier is None:
            return ()
        out: list[AppliedConsequence] = []
        for hit in self.profile(target, on_date).memberships:
            for c in self.consequences.triggered_by(hit.list_code, hit.classification, on_date):
                if c.applying_jurisdiction_id != applier.id:
                    continue
                if consequence_type is not None and c.consequence_type != consequence_type:
                    continue
                out.append(
                    AppliedConsequence(
                        list_code=hit.list_code,
                        classification=hit.classification,
                        consequence_type=c.consequence_type,
                        rate=c.rate,
                        legal_ref=c.legal_ref,
                        citations=(hit.citation, c.source_evidence_id),
                    )
                )
        return tuple(out)
