"""Unit tests for HTML parsing in M2 source parsers.

These tests exercise the regex-based extractors (`CARD_RE`, `LINK_RE`,
`DEADLINE_RE`) directly on synthetic HTML fragments so they don't depend on
live network access. They guard against accidental regression in the parsing
rules used by `AstanaHubSource` and `InternewsSource`.
"""

from __future__ import annotations

import pytest

from sources import astana_hub as ah
from sources import eeas_kazakhstan as eeas
from sources import internews as iw

ASTANA_HTML = """
<html><body>
<div class="programs">
  <a href="/ru/service/programs/tech-orda/" class="card">
    <h3>Tech Orda Program</h3>
  </a>
  <p>Приём заявок до 15.06.2026</p>

  <a href="/ru/service/programs/silkway-accelerator/" class="card">
    <h3>Silkway Accelerator</h3>
  </a>
  <p>Deadline: 01-09-2026</p>
</div>
</body></html>
"""

INTERNEWS_HTML = """
<html><body>
<ul>
  <li><a href="https://internews.org/opportunity/media-grant-2026/">Media Grant 2026</a></li>
  <p>Deadline: 30 Jun 2026</p>
  <li><a href="https://internews.org/resource/journalism-fellowship/">Journalism Fellowship</a></li>
  <p>Apply by 12 Sep 2026</p>
</ul>
</body></html>
"""

EEAS_LISTING_HTML = """
<html><body>
<div class="card">
  <h3 class="h2 card-title">
    <a
      href=/delegations/kazakhstan/call-proposals-%E2%80%9Csupport-civil-society-kazakhstan%E2%80%9D-2_en
    >
      Call for Proposals “Support to Civil Society in Kazakhstan”
    </a>
  </h3>
  <time datetime="2026-05-12T12:00:00Z" class="datetime">12.05.2026</time>
</div>
<div class="card">
  <h3 class="h2 card-title">
    <a href=/delegations/kazakhstan/list-contracts-concluded_en>
      The list of contracts that were concluded
    </a>
  </h3>
  <time datetime="2024-05-30T12:00:00Z" class="datetime">30.05.2024</time>
</div>
</body></html>
"""


def test_astana_card_regex_finds_two_programs():
    matches = list(ah.CARD_RE.finditer(ASTANA_HTML))
    assert len(matches) >= 2
    hrefs = {m.group("href") for m in matches}
    assert "/ru/service/programs/tech-orda/" in hrefs
    assert "/ru/service/programs/silkway-accelerator/" in hrefs


def test_astana_deadline_regex_parses_dotted_date():
    m = ah.DEADLINE_RE.search("Срок до 15.06.2026 включительно")
    assert m is not None
    day, month, year = m.groups()
    assert (int(day), int(month), int(year)) == (15, 6, 2026)


def test_internews_link_regex_finds_opportunities():
    matches = list(iw.LINK_RE.finditer(INTERNEWS_HTML))
    assert len(matches) == 2
    titles = [m.group("title").strip() for m in matches]
    assert "Media Grant 2026" in titles
    assert "Journalism Fellowship" in titles


def test_internews_deadline_regex_parses_text_month():
    m = iw.DEADLINE_RE.search("Deadline: 30 Jun 2026")
    assert m is not None
    assert int(m.group("d")) == 30
    assert m.group("m").lower().startswith("jun")
    assert int(m.group("y")) == 2026


def test_eeas_listing_extractor_finds_kazakhstan_grant_card():
    entries = eeas._extract_listing_entries(EEAS_LISTING_HTML)

    assert len(entries) == 1
    assert (
        entries[0].title
        == "Call for Proposals “Support to Civil Society in Kazakhstan”"
    )
    assert entries[0].url == (
        "https://www.eeas.europa.eu/delegations/kazakhstan/"
        "call-proposals-%E2%80%9Csupport-civil-society-kazakhstan%E2%80%9D-2_en"
    )
    assert entries[0].deadline.isoformat() == "2026-05-12"


def test_eeas_fallback_summary_is_public_ready():
    summary = eeas._fallback_summary("Call for Proposals on climate resilience")

    assert summary.startswith("Official EEAS Kazakhstan call:")
    assert "submission documents" in summary
    assert len(summary) >= 120


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Deadline: 12 Sep 2026", (12, "sep", 2026)),
        ("Apply by 1 Jan 2027", (1, "jan", 2027)),
        ("Closes 28 February 2026", (28, "feb", 2026)),
    ],
)
def test_internews_deadline_regex_variants(text, expected):
    m = iw.DEADLINE_RE.search(text)
    assert m is not None
    d, mo, y = expected
    assert int(m.group("d")) == d
    assert m.group("m").lower().startswith(mo)
    assert int(m.group("y")) == y
