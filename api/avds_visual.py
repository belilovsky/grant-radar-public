"""AV DS 4.6 visual composition overrides for public QAZ.FUND pages."""

from __future__ import annotations

DASHBOARD_AVDS4_CSS = r"""
    /*
     * AV DS 4.6 public-catalog pass.
     * One clear starting point, quiet separators and compact controls.
     */
    :root {
      --qaz-hero: var(--qaz-brand-hero-start);
      --qaz-hero-muted: #d9e8e5;
      --qaz-hero-line: rgb(255 255 255 / 0.16);
      --qaz-hero-panel: rgb(2 61 66 / 0.86);
      --qaz-page: var(--qaz-brand-cream);
      --qaz-card-radius: 10px;
      --qaz-section-radius: 8px;
    }

    body {
      background: var(--qaz-page);
    }

    ::selection {
      background: color-mix(in oklab, var(--brand), white 72%);
      color: var(--ink);
    }

    .shell {
      width: min(1380px, calc(100% - 40px));
      padding: 20px 0 36px;
    }

    .hero-band {
      padding: clamp(26px, 3vw, 44px) clamp(24px, 4vw, 64px);
      margin-bottom: 14px;
      border: 1px solid rgb(230 242 240 / 0.2);
      border-radius: var(--qaz-card-radius);
      background: var(--qaz-hero);
      color: white;
      box-shadow: none;
    }

    .hero-band .topbar {
      margin-bottom: 0;
    }

    .hero-band .eyebrow {
      color: #b9ddd8;
      letter-spacing: 0.08em;
    }

    .hero-band .brand h1 {
      color: white;
      font-size: clamp(40px, 4.2vw, 60px);
    }

    .hero-band .hero-copy > .topbar .brand > p {
      display: block;
      max-width: 620px;
      margin: 0;
      color: #e9f1ef;
      font-size: clamp(17px, 1.45vw, 21px);
      line-height: 1.45;
    }

    .hero-grid {
      grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
      align-items: stretch;
      max-width: none;
      gap: clamp(24px, 4vw, 56px);
      margin-bottom: 0;
    }

    .hero-copy {
      align-content: center;
      gap: 18px;
      padding: 0;
    }

    .hero-intro {
      max-width: 50ch;
      color: #e9f1ef;
      font-size: clamp(18px, 1.5vw, 21px);
      line-height: 1.42;
    }

    .hero-band .hero-point {
      color: #d9e8e5;
    }

    .hero-band .hero-point-index {
      background: rgb(243 239 233 / 0.92);
      color: var(--qaz-brand-teal);
      box-shadow: inset 0 0 0 1px var(--qaz-brand-gold);
    }

    .hero-band .button.primary {
      border-color: #fffdfc;
      background: #fffdfc;
      color: var(--qaz-brand-ink);
      box-shadow: none;
    }

    .hero-band .button.primary:hover {
      border-color: var(--qaz-brand-gold-soft);
      background: var(--qaz-brand-gold-soft);
      color: var(--qaz-brand-ink);
    }

    .hero-stage {
      align-content: center;
      gap: 11px;
      padding: 18px;
      border: 1px solid var(--qaz-hero-line);
      border-radius: var(--qaz-section-radius);
      background: var(--qaz-hero-panel);
      box-shadow: none;
    }

    .hero-stage-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .hero-stage-eyebrow {
      color: var(--qaz-hero-muted);
    }

    .hero-stage-title {
      color: white;
      font-size: 20px;
    }

    .hero-stage .lang-switch {
      flex: 0 0 auto;
      gap: 2px;
    }

    .hero-stage .lang-link {
      min-height: 26px;
      padding-inline: 6px;
      color: var(--qaz-hero-muted);
    }

    .hero-stage .lang-link:hover,
    .hero-stage .lang-link:focus-visible {
      color: white;
    }

    .hero-stage .lang-link.active {
      color: white;
      box-shadow: inset 0 -2px 0 white;
    }

    .hero-pick-row {
      gap: 6px;
    }

    .hero-pick {
      min-height: 38px;
      padding: 7px 10px;
      border-color: var(--qaz-hero-line);
      border-radius: 6px;
      background: rgb(255 255 255 / 0.05);
      color: #fffdfc;
      font-size: 12px;
    }

    .hero-pick:hover,
    .hero-pick:focus-visible {
      border-color: rgb(255 255 255 / 0.34);
      background: rgb(255 255 255 / 0.12);
      color: white;
    }

    @media (min-width: 981px) {
      .hero-band .hero-actions {
        display: none;
      }
    }

    .hero-band .grid {
      gap: 0;
      border-top: 1px solid var(--qaz-hero-line);
    }

    .hero-band .metric {
      min-height: 66px;
      padding: 14px 18px 4px;
      border: 0;
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }

    .hero-band .metric + .metric {
      border-left: 1px solid var(--qaz-hero-line);
    }

    .hero-band .metric span {
      color: var(--qaz-brand-teal);
    }

    .hero-band .metric strong {
      color: var(--qaz-brand-ink);
      font-size: 28px;
    }

    .hero-band .metric.strong strong {
      color: var(--qaz-brand-teal-light);
    }

    .hero-band .metric.sources strong {
      color: var(--qaz-brand-gold);
    }

    .sticky-shell {
      display: none;
    }

    .sticky-bar {
      min-height: 50px;
      padding: 6px 10px;
      border-radius: var(--qaz-section-radius);
      background: rgb(255 255 255 / 0.94);
      box-shadow: 0 7px 22px rgb(15 23 42 / 0.07);
    }

    .utility-links {
      display: none;
    }

    .panel.primary {
      padding-top: 6px;
    }

    .panel-head {
      margin-bottom: 12px;
    }

    .panel-head h2 {
      font-size: clamp(27px, 2.3vw, 34px);
    }

    .panel-head p {
      max-width: 78ch;
      margin-top: 4px;
      font-size: 14px;
    }

    .preset-grid {
      padding: 14px;
      border-radius: var(--qaz-section-radius) var(--qaz-section-radius) 0 0;
      background: var(--panel);
    }

    .preset-group {
      gap: 7px;
      padding: 0 14px;
    }

    .preset-button {
      min-height: 32px;
      padding: 0 10px;
      border-radius: 6px;
      font-weight: 650;
    }

    .preset-button[aria-pressed="true"] {
      box-shadow: none;
    }

    .filters-shell {
      gap: 12px;
      margin-bottom: 10px;
      padding: 14px;
      border-radius: 0 0 var(--qaz-section-radius) var(--qaz-section-radius);
      box-shadow: none;
    }

    .advanced-filters {
      padding-top: 9px;
    }

    .advanced-filters > summary {
      min-height: 34px;
      padding: 0 9px;
      border-radius: 6px;
    }

    .saved-views {
      margin-bottom: 10px;
      padding: 9px 12px;
      border-radius: var(--qaz-section-radius);
      background: var(--panel);
    }

    .list {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      align-items: start;
    }

    .opportunity {
      height: auto;
      padding: 18px;
      border-radius: var(--qaz-card-radius);
      box-shadow: none;
    }

    .opportunity:hover {
      border-color: color-mix(in oklab, var(--brand), white 58%);
      box-shadow: 0 8px 24px rgb(15 23 42 / 0.07);
      transform: none;
    }

    .opportunity-main {
      grid-template-columns: minmax(0, 1fr);
      gap: 13px;
      height: auto;
    }

    .opportunity-content {
      align-content: start;
      gap: 10px;
      padding: 0;
    }

    .opportunity-heading {
      gap: 8px;
    }

    .opportunity h3 {
      font-size: clamp(18px, 1.55vw, 21px);
      line-height: 1.22;
    }

    .opportunity-summary {
      font-size: 14px;
      line-height: 1.5;
      -webkit-line-clamp: 2;
    }

    .opportunity-facts {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 18px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }

    .opportunity-facts > span {
      display: inline-flex;
      align-items: baseline;
      gap: 5px;
      min-width: 0;
    }

    .opportunity-fact-label {
      color: var(--muted);
    }

    .opportunity-facts strong {
      color: var(--ink);
      font-weight: 700;
      overflow-wrap: anywhere;
    }

    .tag {
      padding: 3px 7px;
      border-radius: 5px;
      font-size: 11px;
    }

    .opportunity-rail {
      grid-template-areas:
        "status"
        "meta"
        "fit"
        "actions";
      align-content: end;
      gap: 10px;
      margin-top: auto;
      padding: 12px 0 0;
      border: 0;
      border-top: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }

    .side {
      gap: 5px;
    }

    .score,
    .badge {
      min-height: 26px;
      padding-inline: 8px;
      font-size: 11px;
    }

    .score {
      min-width: 62px;
    }

    .meta-rows {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 7px 16px;
    }

    .meta-row {
      padding-top: 6px;
      font-size: 11px;
    }

    .fit-block {
      gap: 5px;
    }

    .fit-pill {
      min-height: 20px;
      padding-inline: 6px;
      font-size: 11px;
    }

    .card-actions,
    .card-actions-secondary {
      gap: 7px 12px;
    }

    .detail-link {
      min-height: 31px;
      padding: 0 9px;
      border-radius: 6px;
      font-size: 12px;
    }

    .more-link,
    .footer-funder-link {
      font-size: 12px;
    }

    .discovery-library,
    .trust-library {
      margin-top: 12px;
      border-radius: var(--qaz-section-radius);
      background: var(--panel);
      box-shadow: none;
    }

    .discovery-library > summary,
    .trust-library > summary,
    .funder-library > summary,
    .methodology-library > summary {
      min-height: 48px;
      padding: 11px 14px;
    }

    .discovery-library-body,
    .trust-library-body {
      padding: 0 14px 14px;
    }

    .site-footer {
      gap: 6px;
      margin-top: 18px;
      padding: 18px 4px 0;
      border-top: 1px solid var(--line);
      background: transparent;
    }

    @media (min-width: 1280px) {
      .preset-grid {
        grid-template-columns: 0.82fr 1.08fr 1.35fr;
        padding: 12px;
      }

      .preset-group {
        padding-inline: 12px;
      }
    }

    @media (min-width: 1440px) {
      .shell {
        width: min(1600px, calc(100% - 64px));
      }

      .hero-grid {
        grid-template-columns: minmax(0, 1fr) minmax(440px, 560px);
        gap: clamp(40px, 5vw, 72px);
      }
    }

    @media (min-width: 1600px) {
      .list {
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
      }
    }

    @media (min-width: 1920px) {
      .shell {
        width: min(1760px, calc(100% - 96px));
      }

      .hero-grid {
        grid-template-columns: minmax(0, 1fr) minmax(500px, 620px);
      }
    }

    @media (min-width: 2200px) {
      .shell {
        width: min(1920px, calc(100% - 160px));
      }
    }

    @media (max-width: 1120px) {
      .hero-grid {
        grid-template-columns: minmax(0, 1fr) minmax(320px, 0.84fr);
      }

      .list {
        grid-template-columns: 1fr;
      }

      .opportunity-main {
        grid-template-columns: minmax(0, 1fr) minmax(300px, 0.44fr);
      }

      .opportunity-rail {
        margin-top: 0;
        padding: 13px;
        border: 1px solid var(--line-subtle);
        border-radius: var(--qaz-section-radius);
        background: var(--panel-subtle);
      }
    }

    @media (max-width: 820px) {
      .shell {
        width: min(100%, calc(100% - 20px));
        padding:
          calc(66px + env(safe-area-inset-top))
          0
          calc(82px + env(safe-area-inset-bottom));
      }

      .mobile-app-brand,
      .mobile-lang-switch a,
      .hero-actions .button,
      .hero-pick,
      .preset-button,
      .detail-link,
      .advanced-filters > summary {
        min-height: var(--av-control-height-lg);
      }

      .mobile-app-brand {
        align-content: center;
      }

      .mobile-lang-switch a {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: var(--av-control-height-lg);
      }

      .mobile-icon-button {
        width: var(--av-control-height-lg);
        min-width: var(--av-control-height-lg);
        height: var(--av-control-height-lg);
        min-height: var(--av-control-height-lg);
      }

      .hero-copy > .topbar .brand h1 {
        font-size: 32px;
      }

      .hero-band {
        padding: 24px 20px 18px;
      }

      .hero-grid {
        grid-template-columns: 1fr;
        gap: 20px;
      }

      .hero-stage {
        padding: 14px;
      }

      .hero-band .metric {
        min-height: 58px;
        padding: 12px 10px 2px;
      }

      .hero-band .metric strong {
        font-size: 23px;
      }

      .opportunity-main {
        grid-template-columns: 1fr;
      }

      .opportunity-rail {
        margin-top: auto;
        padding: 11px 0 0;
        border: 0;
        border-top: 1px solid var(--line-subtle);
        border-radius: 0;
        background: transparent;
      }

      .saved-views {
        display: none;
      }
    }

    @media (max-width: 560px) {
      .hero-band {
        padding-inline: 16px;
      }

      .hero-band .hero-actions {
        display: none;
      }

      .hero-stage .hero-lang-switch {
        display: none;
      }

      .hero-copy > .topbar .brand h1 {
        font-size: 30px;
      }

      .hero-intro {
        font-size: 16px;
      }

      .hero-pick-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .hero-pick:last-child {
        grid-column: 1 / -1;
      }

      .hero-band .grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .hero-band .metric span {
        font-size: 10px;
      }

      .hero-band .metric strong {
        font-size: 20px;
      }

      .opportunity {
        padding: 15px;
      }

      .opportunity h3 {
        font-size: 18px;
      }
    }
"""


