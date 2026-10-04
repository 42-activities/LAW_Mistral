from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.recommender.models import QuestionDefinition

QUESTIONS: list[dict[str, Any]] = [
    {
        "code": "size",
        "text": "How large is the client's business?",
        "help": "Sets the substance capacity band: how much real presence the group can "
        "realistically maintain in a holding jurisdiction.",
        "kind": "single",
        "maps_to": "substance_capacity",
        "options": [
            {"value": "micro", "label": "Micro", "hint": "under 10 staff"},
            {"value": "sme", "label": "SME", "hint": "10–249 staff"},
            {"value": "mid_market", "label": "Mid-market", "hint": "250–4,999 staff"},
            {"value": "large", "label": "Large", "hint": "5,000+ staff"},
        ],
    },
    {
        "code": "activity",
        "text": "What does the group mainly do?",
        "help": "Used to propose the income flows the holding is likely to receive.",
        "kind": "single",
        "maps_to": "activity",
        "options": [
            {"value": "trading", "label": "Trading goods", "suggests": ["DIVIDEND"]},
            {
                "value": "saas_ip",
                "label": "SaaS / IP licensing",
                "suggests": ["ROYALTY", "DIVIDEND"],
            },
            {
                "value": "holding_investment",
                "label": "Holding & investment",
                "suggests": ["DIVIDEND", "INTEREST"],
            },
            {"value": "services", "label": "Services", "suggests": ["DIVIDEND"]},
        ],
    },
    {
        "code": "flows",
        "text": "Which income will the holding receive, from where, and who owns it?",
        "help": "Tick the flows, the jurisdictions where the paying companies are resident, "
        "and the ultimate parent's jurisdiction.",
        "kind": "flows",
        "maps_to": "flows",
        "options": [
            {"value": "DIVIDEND", "label": "Dividends from subsidiaries"},
            {"value": "ROYALTY", "label": "Royalties / IP income"},
            {"value": "INTEREST", "label": "Interest / intra-group financing"},
            {
                "value": "CAPITAL_GAIN",
                "label": "Capital gains on exit",
                "enabled": False,
                "hint": "not modelled yet",
            },
        ],
    },
]


def seed_questions(session: Session) -> None:
    for position, q in enumerate(QUESTIONS, start=1):
        row = session.scalar(
            select(QuestionDefinition).where(QuestionDefinition.code == q["code"])
        )
        if row is None:
            row = QuestionDefinition(code=q["code"])
            session.add(row)
        row.text = q["text"]
        row.help = q["help"]
        row.kind = q["kind"]
        row.maps_to = q["maps_to"]
        row.options = q["options"]
        row.position = position
        row.active = True
    session.flush()
