from src.number_parser import parse_transcript


def test_numeric_transcript_is_split_into_supported_tokens() -> None:
    parsed = parse_transcript("00306974092252", "en")
    assert "".join(parsed.tokens) == "00306974092252"


def test_english_word_fallback() -> None:
    parsed = parse_transcript("one hundred and two", "en")
    assert parsed.tokens == ["102"]


def test_spanish_word_fallback() -> None:
    parsed = parse_transcript("ciento dos", "es")
    assert parsed.tokens == ["102"]


def test_spanish_transcript_preserves_mixed_digit_groups() -> None:
    parsed = parse_transcript("dos, 10, 69, 30 y 6 y 60 y 4.", "es")
    assert parsed.tokens == ["2", "10", "69", "30", "6", "60", "4"]


def test_english_transcript_uses_number_groups() -> None:
    parsed = parse_transcript("two ten sixty nine thirty six six four", "en")
    assert parsed.tokens == ["2", "10", "69", "36", "6", "4"]