OPPORTUNITY_AVDS4_CSS = r"""
    :root {
      --qaz-detail-hero: var(--qaz-brand-hero-start);
      --qaz-detail-muted: #d9e8e5;
      --qaz-detail-line: rgb(255 255 255 / 0.16);
      --qaz-detail-page: var(--qaz-brand-cream);
      --qaz-detail-radius: 10px;
    }

    body {
      background: var(--qaz-detail-page);
    }

    .shell {
      width: min(1320px, calc(100% - 40px));
      padding: 18px 0 34px;
    }

    .topbar {
      position: static;
      min-height: 42px;
      margin-bottom: 12px;
      padding: 0 4px;
      border: 0;
      border-radius: 0;
      background: transparent;
      box-shadow: none;
      backdrop-filter: none;
    }

    .breadcrumbs {
      min-width: 0;
      overflow: hidden;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .breadcrumbs span:last-child {
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .hero {
      margin-bottom: 0;
      padding: clamp(28px, 4vw, 46px);
      border: 1px solid rgb(230 242 240 / 0.2);
      border-radius: var(--qaz-detail-radius);
      background: var(--qaz-detail-hero);
      color: white;
      box-shadow: none;
    }

    .hero-grid {
      grid-template-columns: minmax(0, 1.55fr) minmax(280px, 0.55fr);
      gap: clamp(28px, 4vw, 52px);
      align-items: center;
    }

    .hero .eyebrow {
      color: #b9ddd8;
    }

    .hero h1 {
      max-width: 25ch;
      color: white;
      font-size: clamp(36px, 4vw, 56px);
      line-height: 1.01;
    }

    .summary {
      max-width: 62ch;
      color: #e9f1ef;
      font-size: clamp(16px, 1.35vw, 19px);
      line-height: 1.48;
    }

    .hero-actions {
      margin-top: 18px;
    }

    .hero .button {
      min-height: 44px;
      border-color: var(--qaz-detail-line);
      border-radius: 6px;
      box-shadow: none;
    }

    .hero .button:hover {
      transform: none;
      box-shadow: none;
    }

    .hero .button.primary {
      border-color: #fffdfc;
      background: #fffdfc;
      color: var(--qaz-brand-ink);
    }

    .hero .button.slim {
      background: rgb(255 255 255 / 0.07);
      color: white;
    }

    .hero-action-status {
      color: var(--qaz-brand-teal-light);
    }

    .hero-stats {
      padding: 16px;
      border-color: var(--qaz-detail-line);
      border-radius: 8px;
      background: rgb(255 255 255 / 0.06);
      box-shadow: none;
    }

    .hero-stats > div {
      padding: 10px 0;
      border-color: var(--qaz-detail-line);
    }

    .hero-stats > div:first-child {
      display: none;
    }

    .hero-stats strong {
      color: white;
      font-size: 15px;
    }

    .hero-stats .status-note {
      color: var(--qaz-detail-muted);
    }

    .hero .pills {
      margin: 16px 0 0;
      padding: 0;
    }

    .hero .pill {
      min-height: 28px;
      padding: 0 9px;
      border-color: var(--qaz-detail-line);
      border-radius: 5px;
      background: rgb(255 255 255 / 0.08);
      color: #fffdfc;
      font-size: 12px;
    }

    .detail-flow {
      margin-top: 12px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: var(--qaz-detail-radius);
      background: var(--surface);
    }

    .content-grid {
      grid-template-columns: minmax(0, 1.45fr) minmax(260px, 0.55fr);
      gap: 0;
      padding: 0;
    }

    .content-grid--single,
    .content-grid--single .section-stack {
      grid-template-columns: minmax(0, 1fr);
    }

    .section-stack {
      gap: 0;
    }

    .section-card {
      border: 0;
      border-radius: 0;
      box-shadow: none;
    }

    .source-disclosure summary {
      min-height: 54px;
      padding: 14px 20px;
    }

    .source-disclosure-title {
      font-size: 18px;
    }

    .source-disclosure-action {
      border-radius: 5px;
    }

    .source-excerpts {
      padding: 18px 20px 22px;
    }

    .sidebar-card {
      position: static;
      padding: 20px;
      border: 0;
      border-left: 1px solid var(--line-subtle);
      border-radius: 0;
      background: var(--surface-subtle);
      box-shadow: none;
    }

    .decision-check-section,
    .prepare-section,
    .apply-section,
    .related-section {
      gap: 16px;
      margin-top: 0;
      padding: 24px 26px 26px;
      border: 0;
      border-top: 1px solid var(--line);
      border-radius: 0;
      background: var(--surface);
      box-shadow: none;
    }

    .decision-check-head,
    .prepare-head,
    .apply-head,
    .related-head {
      gap: 4px;
      max-width: 72ch;
    }

    .decision-check-head h2,
    .prepare-head h2,
    .apply-head h2,
    .related-head h2 {
      font-size: clamp(22px, 2vw, 28px);
      letter-spacing: -0.02em;
    }

    .decision-check-head p,
    .prepare-head p,
    .apply-head p,
    .related-head p {
      font-size: 14px;
    }

    .decision-check-grid,
    .prepare-grid,
    .apply-list {
      gap: 18px;
    }

    .decision-check-card,
    .prepare-card,
    .prepare-card:first-child,
    .apply-step,
    .apply-step:first-child {
      min-height: auto;
      padding: 13px 0 0;
      border: 0;
      border-top: 2px solid var(--line);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }

    .decision-check-card:first-child,
    .prepare-card:first-child {
      border-top-color: var(--brand);
    }

    .decision-check-label {
      color: var(--brand);
      font-family: var(--font-sans);
      letter-spacing: 0.035em;
    }

    .prepare-index,
    .apply-index {
      width: 26px;
      height: 22px;
      border-radius: 4px;
    }

    .apply-step {
      grid-template-columns: 26px minmax(0, 1fr);
      gap: 9px;
    }

    .related-section {
      background: var(--surface-subtle);
    }

    .related-grid {
      gap: 10px;
    }

    .related-card {
      padding: 16px;
      border-radius: 8px;
      box-shadow: none;
    }

    .related-reason,
    .related-deadline {
      min-height: 26px;
      padding-inline: 8px;
      border-radius: 5px;
    }

    .site-footer {
      margin-top: 14px;
      padding: 18px 4px 0;
      border: 0;
      border-top: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
    }

    @media (max-width: 900px) {
      .hero-grid {
        grid-template-columns: 1fr;
      }

      .hero-stats {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .hero-stats > div:nth-child(2) {
        grid-column: auto;
      }

      .content-grid {
        grid-template-columns: 1fr;
      }

      .sidebar-card {
        border-left: 0;
        border-top: 1px solid var(--line-subtle);
      }

      .decision-check-grid,
      .prepare-grid,
      .apply-list {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .related-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 640px) {
      .shell {
        width: min(100%, calc(100% - 20px));
        padding-top: 10px;
      }

      .topbar {
        top: auto;
        padding: 0 2px;
      }

      .hero {
        padding: 24px 18px;
        border-left-width: 3px;
        border-radius: 8px;
      }

      .hero h1 {
        font-size: 32px;
      }

      .hero-stats {
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        padding: 12px 14px;
      }

      .hero-stats > div:nth-child(2) {
        grid-column: auto;
      }

      .hero-stats > div {
        min-width: 0;
        padding: 4px;
        border: 0;
        border-left: 1px solid var(--qaz-detail-line);
      }

      .hero-stats > div:nth-child(2) {
        border-left: 0;
      }

      .hero-stats strong,
      .hero-stats .status-note {
        overflow-wrap: anywhere;
      }

      .hero-stats strong {
        font-size: 13px;
        line-height: 1.15;
      }

      .hero .pills {
        gap: 5px;
      }

      .detail-flow {
        border-radius: 8px;
      }

      .decision-check-section,
      .prepare-section,
      .apply-section,
      .related-section {
        padding: 20px 18px 22px;
        border-radius: 0;
      }

      .decision-check-grid,
      .prepare-grid,
      .apply-list {
        grid-template-columns: 1fr;
        gap: 14px;
      }

      .source-disclosure summary {
        padding: 14px 16px;
      }

      .source-excerpts,
      .sidebar-card {
        padding: 16px;
      }
    }
"""
