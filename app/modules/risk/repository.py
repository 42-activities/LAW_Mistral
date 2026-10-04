from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, ListMembership, RegulatoryConsequence


class ListDefinitionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, code: str) -> ListDefinition | None:
        return self.session.scalar(select(ListDefinition).where(ListDefinition.code == code))

    def get_or_create(
        self,
        code: str,
        *,
        name: str,
        family: str,
        publisher: str,
        update_cadence: str | None,
        source_evidence_id: int,
    ) -> ListDefinition:
        row = self.get(code)
        if row is None:
            row = ListDefinition(
                code=code, name=name, family=family, publisher=publisher,
                update_cadence=update_cadence, source_evidence_id=source_evidence_id,
            )
            self.session.add(row)
        return row


class ListRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def is_listed(
        self, jurisdiction_code: str, list_code: str, on_date: date
    ) -> ListMembership | None:
        stmt = (
            select(ListMembership)
            .join(Jurisdiction, ListMembership.jurisdiction_id == Jurisdiction.id)
            .join(ListDefinition, ListMembership.list_definition_id == ListDefinition.id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                ListDefinition.code == list_code,
                ListMembership.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)

    def members(self, list_code: str, on_date: date) -> list[ListMembership]:
        stmt = (
            select(ListMembership)
            .join(ListDefinition, ListMembership.list_definition_id == ListDefinition.id)
            .where(ListDefinition.code == list_code, ListMembership.valid_period.contains(on_date))
        )
        return list(self.session.scalars(stmt))

    def lists_for(self, jurisdiction_code: str, on_date: date) -> list[ListMembership]:
        stmt = (
            select(ListMembership)
            .join(Jurisdiction, ListMembership.jurisdiction_id == Jurisdiction.id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                ListMembership.valid_period.contains(on_date),
            )
        )
        return list(self.session.scalars(stmt))


class ConsequenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def for_applying_jurisdiction(self, code: str, on_date: date) -> list[RegulatoryConsequence]:
        stmt = (
            select(RegulatoryConsequence)
            .join(Jurisdiction, RegulatoryConsequence.applying_jurisdiction_id == Jurisdiction.id)
            .where(Jurisdiction.code == code, RegulatoryConsequence.valid_period.contains(on_date))
        )
        return list(self.session.scalars(stmt))

    def triggered_by(
        self, list_code: str, classification: str | None, on_date: date
    ) -> list[RegulatoryConsequence]:
        # classification_trigger '' is the wildcard ("any classification on the list"), so match
        # rows with '' OR the exact requested classification.
        stmt = (
            select(RegulatoryConsequence)
            .join(ListDefinition, RegulatoryConsequence.list_definition_id == ListDefinition.id)
            .where(
                ListDefinition.code == list_code,
                RegulatoryConsequence.valid_period.contains(on_date),
                RegulatoryConsequence.classification_trigger.in_(["", classification or ""]),
            )
        )
        return list(self.session.scalars(stmt))
