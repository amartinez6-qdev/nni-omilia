import pytest

from src.engine import InterpretationError, _generate_candidates, interpret_tokens, is_valid_greek_phone


def numbers(tokens: list[str]) -> list[str]:
    return [candidate.number for candidate in _generate_candidates(tokens)]


def test_direct_interpretation_and_assignment_examples() -> None:
    assert interpret_tokens(["30", "2", "5", "58"])[0] == "302558"
    assert interpret_tokens(["2", "10", "69", "30", "6", "60", "4"])[0] == "21069306604"


def test_ambiguity_examples_are_generated() -> None:
    assert numbers(["2", "10", "6", "9", "30", "6", "6", "4"]) == [
        "2106930664",
        "210693664",
    ]
    generated = numbers(["2", "10", "69", "30", "6", "6", "4"])
    assert generated[:4] == [
        "2106930664",
        "210693664",
        "21060930664",
        "2106093664",
    ]


def test_direct_candidate_wins_even_when_an_alternative_is_valid() -> None:
    number, score, valid = interpret_tokens(
        ["0", "0", "30", "69", "700", "24", "1", "3", "50", "2"]
    )
    assert number == "0030697002413502"
    assert score == 1.0
    assert valid is False


def test_advanced_example_contains_the_valid_ambiguous_variant() -> None:
    candidates = _generate_candidates(
        ["0", "0", "30", "69", "700", "24", "1", "3", "50", "2"]
    )

    valid_numbers = [
        candidate.number
        for candidate in candidates
        if is_valid_greek_phone(candidate.number)
    ]

    assert "00306972413502" in valid_numbers


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        ("2106930664", True),
        ("00306974092252", True),
        ("302558", False),
        ("21069306604", False),
    ],
)
def test_greek_phone_validation(number: str, expected: bool) -> None:
    assert is_valid_greek_phone(number) is expected


def test_tokens_are_limited_to_three_digits() -> None:
    with pytest.raises(InterpretationError):
        interpret_tokens(["1000"])
