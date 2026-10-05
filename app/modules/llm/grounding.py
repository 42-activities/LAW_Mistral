"""Grounding validator (spec §5): reject LLM prose that says anything the engine did not.

Checks, against the structured input the model was given:
- every number matches a value present in the input (within formatting tolerance);
- every citation tag [n] is one of the input's citation ids;
- every percentage appears in a sentence that carries at least one citation;
- every jurisdiction mentioned (by code or name) is one of the input's jurisdictions;
- every list named (FATF, ETNC, EU list ...) appears somewhere in the input.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

CITATION = re.compile(r"\[(\d+)\]")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?")
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
LIST_TERMS = {
    "FATF": ("FATF",),
    "ETNC": ("ETNC", "non-cooperative", "non cooperative"),
    "ANNEX": ("Annex I", "Annex II", "EU list of non-cooperative"),
    "AML": ("AML", "high-risk third"),
    "GLOBAL_FORUM": ("Global Forum",),
}


@dataclass(frozen=True)
class GroundingResult:
    ok: bool
    errors: tuple[str, ...]
    citations: tuple[int, ...] = field(default_factory=tuple)


def _walk(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list | tuple):
        for v in value:
            yield from _walk(v)
    else:
        yield value


def _decimals(text: str) -> list[Decimal]:
    out = []
    for raw in NUMBER.findall(text):
        try:
            out.append(Decimal(raw.replace(",", ".")))
        except InvalidOperation:
            continue
    return out


def allowed_numbers(payload: Any) -> set[Decimal]:
    nums: set[Decimal] = set()
    for v in _walk(payload):
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, int | float | Decimal):
            nums.add(Decimal(str(v)))
        elif isinstance(v, str):
            nums.update(_decimals(ISO_DATE.sub(" ", v)))
    # Weights are fractions in the payload but naturally written as percentages.
    nums |= {n * 100 for n in nums if Decimal("0") < n < Decimal("1")}
    return nums


def _matches(x: Decimal, allowed: set[Decimal]) -> bool:
    exponent = x.as_tuple().exponent
    places = -exponent if isinstance(exponent, int) and exponent < 0 else 0
    quantum = Decimal(1).scaleb(-places)
    return any(a.quantize(quantum) == x for a in allowed)


def validate(
    text: str,
    payload: Any,
    citations: Iterable[int],
    jurisdictions_in_input: dict[str, str],
    all_jurisdictions: dict[str, str],
) -> GroundingResult:
    """`jurisdictions_*` map code → name."""
    errors: list[str] = []
    allowed_cites = set(citations)
    used = [int(c) for c in CITATION.findall(text)]
    for c in sorted(set(used) - allowed_cites):
        errors.append(f"citation [{c}] is not in the input")

    body = CITATION.sub(" ", text)
    input_text = " ".join(str(v) for v in _walk(payload) if isinstance(v, str))
    input_dates = set(ISO_DATE.findall(input_text))
    for d in ISO_DATE.findall(body):
        if d not in input_dates:
            errors.append(f"date {d} is not in the input")
    body_no_dates = ISO_DATE.sub(" ", body)
    allowed = allowed_numbers(payload)
    for x in _decimals(body_no_dates):
        if not _matches(x, allowed):
            errors.append(f"number {x} is not in the input")

    for sentence in SENTENCE.split(text):
        if "%" in sentence and not CITATION.search(sentence):
            errors.append(f"percentage without a citation: {sentence.strip()[:120]!r}")

    for code, name in all_jurisdictions.items():
        mentioned = re.search(rf"\b{re.escape(code)}\b", body) or (
            name and re.search(rf"\b{re.escape(name)}\b", body, re.IGNORECASE)
        )
        if mentioned and code not in jurisdictions_in_input:
            errors.append(f"jurisdiction {code} ({name}) is not in the input")

    for terms in LIST_TERMS.values():
        for term in terms:
            if re.search(re.escape(term), body, re.IGNORECASE) and not re.search(
                re.escape(term), input_text, re.IGNORECASE
            ):
                errors.append(f"list reference {term!r} is not in the input")
                break

    return GroundingResult(not errors, tuple(errors), tuple(sorted(set(used))))
