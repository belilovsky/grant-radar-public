"""Shared visual primitives for the QAZ.FUND public brand layer."""

from __future__ import annotations

from urllib.parse import quote

# A compact four-way arabesque mark derived from the current QAZ.FUND visual
# direction.  It stays inline so the server-rendered pages do not need a new
# asset pipeline or a request that can block first paint.
BRAND_MARK_PATH = """
<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
  <path stroke-width="7"
    d="M50 50C40 43 30 35 27 25c-2-8 3-15 11-16 8-1 14 5 13 12-1 7-8 10-14 6"/>
  <path stroke-width="7"
    d="M50 50C57 40 65 30 75 27c8-2 15 3 16 11 1 8-5 14-12 13-7-1-10-8-6-14"/>
  <path stroke-width="7"
    d="M50 50C60 57 70 65 73 75c2 8-3 15-11 16-8 1-14-5-13-12 1-7 8-10 14-6"/>
  <path stroke-width="7"
    d="M50 50C43 60 35 70 25 73c-8 2-15-3-16-11-1-8 5-14 12-13 7 1 10 8 6 14"/>
</g>
<path fill="currentColor" d="M50 37 63 50 50 63 37 50 50 37Z"/>
<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
  stroke-width="5" d="M19 19h13M81 19H68M81 81H68M19 81h13"/>
""".strip()

BRAND_MARK_SVG = (
    '<svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
    f"{BRAND_MARK_PATH}</svg>"
)

BRAND_FAVICON_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="15" fill="#063f43"/>
  <g transform="translate(7 7) scale(.5)" color="#e2b34e">{BRAND_MARK_PATH}</g>
</svg>"""


BRAND_PATTERN_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180" viewBox="0 0 180 180">
  <g fill="none" stroke="#e2b34e" stroke-opacity=".2" stroke-linecap="round"
    stroke-linejoin="round" stroke-width="4">
    <path d="M90 14c-8 14-24 18-35 8-8-7-7-19 2-24 8-5 18-1 19 8 1 7-5 12-12 10"/>
    <path d="M166 90c-14-8-18-24-8-35 7-8 19-7 24 2 5 8 1 18-8 19-7 1-12-5-10-12"/>
    <path d="M90 166c8-14 24-18 35-8 8 7 7 19-2 24-8 5-18 1-19-8-1-7 5-12 12-10"/>
    <path d="M14 90c14 8 18 24 8 35-7 8-19 7-24-2-5-8-1-18 8-19 7-1 12 5 10 12"/>
  </g>
  <path fill="#e2b34e" fill-opacity=".16" d="m90 72 18 18-18 18-18-18 18-18Z"/>
</svg>
""".strip()
BRAND_PATTERN_DATA_URI = "data:image/svg+xml," + quote(BRAND_PATTERN_SVG, safe="")

# The pattern is intentionally quiet: it gives the hero and branded recovery
# surfaces the same tactile depth as the reference without competing with
# content or reducing contrast.
BRAND_CSS = r"""
    :root {
      --qaz-brand-deep: #063f43;
      --qaz-brand-ink: #12383a;
      --qaz-brand-teal: #0b716c;
      --qaz-brand-teal-hover: #075956;
      --qaz-brand-cream: #f4f0e8;
      --qaz-brand-paper: #fffdf9;
      --qaz-brand-gold: #e2b34e;
      --qaz-brand-gold-soft: #f4e3b8;
      --qaz-brand-pattern: url("BRAND_PATTERN_DATA_URI");
    }

    .brand-mark {
      display: inline-grid;
      flex: 0 0 auto;
      place-items: center;
      width: 42px;
      height: 42px;
      color: var(--qaz-brand-gold);
    }

    .brand-mark svg {
      display: block;
      width: 100%;
      height: 100%;
    }

    .brand-mark--compact {
      width: 28px;
      height: 28px;
    }

    .site-brand {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--qaz-brand-ink);
      font-weight: 800;
      text-decoration: none;
    }

    .site-brand .brand-mark {
      color: var(--qaz-brand-teal);
    }

    .hero-band,
    .hero {
      position: relative;
      overflow: hidden;
      isolation: isolate;
    }

    .hero-band::before,
    .hero::before {
      content: "";
      position: absolute;
      inset: 0;
      z-index: 0;
      background-image: var(--qaz-brand-pattern);
      background-position: right 8% center;
      background-repeat: repeat;
      background-size: 190px;
      -webkit-mask-image: linear-gradient(
        90deg, transparent 0%, transparent 58%, black 74%, black 100%
      );
      mask-image: linear-gradient(
        90deg, transparent 0%, transparent 58%, black 74%, black 100%
      );
      opacity: 0.18;
      pointer-events: none;
    }

    .hero-band > *,
    .hero > * {
      position: relative;
      z-index: 1;
    }

    @media (max-width: 560px) {
      .brand-mark {
        width: 34px;
        height: 34px;
      }

      .hero-band::before,
      .hero::before {
        background-position: 130% center;
        background-size: 180px;
        -webkit-mask-image: linear-gradient(90deg, transparent 35%, black 84%);
        mask-image: linear-gradient(90deg, transparent 35%, black 84%);
        opacity: 0.14;
      }
    }
""".replace("BRAND_PATTERN_DATA_URI", BRAND_PATTERN_DATA_URI)
