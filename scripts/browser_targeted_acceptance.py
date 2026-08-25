"""Targeted browser checks for locale, privacy, focus, touch, and real 404 behavior."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from playwright.sync_api import Page, sync_playwright

LOCALES = ("ru", "kk", "en")
VIEWPORTS = ((390, 844), (1440, 960))


def _overflow(page: Page) -> bool:
    return bool(page.evaluate("""() => document.documentElement.scrollWidth >
              document.documentElement.clientWidth + 1"""))


def _serious_axe(page: Page, axe_source: str) -> list[dict[str, Any]]:
    page.add_script_tag(content=axe_source)
    result = page.evaluate(
        """async () => await axe.run(document, {resultTypes: ['violations']})"""
    )
    return [
        item
        for item in result["violations"]
        if item.get("impact") in {"critical", "serious"}
    ]


def _locale_cases(
    context: Any,
    base_url: str,
    axe_source: str,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for locale in LOCALES:
        for width, height in VIEWPORTS:
            page = context.new_page()
            page.set_viewport_size({"width": width, "height": height})
            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on(
                "console",
                lambda message: (
                    console_errors.append(message.text)
                    if message.type == "error"
                    else None
                ),
            )
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            response = page.goto(
                f"{base_url}/?lang={locale}", wait_until="domcontentloaded"
            )
            page.wait_for_timeout(250)
            serious = _serious_axe(page, axe_source)
            case = {
                "kind": "locale",
                "locale": locale,
                "viewport": {"width": width, "height": height},
                "status": response.status if response else 0,
                "document_language": page.locator("html").get_attribute("lang"),
                "h1_count": page.locator("h1").count(),
                "overflow": _overflow(page),
                "console_errors": console_errors,
                "page_errors": page_errors,
                "serious_accessibility": [item.get("id") for item in serious],
            }
            case["ok"] = (
                case["status"] == 200
                and case["document_language"] == locale
                and case["h1_count"] == 1
                and not case["overflow"]
                and not console_errors
                and not page_errors
                and not serious
            )
            cases.append(case)
            page.close()
    return cases


def _missing_route_case(
    context: Any,
    base_url: str,
    axe_source: str,
) -> dict[str, Any]:
    page = context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on(
        "console",
        lambda message: (
            console_errors.append(message.text) if message.type == "error" else None
        ),
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    response = page.goto(
        f"{base_url}/__qazfund_missing_acceptance__?lang=ru",
        wait_until="domcontentloaded",
    )
    serious = _serious_axe(page, axe_source)
    expected_navigation_errors = [
        message
        for message in console_errors
        if "server responded with a status of 404" in message
    ]
    blocking_console_errors = [
        message
        for message in console_errors
        if message not in expected_navigation_errors
    ]
    case = {
        "kind": "real-404",
        "status": response.status if response else 0,
        "h1_count": page.locator("h1").count(),
        "overflow": _overflow(page),
        "expected_navigation_console": expected_navigation_errors,
        "blocking_console_errors": blocking_console_errors,
        "page_errors": page_errors,
        "serious_accessibility": [item.get("id") for item in serious],
    }
    case["ok"] = (
        case["status"] == 404
        and case["h1_count"] == 1
        and not case["overflow"]
        and not blocking_console_errors
        and not page_errors
        and not serious
    )
    page.close()
    return case


def _focus_and_touch_case(context: Any, base_url: str) -> dict[str, Any]:
    page = context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{base_url}/?lang=ru", wait_until="domcontentloaded")
    page.keyboard.press("Tab")
    focus = page.evaluate("""() => {
          const node = document.activeElement;
          const style = node ? getComputedStyle(node) : null;
          return {
            tag: node?.tagName?.toLowerCase() || null,
            text: String(node?.getAttribute('aria-label') || node?.textContent || '')
              .trim().slice(0, 120),
            visible: Boolean(node && style && style.display !== 'none' &&
              style.visibility !== 'hidden' && node.getClientRects().length),
            outline: style?.outlineStyle || null,
          };
        }""")
    touch = page.locator("[data-compare-opportunity]").evaluate_all(
        """nodes => nodes.slice(0, 4).map(node => {
          const rect = node.getBoundingClientRect();
          return {
            width: Math.round(rect.width),
            height: Math.round(rect.height),
            label: String(node.getAttribute('aria-label') || node.textContent || '')
              .trim().slice(0, 120),
          };
        })"""
    )
    case = {
        "kind": "focus-and-critical-touch-targets",
        "focus": focus,
        "touch_targets": touch,
    }
    case["ok"] = bool(
        focus["visible"]
        and focus["tag"] not in {None, "body", "html"}
        and touch
        and all(item["width"] >= 44 and item["height"] >= 44 for item in touch)
    )
    page.close()
    return case


def _prep_privacy_case(
    context: Any,
    base_url: str,
    opportunity_id: str,
) -> dict[str, Any]:
    page = context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    requests: list[dict[str, str]] = []
    base_parts = urlsplit(base_url)

    def record_request(request: Any) -> None:
        parts = urlsplit(request.url)
        requests.append(
            {
                "method": request.method,
                "url": request.url,
                "first_party": str(
                    parts.scheme == base_parts.scheme
                    and parts.netloc == base_parts.netloc
                ).lower(),
            }
        )

    page.on("request", record_request)
    path = f"/opportunity/{opportunity_id}/prepare?lang=ru"
    response = page.goto(f"{base_url}{path}", wait_until="domcontentloaded")
    page.wait_for_timeout(200)
    requests.clear()
    editor = page.locator("textarea, input[type='text']").first
    editor.fill("Локальный проверочный черновик")
    page.wait_for_timeout(600)
    stored_keys = page.evaluate("() => Object.keys(localStorage)")
    mutating = [
        request
        for request in requests
        if request["method"] in {"POST", "PUT", "PATCH", "DELETE"}
    ]
    third_party = [request for request in requests if request["first_party"] == "false"]
    case = {
        "kind": "browser-only-preparation",
        "status": response.status if response else 0,
        "storage_keys": stored_keys,
        "requests_after_edit": requests,
        "mutating_requests": mutating,
        "third_party_requests": third_party,
    }
    case["ok"] = bool(
        case["status"] == 200 and stored_keys and not mutating and not third_party
    )
    page.close()
    return case


def run(
    *,
    base_url: str,
    axe_path: Path,
    opportunity_id: str,
) -> dict[str, Any]:
    axe_source = axe_path.read_text(encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        cases = _locale_cases(context, base_url, axe_source)
        cases.append(_missing_route_case(context, base_url, axe_source))
        cases.append(_focus_and_touch_case(context, base_url))
        cases.append(_prep_privacy_case(context, base_url, opportunity_id))
        context.close()
        browser.close()
    failures = [case for case in cases if not case["ok"]]
    return {
        "schema_version": "qazfund-targeted-browser-acceptance-v1",
        "base_url": base_url,
        "checks": len(cases),
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--axe-path", type=Path, required=True)
    parser.add_argument("--opportunity-id", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run(
        base_url=args.base_url.rstrip("/"),
        axe_path=args.axe_path,
        opportunity_id=args.opportunity_id,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
