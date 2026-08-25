"""Human page for official Kazakhstan verification routes."""

from __future__ import annotations

from html import escape
from typing import cast

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.public_meta import analytics_head_html, og_image_url
from core.kazakhstan_data_routes import data_routes, data_routes_page_copy
from core.localization import normalize_content_lang

ROUTE_PAGE_CSS = """
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--av-font-sans);
  line-height: 1.5;
}
a { color: inherit; }
.shell {
  width: min(1280px, calc(100% - 48px));
  margin: 0 auto;
  padding: 20px 0 44px;
}
.topbar,
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.back {
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: 750;
  text-decoration: none;
}
.langs { display: flex; gap: 4px; }
.langs a {
  padding: 7px 10px;
  border-bottom: 2px solid transparent;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
}
.langs a.active {
  color: var(--color-text);
  border-color: var(--color-accent);
}
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(280px, .55fr);
  gap: 18px;
  margin-top: 18px;
}
.hero-copy,
.boundary {
  border: 1px solid var(--color-border);
  border-radius: var(--av-radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}
.hero-copy {
  padding: clamp(24px, 4vw, 48px);
  background: color-mix(
    in oklab,
    var(--color-surface),
    var(--color-accent-subtle) 28%
  );
}
.boundary {
  display: grid;
  align-content: center;
  gap: 10px;
  padding: 24px;
}
.eyebrow {
  color: var(--color-accent);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .07em;
  text-transform: uppercase;
}
h1 {
  max-width: 17ch;
  margin: 10px 0 14px;
  font-size: clamp(32px, 4.4vw, 58px);
  line-height: 1.02;
  letter-spacing: -.035em;
}
.hero p,
.boundary p {
  margin: 0;
  color: var(--color-text-muted);
}
.boundary h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
}
.route-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}
.route-card {
  display: grid;
  min-width: 0;
  min-height: 306px;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--av-radius-lg);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-xs);
}
.route-card > *,
.route-card-head > *,
.route-meta,
.route-meta div {
  min-width: 0;
}
.route-card:hover {
  border-color: color-mix(
    in oklab,
    var(--color-accent),
    var(--color-border) 56%
  );
  box-shadow: var(--shadow-md);
}
.route-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.route-card h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.18;
}
.coverage {
  flex: 0 0 auto;
  max-width: 13ch;
  padding: 5px 8px;
  border-radius: 999px;
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-size: 11px;
  font-weight: 800;
  line-height: 1.15;
  text-align: center;
}
.coverage.is-partial {
  background: color-mix(in oklab, var(--color-warning, #ae6b12), transparent 87%);
  color: var(--color-warning, #8f5912);
}
.purpose {
  margin: 12px 0 0;
  color: var(--color-text-muted);
  font-size: 14px;
}
.route-meta {
  display: grid;
  gap: 11px;
  margin: 18px 0;
}
.route-meta div { display: grid; gap: 3px; }
.route-meta dt {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.route-meta dd {
  margin: 0;
  font-size: 13px;
  overflow-wrap: anywhere;
}
.roles {
  color: var(--color-text-muted);
  font-size: 12px;
  overflow-wrap: anywhere;
}
.route-link {
  display: inline-flex;
  align-items: center;
  align-self: end;
  justify-content: space-between;
  gap: 10px;
  min-height: 44px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--color-text);
  color: var(--color-bg);
  font-size: 13px;
  font-weight: 800;
  text-decoration: none;
  overflow-wrap: anywhere;
}
.route-link:hover { background: var(--color-accent); }
.footer {
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 13px;
}
.footer p { max-width: 76ch; margin: 0; }
.footer nav { display: flex; gap: 12px; flex-wrap: wrap; }
.footer a { font-weight: 750; }
@media (min-width: 1440px) {
  .shell {
    width: min(1600px, calc(100% - 96px));
    padding-top: 28px;
  }
  .hero {
    grid-template-columns: minmax(560px, 1.5fr) minmax(360px, .5fr);
    gap: 22px;
  }
  .route-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
  }
  .route-card { min-height: 330px; padding: 22px; }
}
@media (min-width: 2200px) {
  .shell { width: min(2080px, calc(100% - 160px)); }
  .route-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 20px;
  }
  .route-card { min-height: 340px; padding: 26px; }
}
@media (max-width: 980px) {
  .hero { grid-template-columns: 1fr; }
  .route-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .shell {
    width: min(100% - 24px, 680px);
    padding-top: 12px;
  }
  .hero-copy,
  .boundary { padding: 20px; }
  .route-grid { grid-template-columns: 1fr; }
  .route-card { min-height: 0; }
  .route-card-head { flex-wrap: wrap; }
  .coverage { max-width: 100%; }
}
@media (max-width: 820px) {
  .back,
  .langs a,
  .footer a {
    display: inline-flex;
    align-items: center;
    min-height: 44px;
  }
  .langs a {
    justify-content: center;
    min-width: 44px;
  }
}
"""


def _path(base: str, route: str, lang: str) -> str:
    return f"{base}/{route}?lang={lang}" if base else f"/{route}?lang={lang}"


def _language_nav(*, active_lang: str, kk_href: str, ru_href: str, en_href: str) -> str:
    links = (("kk", "KAZ", kk_href), ("ru", "RU", ru_href), ("en", "EN", en_href))
    rows = []
    for code, label, href in links:
        active = "active" if active_lang == code else ""
        current = ' aria-current="page"' if active_lang == code else ""
        rows.append(
            f'<a class="{active}" href="{escape(href, quote=True)}" '
            f'lang="{code}"{current}>{label}</a>'
        )
    return "".join(rows)


