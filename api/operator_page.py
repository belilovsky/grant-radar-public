"""Token-gated operator workbench shell for QAZ.FUND."""

from __future__ import annotations

import json
from html import escape

from api.avds import AVDS_CSS, AVDS_FONT_HEAD

COPY = {
    "ru": {
        "title": "Операторский контроль – QAZ.FUND",
        "brand_context": "Операторский контур",
        "eyebrow": "Состояние конвейера",
        "heading": "Контроль источников",
        "intro": "Техническое состояние сборщиков и последние запуски.",
        "token": "Операторский токен",
        "connect": "Подключиться",
        "disconnect": "Выйти",
        "back": "Каталог",
        "hint": "Токен хранится только в текущей вкладке и не попадает в URL.",
        "loading": "Загружаем состояние...",
        "unauthorized": "Токен не принят или операторский доступ не настроен.",
        "error": "Не удалось загрузить операторские данные.",
        "catalog": "Записей",
        "relevant": "Актуально",
        "sources": "Источники",
        "fresh": "Свежие",
        "stale": "Требуют внимания",
        "failed": "Ошибки запусков",
        "recent": "Последние запуски",
        "source": "Источник",
        "status": "Статус",
        "started": "Начало",
        "seen": "Получено",
        "new": "Новых",
        "message": "Сообщение",
        "empty": "Записей нет.",
    },
    "en": {
        "title": "Operator control – QAZ.FUND",
        "brand_context": "Operator workspace",
        "eyebrow": "Pipeline status",
        "heading": "Source control",
        "intro": "Collector health and recent pipeline runs.",
        "token": "Operator token",
        "connect": "Connect",
        "disconnect": "Sign out",
        "back": "Catalog",
        "hint": "The token stays in this browser tab and is never placed in the URL.",
        "loading": "Loading status...",
        "unauthorized": "The token was rejected or operator access is not configured.",
        "error": "Operator data could not be loaded.",
        "catalog": "Records",
        "relevant": "Current",
        "sources": "Sources",
        "fresh": "Fresh",
        "stale": "Needs attention",
        "failed": "Failed runs",
        "recent": "Recent runs",
        "source": "Source",
        "status": "Status",
        "started": "Started",
        "seen": "Seen",
        "new": "New",
        "message": "Message",
        "empty": "No records.",
    },
}


