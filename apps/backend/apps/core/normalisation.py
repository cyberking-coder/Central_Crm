"""Phone & email normalisation for duplicate detection (Part 17 #7)."""
from __future__ import annotations

import re

_PHONE_NON_DIGIT = re.compile(r"\D+")


def normalise_phone(raw: str | None) -> str:
    """
    Reduce a phone number to digits only. Country-code stripping is NOT
    performed here — the CRM stores the normalised form for matching and
    keeps the raw string for display. A real libphonenumber pass can
    replace this later without changing call sites.
    """
    if not raw:
        return ""
    return _PHONE_NON_DIGIT.sub("", raw)


def normalise_email(raw: str | None) -> str:
    if not raw:
        return ""
    return raw.strip().lower()
