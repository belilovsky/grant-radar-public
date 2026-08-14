"""Approved QAZ.FUND visual assets and shared public-brand tokens."""

from __future__ import annotations

from pathlib import Path

BRANDING_ASSET_DIR = Path(__file__).with_name("static") / "branding"
BRANDING_ASSET_PREFIX = "/assets/branding"
BRAND_FAVICON_PATH = BRANDING_ASSET_DIR / "favicon.ico"

# The public interface uses the supplied sign and its ivory counterpart. The
# ornamental artwork remains an asset, but is deliberately not used as a page
# background: it competes with the interface and reduces text contrast.
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
      --qaz-brand-gold: #B9DDD8;
      --qaz-brand-gold-soft: #E6F2F0;
      --qaz-brand-gold-deep: #4A7975;
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
      background:
        radial-gradient(circle at 92% 6%, rgb(137 206 196 / 0.18), transparent 32%),
        linear-gradient(135deg, var(--qaz-brand-hero-start), var(--qaz-brand-hero-end));
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
      .hero::before { opacity: 1; }
    }
"""
