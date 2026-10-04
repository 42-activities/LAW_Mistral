from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction


class DuplicateCodeError(Exception):
    pass


class JurisdictionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, code: str, name: str) -> Jurisdiction:
        jurisdiction = Jurisdiction(code=code, name=name)
        try:
            # begin_nested() flushes pending state on entry, so add() must happen
            # inside the SAVEPOINT for a failed insert to roll back only to it.
            with self.session.begin_nested():  # SAVEPOINT
                self.session.add(jurisdiction)
                self.session.flush()
        except IntegrityError as exc:
            raise DuplicateCodeError(code) from exc
        return jurisdiction

    def get(self, id: int) -> Jurisdiction | None:
        return self.session.get(Jurisdiction, id)

    def get_by_code(self, code: str) -> Jurisdiction | None:
        return self.session.scalar(select(Jurisdiction).where(Jurisdiction.code == code))

    def list(self) -> list[Jurisdiction]:
        return list(self.session.scalars(select(Jurisdiction).order_by(Jurisdiction.code)))
