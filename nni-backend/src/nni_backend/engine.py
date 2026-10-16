from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


MAX_INTERPRETATIONS = 4096
TRANSFORMATION_PENALTY = 0.1


class InterpretationError(ValueError):
    """Raised when recognized number tokens cannot be interpreted safely."""


@dataclass(frozen=True)
class Candidate:
    number: str
    transformations: int
    order: int

    @property
    def score(self) -> float:
        return max(0.0, 1.0 - self.transformations * TRANSFORMATION_PENALTY)


def validate_tokens(tokens: Iterable[str]) -> list[str]:
    normalized = [str(token).strip() for token in tokens]
    if not normalized:
        raise InterpretationError("No numeric tokens were recognized")

    for token in normalized:
        if not token.isdigit() or not 1 <= len(token) <= 3:
            raise InterpretationError(
                "Each recognized number must contain between one and three digits"
            )

    return normalized


def _generate_candidates(tokens: list[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    seen: set[str] = set()

    def add(parts: list[str], transformations: int) -> None:
        number = "".join(parts)
        if number in seen:
            return
        if len(candidates) >= MAX_INTERPRETATIONS:
            raise InterpretationError(
                "The input produces too many possible interpretations"
            )
        seen.add(number)
        candidates.append(
            Candidate(
                number=number,
                transformations=transformations,
                order=len(candidates),
            )
        )

    def visit(index: int, parts: list[str], transformations: int) -> None:
        if index == len(tokens):
            add(parts, transformations)
            return

        token = tokens[index]

        # The literal token is always visited first, ensuring the direct
        # interpretation wins every tie.
        visit(index + 1, [*parts, token], transformations)

        # A two-digit number such as 75 can also be heard as 70 5.
        if len(token) == 2 and token[1] != "0":
            expanded = f"{token[0]}0{token[1]}"
            visit(index + 1, [*parts, expanded], transformations + 1)

        # A three-digit number such as 700 may be heard as the leading digit.
        if len(token) == 3 and token[0] != "0" and token[1:] == "00":
            visit(index + 1, [*parts, token[0]], transformations + 1)

        # A sequence such as 20 5 can also be heard as 25.
        if (
            len(token) == 2
            and token[0] != "1"
            and token[1] == "0"
            and index + 1 < len(tokens)
            and len(tokens[index + 1]) == 1
        ):
            collapsed = f"{token[0]}{tokens[index + 1]}"
            visit(index + 2, [*parts, collapsed], transformations + 1)

    visit(0, [], 0)
    return candidates


def is_valid_greek_phone(number: str) -> bool:
    return (
        (len(number) == 10 and (number.startswith("2") or number.startswith("69")))
        or (
            len(number) == 14
            and (number.startswith("00302") or number.startswith("003069"))
        )
    )


def generate_interpretations(tokens: Iterable[str]) -> list[Candidate]:
    normalized = validate_tokens(tokens)
    return _generate_candidates(normalized)


def interpret_tokens(tokens: Iterable[str]) -> tuple[str, float, bool]:
    candidates = generate_interpretations(tokens)

    # Score is intentionally independent from phone validity. The primary
    # criterion is directness, with generation order as the deterministic tie-breaker.
    selected = max(candidates, key=lambda candidate: (candidate.score, -candidate.order))
    return selected.number, selected.score, is_valid_greek_phone(selected.number)
