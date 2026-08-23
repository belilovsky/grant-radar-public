"""Protect public sequence labels from decorative leading zeroes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_sequence_labels_are_plain_integers() -> None:
    public_renderers = (
        ROOT / "api" / "application_prep_page.py",
        ROOT / "api" / "media_page.py",
        ROOT / "api" / "opportunity_page.py",
        ROOT / "api" / "public_info_page.py",
    )

    for renderer in public_renderers:
        source = renderer.read_text()
        assert "{index:02d}" not in source
        assert "{number:02d}" not in source
