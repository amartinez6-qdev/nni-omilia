from nni_backend.number_parser import parse_transcript


def test_numeric_transcript_is_split_into_supported_tokens() -> None:
    parsed = parse_transcript("00306974092252", "en")
    assert "".join(parsed.tokens) == "00306974092252"


def test_english_word_fallback() -> None:
    parsed = parse_transcript("one hundred and two", "en")
    assert parsed.tokens == ["102"]


def test_spanish_word_fallback() -> None:
    parsed = parse_transcript("ciento dos", "es")
    assert parsed.tokens == ["102"]
