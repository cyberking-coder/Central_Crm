"""
CSV export helpers (Part 17 control #10).

- Sanitises against CSV formula injection (=, +, -, @, tab, CR).
- Call-sites must apply the same permission class as the data API.
"""
from __future__ import annotations

import csv
import io
from typing import Iterable, Sequence

_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitise_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text and text[0] in _DANGEROUS_PREFIXES:
        return "'" + text
    return text


def write_csv(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([sanitise_cell(h) for h in headers])
    for row in rows:
        writer.writerow([sanitise_cell(c) for c in row])
    return buf.getvalue().encode("utf-8")
