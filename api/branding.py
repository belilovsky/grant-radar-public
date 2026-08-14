"""Approved QAZ.FUND visual assets and shared public-brand tokens."""

from __future__ import annotations

from pathlib import Path

BRANDING_ASSET_DIR = Path(__file__).with_name("static") / "branding"
BRANDING_ASSET_PREFIX = "/assets/branding"
BRAND_FAVICON_PATH = BRANDING_ASSET_DIR / "favicon.ico"

# These files are the original approved QAZ.FUND package: a clean sign without
# wordmark, its ivory counterpart, and the supplied ornamental backgrounds.
BRAND_MARK_IVORY_HTML = (
    f'<img src="{BRANDING_ASSET_PREFIX}/qaz-fund-symbol-ivory.svg" '
    'alt="" decoding="async">'
)
BRAND_MARK_TEAL_HTML = (
    f'<img src="{BRANDING_ASSET_PREFIX}/qaz-fund-symbol.svg" '
    'alt="" decoding="async">'
)

BRAND_CSS = r"""
    :root {
      --qaz-brand-deep: #002D34;
      --qaz-brand-hero-start: #00343B;
      --qaz-brand-hero-end: #00464D;
      --qaz-brand-ink: #00343B;
      --qaz-brand-teal: #00545B;
      --qaz-brand-teal-hover: #00464D;
      --qaz-brand-teal-light: #08747B;
      --qaz-brand-cream: #F3EFE9;
      --qaz-brand-paper: #FFFDFC;
      --qaz-brand-gold: #F0C64D;
      --qaz-brand-gold-soft: #FFF2A8;
      --qaz-brand-gold-deep: #D59A17;
      --qaz-brand-hero-art: url("/assets/branding/qaz-fund-ornamental-background-1920x1080.webp");
      --qaz-brand-pattern: url("/assets/branding/qaz-fund-pattern-tile.svg");
    }

    .brand-mark {
      display: inline-grid;
      flex: 0 0 auto;
      place-items: center;
      width: 42px;
      height: 42px;
    }

    .brand-mark img {
      display: block;
      width: 100%;
      height: 100%;
      object-fit: contain;
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
      background-color: var(--qaz-brand-hero-start);
      background-image: var(--qaz-brand-hero-art);
      background-position: center;
      background-repeat: no-repeat;
      background-size: cover;
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
        background-image: var(--qaz-brand-hero-art);
        background-position: center;
        background-size: cover;
        opacity: 1;
      }
    }
"""
