from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.risk.models import ListDefinition


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
