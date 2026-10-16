from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class NumberParsingError(ValueError):
    """Raised when a transcript does not contain supported number content."""


@dataclass(frozen=True)
class ParsedTranscript:
    tokens: list[str]
    language: str


_DIGIT_RUN = re.compile(r"\d+")
_ALPHA_CHARACTER = re.compile(r"[A-Za-zÀ-ÿ]", re.UNICODE)
_WORD_TOKEN = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)


def _resolution_value(result: Any) -> str | None:
    resolution = getattr(result, "resolution", None)
    if isinstance(resolution, dict):
        value = resolution.get("value")
        if value is not None:
            return str(value)
        values = resolution.get("values")
        if isinstance(values, list) and values:
            first = values[0]
            if isinstance(first, dict) and first.get("value") is not None:
                return str(first["value"])

    value = getattr(result, "value", None)
    return None if value is None else str(value)


def _split_numeric_value(value: str) -> list[str]:
    digits = re.sub(r"\D", "", value)
    if not digits:
        return []
    if len(digits) <= 3:
        return [digits]
    return list(digits)


def _recognize_with_microsoft(text: str, language: str) -> list[str]:
    try:
        from recognizers_number import NumberRecognizer
        culture = "English" if language == "en" else "Spanish"
        recognizer = NumberRecognizer()
        model = recognizer.get_number_model(culture)
        results = model.parse(text)
    except Exception:  # noqa: BLE001 - fallback keeps the app usable if the alpha package changes
        return []

    tokens: list[str] = []
    for result in results:
        value = _resolution_value(result)
        if value is not None:
            tokens.extend(_split_numeric_value(value))
    return tokens


_ENGLISH_UNITS = {
    "zero": 0,
    "oh": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_ENGLISH_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_SPANISH_UNITS = {
    "cero": 0,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciséis": 16,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
}
_SPANISH_TENS = {
    "veinte": 20,
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
}


def _fallback_word_tokens(text: str, language: str) -> list[str]:
    words = [token.lower() for token in _WORD_TOKEN.findall(text)]
    units = _ENGLISH_UNITS if language == "en" else _SPANISH_UNITS
    tens = _ENGLISH_TENS if language == "en" else _SPANISH_TENS
    hundred_words = {"hundred"} if language == "en" else {"cien", "ciento", "cientos", "cientas"}

    tokens: list[str] = []
    current = 0
    has_number = False

    def flush() -> None:
        nonlocal current, has_number
        if has_number:
            tokens.extend(_split_numeric_value(str(current)))
            current = 0
            has_number = False

    for word in words:
        if word in units:
            current += units[word]
            has_number = True
        elif word in tens:
            current += tens[word]
            has_number = True
        elif word in hundred_words:
            current = max(current, 1) * 100
            has_number = True
        elif word in {"and", "y", "con", "veinti", "veintiún", "veintiuno"}:
            continue
        else:
            flush()

    flush()
    return tokens


def parse_transcript(text: str, language: str) -> ParsedTranscript:
    if language not in {"en", "es"}:
        raise NumberParsingError("Only English and Spanish audio are supported")

    direct_tokens: list[str] = []
    if _DIGIT_RUN.search(text) and not _ALPHA_CHARACTER.search(text):
        for match in _DIGIT_RUN.finditer(text):
            direct_tokens.extend(_split_numeric_value(match.group(0)))
    else:
        direct_tokens = _recognize_with_microsoft(text, language)
        if not direct_tokens:
            direct_tokens = _fallback_word_tokens(text, language)

    if not direct_tokens:
        raise NumberParsingError("No numeric content was recognized")

    if any(not token.isdigit() or not 1 <= len(token) <= 3 for token in direct_tokens):
        raise NumberParsingError("Recognized numbers must contain one to three digits")

    return ParsedTranscript(tokens=direct_tokens, language=language)
