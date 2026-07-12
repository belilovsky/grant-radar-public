from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "QAZSTACK_PRIMITIVES_REVIEW_2026-07-11.md"


def test_qazstack_primitives_review_exists_with_bidirectional_sections() -> None:
    text = DOC.read_text()

    assert "Pass 1 – QAZ.FUND primitives to upstream into QazStack" in text
    assert "Pass 2 – QazStack/platform primitives QAZ.FUND should adopt" in text
    assert "Kazakhstan/Central Asia geo-fit rules" in text
    assert "Public AI/discovery surface contract" in text
    assert "Operator list card anatomy" in text
    assert "collectors-and-entity-pipeline" in text
    assert "tasking-and-resilience" in text
    assert "Do not upstream now" in text
