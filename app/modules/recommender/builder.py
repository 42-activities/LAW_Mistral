"""Profile builder (spec §6): tickable answers → ScoringProfile. Deterministic, no LLM."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.repository import JurisdictionRepository
from app.modules.recommender.models import QuestionDefinition
from app.modules.scoring.types import ProfileFlow, ScoringProfile

SIZE_TO_CAPACITY = {"micro": "low", "sme": "medium", "mid_market": "high", "large": "high"}


class InvalidAnswers(ValueError):
    pass


@dataclass(frozen=True)
class Answers:
    size: str
    activity: str
    flows: tuple[str, ...]
    sources: tuple[str, ...]
    parent: str

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> "Answers":
        try:
            return cls(
                size=str(raw["size"]),
                activity=str(raw["activity"]),
                flows=tuple(sorted({str(f) for f in raw["flows"]})),
                sources=tuple(sorted({str(s) for s in raw["sources"]})),
                parent=str(raw["parent"]),
            )
        except (KeyError, TypeError) as exc:
            raise InvalidAnswers(f"missing or malformed answer: {exc}") from exc

    def to_json(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "activity": self.activity,
            "flows": list(self.flows),
            "sources": list(self.sources),
            "parent": self.parent,
        }


def questions(session: Session) -> list[QuestionDefinition]:
    stmt = (
        select(QuestionDefinition)
        .where(QuestionDefinition.active.is_(True))
        .order_by(QuestionDefinition.position)
    )
    return list(session.scalars(stmt))


def _allowed(q: QuestionDefinition) -> set[str]:
    return {str(o["value"]) for o in q.options if o.get("enabled", True)}


def build_profile(session: Session, raw: dict[str, Any]) -> tuple[Answers, ScoringProfile]:
    answers = Answers.parse(raw)
    by_code = {q.code: q for q in questions(session)}
    for code, value in (("size", answers.size), ("activity", answers.activity)):
        q = by_code.get(code)
        if q is None or value not in _allowed(q):
            raise InvalidAnswers(f"{code}: {value!r} is not an offered option")
    flows_q = by_code.get("flows")
    if flows_q is None:
        raise InvalidAnswers("flows question not configured")
    if not answers.flows or not set(answers.flows) <= _allowed(flows_q):
        raise InvalidAnswers(f"flows: choose one or more of {sorted(_allowed(flows_q))}")
    if not answers.sources:
        raise InvalidAnswers("sources: choose at least one jurisdiction where income arises")
    jurisdictions = JurisdictionRepository(session)
    for code in (*answers.sources, answers.parent):
        if jurisdictions.get_by_code(code) is None:
            raise InvalidAnswers(f"unknown jurisdiction {code}")

    profile = ScoringProfile(
        parent=answers.parent,
        flows=tuple(ProfileFlow(f, s) for f in answers.flows for s in answers.sources),
        substance_capacity=SIZE_TO_CAPACITY[answers.size],
        activity=answers.activity,
        size=answers.size,
    )
    return answers, profile
