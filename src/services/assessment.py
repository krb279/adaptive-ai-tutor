from __future__ import annotations

import re
from typing import Iterable


def contains_any(text: str, expected_terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in expected_terms)


def extract_number(text: str) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group())


def close_enough(user_answer: str, expected: float, tolerance: float = 0.01) -> bool:
    number = extract_number(user_answer)
    if number is None:
        return False
    return abs(number - expected) <= tolerance