def render_data_routes_page(
    *,
    lang: str,
    root_path: str,
    site_origin: str,
) -> str:
    """Render a responsive, source-first route directory."""

    active_lang = normalize_content_lang(lang)
    copy = data_routes_page_copy(active_lang)
    base = root_path.rstrip("/")
    home = (
        f"{base}/?lang={active_lang}#opportunities"
        if base
        else f"/?lang={active_lang}#opportunities"
    )
    status = _path(base, "status", active_lang)
    policy = _path(base, "data-policy", active_lang)
    canonical_path = _path(base, "data-routes", active_lang)
    canonical = (
        f"{site_origin.rstrip('/')}{canonical_path}" if site_origin else canonical_path
    )
    role_labels = copy.get("role_labels")
    cards = "".join(
        _route_card(route, copy=copy, role_labels=role_labels)
        for route in data_routes(active_lang)
    )
    ru_href = _path(base, "data-routes", "ru")
    kk_href = _path(base, "data-routes", "kk")
    en_href = _path(base, "data-routes", "en")
    nav = _language_nav(
        active_lang=active_lang,
        kk_href=kk_href,
        ru_href=ru_href,
        en_href=en_href,
    )
    origin = site_origin.rstrip("/") if site_origin else ""
    title = escape(str(copy.get("title") or "QAZ.FUND"))
    description = escape(str(copy.get("description") or ""), quote=True)
    style = f"{AVDS_CSS}\n{ROUTE_PAGE_CSS}"

    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <link rel="alternate" hreflang="kk" href="{escape(origin + kk_href, quote=True)}">
  <link rel="alternate" hreflang="ru" href="{escape(origin + ru_href, quote=True)}">
  <link rel="alternate" hreflang="en" href="{escape(origin + en_href, quote=True)}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{escape(og_image_url(site_origin, root_path), quote=True)}">
  {analytics_head_html()}{AVDS_FONT_HEAD}
  <style>{style}</style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <a class="back" href="{escape(home, quote=True)}">← {escape(str(copy.get("back") or ""))}</a>
      <nav class="langs" aria-label="Language">{nav}</nav>
    </div>
    <section class="hero" data-avds-component="data-routes-hero">
      <div class="hero-copy">
        <span class="eyebrow">{escape(str(copy.get("eyebrow") or ""))}</span>
        <h1>{escape(str(copy.get("heading") or ""))}</h1>
        <p>{escape(str(copy.get("intro") or ""))}</p>
      </div>
      <aside class="boundary" data-avds-component="source-boundary">
        <span class="eyebrow">QAZ.FUND</span>
        <h2>{escape(str(copy.get("boundary_title") or ""))}</h2>
        <p>{escape(str(copy.get("boundary_text") or ""))}</p>
      </aside>
    </section>
    <section class="route-grid" aria-label="{escape(str(copy.get("eyebrow") or ""), quote=True)}">
      {cards}
    </section>
    <footer class="footer">
      <a class="footer-contact" href="mailto:contact@qaz.fund">contact@qaz.fund</a>
      <p>{escape(str(copy.get("footer") or ""))}</p>
      <nav>
        <a href="{escape(status, quote=True)}">{escape(str(copy.get("status") or ""))}</a>
        <a href="{escape(policy, quote=True)}">{escape(str(copy.get("policy") or ""))}</a>
      </nav>
    </footer>
  </main>
</body>
</html>"""


def _route_card(
    route: dict[str, object],
    *,
    copy: dict[str, object],
    role_labels: object,
) -> str:
    labels = (
        cast(dict[object, object], role_labels) if isinstance(role_labels, dict) else {}
    )
    raw_roles = route.get("roles")
    roles = cast(list[object], raw_roles) if isinstance(raw_roles, list) else []
    role_text = ", ".join(
        str(labels.get(role, role)) for role in roles if str(role).strip()
    )
    coverage = str(route.get("coverage") or "not_indexed")
    coverage_label = str(copy.get(coverage, coverage))
    coverage_class = " is-partial" if coverage == "partial" else ""
    route_id = escape(str(route.get("id") or ""), quote=True)
    title = escape(str(route.get("title") or ""))
    purpose = escape(str(route.get("purpose") or ""))
    use = escape(str(route.get("use") or ""))
    access = escape(str(route.get("access") or ""))
    url = escape(str(route.get("url") or ""), quote=True)
    link_label = escape(str(route.get("link_label") or ""))
    what_to_check = escape(str(copy.get("what_to_check") or ""))
    access_label = escape(str(copy.get("access") or ""))
    role_prefix = escape(str(copy.get("role_prefix") or ""))

    return f"""
      <article
        class="route-card"
        data-avds-component="data-route-card"
        data-route="{route_id}"
      >
        <div>
          <div class="route-card-head">
            <h2>{title}</h2>
            <span class="coverage{coverage_class}">{escape(coverage_label)}</span>
          </div>
          <p class="purpose">{purpose}</p>
          <dl class="route-meta">
            <div><dt>{what_to_check}</dt><dd>{use}</dd></div>
            <div><dt>{access_label}</dt><dd>{access}</dd></div>
          </dl>
          <p class="roles"><strong>{role_prefix}:</strong> {escape(role_text)}</p>
        </div>
        <a class="route-link" href="{url}" target="_blank" rel="noopener">
          {link_label}<span aria-hidden="true">↗</span>
        </a>
      </article>"""
