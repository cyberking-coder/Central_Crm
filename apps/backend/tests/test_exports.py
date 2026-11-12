"""Part 17 control #10 — CSV formula-injection sanitisation."""
from __future__ import annotations

from apps.core.exports import sanitise_cell, write_csv


def test_sanitise_cell_prefixes_dangerous_characters() -> None:
    assert sanitise_cell("=SUM(A1:A2)") == "'=SUM(A1:A2)"
    assert sanitise_cell("+cmd|'/C calc'") == "'+cmd|'/C calc'"
    assert sanitise_cell("-1") == "'-1"
    assert sanitise_cell("@domain") == "'@domain"
    assert sanitise_cell("\tinjected") == "'\tinjected"
    assert sanitise_cell("safe") == "safe"
    assert sanitise_cell(None) == ""


def test_write_csv_sanitises_rows() -> None:
    data = write_csv(["name", "value"], [["=1+1", "ok"], ["plain", "@evil"]])
    text = data.decode("utf-8")
    assert "'=1+1" in text
    assert "'@evil" in text
    assert "plain" in text
