"""Static dashboard CSS extracted from the server-rendered shell."""

from __future__ import annotations

DASHBOARD_CSS = r"""    :root {
      color-scheme: light;
      --bg: var(--color-bg);
      --panel: var(--color-surface);
      --panel-subtle: var(--color-bg-subtle);
      --panel-strong: color-mix(in oklab, var(--panel), var(--brand-soft) 16%);
      --panel-wash: color-mix(in oklab, var(--panel), var(--panel-subtle) 44%);
      --accent-wash: color-mix(in oklab, var(--panel), var(--brand-soft) 26%);
      --ink: var(--color-text);
      --muted: var(--color-text-muted);
      --line: var(--color-border);
      --line-strong: var(--color-border-strong);
      --line-subtle: var(--color-border-subtle);
      --brand: var(--color-accent);
      --brand-hover: var(--color-accent-hover);
      --brand-soft: var(--color-accent-subtle);
      --good: var(--color-success);
      --good-soft: var(--color-success-subtle);
      --warn: var(--color-warning);
      --warn-soft: var(--color-warning-subtle);
      --danger: var(--color-danger);
      --danger-soft: var(--color-danger-subtle);
      --surface-raised: var(--color-surface-raised);
      --focus-ring: var(--color-focus-ring);
      --container-max: var(--av-container-dashboard);
      --control-height: var(--av-control-height-md);
      --control-height-sm: var(--av-control-height-sm);
      --card-padding: var(--av-card-padding-md);
      --compact-card-padding: var(--av-card-padding-sm);
      --section-gap: var(--av-section-gap);
    }

    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: var(--av-font-sans);
      font-size: var(--av-text-base);
      line-height: var(--av-leading-normal);
      background: var(--bg);
      color: var(--ink);
    }
    body.modal-open,
    body.filter-sheet-open {
      overflow: hidden;
    }
    a { color: inherit; }
    button, input, select { font: inherit; }
    input, select { min-width: 0; }
    .mobile-app-bar,
    .mobile-app-nav,
    .mobile-filter-sheet-actions,
    .mobile-filter-backdrop {
      display: none;
    }
    .shell {
      width: min(var(--container-max), calc(100% - 48px));
      margin: 0 auto;
      padding: 22px 0 var(--av-spacing-8);
    }
    .hero-band {
      position: relative;
      overflow: hidden;
      padding: 20px 0 0;
      margin-bottom: 16px;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
      isolation: isolate;
    }
    .hero-band::before {
      content: none;
    }
    .hero-band::after {
      content: none;
    }
    .sticky-shell {
      position: sticky;
      top: 0;
      z-index: 24;
      padding: 0;
      margin-bottom: 10px;
      background: color-mix(in oklab, var(--bg), transparent 5%);
      backdrop-filter: blur(14px);
    }
    .sticky-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-3);
      min-height: 52px;
      padding: 7px 0;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
      backdrop-filter: none;
    }
    .topbar {
      display: grid;
      gap: var(--av-spacing-1);
      margin-bottom: var(--av-spacing-2);
    }
    .brand {
      min-width: 0;
      display: grid;
      gap: var(--av-spacing-1);
    }
    .eyebrow {
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-family: var(--font-sans);
      font-weight: 650;
      letter-spacing: 0;
      text-transform: none;
    }
    .brand-row {
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .brand h1 {
      margin: 0;
      font-size: 42px;
      line-height: 1.05;
      letter-spacing: 0;
    }
    .brand p {
      display: none;
      margin: 0;
      max-width: 760px;
      color: color-mix(in oklab, var(--ink), white 28%);
      font-size: var(--av-text-base);
      line-height: 1.5;
    }
    .focus-row {
      display: none;
      flex-wrap: wrap;
      gap: var(--av-spacing-2);
      align-items: flex-start;
    }
    .focus-chip {
      display: inline-flex;
      align-items: center;
      width: fit-content;
      max-width: 100%;
      min-height: 28px;
      padding: 1px 10px;
      border: 1px solid color-mix(in oklab, var(--brand), white 64%);
      border-radius: var(--av-radius-full);
      background: rgb(255 255 255 / 0.72);
      color: color-mix(in oklab, var(--brand), var(--ink) 18%);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      overflow-wrap: anywhere;
    }
    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(390px, 0.6fr);
      gap: 48px;
      align-items: start;
      margin-bottom: var(--av-spacing-3);
    }
    .hero-copy {
      display: grid;
      gap: var(--av-spacing-3);
      align-content: start;
      min-width: 0;
      padding: var(--av-spacing-2) 0 0;
    }
    .hero-intro {
      margin: 0;
      max-width: 64ch;
      color: color-mix(in oklab, var(--ink), white 20%);
      font-size: 15px;
      line-height: 1.6;
    }
    .hero-actions {
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .button.primary {
      border-color: transparent;
      background: var(--brand);
      color: var(--color-accent-contrast);
      box-shadow: 0 10px 20px rgb(37 99 235 / 0.18);
    }
    .button.primary:hover {
      background: var(--brand-hover);
      border-color: transparent;
      color: var(--color-accent-contrast);
    }
    .button.soft {
      border-color: color-mix(in oklab, var(--brand), white 52%);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 36%);
      color: var(--brand);
    }
    .button.soft:hover {
      border-color: color-mix(in oklab, var(--brand), white 34%);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 56%);
      color: var(--brand-hover);
    }
    .button.subtle {
      border-color: var(--line);
      background: rgb(255 255 255 / 0.5);
      color: var(--ink);
    }
    .button.subtle:hover {
      background: rgb(255 255 255 / 0.8);
    }
    .hero-stage {
      display: grid;
      gap: var(--av-spacing-3);
      min-width: 0;
      align-content: start;
      padding: 4px 0 4px 28px;
      border: 0;
      border-left: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }
    .hero-stage-eyebrow {
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 650;
      letter-spacing: 0;
      text-transform: none;
    }
    .hero-stage-title {
      margin: 0;
      font-family: var(--font-sans);
      font-size: 18px;
      font-weight: 700;
      line-height: var(--av-leading-tight);
      letter-spacing: 0;
    }
    .hero-points {
      display: none;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-2);
    }
    .hero-point {
      display: grid;
      grid-template-columns: 24px minmax(0, 1fr);
      gap: var(--av-spacing-1);
      align-items: start;
      color: color-mix(in oklab, var(--ink), white 22%);
      font-size: var(--av-text-xs);
      line-height: 1.45;
    }
    .hero-point-index {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: var(--av-radius-md);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 58%);
      color: var(--brand);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--brand), white 52%);
    }
    .hero-picks {
      display: grid;
      gap: 6px;
      min-width: 0;
    }
    .hero-pick-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-1);
    }
    .hero-pick {
      min-height: 28px;
      padding-inline: 8px;
      border-radius: var(--av-radius-md);
      border: 1px solid var(--line-subtle);
      background: transparent;
      color: var(--ink);
      font-size: var(--av-text-xs);
      font-weight: 700;
      text-align: left;
      justify-content: flex-start;
    }
    .hero-pick:last-child {
      grid-column: auto;
    }
    .hero-pick:hover,
    .hero-pick:focus-visible {
      border-color: color-mix(in oklab, var(--brand), white 36%);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 36%);
      color: var(--brand);
    }
    .hero-band .grid {
      width: 100%;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-bottom: 0;
      border: 0;
      border-top: 1px solid var(--line-subtle);
      background: transparent;
      box-shadow: none;
      backdrop-filter: none;
      border-radius: 0;
    }
    .hero-band .metric {
      min-height: 72px;
      padding: 14px 18px;
      border-top: 0;
    }
    .hero-band .metric span {
      color: color-mix(in oklab, var(--muted), var(--ink) 22%);
    }
    .spotlight-section {
      display: grid;
      gap: var(--av-spacing-2);
      margin-bottom: var(--av-spacing-3);
    }
    .funder-section {
      display: grid;
      gap: var(--av-spacing-2);
      margin-bottom: var(--av-spacing-3);
    }
    .spotlight-copy {
      display: grid;
      gap: 4px;
      max-width: 760px;
    }
    .spotlight-copy h2 {
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(17px, 1.75vw, 20px);
      font-weight: 700;
      line-height: var(--av-leading-tight);
      letter-spacing: 0;
    }
    .spotlight-copy p {
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 28%);
      font-size: var(--av-text-xs);
      line-height: 1.45;
    }
    .spotlight-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: var(--av-spacing-2);
    }
    .spotlight-card {
      display: grid;
      gap: var(--av-spacing-2);
      min-height: 0;
      padding: 12px;
      border: 1px solid var(--line);
      border-top: 2px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      box-shadow: var(--shadow-xs);
    }
    .spotlight-card[data-tone="brand"] {
      border-top-color: var(--brand);
    }
    .spotlight-card[data-tone="good"] {
      border-top-color: var(--good);
    }
    .spotlight-card[data-tone="amber"] {
      border-top-color: var(--warn);
    }
    .spotlight-card[data-tone="neutral"] {
      border-top-color: var(--line-strong);
    }
    .spotlight-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
    }
    .spotlight-label {
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }
    .spotlight-count {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: auto;
      padding: 0;
      border-radius: 0;
      background: transparent;
      color: var(--ink);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
      box-shadow: none;
    }
    .spotlight-card h3 {
      margin: 0;
      font-size: 17px;
      line-height: 1.18;
      letter-spacing: 0;
    }
    .spotlight-note {
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 30%);
      font-size: var(--av-text-sm);
      line-height: 1.42;
    }
    .spotlight-list {
      display: grid;
      gap: 8px;
      min-width: 0;
    }
    .spotlight-item {
      display: grid;
      gap: 2px;
      padding: 6px 8px;
      border: 1px solid transparent;
      border-radius: var(--av-radius-sm);
      background: color-mix(in oklab, var(--panel), var(--panel-subtle) 30%);
      color: var(--ink);
      text-align: left;
      cursor: pointer;
    }
    .spotlight-item:hover strong,
    .spotlight-item:focus-visible strong {
      color: var(--brand);
    }
    .spotlight-item strong {
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
      overflow: hidden;
      font-size: var(--av-text-sm);
      line-height: 1.45;
      transition: color var(--av-duration-base) var(--av-easing-emphasized);
    }
    .spotlight-item span {
      color: var(--muted);
      font-size: var(--av-text-xs);
    }
    .spotlight-empty {
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }
    .spotlight-more {
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }
    .spotlight-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      margin-top: auto;
      flex-wrap: wrap;
    }
    .pathways-section {
      display: grid;
      gap: var(--av-spacing-2);
      margin: 0;
    }
    .themes-section {
      display: grid;
      gap: var(--av-spacing-2);
      margin: 0;
    }
    .discovery-grid {
      display: grid;
      grid-template-columns: minmax(280px, 0.78fr) minmax(0, 1.22fr);
      gap: var(--av-spacing-5);
      padding-top: var(--av-spacing-3);
    }
    .discovery-library,
    .trust-library {
      margin: var(--av-spacing-4) 0;
      padding: 0 12px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel-wash);
    }
    .discovery-library > summary,
    .trust-library > summary {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: var(--av-spacing-3);
      min-height: 52px;
      cursor: pointer;
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 700;
      list-style: none;
    }
    .discovery-library > summary::-webkit-details-marker,
    .trust-library > summary::-webkit-details-marker { display: none; }
    .discovery-library > summary::after,
    .trust-library > summary::after {
      content: "+";
      flex: 0 0 auto;
      color: var(--brand);
      font-size: 20px;
      font-weight: 500;
      line-height: 1;
    }
    .discovery-library[open] > summary::after,
    .trust-library[open] > summary::after { content: "−"; }
    .discovery-library > summary:focus-visible,
    .trust-library > summary:focus-visible {
      outline: 2px solid var(--focus-ring);
      outline-offset: -2px;
    }
    .discovery-library-description,
    .trust-library-description {
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 500;
      text-align: right;
    }
    .discovery-library-body,
    .trust-library-body {
      padding: 0 0 var(--av-spacing-4);
    }
    .trust-library-body {
      display: grid;
      gap: var(--av-spacing-4);
    }
    .trust-library-body > section {
      margin: 0;
    }
    .funder-library,
    .methodology-library {
      margin: 0;
      border: 0;
      border-top: 1px solid var(--line-subtle);
      background: transparent;
    }
    .funder-library > summary,
    .methodology-library > summary {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: var(--av-spacing-3);
      min-height: 48px;
      cursor: pointer;
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 700;
      list-style: none;
    }
    .funder-library > summary::-webkit-details-marker,
    .methodology-library > summary::-webkit-details-marker { display: none; }
    .funder-library > summary::after,
    .methodology-library > summary::after {
      content: "+";
      flex: 0 0 auto;
      color: var(--brand);
      font-size: 20px;
      font-weight: 500;
      line-height: 1;
    }
    .funder-library[open] > summary::after,
    .methodology-library[open] > summary::after { content: "−"; }
    .funder-library > summary:focus-visible,
    .methodology-library > summary:focus-visible {
      outline: 2px solid var(--focus-ring);
      outline-offset: -2px;
    }
    .funder-library-description,
    .methodology-library-description {
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 500;
      text-align: right;
    }
    .funder-library-body,
    .methodology-library-body {
      display: grid;
      gap: var(--av-spacing-3);
      padding: 0 0 var(--av-spacing-3);
    }
    .funder-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-2);
    }
    .funder-card {
      display: grid;
      gap: var(--av-spacing-1);
      min-height: 0;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      box-shadow: var(--shadow-xs);
    }
    .funder-card-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
    }
    .funder-card h3 {
      margin: 0;
      font-size: 17px;
      line-height: 1.2;
      letter-spacing: 0;
    }
    .funder-card p {
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 26%);
      font-size: var(--av-text-sm);
      line-height: 1.42;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .funder-kpi {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--av-radius-full);
      background: var(--brand-soft);
      color: var(--brand);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
    }
    .funder-meta {
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }
    .funder-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      margin-top: auto;
      flex-wrap: wrap;
    }
    .funder-actions .button {
      min-height: 34px;
    }
    .themes-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--av-spacing-1);
    }
    .theme-card {
      display: grid;
      gap: var(--av-spacing-2);
      min-height: 0;
      padding: 10px 12px;
      border: 1px solid var(--line-subtle);
      border-left: 2px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel-wash);
      box-shadow: none;
    }
    .theme-card[data-tone="brand"] {
      border-left-color: var(--brand);
    }
    .theme-card[data-tone="good"] {
      border-left-color: var(--good);
    }
    .theme-card[data-tone="amber"] {
      border-left-color: var(--warn);
    }
    .theme-card[data-tone="violet"] {
      border-left-color: var(--accent-violet);
    }
    .theme-card[data-tone="neutral"] {
      border-left-color: var(--line-strong);
    }
    .theme-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
    }
    .theme-label {
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }
    .theme-count {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: auto;
      padding: 0;
      border-radius: 0;
      background: transparent;
      color: var(--ink);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
      box-shadow: none;
    }
    .theme-card h3 {
      margin: 0;
      font-size: 15px;
      line-height: 1.24;
      letter-spacing: 0;
    }
    .theme-note {
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 30%);
      font-size: var(--av-text-xs);
      line-height: 1.42;
    }
    .theme-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      margin-top: auto;
      flex-wrap: wrap;
    }
    .topic-brief {
      display: grid;
      gap: 10px;
      margin-bottom: var(--av-spacing-2);
      padding: 12px 14px;
      border-inline-start: 3px solid color-mix(in oklab, var(--brand), white 20%);
      border-radius: var(--av-radius-md);
      background: var(--accent-wash);
    }
    .topic-brief.hidden {
      display: none;
    }
    .topic-brief-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .topic-brief-kicker {
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }
    .topic-brief-count {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--av-radius-full);
      background: rgb(255 255 255 / 0.78);
      color: var(--ink);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
      box-shadow: inset 0 0 0 1px var(--line-subtle);
    }
    .topic-brief h3 {
      margin: 0;
      font-size: clamp(17px, 1.7vw, 19px);
      line-height: 1.15;
      letter-spacing: 0;
    }
    .topic-brief-note {
      margin: 0;
      max-width: 720px;
      color: color-mix(in oklab, var(--muted), var(--ink) 28%);
      font-size: var(--av-text-xs);
      line-height: 1.45;
    }
    .topic-brief-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.3fr) minmax(220px, 0.9fr);
      gap: var(--av-spacing-2);
      align-items: start;
    }
    .topic-brief-group {
      display: grid;
      gap: 8px;
      min-width: 0;
    }
    .topic-brief-label {
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }
    .topic-brief-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .topic-brief-chip {
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 0 12px;
      border-radius: var(--av-radius-full);
      background: rgb(255 255 255 / 0.72);
      color: var(--ink);
      font-size: var(--av-text-xs);
      font-weight: 700;
      box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--line), var(--brand) 10%);
    }
    .topic-brief-audience {
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      line-height: 1.6;
    }
    .topic-brief-actions {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: var(--av-spacing-2);
    }
    .pathways-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: var(--av-spacing-1);
    }
    .pathway-card {
      display: grid;
      gap: var(--av-spacing-2);
      min-height: 0;
      padding: 10px 12px;
      border: 1px solid var(--line-subtle);
      border-left: 2px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel-wash);
      box-shadow: none;
    }
    .pathway-card[data-tone="brand"] {
      border-left-color: var(--brand);
    }
    .pathway-card[data-tone="good"] {
      border-left-color: var(--good);
    }
    .pathway-card[data-tone="amber"] {
      border-left-color: var(--warn);
    }
    .pathway-card[data-tone="violet"] {
      border-left-color: var(--accent-violet);
    }
    .pathway-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
    }
    .pathway-label {
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }
    .pathway-count {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: auto;
      padding: 0;
      border-radius: 0;
      background: transparent;
      color: var(--ink);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
      box-shadow: none;
    }
    .pathway-card h3 {
      margin: 0;
      font-size: 15px;
      line-height: 1.22;
      letter-spacing: 0;
    }
    .pathway-note {
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 28%);
      font-size: var(--av-text-xs);
      line-height: 1.42;
    }
    .pathway-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      margin-top: auto;
      flex-wrap: wrap;
    }
    .status-pill {
      display: inline-flex;
      align-items: center;
      width: fit-content;
      gap: var(--av-spacing-1);
      min-height: var(--control-height-sm);
      padding: 0 10px;
      border: 1px solid color-mix(in oklab, var(--good), white 62%);
      border-radius: var(--av-radius-full);
      background: var(--good-soft);
      color: var(--good);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: var(--av-radius-full);
      background: currentColor;
    }
    .topbar-actions {
      display: grid;
      gap: var(--av-spacing-1);
      justify-items: end;
      min-width: 0;
    }
    .sticky-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: var(--av-spacing-1);
      flex-wrap: wrap;
      min-width: 0;
    }
    .utility-links {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: var(--av-spacing-3);
      flex-wrap: wrap;
    }
    .utility-link {
      color: var(--muted);
      font-size: var(--av-text-sm);
      font-weight: 600;
      text-decoration: none;
      white-space: nowrap;
    }
    .utility-link:hover,
    .utility-link:focus-visible {
      color: var(--brand);
      text-decoration: underline;
      text-underline-offset: 2px;
    }
    .lang-switch {
      display: inline-flex;
      align-items: center;
      gap: 2px;
      padding: 0;
      border: 0;
      border-radius: 0;
      background: transparent;
    }
    .lang-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 42px;
      min-height: var(--control-height-sm);
      padding: 0 var(--av-spacing-2);
      border-radius: var(--av-radius-sm);
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 700;
      text-decoration: none;
    }
    .lang-link.active {
      background: transparent;
      color: var(--ink);
      box-shadow: inset 0 -2px 0 var(--brand);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 4px;
      overflow-x: auto;
      min-height: 36px;
      max-width: 100%;
      padding: 0;
      border: 0;
      border-radius: 0;
      background: transparent;
      scrollbar-width: none;
      white-space: nowrap;
      flex: 1 1 auto;
      min-width: 0;
    }
    .toolbar::-webkit-scrollbar { display: none; }
    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: var(--control-height-sm);
      padding: 0 var(--av-spacing-3);
      border: 1px solid var(--button-outline);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition:
        border-color var(--av-duration-base) var(--av-easing-emphasized),
        background var(--av-duration-base) var(--av-easing-emphasized),
        color var(--av-duration-base) var(--av-easing-emphasized),
        box-shadow var(--av-duration-base) var(--av-easing-emphasized);
    }
    .button:hover {
      border-color: var(--line-strong);
      background: var(--panel-subtle);
      box-shadow: var(--shadow-xs);
    }
    .button.slim {
      min-height: var(--control-height-sm);
      padding: 0 var(--av-spacing-2);
    }
    .button.tab {
      border-color: transparent;
      background: transparent;
      box-shadow: none;
      color: var(--muted);
      white-space: nowrap;
      flex: 0 0 auto;
      min-height: 32px;
      border-radius: 0;
    }
    .button.tab:hover {
      color: var(--brand);
      background: var(--panel-subtle);
      border-color: transparent;
    }
    .button[aria-pressed="true"] {
      border-color: transparent;
      background: transparent;
      color: var(--ink);
      font-weight: 700;
      box-shadow: inset 0 -2px 0 var(--brand);
    }
    .button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    #clear-filters:disabled { display: none; }
    .button:focus-visible,
    .field:focus-visible,
    .text-button:focus-visible,
    .source-card:focus-visible,
    .more-link:focus-visible,
    .utility-link:focus-visible,
    .lang-link:focus-visible {
      outline: 0;
      box-shadow: var(--focus-ring);
      outline-offset: 2px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(148px, 196px));
      gap: 0;
      width: fit-content;
      max-width: 100%;
      justify-content: start;
      margin-bottom: var(--av-spacing-2);
      align-items: stretch;
      overflow: visible;
      border: 0;
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }
    .metric {
      border: 0;
      border-radius: 0;
      background: transparent;
      box-shadow: none;
      min-height: 60px;
      min-width: 0;
      padding: 10px 12px;
      display: grid;
      align-content: center;
    }
    .metric + .metric { border-left: 1px solid var(--line-subtle); }
    .metric.strong strong { color: var(--good); }
    .metric.sources strong { color: var(--warn); }
    .metric span {
      display: block;
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
      margin-bottom: var(--av-spacing-1);
    }
    .metric strong {
      font-family: var(--font-sans);
      font-size: 20px;
      font-weight: 700;
      line-height: 1;
      letter-spacing: 0;
      font-feature-settings: "tnum" 1, "lnum" 1;
    }
    .panel {
      padding: calc(var(--section-gap) * 0.58) 0 0;
      margin-top: calc(var(--section-gap) * 0.58);
      border-top: 1px solid var(--line);
      scroll-margin-top: 156px;
    }
    .panel.primary {
      border-top: 0;
      margin-top: 0;
      padding-top: var(--av-spacing-1);
    }
    .panel-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
      margin-bottom: 12px;
    }
    .panel-head h2 {
      margin: 0;
      font-family: var(--font-sans);
      font-size: 22px;
      font-weight: 700;
      line-height: var(--av-leading-tight);
    }
    .panel-head p {
      margin: var(--av-spacing-1) 0 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
    }
    .panel-actions {
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .panel-summary {
      color: var(--muted);
      font-size: var(--av-text-sm);
    }
    .filter-disclosure > summary { display: none; }
    .filter-disclosure-body { display: contents; }
    .filters-shell {
      display: grid;
      gap: 12px;
      margin-bottom: 12px;
      padding: 14px 0 16px;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }
    .filters {
      display: grid;
      grid-template-columns: minmax(220px, 1fr) repeat(3, minmax(128px, 0.28fr));
      gap: 10px;
      margin: 0;
      padding: 0;
      border: 0;
      border-radius: 0;
      background: transparent;
      align-items: end;
    }
    .filters.primary-filters {
      grid-template-columns: minmax(240px, 1fr) repeat(2, minmax(150px, 0.25fr));
    }
    .advanced-filters {
      border-top: 1px solid var(--line-subtle);
      padding-top: 10px;
    }
    .advanced-filters > summary {
      display: inline-flex;
      width: fit-content;
      min-height: 32px;
      align-items: center;
      gap: 6px;
      padding: 0 10px;
      border: 0;
      border-radius: var(--av-radius-sm);
      background: transparent;
      color: var(--ink);
      cursor: pointer;
      font-size: var(--av-text-sm);
      font-weight: 650;
      list-style: none;
    }
    .advanced-filters > summary::-webkit-details-marker { display: none; }
    .advanced-filters > summary::after {
      content: "⌄";
      color: var(--muted);
      font-size: 14px;
    }
    .advanced-filters[open] > summary {
      margin-bottom: 8px;
      border-color: color-mix(in oklab, var(--brand), white 46%);
      background: var(--brand-soft);
      color: var(--brand);
    }
    .advanced-filters[open] > summary::after {
      transform: rotate(180deg);
    }
    .advanced-filters .filters {
      grid-template-columns: repeat(5, minmax(138px, 1fr));
    }
    .filter-help {
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 500;
      line-height: 1.35;
    }
    .preset-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0;
      margin-bottom: 0;
      padding: 14px 0;
      border: 0;
      border-top: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
    }
    .preset-group {
      display: grid;
      align-content: start;
      gap: 6px;
      min-width: 0;
      padding: 0 12px;
      border: 0;
      border-radius: 0;
      background: transparent;
    }
    .preset-group:first-child { padding-left: 0; }
    .preset-group:last-child { padding-right: 0; }
    .preset-group + .preset-group {
      border-left: 1px solid var(--line-subtle);
    }
    .preset-row {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      min-width: 0;
    }
    .preset-button {
      min-height: 32px;
      padding: 0 11px;
      border: 1px solid transparent;
      border-radius: var(--av-radius-md);
      background: var(--panel-subtle);
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 700;
      cursor: pointer;
      transition:
        border-color var(--av-duration-base) var(--av-easing-emphasized),
        background var(--av-duration-base) var(--av-easing-emphasized),
        color var(--av-duration-base) var(--av-easing-emphasized),
        box-shadow var(--av-duration-base) var(--av-easing-emphasized);
    }
    .preset-button:hover {
      border-color: color-mix(in oklab, var(--brand), transparent 58%);
      background: var(--brand-soft);
      color: var(--ink);
    }
    .preset-button[aria-pressed="true"] {
      border-color: color-mix(in oklab, var(--brand), black 4%);
      background: var(--brand);
      color: white;
      box-shadow: 0 6px 14px rgb(33 75 184 / 0.16);
    }
    .filter-block {
      display: grid;
      gap: 6px;
    }
    .filter-label {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }
    .filter-label::before {
      content: none;
    }
    .filters-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-1);
      flex-wrap: wrap;
      margin-bottom: var(--av-spacing-2);
    }
    .filter-summary {
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .saved-views {
      display: grid;
      gap: 6px;
      margin-bottom: var(--av-spacing-2);
      padding: 8px 2px;
      border: 0;
      border-bottom: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }
    .saved-views-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .saved-actions {
      display: flex;
      align-items: center;
      gap: var(--av-spacing-1);
      flex-wrap: wrap;
    }
    .workspace-filter[aria-pressed="true"] {
      border-color: color-mix(in oklab, var(--brand), transparent 55%);
      background: var(--brand-soft);
      color: var(--brand);
    }
    .workspace-backup {
      position: relative;
    }
    .workspace-backup > summary {
      list-style: none;
      cursor: pointer;
    }
    .workspace-backup > summary::-webkit-details-marker { display: none; }
    .workspace-backup-menu {
      position: absolute;
      z-index: 24;
      top: calc(100% + 6px);
      right: 0;
      display: grid;
      min-width: 168px;
      padding: 6px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      box-shadow: 0 12px 30px rgb(15 23 42 / 0.14);
    }
    .workspace-backup-menu .text-button {
      justify-content: flex-start;
      width: 100%;
      min-height: 34px;
      padding: 0 9px;
      border-radius: var(--av-radius-sm);
      cursor: pointer;
    }
    .saved-view-row {
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }
    .saved-view-row:has(.saved-empty) { display: none; }
    .workspace-queue {
      display: grid;
      gap: var(--av-spacing-2);
      margin: 0 0 var(--av-spacing-3);
      padding: 12px 0;
      border: 0;
      border-bottom: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }
    .workspace-queue[hidden] { display: none; }
    .workspace-queue-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .workspace-queue-title {
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 750;
    }
    .workspace-queue-local {
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: 1.35;
    }
    .workspace-queue-list {
      display: grid;
      gap: 6px;
    }
    .workspace-queue-item {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 8px 12px;
      padding: 8px 0;
      border-top: 1px solid var(--line-subtle);
    }
    .workspace-queue-item:first-child {
      padding-top: 0;
      border-top: 0;
    }
    .workspace-queue-copy {
      display: grid;
      gap: 3px;
      min-width: 0;
    }
    .workspace-queue-name {
      overflow: hidden;
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 700;
      line-height: 1.3;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .workspace-queue-action {
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: 1.35;
    }
    .workspace-queue-meta {
      display: inline-flex;
      align-items: center;
      justify-content: flex-end;
      gap: 6px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 650;
      text-align: right;
      white-space: nowrap;
    }
    .workspace-queue-deadline.is-urgent { color: var(--warn); }
    .workspace-queue-more {
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }
    .saved-view-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 30px;
      max-width: 100%;
      padding: 0 10px;
      border: 1px solid var(--badge-outline);
      border-radius: var(--av-radius-sm);
      background: var(--panel);
    }
    .saved-view-pill button {
      border: 0;
      background: transparent;
      padding: 0;
      cursor: pointer;
      font: inherit;
    }
    .saved-view-pill .saved-apply {
      color: var(--ink);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }
    .saved-view-pill .saved-remove {
      color: var(--muted);
      font-size: 14px;
      line-height: 1;
    }
    .saved-empty {
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: 1.45;
    }
    .saved-view-notice {
      min-height: 20px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: 1.45;
    }
    .summary-pill {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border: 0;
      border-radius: var(--av-radius-full);
      padding: 0 9px;
      background: var(--panel-wash);
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }
    .summary-pill.result {
      background: var(--brand-soft);
      color: var(--brand);
    }
    .text-button {
      min-height: var(--control-height-sm);
      border: 1px solid transparent;
      border-radius: var(--av-radius-md);
      background: transparent;
      color: var(--muted);
      font-size: var(--av-text-sm);
      font-weight: 600;
      padding: 0 var(--av-spacing-2);
      cursor: pointer;
    }
    .text-button:hover,
    .text-button:focus-visible {
      color: var(--brand);
      background: var(--brand-soft);
      text-decoration: none;
    }
    .field {
      width: 100%;
      min-height: var(--control-height);
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: rgb(255 255 255 / 0.82);
      padding: 0 var(--av-spacing-3);
      color: var(--ink);
      outline: 0;
      transition:
        border-color var(--av-duration-base) var(--av-easing-emphasized),
        box-shadow var(--av-duration-base) var(--av-easing-emphasized);
    }
    .field:focus-visible {
      border-color: var(--brand);
      box-shadow: var(--focus-ring);
    }
    select.field {
      appearance: none;
      padding-right: var(--av-spacing-8);
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position:
        calc(100% - 16px) calc(50% - 2px),
        calc(100% - 11px) calc(50% - 2px);
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
    }
    .message {
      min-height: auto;
      display: flex;
      align-items: center;
      color: color-mix(in oklab, var(--muted), var(--ink) 18%);
      border: 1px dashed var(--line-strong);
      border-radius: var(--av-radius-md);
      padding: 8px 10px;
      background: var(--panel-subtle);
    }
    .message.empty {
      align-items: stretch;
    }
    .message-shell {
      width: 100%;
      display: grid;
      gap: var(--av-spacing-2);
    }
    .message-title {
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 650;
      line-height: var(--av-leading-snug);
    }
    .message-note {
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }
    .message-actions {
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }
    .message-action {
      min-height: 32px;
      padding-inline: 10px;
      border-radius: var(--av-radius-sm);
      border: 1px solid var(--line);
      background: var(--panel);
    }
    .message.error {
      color: var(--danger);
      border-color: var(--danger);
      background: var(--danger-soft);
    }
    .list {
      display: grid;
      gap: 0;
      border-bottom: 1px solid var(--line);
    }
    .list-actions {
      display: flex;
      justify-content: center;
      margin-top: var(--av-spacing-3);
    }
    .opportunity {
      border: 0;
      border-top: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      padding: 22px 4px;
      box-shadow: none;
      position: relative;
      overflow: visible;
      transition:
        background var(--av-duration-base) var(--av-easing-emphasized),
        color var(--av-duration-base) var(--av-easing-emphasized);
    }
    .opportunity:hover {
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 7%);
      box-shadow: none;
    }
    .opportunity.good,
    .opportunity.warn { border-left-color: transparent; }
    .opportunity-main {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(310px, 0.36fr);
      gap: 36px;
      align-items: start;
    }
    .opportunity-content {
      display: grid;
      gap: 12px;
      min-width: 0;
    }
    .opportunity-rail {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      grid-template-areas:
        "status"
        "meta"
        "fit"
        "actions";
      align-content: start;
      gap: 12px;
      min-width: 0;
      padding: 2px 0 2px 24px;
      border: 0;
      border-left: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }
    .opportunity-heading {
      display: grid;
      gap: 9px;
    }
    .opportunity h3 {
      margin: 0;
      font-size: 19px;
      font-weight: 700;
      line-height: 1.3;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .opportunity h3 a {
      color: var(--ink);
      text-decoration: none;
      transition: color var(--av-duration-base) var(--av-easing-emphasized);
    }
    .opportunity h3 a:hover,
    .opportunity h3 a:focus-visible {
      color: var(--brand);
      text-decoration: underline;
      text-underline-offset: 2px;
    }
    .opportunity-summary {
      margin: 0;
      color: var(--muted);
      max-width: 78ch;
      font-size: 14px;
      line-height: 1.58;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .tags { display: flex; flex-wrap: wrap; gap: var(--av-spacing-1); }
    .tag {
      border-radius: var(--av-radius-sm);
      border: 0;
      background: var(--panel-subtle);
      color: var(--muted);
      padding: 3px 7px;
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      line-height: 1.4;
    }
    .fit-block {
      grid-area: fit;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
    }
    .fit-label {
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }
    .fit-pills {
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }
    .fit-pill {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      max-width: 100%;
      padding: 0 8px;
      border: 0;
      border-radius: var(--av-radius-sm);
      background: var(--panel-subtle);
      color: color-mix(in oklab, var(--muted), var(--ink) 18%);
      font-size: var(--av-text-xs);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .fit-pill.good {
      background: var(--good-soft);
      color: var(--good);
    }
    .fit-pill.warn {
      background: var(--warn-soft);
      color: var(--warn);
    }
    .signal-box {
      display: grid;
      gap: 6px;
      padding: 10px 12px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel);
    }
    .focus-copy {
      display: grid;
      gap: 5px;
      padding-left: 0;
      border-left: 0;
    }
    .signal-label {
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }
    .signal-lede {
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 600;
      line-height: var(--av-leading-snug);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .signal-pills {
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }
    .meta-rows {
      grid-area: meta;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 18px;
    }
    .meta-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 3px;
      align-items: start;
      min-width: 0;
      padding-top: 8px;
      border-top: 1px solid var(--line-subtle);
      font-size: 12px;
      line-height: 1.4;
    }
    .meta-row::before {
      content: none !important;
      display: none;
    }
    .meta-row:nth-child(1)::before {
      content: "";
      background:
        linear-gradient(currentColor 0 0) 50% 40% / 9px 2px no-repeat,
        linear-gradient(currentColor 0 0) 50% 62% / 9px 2px no-repeat,
        var(--panel);
    }
    .meta-row:nth-child(2)::before {
      content: "";
      border-radius: var(--av-radius-full);
      background:
        radial-gradient(circle at 50% 50%, currentColor 0 2px, transparent 2.5px),
        var(--panel);
    }
    .meta-row:nth-child(3)::before {
      content: "";
      border-radius: var(--av-radius-full);
      background:
        conic-gradient(currentColor 0 25%, transparent 0 100%),
        var(--panel);
    }
    .meta-row:nth-child(4)::before {
      content: "";
      background:
        linear-gradient(135deg, transparent 42%, currentColor 43% 57%, transparent 58%),
        var(--panel);
    }
    .meta-row span {
      grid-column: 1;
      color: var(--muted);
      font-weight: 600;
    }
    .meta-row strong {
      grid-column: 1;
      min-width: 0;
      color: var(--ink);
      font-weight: 650;
      overflow-wrap: anywhere;
    }
    .operator-note {
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 600;
      line-height: var(--av-leading-snug);
    }
    .signal-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 24px;
      max-width: 100%;
      padding: 0 8px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-full);
      background: var(--panel);
      color: var(--ink);
      font-size: var(--av-text-xs);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .signal-pill span {
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }
    .side {
      grid-area: status;
      min-width: 0;
      display: flex;
      align-items: center;
      justify-content: flex-start;
      flex-wrap: wrap;
      gap: 7px;
    }
    .score {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      min-width: 72px;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--av-radius-full);
      background: var(--brand-soft);
      color: var(--brand);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }
    .score::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: var(--av-radius-full);
      background: currentColor;
      opacity: 0.76;
    }
    .score.good { background: var(--good-soft); color: var(--good); }
    .score.warn { background: var(--warn-soft); color: var(--warn); }
    .score.low {
      background: var(--panel-subtle);
      color: var(--muted);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      min-height: 28px;
      width: max-content;
      max-width: 100%;
      border: 1px solid transparent;
      border-radius: var(--av-radius-full);
      padding: 0 var(--av-spacing-2);
      background: color-mix(in oklab, var(--brand-soft), white 12%);
      color: var(--brand);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }
    .badge::before {
      content: "";
      width: 6px;
      height: 6px;
      border-radius: var(--av-radius-full);
      background: currentColor;
      opacity: 0.7;
    }
    .badge.watchlist { background: var(--good-soft); color: var(--good); }
    .badge.regional {
      background: color-mix(in oklab, var(--warn-soft), white 10%);
      color: var(--warn);
    }
    .badge.lifecycle {
      background: var(--panel-subtle);
      color: var(--ink);
    }
    .health-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: var(--av-spacing-2);
    }
    .method-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-3);
    }
    .role-guide {
      display: grid;
      gap: var(--av-spacing-3);
      margin-top: var(--av-spacing-4);
      padding-top: var(--av-spacing-4);
      border-top: 1px solid var(--line-subtle);
    }
    .role-guide-head {
      display: grid;
      gap: 4px;
      max-width: 72ch;
    }
    .role-guide-head h3 {
      margin: 0;
      font-size: var(--av-text-xl);
      line-height: 1.2;
    }
    .role-guide-head p {
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.5;
    }
    .role-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      column-gap: var(--av-spacing-5);
    }
    .role-item {
      display: grid;
      grid-template-columns: minmax(100px, 0.34fr) minmax(0, 1fr);
      gap: var(--av-spacing-3);
      padding: 10px 0;
      border-top: 1px solid var(--line-subtle);
    }
    .role-item h4,
    .role-item p {
      margin: 0;
      font-size: var(--av-text-sm);
      line-height: 1.45;
    }
    .role-item h4 { font-weight: 700; }
    .role-item p { color: var(--muted); }
    .source-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: var(--av-spacing-1);
    }
    .source-card {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      border: 0;
      border-top: 1px solid var(--line-subtle);
      border-radius: 0;
      padding: 14px 4px;
      background: transparent;
      min-height: 66px;
      color: inherit;
      text-decoration: none;
      transition:
        background var(--av-duration-base) var(--av-easing-emphasized),
        color var(--av-duration-base) var(--av-easing-emphasized);
    }
    .source-icon {
      width: 34px;
      height: 34px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex: 0 0 auto;
      border-radius: 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0;
      box-shadow: inset 0 0 0 1px color-mix(in oklab, currentColor, transparent 80%);
    }
    .source-icon--blue {
      background: rgb(96 165 250 / 0.12);
      color: var(--av-color-blue-700);
    }
    .source-icon--green {
      background: rgb(16 185 129 / 0.12);
      color: var(--av-color-emerald-700);
    }
    .source-icon--amber {
      background: rgb(245 158 11 / 0.14);
      color: var(--av-color-amber-700);
    }
    .source-icon--violet {
      background: rgb(139 92 246 / 0.12);
      color: #6d28d9;
    }
    .source-icon--slate {
      background: rgb(100 116 139 / 0.12);
      color: var(--av-color-slate-500);
    }
    .source-icon--red {
      background: rgb(239 68 68 / 0.11);
      color: var(--av-color-red-700);
    }
    .source-card:hover {
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 7%);
      box-shadow: none;
      transform: none;
    }
    .source-card strong {
      display: block;
      font-size: 14px;
      font-weight: 650;
      line-height: var(--av-leading-snug);
    }
    .source-main {
      min-width: 0;
      flex: 1 1 auto;
    }
    .source-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--av-spacing-1);
      margin-top: var(--av-spacing-1);
      min-width: 0;
    }
    .source-note {
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: 1.2;
      min-width: 0;
      overflow-wrap: anywhere;
    }
    .source-freshness {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 0 7px;
      border-radius: var(--av-radius-full);
      background: var(--good-soft);
      color: var(--good);
      font-size: 11px;
      font-weight: 700;
      white-space: nowrap;
    }
    .source-freshness.is-stale {
      background: var(--warn-soft);
      color: var(--warn);
    }
    .source-freshness.is-unknown {
      background: var(--panel-subtle);
      color: var(--muted);
    }
    .source-url {
      flex: 0 1 180px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      display: inline-block;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .source-card:hover .source-url { color: var(--brand); }
    .source-count {
      flex: 0 0 104px;
      justify-self: end;
      display: grid;
      gap: 4px;
      min-width: 0;
      text-align: right;
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: var(--av-leading-snug);
    }
    .source-count span {
      min-width: 0;
      overflow-wrap: anywhere;
    }
    .source-arrow {
      flex: 0 0 auto;
      color: color-mix(in oklab, var(--muted), transparent 18%);
      font-size: 20px;
      line-height: 1;
      transition:
        color var(--av-duration-base) var(--av-easing-emphasized),
        transform var(--av-duration-base) var(--av-easing-emphasized);
    }
    .source-card:hover .source-arrow {
      color: var(--brand);
      transform: translateX(2px);
    }
    .opportunity-footer {
      display: grid;
      gap: 5px;
      padding-top: 10px;
      border-top: 1px solid var(--line-subtle);
      color: var(--muted);
      font-size: var(--av-text-xs);
    }
    .card-actions {
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .card-actions-secondary {
      grid-area: actions;
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .workflow-control {
      grid-column: 1 / -1;
      display: grid;
      gap: 5px;
      padding-top: 7px;
      border-top: 1px solid var(--line-subtle);
    }
    .workflow-control span {
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }
    .workflow-control select {
      width: 100%;
      min-height: 32px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      color: var(--ink);
      padding: 0 28px 0 9px;
      font-size: var(--av-text-xs);
      font-weight: 650;
    }
    .detail-link {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      min-height: 28px;
      border: 1px solid transparent;
      border-radius: var(--av-radius-md);
      background: transparent;
      color: var(--brand);
      font-size: var(--av-text-sm);
      font-weight: 600;
      padding: 0;
      cursor: pointer;
    }
    .detail-link::before {
      content: none;
    }
    .detail-link:hover,
    .detail-link:focus-visible {
      color: var(--brand-hover);
      text-decoration: underline;
      text-underline-offset: 2px;
      background: transparent;
      box-shadow: none;
    }
    .opportunity-click {
      position: absolute;
      inset: 0;
      border: 0;
      background: transparent;
      cursor: pointer;
      opacity: 0;
      appearance: none;
      z-index: 0;
    }
    .opportunity-click:focus-visible {
      outline: 0;
      box-shadow: inset var(--focus-ring);
      outline-offset: 2px;
      opacity: 1;
    }
    .opportunity-main,
    .opportunity-content,
    .opportunity-rail,
    .opportunity-footer,
    .side,
    .opportunity h3,
    .tags,
    .focus-copy,
    .signal-box,
    .signal-pills,
    .card-actions,
    .detail-link,
    .more-link {
      position: relative;
      z-index: 1;
    }
    .opportunity:hover .score,
    .opportunity:hover .tag {
      background-color: color-mix(in oklab, currentColor, transparent 92%);
    }
    .score,
    .tag {
      transition: background-color var(--av-duration-base) var(--av-easing-emphasized);
    }
    .footer-source {
      display: inline-flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .footer-funder-link {
      color: var(--brand);
      font-weight: 600;
      text-decoration: none;
    }
    .footer-funder-link:hover,
    .footer-funder-link:focus-visible {
      text-decoration: underline;
      text-underline-offset: 2px;
    }
    .footer-sep { color: var(--line-strong); }
    .site-footer {
      display: grid;
      gap: 10px;
      margin-top: var(--section-gap);
      padding: 24px 0 0;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }
    .site-footer-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 16px;
      align-items: center;
      font-size: var(--av-text-xs);
      font-weight: 650;
    }
    .site-footer p {
      margin: 0;
      max-width: 920px;
    }
    .site-footer a {
      color: var(--ink);
      font-weight: 650;
      text-decoration: none;
    }
    .site-footer a:hover,
    .site-footer a:focus-visible {
      color: var(--brand);
      text-decoration: underline;
      text-underline-offset: 2px;
    }
    .more-link {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      color: var(--brand);
      font-size: var(--av-text-sm);
      font-weight: 600;
      text-decoration: none;
    }
    .more-link::before {
      content: none;
    }
    .more-link:hover,
    .more-link:focus-visible {
      text-decoration: underline;
      text-underline-offset: 2px;
    }
    .detail-backdrop {
      position: fixed;
      inset: 0;
      z-index: 70;
      background: rgb(15 23 42 / 0.38);
      backdrop-filter: blur(8px);
      opacity: 0;
      pointer-events: none;
      transition: opacity var(--av-duration-base) var(--av-easing-emphasized);
    }
    .detail-backdrop.open {
      opacity: 1;
      pointer-events: auto;
    }
    .detail-backdrop[hidden],
    .detail-drawer[hidden] {
      display: none;
    }
    .detail-drawer {
      position: fixed;
      inset: 0 0 0 auto;
      z-index: 80;
      width: min(640px, 100vw);
      border-left: 1px solid var(--line);
      background: color-mix(in oklab, var(--panel), white 6%);
      box-shadow: -24px 0 64px rgb(15 23 42 / 0.18);
      transform: translateX(100%);
      transition: transform var(--av-duration-base) var(--av-easing-emphasized);
      display: grid;
      grid-template-rows: auto 1fr auto;
    }
    .detail-drawer.open {
      transform: translateX(0);
    }
    .detail-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: var(--av-spacing-2);
      padding: 18px 20px;
      border-bottom: 1px solid var(--line-subtle);
      background: var(--panel);
    }
    .detail-header h2 {
      margin: var(--av-spacing-1) 0 0;
      font-family: var(--font-sans);
      font-size: 19px;
      line-height: var(--av-leading-tight);
    }
    .detail-status {
      margin: var(--av-spacing-2) 0 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }
    .detail-close {
      min-width: var(--control-height);
      padding: 0;
      flex: 0 0 auto;
    }
    .detail-body {
      overflow-y: auto;
      padding: 18px 20px;
      display: grid;
      gap: 18px;
      align-content: start;
    }
    .detail-meta {
      display: grid;
      gap: var(--av-spacing-2);
    }
    .detail-fit {
      display: grid;
      gap: var(--av-spacing-2);
      padding: 12px 0 12px 14px;
      border: 0;
      border-left: 2px solid var(--brand);
      border-radius: 0;
      background: transparent;
    }
    .detail-fit h3 {
      margin: 0;
      font-size: var(--av-text-sm);
      font-weight: 700;
      line-height: var(--av-leading-snug);
    }
    .detail-fit p {
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }
    .detail-readiness {
      display: grid;
      gap: 5px;
      padding: 12px 0;
      border-top: 1px solid var(--line-subtle);
      border-bottom: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }
    .detail-readiness h3 {
      margin: 0;
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }
    .detail-readiness p {
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }
    .detail-meta-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0 18px;
    }
    .detail-meta-item {
      min-width: 0;
      padding: 11px 0;
      border: 0;
      border-top: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }
    .detail-meta-item span {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }
    .detail-meta-item strong {
      display: block;
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
      overflow-wrap: anywhere;
    }
    .detail-section-block {
      padding-top: var(--av-spacing-2);
      border-top: 1px solid var(--line-subtle);
    }
    .detail-section-block h3,
    .detail-meta h3 {
      margin: 0 0 var(--av-spacing-2);
      font-size: var(--av-text-sm);
      font-weight: 700;
      line-height: var(--av-leading-snug);
    }
    .detail-richtext {
      display: grid;
      gap: var(--av-spacing-2);
    }
    .detail-richtext p {
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      line-height: 1.65;
      overflow-wrap: anywhere;
    }
    .detail-empty {
      padding: 12px;
      border: 1px dashed var(--line-strong);
      border-radius: var(--av-radius-md);
      background: var(--panel-subtle);
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }
    .detail-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
      padding: 14px 20px;
      border-top: 1px solid var(--line-subtle);
      background: transparent;
    }
    .detail-footer-actions {
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }
    .health-item {
      border: 1px solid var(--line-subtle);
      border-left: 3px solid var(--brand);
      border-radius: var(--av-radius-md);
      padding: 10px 12px;
      background: var(--panel);
    }
    .health-item span {
      display: block;
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
      margin-bottom: var(--av-spacing-2);
    }
    .health-item strong {
      display: block;
      font-family: var(--font-sans);
      font-size: var(--av-text-lg);
      line-height: 1.1;
      overflow-wrap: anywhere;
    }
    .health-note {
      margin: var(--av-spacing-3) 0 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }
    .method-card,
    .faq-item {
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      padding: var(--av-spacing-3);
    }
    .method-card h3,
    .faq-item h3,
    .method-disclaimer strong {
      display: block;
      margin: 0 0 var(--av-spacing-2);
      font-size: var(--av-text-lg);
      line-height: 1.25;
    }
    .method-card p,
    .faq-item p,
    .method-disclaimer p {
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.6;
    }
    .method-disclaimer {
      margin-top: var(--av-spacing-3);
      padding: 12px 14px;
      background: var(--accent-wash);
      border: 1px solid var(--line-subtle);
      border-left: 3px solid var(--brand);
      border-radius: var(--av-radius-md);
    }
    .faq-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--av-spacing-2);
      margin-top: var(--av-spacing-2);
    }
    .hidden { display: none; }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }
    .async-grid[aria-busy="true"]::before,
    .loading-state::before {
      content: "";
      display: block;
      grid-column: 1 / -1;
      min-height: 72px;
      border-radius: var(--av-radius-md);
      border: 1px solid var(--line-subtle);
      background:
        linear-gradient(
          90deg,
          transparent 0,
          rgb(255 255 255 / 0.62) 50%,
          transparent 100%
        ) 0 0 / 220% 100%,
        linear-gradient(var(--line-subtle) 0 0) 18px 20px / 42% 8px no-repeat,
        linear-gradient(var(--line-subtle) 0 0) 18px 40px / 70% 7px no-repeat,
        linear-gradient(var(--line-subtle) 0 0) calc(100% - 88px) 20px / 64px 22px no-repeat,
        var(--panel);
      background-size: 220% 100%;
      animation: loading-sheen 1.2s ease-in-out infinite;
    }
    .spotlight-grid[aria-busy="true"]::before,
    .funder-grid[aria-busy="true"]::before {
      min-height: 132px;
    }
    .pathways-grid[aria-busy="true"]::before,
    .themes-grid[aria-busy="true"]::before {
      min-height: 88px;
    }
    .loading-state {
      display: block;
      min-height: 72px;
      padding: 0;
      border: 0;
      background: transparent;
    }
    @keyframes loading-sheen {
      from { background-position: 100% 0; }
      to { background-position: -100% 0; }
    }
    @media (prefers-reduced-motion: reduce) {
      .async-grid[aria-busy="true"]::before,
      .loading-state::before { animation: none; }
    }

    @media (max-width: 980px) {
      .mobile-app-bar {
        position: fixed;
        inset: 0 0 auto;
        z-index: 52;
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: calc(58px + env(safe-area-inset-top));
        padding: calc(7px + env(safe-area-inset-top)) 16px 7px;
        border-bottom: 1px solid var(--line-subtle);
        background: color-mix(in oklab, var(--panel), transparent 4%);
        box-shadow: 0 1px 12px rgb(15 23 42 / 0.06);
        backdrop-filter: blur(18px);
      }
      .mobile-app-brand {
        display: grid;
        gap: 1px;
        min-width: 0;
        color: var(--ink);
        text-decoration: none;
      }
      .mobile-app-brand strong {
        font-size: var(--av-text-base);
        line-height: 1.1;
        letter-spacing: 0;
      }
      .mobile-app-brand span {
        color: var(--muted);
        font-size: 11px;
        line-height: 1.2;
      }
      .mobile-app-actions,
      .mobile-lang-switch {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .mobile-lang-switch {
        padding: 3px;
        border: 1px solid var(--line-subtle);
        border-radius: var(--av-radius-full);
        background: var(--panel-subtle);
      }
      .mobile-lang-switch a {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 34px;
        min-height: 34px;
        border-radius: var(--av-radius-full);
        color: var(--muted);
        font-size: var(--av-text-xs);
        font-weight: 700;
        text-decoration: none;
      }
      .mobile-lang-switch a[aria-current="page"] {
        background: var(--panel);
        color: var(--ink);
        box-shadow: var(--shadow-xs);
      }
      .mobile-icon-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        padding: 0;
        border: 1px solid var(--line-subtle);
        border-radius: var(--av-radius-full);
        background: var(--panel);
        color: var(--ink);
        cursor: pointer;
      }
      .mobile-icon-button svg,
      .mobile-nav-item svg {
        width: 21px;
        height: 21px;
        fill: none;
        stroke: currentColor;
        stroke-width: 1.8;
        stroke-linecap: round;
        stroke-linejoin: round;
      }
      .shell {
        padding-top: calc(70px + env(safe-area-inset-top));
      }
      .hero-band {
        padding: 14px 16px 0;
      }
      .hero-band .topbar,
      .hero-stage {
        display: none;
      }
      .hero-grid {
        grid-template-columns: 1fr;
        margin-bottom: 10px;
      }
      .hero-copy {
        gap: 10px;
        padding: 0;
      }
      .hero-intro {
        max-width: 72ch;
        display: -webkit-box;
        overflow: hidden;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
      }
      .hero-actions .button {
        min-height: 38px;
      }
      .hero-pick-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .hero-pick:last-child { grid-column: 1 / -1; }
      .spotlight-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .funder-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .discovery-grid {
        grid-template-columns: 1fr;
        gap: var(--av-spacing-4);
      }
      .themes-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .pathways-grid {
        grid-template-columns: 1fr;
      }
      .method-grid,
      .faq-list {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .topic-brief-grid {
        grid-template-columns: 1fr;
      }
      .hero-stage {
        padding: 16px 0 0;
        border-left: 0;
        border-top: 1px solid var(--line);
      }
      .sticky-bar {
        align-items: flex-start;
        flex-wrap: wrap;
      }
      .sticky-shell { top: calc(66px + env(safe-area-inset-top)); }
      .sticky-actions {
        width: 100%;
        justify-content: space-between;
      }
      .preset-grid,
      .filters,
      .filters.primary-filters,
      .advanced-filters .filters {
        grid-template-columns: 1fr 1fr;
      }
      .preset-group { padding: 8px 10px; }
      .preset-group:first-child { padding-left: 0; }
      .preset-group:last-child { padding-right: 0; }
      .filters .filter-block:first-child {
        grid-column: 1 / -1;
      }
      .health-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .opportunity-main { grid-template-columns: 1fr; }
      .opportunity-rail {
        padding: 10px 0 0;
        border: 0;
        border-top: 1px solid var(--line-subtle);
      }
    }

    @media (max-width: 820px) {
      .button,
      .button.slim,
      .button.tab,
      .field,
      .text-button,
      .preset-button,
      .detail-link,
      .advanced-filters > summary,
      .workflow-control select {
        min-height: var(--av-control-height-lg);
      }
      .toolbar { min-height: var(--av-control-height-lg); }
      .utility-link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: var(--av-control-height-lg);
        min-height: var(--av-control-height-lg);
      }
      .shell {
        width: 100%;
        padding: calc(66px + env(safe-area-inset-top)) 12px
          calc(82px + env(safe-area-inset-bottom));
      }
      .hero-band {
        padding: 12px 12px 0;
        margin-bottom: 8px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .topic-brief {
        padding: 14px 16px;
      }
      .filter-disclosure {
        margin-bottom: var(--av-spacing-2);
        border: 0;
        border-top: 1px solid var(--line-subtle);
        border-bottom: 1px solid var(--line-subtle);
        border-radius: 0;
        background: transparent;
      }
      .filter-disclosure > summary {
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 44px;
        padding: 0 12px;
        color: var(--ink);
        cursor: pointer;
        font-size: var(--av-text-sm);
        font-weight: 700;
        list-style: none;
      }
      .filter-disclosure > summary::-webkit-details-marker { display: none; }
      .filter-disclosure > summary::after {
        content: "+";
        color: var(--brand);
        font-size: 18px;
      }
      .filter-disclosure[open] > summary::after { content: "−"; }
      html[data-compact-filters="true"]
        .filter-disclosure[open] > summary::after { content: "+"; }
      html[data-compact-filters="true"]
        .filter-disclosure[open] > .filter-disclosure-body { display: none; }
      .filter-disclosure-body {
        display: grid;
        gap: var(--av-spacing-2);
        padding: 0 10px 10px;
      }
      .filter-disclosure .preset-grid,
      .filter-disclosure .filters-shell {
        margin-bottom: 0;
      }
      .sticky-shell {
        display: none;
      }
      .sticky-bar {
        display: grid;
        gap: var(--av-spacing-2);
        padding: 8px 0;
      }
      .topbar {
        gap: var(--av-spacing-2);
        margin-bottom: var(--av-spacing-3);
      }
      .hero-intro {
        font-size: var(--av-text-base);
        line-height: 1.55;
      }
      .hero-actions,
      .hero-pick-row {
        width: 100%;
      }
      .hero-actions > .button,
      .hero-pick-row > .button {
        flex: 1 1 auto;
      }
      .topbar-actions {
        width: auto;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: var(--av-spacing-2);
      }
      .sticky-actions {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--av-spacing-2);
      }
      .utility-links {
        justify-content: flex-start;
      }
      .brand p {
        max-width: 34rem;
        font-size: var(--av-text-sm);
        line-height: var(--av-leading-snug);
      }
      .hero-stage-title {
        font-size: 22px;
      }
      .focus-chip {
        min-height: var(--control-height-sm);
        font-size: 11px;
      }
      .grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
        width: 100%;
        gap: 0;
      }
      .health-grid,
      .source-grid,
      .method-grid,
      .faq-list,
      .role-list {
        grid-template-columns: 1fr;
      }
      .role-item {
        grid-template-columns: 1fr;
        gap: 2px;
      }
      .preset-grid,
      .filters,
      .filters.primary-filters,
      .advanced-filters .filters {
        grid-template-columns: 1fr;
      }
      .preset-grid { padding-block: 4px; }
      .preset-group,
      .preset-group:first-child,
      .preset-group:last-child {
        padding: 8px 0;
      }
      .preset-group + .preset-group {
        border-left: 0;
        border-top: 1px solid var(--line-subtle);
      }
      .panel {
        padding-top: var(--av-spacing-5);
        margin-top: var(--av-spacing-5);
      }
      .source-card {
        display: grid;
        grid-template-columns: 32px minmax(0, 1fr) auto;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 14px 2px;
      }
      .source-icon {
        grid-column: 1;
        grid-row: 1 / 4;
        width: 32px;
        height: 32px;
        border-radius: var(--av-radius-md);
        font-size: 10px;
      }
      .source-main,
      .source-url,
      .source-count {
        grid-column: 2;
        min-width: 0;
        width: auto;
      }
      .source-count {
        flex-basis: auto;
        justify-self: stretch;
        text-align: left;
      }
      .source-arrow {
        grid-column: 3;
        grid-row: 1;
        margin-left: 0;
        padding-top: 4px;
      }
      .opportunity-main {
        grid-template-columns: 1fr;
      }
      .opportunity-rail {
        padding: 10px 0 0;
        border: 0;
        border-top: 1px solid var(--line-subtle);
      }
      .meta-rows { grid-template-columns: 1fr; }
      .meta-row {
        grid-template-columns: minmax(86px, 0.42fr) minmax(0, 1fr);
      }
      .meta-row span,
      .meta-row strong { grid-column: auto; }
      .side {
        justify-content: flex-start;
        min-width: 0;
      }
      .panel-actions,
      .filters-meta {
        width: 100%;
        justify-content: space-between;
      }
      .saved-views-head {
        align-items: flex-start;
      }
      .saved-actions {
        width: 100%;
      }
      .workspace-queue {
        padding: 10px;
      }
      .workspace-queue-item {
        grid-template-columns: 1fr;
        gap: 6px;
      }
      .workspace-queue-meta {
        justify-content: flex-start;
        text-align: left;
        white-space: normal;
      }
      .health-grid {
        grid-template-columns: 1fr;
      }
      .detail-drawer {
        width: 100vw;
        border-left: 0;
      }
      .detail-header,
      .detail-body,
      .detail-footer {
        padding-left: var(--av-spacing-2);
        padding-right: var(--av-spacing-2);
      }
      .detail-meta-grid {
        grid-template-columns: 1fr;
      }
      .mobile-app-nav {
        position: fixed;
        inset: auto 0 0;
        z-index: 48;
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        min-height: calc(62px + env(safe-area-inset-bottom));
        padding: 5px 8px calc(5px + env(safe-area-inset-bottom));
        border-top: 1px solid var(--line-subtle);
        background: color-mix(in oklab, var(--panel), transparent 3%);
        box-shadow: 0 -8px 24px rgb(15 23 42 / 0.08);
        backdrop-filter: blur(18px);
      }
      .mobile-nav-item {
        display: grid;
        place-items: center;
        align-content: center;
        gap: 3px;
        min-width: 0;
        min-height: 52px;
        padding: 3px 2px;
        border: 0;
        border-radius: var(--av-radius-md);
        background: transparent;
        color: var(--muted);
        cursor: pointer;
        font-size: 10px;
        font-weight: 650;
        line-height: 1.1;
      }
      .mobile-nav-item[aria-pressed="true"] {
        background: var(--brand-soft);
        color: var(--brand);
      }
      .mobile-filter-backdrop {
        position: fixed;
        inset: 0;
        z-index: 60;
        border: 0;
        background: rgb(15 23 42 / 0.4);
        opacity: 0;
        pointer-events: none;
        transition: opacity var(--av-duration-base) var(--av-easing-emphasized);
      }
      .mobile-filter-backdrop.is-open {
        display: block;
        opacity: 1;
        pointer-events: auto;
      }
      body.filter-sheet-open .filter-disclosure {
        position: fixed;
        inset: auto 0 0;
        z-index: 64;
        display: block;
        width: min(100%, 680px);
        max-height: min(88dvh, 760px);
        margin: 0 auto;
        padding: 0 0 calc(72px + env(safe-area-inset-bottom));
        overflow: hidden;
        border: 1px solid var(--line-subtle);
        border-bottom: 0;
        border-radius: var(--av-radius-lg) var(--av-radius-lg) 0 0;
        background: var(--panel);
        box-shadow: 0 -24px 64px rgb(15 23 42 / 0.2);
      }
      body.filter-sheet-open .filter-disclosure > summary {
        position: sticky;
        top: 0;
        z-index: 2;
        min-height: 54px;
        padding: 0 18px;
        border-bottom: 1px solid var(--line-subtle);
        background: var(--panel);
      }
      body.filter-sheet-open .filter-disclosure > summary::after {
        content: "×";
        font-size: 24px;
        font-weight: 400;
      }
      body.filter-sheet-open .filter-disclosure-body {
        display: grid !important;
        max-height: calc(min(88dvh, 760px) - 126px - env(safe-area-inset-bottom));
        padding: 4px 14px 18px;
        overflow-y: auto;
        overscroll-behavior: contain;
      }
      body.filter-sheet-open .mobile-filter-sheet-actions {
        position: fixed;
        inset: auto 0 0;
        z-index: 66;
        display: flex;
        justify-content: center;
        width: min(100%, 680px);
        margin: 0 auto;
        padding: 10px 14px calc(10px + env(safe-area-inset-bottom));
        border-top: 1px solid var(--line-subtle);
        background: var(--panel);
      }
      body.filter-sheet-open .mobile-filter-sheet-actions .button {
        width: 100%;
        min-height: 46px;
      }
      body.modal-open .mobile-app-nav,
      body.filter-sheet-open .mobile-app-nav {
        visibility: hidden;
      }
      .panel.primary {
        margin-top: 0;
        padding-top: 14px;
      }
      .panel.primary .panel-head {
        margin-bottom: 8px;
      }
      .panel.primary .panel-head h2 {
        font-size: var(--av-text-xl);
      }
      .panel.primary .panel-head p {
        display: none;
      }
    }

    @media (max-width: 560px) {
      .hero-grid {
        gap: var(--av-spacing-3);
        margin-bottom: var(--av-spacing-3);
      }
      .hero-copy {
        gap: var(--av-spacing-2);
      }
      .hero-points {
        grid-template-columns: 1fr;
        gap: var(--av-spacing-2);
      }
      .grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
      .spotlight-grid {
        grid-template-columns: 1fr;
      }
      .funder-grid {
        grid-template-columns: 1fr;
      }
      .discovery-grid {
        padding-block: var(--av-spacing-3);
      }
      .discovery-library > summary,
      .trust-library > summary {
        min-height: 48px;
      }
      .discovery-library-description,
      .trust-library-description,
      .funder-library-description,
      .methodology-library-description {
        display: none;
      }
      .themes-grid {
        grid-template-columns: 1fr;
      }
      .pathways-grid {
        grid-template-columns: 1fr;
      }
      .spotlight-card {
        min-height: 0;
        padding: 12px;
      }
      .theme-card {
        min-height: 0;
        padding: 12px;
      }
      .pathway-card {
        min-height: 0;
        padding: 12px;
      }
      .metric.sources {
        grid-column: auto;
        border-left: 1px solid var(--line-subtle);
      }
      .filters-meta {
        align-items: flex-start;
        display: grid;
        grid-template-columns: 1fr;
        justify-items: start;
      }
      .filter-summary {
        width: 100%;
      }
      .focus-row {
        display: flex;
        flex-wrap: wrap;
        gap: var(--av-spacing-1);
      }
      .hero-actions { display: block; }
      .hero-actions > .button.primary { width: 100%; }
      .hero-stage {
        display: grid;
        gap: 6px;
        padding: 10px 0 0;
      }
      .hero-stage-title { font-size: 16px; }
      .hero-pick-row {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 6px;
        overflow: visible;
        padding-bottom: 0;
      }
      .hero-pick {
        min-height: var(--av-control-height-lg);
        min-width: 0;
        padding: 6px 8px;
        white-space: normal;
        text-align: center;
        justify-content: center;
        line-height: 1.2;
      }
      .hero-pick:last-child { grid-column: 1 / -1; }
      .hero-point {
        font-size: var(--av-text-xs);
        line-height: 1.45;
      }
      .spotlight-copy h2 {
        font-size: 20px;
      }
      .pathway-card h3 {
        font-size: var(--av-text-lg);
      }
      .hero-point {
        grid-template-columns: 24px minmax(0, 1fr);
        font-size: var(--av-text-sm);
      }
      .hero-point-index {
        width: 24px;
        height: 24px;
      }
      .preset-row {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .preset-button {
        min-height: var(--av-control-height-lg);
        text-align: left;
      }
      .focus-chip {
        width: auto;
        min-height: 24px;
      }
      .opportunity,
      .source-card,
      .health-item {
        min-width: 0;
      }
      .opportunity-rail {
        grid-template-columns: 1fr;
        grid-template-areas:
          "status"
          "meta"
          "fit"
          "actions";
      }
      .saved-actions .workspace-backup,
      .saved-actions .workspace-filter:disabled { display: none; }
    }

    @media (max-width: 480px) {
      .brand-row {
        gap: var(--av-spacing-1);
      }
      .brand h1 { font-size: 24px; }
      .hero-band {
        padding: 14px 12px 10px;
      }
      .topbar {
        gap: var(--av-spacing-1);
        margin-bottom: var(--av-spacing-2);
      }
      .brand {
        gap: var(--av-spacing-1);
      }
      .brand p {
        font-size: var(--av-text-xs);
        line-height: 1.42;
      }
      .focus-chip:last-child {
        display: none;
      }
      .hero-intro {
        font-size: var(--av-text-sm);
        line-height: 1.48;
      }
      .hero-actions {
        gap: var(--av-spacing-1);
      }
      .hero-actions > .button,
      .hero-pick-row > .button {
        min-height: var(--av-control-height-lg);
      }
      .utility-links {
        display: flex;
        gap: 6px var(--av-spacing-2);
        width: auto;
        justify-content: flex-start;
      }
      .sticky-actions {
        display: grid;
        grid-template-columns: 1fr;
        align-items: start;
      }
      .topbar-actions {
        width: 100%;
        justify-content: space-between;
      }
      .status-pill {
        min-height: var(--control-height-sm);
        justify-content: flex-start;
      }
      .lang-link {
        min-width: var(--av-control-height-lg);
        min-height: var(--av-control-height-lg);
      }
      .metric {
        min-height: 62px;
        padding: 10px;
      }
      .metric span {
        font-size: 10px;
        line-height: var(--av-leading-snug);
      }
      .metric strong { font-size: 22px; }
      .toolbar { gap: var(--av-spacing-1); }
      .button.tab {
        padding-left: var(--av-spacing-2);
        padding-right: var(--av-spacing-2);
      }
      .spotlight-footer {
        align-items: flex-start;
        flex-direction: column;
      }
      .pathway-footer {
        align-items: flex-start;
        flex-direction: column;
      }
      .focus-row {
        align-items: flex-start;
        gap: var(--av-spacing-1);
      }
      .opportunity p {
        -webkit-line-clamp: 2;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      html {
        scroll-behavior: auto;
      }
      *,
      *::before,
      *::after {
        animation-duration: 1ms !important;
        transition-duration: 1ms !important;
      }
    }
"""
