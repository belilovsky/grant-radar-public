from __future__ import annotations

import json
from pathlib import Path

from api.error_page import render_not_found_page
from api.operator_page import render_operator_page
from api.public_info_page import render_public_info_page
from core.localization import normalize_content_lang

ROOT = Path(__file__).resolve().parents[1]


def test_locale_aliases_normalize_to_canonical_codes() -> None:
    assert normalize_content_lang("kz") == "kk"
    assert normalize_content_lang("kaz_Cyrl") == "kk"
    assert normalize_content_lang("ru-RU") == "ru"
    assert normalize_content_lang("eng") == "en"
    assert normalize_content_lang("unknown") == "ru"


def test_public_explanation_supports_kazakh_without_russian_shell_fallback() -> None:
    html = render_public_info_page(
        kind="terms",
        lang="kz",
        root_path="",
        site_origin="https://qaz.fund",
    )

    assert '<html lang="kk"' in html
    assert "Каталогқа оралу" in html
    assert "Пайдалану шарттары" in html
    assert 'hreflang="kk"' in html
    assert "Вернуться в каталог" not in html


def test_error_and_operator_surfaces_support_kazakh_alias() -> None:
    not_found = render_not_found_page(lang="kz")
    operator = render_operator_page(lang="kaz_Cyrl")

    assert '<html lang="kk"' in not_found
    assert "Мұндай бет жоқ" in not_found
    assert '<html lang="kk"' in operator
    assert "Дереккөздерді бақылау" in operator
    assert 'lang="kk"' in operator
    assert 'href="/does-not-exist?lang=kk"' in not_found
    assert 'href="/does-not-exist?lang=ru"' in not_found
    assert 'href="/does-not-exist?lang=en"' in not_found
    assert 'hreflang="kk"' in operator


def test_language_surface_contract_matches_public_pages() -> None:
    contract = json.loads(
        (ROOT / "docs/qazstack/language-surface.json").read_text(encoding="utf-8")
    )
    assert contract["canonical_locales"] == ["kk", "ru", "en"]
    assert set(contract["surfaces"]) == {
        "dashboard",
        "opportunity_detail",
        "funder_detail",
        "insights",
        "status",
        "public_info",
        "error_page",
        "operator",
    }
    assert contract["content_policy"]["automatic_translation_publishing"] is False
    observability = contract["observability"]
    assert observability["runtime_connected"] is False
    assert observability["mode"] == "contract-only"
    assert observability["report_schema"].endswith(
        "qazstack-language-observability-v1.json"
    )
    assert observability["raw_text_export"] is False
    assert observability["remote_write"] is False
    assert observability["automatic_memory_promotion"] is False
    assert "source_language" in observability["dimensions"]