def render_operator_page(*, lang: str, root_path: str = "") -> str:
    active_lang = lang if lang in COPY else "ru"
    copy = COPY[active_lang]
    base = root_path.rstrip("/")
    catalog_href = f"{base}/?lang={active_lang}" if base else f"/?lang={active_lang}"
    ru_href = f"{base}/operator?lang=ru" if base else "/operator?lang=ru"
    en_href = f"{base}/operator?lang=en" if base else "/operator?lang=en"
    health_path = f"{base}/operator/health" if base else "/operator/health"
    copy_json = json.dumps(copy, ensure_ascii=False)
    endpoint_json = json.dumps(health_path, ensure_ascii=False)
    ru_current = ' aria-current="page"' if active_lang == "ru" else ""
    en_current = ' aria-current="page"' if active_lang == "en" else ""
    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{escape(str(copy["title"]))}</title>
  {AVDS_FONT_HEAD}
  <style>
    {AVDS_CSS}
    :root {{ --ink:var(--color-text); --muted:var(--color-text-muted);
      --line:var(--color-border); --line-subtle:var(--color-border-subtle);
      --panel:var(--color-surface); --wash:var(--color-bg); --brand:var(--color-accent);
      --brand-soft:var(--color-accent-subtle); --good:var(--color-success);
      --warn:var(--color-warning); --bad:var(--color-danger); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--wash); color:var(--ink);
      font-family:var(--av-font-sans); font-size:var(--av-text-base); }}
    button,input {{ font:inherit; }}
    .visually-hidden {{ position:absolute; width:1px; height:1px; padding:0;
      margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap;
      border:0; }}
    main {{ width:min(var(--av-container-dashboard),calc(100% - 32px)); margin:auto;
      padding:16px 0 40px; }}
    .operator-topbar {{ display:flex; align-items:center; justify-content:space-between;
      gap:16px; margin-bottom:18px; }}
    .operator-brand {{ display:inline-flex; align-items:baseline; gap:10px; color:var(--ink);
      font-size:17px; font-weight:800; letter-spacing:0; }}
    .operator-brand span {{ color:var(--muted); font-size:12px; font-weight:650; }}
    .operator-tools {{ display:flex; align-items:center; gap:14px; }}
    .lang-switch {{ display:inline-flex; align-items:center; gap:4px; }}
    .lang-switch a {{ min-width:34px; padding:6px 8px; border-bottom:2px solid transparent;
      color:var(--muted); text-align:center; font-size:12px; }}
    .lang-switch a[aria-current="page"] {{ border-bottom-color:var(--brand); color:var(--ink); }}
    .catalog-link {{ min-height:32px; display:inline-flex; align-items:center; }}
    .intro-grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(360px,520px);
      gap:28px; align-items:center; padding:24px 0; border-top:1px solid var(--line);
      border-bottom:1px solid var(--line); }}
    .eyebrow {{ display:block; margin-bottom:6px; color:var(--brand); font-size:12px;
      font-weight:700; }}
    h1 {{ max-width:18ch; margin:0 0 6px; font-size:clamp(27px,3vw,36px); line-height:1.05; }}
    p {{ margin:0; color:var(--muted); line-height:1.5; }}
    a {{ color:var(--brand); font-weight:700; text-decoration:none; }}
    .auth,.panel {{ padding:14px; border:1px solid var(--line); border-radius:var(--av-radius-md);
      background:var(--panel); }}
    .auth form {{ display:grid; gap:7px; }}
    .auth label {{ color:var(--muted); font-size:12px; font-weight:700; }}
    .auth-controls {{ display:grid; grid-template-columns:1fr auto; gap:10px; }}
    input {{ min-height:var(--av-control-height-md); padding:0 12px; border:1px solid var(--line);
      border-radius:var(--av-radius-md); color:var(--ink); }}
    button {{ min-height:var(--av-control-height-md); padding:0 16px; border:0;
      border-radius:var(--av-radius-md);
      background:var(--brand); color:#fff; font-weight:700; cursor:pointer; }}
    button.secondary {{ background:var(--brand-soft); color:var(--brand); }}
    .hint {{ margin-top:9px; font-size:12px; }}
    .message {{ min-height:20px; margin:10px 0 0; color:var(--muted); }}
    .message.bad {{ color:var(--bad); }}
    .dashboard[hidden],.auth[hidden] {{ display:none; }}
    .dashboard {{ padding-top:14px; }}
    .dashboard-toolbar {{ display:flex; align-items:center; justify-content:space-between;
      gap:12px; }}
    .dashboard-toolbar .message {{ margin:0; }}
    .metrics {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr));
      gap:0; margin:12px 0; border:1px solid var(--line); border-radius:var(--av-radius-md);
      background:var(--panel); }}
    .metric {{ padding:10px 12px; border:0; border-left:1px solid var(--line-subtle);
      background:transparent; }}
    .metric:first-child {{ border-left:0; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; }}
    .metric strong {{ display:block; margin-top:3px; font-size:22px; }}
    .grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,2fr);
      gap:14px; }}
    h2 {{ margin:0 0 12px; font-size:18px; }}
    .list {{ display:grid; gap:8px; }}
    .list-row {{ padding:10px 0; border-bottom:1px solid var(--line); }}
    .list-row:last-child {{ border:0; }}
    .list-row strong,.list-row span {{ display:block; }}
    .list-row span {{ margin-top:3px; color:var(--muted); font-size:12px; }}
    .table-wrap {{ overflow:auto; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ padding:10px; border-bottom:1px solid var(--line); text-align:left;
      font-size:13px; }}
    th {{ color:var(--muted); font-size:11px; }}
    .status-ok {{ color:var(--good); }}
    .status-error {{ color:var(--bad); }}
    .status-running {{ color:var(--warn); }}
    @media(max-width:760px) {{
      main {{ width:min(100% - 20px,var(--av-container-dashboard)); padding-top:10px; }}
      .operator-topbar {{ align-items:flex-start; }}
      .operator-brand {{ display:grid; gap:2px; }}
      .operator-tools {{ gap:6px; }}
      .catalog-link {{ font-size:0; }}
      .catalog-link::before {{ content:"←"; font-size:18px; }}
      .intro-grid,.grid {{ grid-template-columns:1fr; gap:16px; padding:18px 0; }}
      .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
      .auth-controls {{ grid-template-columns:1fr; }}
      .dashboard-toolbar {{ align-items:flex-start; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div class="operator-topbar">
        <a class="operator-brand" href="{escape(catalog_href, quote=True)}">
          QAZ.FUND <span>{escape(str(copy["brand_context"]))}</span>
        </a>
        <div class="operator-tools">
          <nav class="lang-switch" aria-label="Language">
            <a href="{escape(ru_href, quote=True)}" lang="ru"{ru_current}>RU</a>
            <a href="{escape(en_href, quote=True)}" lang="en"{en_current}>EN</a>
          </nav>
          <a class="catalog-link" href="{escape(catalog_href, quote=True)}">
            {escape(str(copy["back"]))}
          </a>
        </div>
      </div>
      <div class="intro-grid">
        <div>
          <span class="eyebrow">{escape(str(copy["eyebrow"]))}</span>
          <h1>{escape(str(copy["heading"]))}</h1>
          <p>{escape(str(copy["intro"]))}</p>
        </div>
        <section class="auth" id="auth">
          <form id="auth-form">
            <input class="visually-hidden" type="text" name="username"
              value="operator" autocomplete="username" tabindex="-1" aria-hidden="true">
            <label for="token">{escape(str(copy["token"]))}</label>
            <div class="auth-controls">
              <input id="token" type="password" autocomplete="current-password"
                placeholder="{escape(str(copy["token"]), quote=True)}" required>
              <button type="submit">{escape(str(copy["connect"]))}</button>
            </div>
          </form>
          <p class="hint">{escape(str(copy["hint"]))}</p>
          <p class="message" id="auth-message" aria-live="polite"></p>
        </section>
      </div>
    </header>
    <section class="dashboard" id="dashboard" hidden>
      <div class="dashboard-toolbar">
        <p class="message" id="message" aria-live="polite">{escape(str(copy["loading"]))}</p>
        <button class="secondary" type="button" id="disconnect">
          {escape(str(copy["disconnect"]))}
        </button>
      </div>
      <div class="metrics" id="metrics"></div>
      <div class="grid">
        <section class="panel">
          <h2>{escape(str(copy["stale"]))}</h2><div class="list" id="stale-list"></div>
        </section>
        <section class="panel"><h2>{escape(str(copy["recent"]))}</h2>
          <div class="table-wrap"><table><thead><tr>
            <th>{escape(str(copy["source"]))}</th><th>{escape(str(copy["status"]))}</th>
            <th>{escape(str(copy["started"]))}</th><th>{escape(str(copy["seen"]))}</th>
            <th>{escape(str(copy["new"]))}</th><th>{escape(str(copy["message"]))}</th>
          </tr></thead><tbody id="runs"></tbody></table></div>
        </section>
      </div>
    </section>
  </main>
  <script>
    const copy = {copy_json};
    const endpoint = {endpoint_json};
    const storageKey = "qazfundOperatorToken.v1";
    const escapeHtml = (value) => String(value ?? "").replace(
      /[&<>"']/g,
      (char) => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[char])
    );
    const locales = {{"ru": "ru-RU", "en": "en-GB"}};
    const formatDate = (value) => value
      ? new Date(value).toLocaleString(locales[document.documentElement.lang] || "ru-RU")
      : "–";
    function metric(label, value) {{
      return `<div class="metric"><span>${{escapeHtml(label)}}</span>`
        + `<strong>${{escapeHtml(value)}}</strong></div>`;
    }}
    function signOut() {{
      sessionStorage.removeItem(storageKey);
      document.querySelector("#dashboard").hidden=true;
      document.querySelector("#auth").hidden=false;
      document.querySelector("#token").value="";
    }}
    function render(data) {{
      document.querySelector("#metrics").innerHTML = [
        metric(copy.catalog,data.catalog_items),
        metric(copy.relevant,data.relevant_open_items),
        metric(copy.sources,data.enabled_sources),
        metric(copy.fresh,data.fresh_sources),
        metric(copy.failed,(data.failed_runs||[]).length)
      ].join("");
      const stale = data.stale_sources || [];
      document.querySelector("#stale-list").innerHTML = stale.length
        ? stale.map((row)=>`<div class="list-row">`
          + `<strong>${{escapeHtml(row.name||row.slug)}}</strong>`
          + `<span>${{escapeHtml(formatDate(row.last_discovered_at))}}</span></div>`).join("")
        : `<p>${{escapeHtml(copy.empty)}}</p>`;
      const runs = data.recent_runs || [];
      document.querySelector("#runs").innerHTML = runs.length
        ? runs.map((row)=>`<tr><td>${{escapeHtml(row.source)}}</td>`
          + `<td class="status-${{escapeHtml(row.status)}}">${{escapeHtml(row.status)}}</td>`
          + `<td>${{escapeHtml(formatDate(row.started_at))}}</td>`
          + `<td>${{escapeHtml(row.items_seen)}}</td><td>${{escapeHtml(row.items_new)}}</td>`
          + `<td>${{escapeHtml(row.error)}}</td></tr>`).join("")
        : `<tr><td colspan="6">${{escapeHtml(copy.empty)}}</td></tr>`;
      document.querySelector("#message").textContent = data.status === "ok"
        ? "OK" : copy.stale;
    }}
    async function connect(token) {{
      document.querySelector("#auth-message").textContent = copy.loading;
      try {{
        const response = await fetch(endpoint, {{
          headers: {{"X-Grant-Radar-Admin-Token": token}}, cache:"no-store"
        }});
        if (!response.ok) {{
          throw new Error(response.status === 401 || response.status === 404
            ? "unauthorized" : "request");
        }}
        const data = await response.json();
        sessionStorage.setItem(storageKey, token);
        render(data);
        document.querySelector("#auth").hidden=true;
        document.querySelector("#dashboard").hidden=false;
      }} catch (error) {{
        document.querySelector("#auth-message").textContent = error.message === "unauthorized"
          ? copy.unauthorized : copy.error;
        document.querySelector("#auth-message").className="message bad";
      }}
    }}
    document.querySelector("#auth-form").addEventListener("submit",(event)=>{{
      event.preventDefault();
      connect(document.querySelector("#token").value.trim());
    }});
    document.querySelector("#disconnect").addEventListener("click",signOut);
    const stored=sessionStorage.getItem(storageKey); if(stored) connect(stored);
  </script>
</body>
</html>"""
