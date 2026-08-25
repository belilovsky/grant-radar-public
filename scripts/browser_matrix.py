"""Playwright browser, overflow, console, and axe checks for launch surfaces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from playwright.sync_api import ConsoleMessage, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE_SURFACES = (
    "/?lang=ru",
    "/status?lang=ru",
    "/media?lang=ru",
    "/compare?lang=ru",
    "/insights?lang=ru",
    "/embed/opportunities?lang=ru",
    "/embed/coverage?lang=ru",
    "/terms?lang=ru",
    "/data-policy?lang=ru",
    "/attribution?lang=ru",
    "/data-routes?lang=ru",
    "/operator?lang=ru",
    "/docs?lang=ru",
)
VIEWPORTS = (
    (320, 800),
    (390, 844),
    (768, 1024),
    (1024, 768),
    (1440, 960),
    (1920, 1080),
    (2560, 1440),
)


def _overflow_nodes(page: Page) -> list[dict[str, Any]]:
    return page.evaluate("""() => {
          const viewport = document.documentElement.clientWidth;
          return [...document.querySelectorAll('body *')]
            .filter((node) => {
              const rect = node.getBoundingClientRect();
              return rect.right > viewport + 1 || rect.left < -1;
            })
            .slice(0, 20)
            .map((node) => ({
              tag: node.tagName.toLowerCase(),
              id: node.id || null,
              class: String(node.className || '').slice(0, 160),
              left: Math.round(node.getBoundingClientRect().left),
              right: Math.round(node.getBoundingClientRect().right),
              viewport,
            }));
        }""")


def _surfaces(
    *, opportunity_id: str = "", funder_slug: str = "", comparison_ids: str = ""
) -> tuple[str, ...]:
    surfaces = list(BASE_SURFACES)
    if opportunity_id:
        surfaces.extend(
            [
                f"/opportunity/{opportunity_id}?lang=ru",
                f"/opportunity/{opportunity_id}/prepare?lang=ru",
            ]
        )
    if funder_slug:
        surfaces.append(f"/funder/{funder_slug}?lang=ru")
    if comparison_ids:
        surfaces.append(f"/compare?lang=ru&ids={comparison_ids}")
    return tuple(surfaces)


def _interaction_errors(page: Page, surface: str, *, width: int) -> list[str]:
    errors: list[str] = []
    if surface.startswith("/?") and width == 390:
        compare_buttons = page.locator("[data-compare-opportunity]")
        try:
            compare_buttons.nth(1).wait_for(state="attached", timeout=10_000)
        except PlaywrightTimeoutError:
            pass
        if compare_buttons.count() < 2:
            errors.append("catalog did not render two comparison controls")
        else:
            compare_buttons.nth(0).click()
            compare_buttons.nth(1).click()
            compare_link = page.locator("#compare-selected")
            compare_href = compare_link.get_attribute("href") or ""
            if (
                compare_link.get_attribute("aria-disabled") != "false"
                or "ids=" not in compare_href
                or ("," not in compare_href and "%2C" not in compare_href)
            ):
                errors.append(
                    f"comparison selection did not produce a usable link: {compare_href}"
                )
            else:
                page.goto(
                    f"{urlsplit(page.url).scheme}://{urlsplit(page.url).netloc}{compare_href}",
                    wait_until="domcontentloaded",
                )
                if (
                    page.locator('[data-avds-component="comparison-table"]').count()
                    != 1
                ):
                    errors.append(
                        "comparison journey did not reach the comparison table"
                    )
            page.evaluate("localStorage.clear()")
    elif surface.startswith("/?") and width == 1440:
        export = page.locator(".catalog-export > summary")
        export.click()
        with page.expect_download() as csv_download:
            page.locator("#export-csv").click()
        if not csv_download.value.suggested_filename.endswith(".csv"):
            errors.append("CSV export did not produce a CSV download")
        with page.expect_download() as calendar_download:
            page.locator("#export-deadlines").click()
        if not calendar_download.value.suggested_filename.endswith(".ics"):
            errors.append("deadline export did not produce an ICS download")
    elif surface.startswith("/funder/"):
        search = page.locator("#funder-program-search")
        if search.count():
            query = page.locator(".opportunity-card h3").first.inner_text().strip()
            if not query:
                return errors
            search.fill(query)
            state = page.locator(".opportunity-card").evaluate_all(
                """cards => cards.map(card => ({
                  title: String(card.querySelector('h3')?.textContent || '').trim(),
                  hidden: card.hidden,
                  display: getComputedStyle(card).display,
                }))"""
            )
            visible = [row for row in state if row["display"] != "none"]
            if not visible or any(
                query.casefold() not in row["title"].casefold() for row in visible
            ):
                errors.append(f"funder search did not isolate exact program: {state}")
    elif surface.startswith("/media?"):
        search = page.locator("#media-search")
        if search.count():
            search.fill("нет-такого-обновления")
            visible_count = page.locator(".media-latest .media-card:visible").count()
            empty_display = page.locator("#media-search-empty").evaluate(
                "node => getComputedStyle(node).display"
            )
            if visible_count or empty_display == "none":
                errors.append("media search empty state is not visible")
    elif surface.startswith("/status?"):
        state = page.locator("tbody tr[data-source-state]").evaluate_all("""rows => ({
              total: rows.length,
              visible: rows.filter(row => getComputedStyle(row).display !== 'none').length,
            })""")
        if state["total"] != state["visible"]:
            errors.append(f"attention-first status view hid rows: {state}")
    elif "/prepare?" in surface and width == 390:
        organisation = page.locator('[name="org_name"]')
        if organisation.count():
            organisation.fill("QAZ.FUND browser-only probe")
            page.wait_for_timeout(150)
            page.reload(wait_until="domcontentloaded")
            if organisation.input_value() != "QAZ.FUND browser-only probe":
                errors.append(
                    "browser-only application autosave did not survive reload"
                )
            page.evaluate("localStorage.clear()")
    return errors


def run_matrix(
    *,
    base_url: str,
    axe_path: Path,
    opportunity_id: str = "",
    funder_slug: str = "",
    comparison_ids: str = "",
) -> dict[str, Any]:
    axe_source = axe_path.read_text(encoding="utf-8")
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    base_parts = urlsplit(base_url)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for width, height in VIEWPORTS:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                reduced_motion="reduce",
                bypass_csp=True,
            )
            for surface in _surfaces(
                opportunity_id=opportunity_id,
                funder_slug=funder_slug,
                comparison_ids=comparison_ids,
            ):
                page = context.new_page()
                console_errors: list[str] = []
                page_errors: list[str] = []
                request_failures: list[str] = []
                first_party_errors: list[str] = []

                def on_console(message: ConsoleMessage) -> None:
                    if message.type == "error":
                        console_errors.append(message.text)

                page.on("console", on_console)
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.on(
                    "requestfailed",
                    lambda request: request_failures.append(
                        f"{request.method} {request.url}: {request.failure}"
                    ),
                )

                def on_response(response: Any) -> None:
                    parts = urlsplit(response.url)
                    if (
                        parts.scheme == base_parts.scheme
                        and parts.netloc == base_parts.netloc
                        and response.status >= 400
                    ):
                        first_party_errors.append(
                            f"{response.request.method} {response.url}: HTTP {response.status}"
                        )

                page.on("response", on_response)
                response = page.goto(
                    f"{base_url.rstrip('/')}{surface}", wait_until="domcontentloaded"
                )
                page.wait_for_timeout(400)
                try:
                    page.locator("h1").first.wait_for(state="attached", timeout=10_000)
                except PlaywrightTimeoutError:
                    pass
                status = response.status if response is not None else 0
                h1_count = page.locator("h1").count()
                overflow = _overflow_nodes(page)
                page.add_script_tag(content=axe_source)
                axe = page.evaluate("""async () => await axe.run(document, {
                      resultTypes: ['violations'],
                      rules: {'color-contrast': {enabled: true}}
                    })""")
                serious = [
                    violation
                    for violation in axe["violations"]
                    if violation.get("impact") in {"critical", "serious"}
                ]
                interaction_errors = _interaction_errors(page, surface, width=width)
                key = f"{surface}@{width}x{height}"
                if status >= 400:
                    failures.append(f"{key}: HTTP {status}")
                if h1_count != 1:
                    failures.append(f"{key}: expected one H1, found {h1_count}")
                if overflow:
                    failures.append(f"{key}: horizontal overflow {overflow}")
                if console_errors or page_errors:
                    failures.append(
                        f"{key}: console={console_errors} page_errors={page_errors}"
                    )
                if request_failures or first_party_errors:
                    failures.append(
                        f"{key}: request_failures={request_failures} "
                        f"first_party_errors={first_party_errors}"
                    )
                if serious:
                    failures.append(
                        f"{key}: serious accessibility findings "
                        + ", ".join(str(item.get("id")) for item in serious)
                    )
                if interaction_errors:
                    failures.append(f"{key}: interactions={interaction_errors}")
                results.append(
                    {
                        "surface": surface,
                        "viewport": {"width": width, "height": height},
                        "status": status,
                        "h1_count": h1_count,
                        "overflow": overflow,
                        "console_errors": console_errors,
                        "page_errors": page_errors,
                        "request_failures": request_failures,
                        "first_party_errors": first_party_errors,
                        "serious_accessibility": serious,
                        "interaction_errors": interaction_errors,
                    }
                )
                page.close()
            context.close()
        browser.close()
    return {"checks": len(results), "failures": failures, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--axe-path", type=Path, required=True)
    parser.add_argument("--opportunity-id", default="")
    parser.add_argument("--funder-slug", default="")
    parser.add_argument("--comparison-ids", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_matrix(
        base_url=args.base_url,
        axe_path=args.axe_path,
        opportunity_id=args.opportunity_id,
        funder_slug=args.funder_slug,
        comparison_ids=args.comparison_ids,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
