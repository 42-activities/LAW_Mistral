from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.engine.types import ZERO, Flag, TreatyTerms
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyRate
from app.modules.treaty.repository import TreatyRepository


class TreatyEngine:
    """The treaty cap a source state must respect for one payment, or why there is none."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = TreatyRepository(session)

    def in_force(self, a: str, b: str, on_date: date) -> Treaty | None:
        treaty = self.repo.find_by_parties(a, b)
        if treaty is None or treaty.entry_into_force_date is None:
            return None
        return treaty if treaty.entry_into_force_date <= on_date else None

    def terms(
        self,
        source: str,
        recipient: str,
        category: str,
        on_date: date,
        holding_pct: Decimal | None = None,
        holding_days: int | None = None,
    ) -> tuple[TreatyTerms | None, tuple[Flag, ...]]:
        treaty = self.repo.find_by_parties(source, recipient)
        if treaty is None:
            msg = (
                f"no treaty between {source} and {recipient} is recorded in the database; "
                f"this is a data gap, not a finding that no treaty exists"
            )
            return None, (Flag("no_treaty", msg),)
        if treaty.entry_into_force_date is None:
            return None, (
                Flag(
                    "treaty_in_force_unknown",
                    f"{treaty.name}: entry into force not recorded; treaty not applied",
                ),
            )
        if treaty.entry_into_force_date > on_date:
            return None, (
                Flag(
                    "treaty_not_in_force",
                    f"{treaty.name} enters into force {treaty.entry_into_force_date}",
                ),
            )
        rates = self.repo.get_rates(treaty.id, category, on_date, source_code=source)
        if not rates:
            return None, (
                Flag(
                    "treaty_rate_not_recorded",
                    f"{treaty.name}: no {category} rate recorded for {on_date}",
                ),
            )

        flags: list[Flag] = []
        cites = [treaty.source_evidence_id]
        mli = self.repo.get_mli(treaty.id, on_date)
        if mli is not None:
            cites.append(mli.source_evidence_id)
            if mli.ppt_applies:
                flags.append(
                    Flag(
                        "mli_ppt",
                        "Principal purpose test applies (MLI or treaty clause): benefits are "
                        "denied if obtaining them was a principal purpose of the arrangement",
                    )
                )

        def cap_of(r: TreatyRate) -> Decimal | None:
            return ZERO if r.exclusive_residence_taxation else r.max_rate

        tiers = sorted((r for r in rates if cap_of(r) is not None), key=lambda r: (cap_of(r), r.id))
        if not tiers:
            return None, (
                Flag("treaty_rate_not_recorded", f"{treaty.name}: {category} rate has no cap"),
            )
        # The lowest-capped tier whose ownership and holding-period conditions are met wins.
        rate: TreatyRate | None = None
        for tier in tiers:
            tier_cap = cap_of(tier)
            if tier.ownership_threshold is not None and (
                holding_pct is None or holding_pct < tier.ownership_threshold
            ):
                flags.append(
                    Flag(
                        "treaty_threshold_not_met",
                        f"{treaty.name}: the {tier_cap}% {category} rate requires "
                        f"≥{tier.ownership_threshold}% holding (given: {holding_pct})",
                    )
                )
                continue
            if tier.min_holding_days is not None and (
                holding_days is None or holding_days < tier.min_holding_days
            ):
                flags.append(
                    Flag(
                        "treaty_holding_period_not_met",
                        f"{treaty.name}: the {tier_cap}% {category} rate requires holding "
                        f"≥{tier.min_holding_days} days (given: {holding_days})",
                    )
                )
                continue
            if (
                mli is not None
                and category == "DIVIDEND"
                and tier.ownership_threshold is not None
                and mli.dividend_min_holding_days is not None
                and (holding_days is None or holding_days < mli.dividend_min_holding_days)
            ):
                flags.append(
                    Flag(
                        "mli_holding_period_not_met",
                        f"MLI art. 8: dividend rate requires holding ≥"
                        f"{mli.dividend_min_holding_days} days (given: {holding_days})",
                    )
                )
                continue
            rate = tier
            break
        if rate is None:
            return None, tuple(flags)
        cites.append(rate.source_evidence_id)
        cap = cap_of(rate)
        assert cap is not None

        mfn = self.repo.get_mfn(treaty.id, category, on_date)
        if mfn is not None:
            cites.append(mfn.source_evidence_id)
            flags.append(
                Flag(
                    "mfn_clause",
                    f"most-favoured-nation clause may lower this rate: {mfn.description}",
                    interpretation_required=True,
                )
            )
        if rate.beneficial_owner_required:
            flags.append(
                Flag("beneficial_owner_condition", "treaty rate requires beneficial ownership")
            )

        article = self.session.get(TreatyArticle, rate.treaty_article_id)
        return (
            TreatyTerms(
                treaty_id=treaty.id,
                treaty_name=treaty.name,
                article_ref=article.article_ref if article else None,
                cap=cap,
                exclusive_residence_taxation=rate.exclusive_residence_taxation,
                relief_mechanism=rate.relief_mechanism,
                citations=tuple(cites),
                flags=tuple(flags),
            ),
            tuple(flags),
        )
