# AVDS visual uplift — QAZ.FUND — 2026-08-23

Status: **код готов · local-only**. The result has not been deployed or
presented as live-public evidence.

Follow-up audit evidence was taken from committed base revision
`6160edd5839ecd7387dd565687a939ee3c8bc7a7` plus one uncommitted
source-wording label remediation. The follow-up did not alter the visual
adapter, shared CSS or route composition.

## Diagnosis

Key route: `/?lang=ru`, anonymous catalogue-ready state, synthetic
production-like fixture. The primary task is to narrow the catalogue and open
an official source; success is a visible active filter or an opportunity card.
The teal brand, ornament, source-first card metadata and compact operational
tone were retained. Before evidence showed a large first frame, generic labels
on real filters, and all topic chips competing with the first results.

## Decisions

| Category | User-facing change | AVDS semantic contract | Before / after | Acceptance |
|---|---|---|---|---|
| Primary journey | Each quick filter now names its actual outcome. `Стартапам` applies the startup filter and reduces the local fixture from 4 to 2 cards. | Labelled Button group and FilterStateSummary | `output/playwright/qazfund-home-before-1440.png` → `output/playwright/qazfund-home-after-1440.png` | active filter and result summary observed |
| Hierarchy / composition | The desktop hero is shorter, its task chooser uses a three-column action row, and the catalogue begins higher. | PageHeader, Button group and section rhythm | `output/playwright/qazfund-home-before-1440.png` → `output/playwright/qazfund-home-after-1440.png` | one H1, no overlap or console error |
| Density / progressive disclosure | Optional topic refinement is collapsed behind an accessible `Тема` disclosure; audience, format and search remain directly available. On compact screens its summary has a 44 px minimum touch target. | FilterChipRow and progressive disclosure | `output/playwright/qazfund-home-before-1440.png` → `output/playwright/qazfund-home-after-1440.png` | keyboard-visible native summary; no overflow |
| Provenance / locale boundary | The preparation workspace now calls an untranslated official name and eligibility text `Source title` / `Source requirements` (and the RU/KK equivalents), rather than presenting it as a broken interface translation. | PublicSummaryStrip and evidence-source boundary | local pre-fix snapshot `page-2026-08-23T15-34-15-047Z.yml` → `output/playwright/qazfund-prepare-kk-after-mobile.png` | the compact KK surface retains its source text, names its provenance, and has no overflow |

## Browser evidence

- AVDS acceptance ledger: one desktop route/state cell passed with stylesheet,
  JavaScript, H1, overflow, console and visual-craft checks.
- Browser matrix: six primary RU surfaces at 393×852, 768×1024, 1440×960,
  320×800 and 1920×1080: 30/30 checks passed. The RU/KK/EN home locale matrix
  also passed 15/15. Neither run found console errors, serious/critical axe
  findings or undeclared horizontal overflow.
- Follow-up current-candidate matrix: the same six RU surfaces at compact and
  desktop widths passed 12/12 with the same console, axe and overflow checks.
- Final current-candidate matrix: ten public RU surfaces (catalogue, status,
  media, comparison, insights, embed, opportunity, preparation, funder and
  comparison-with-selection) across 393×852, 768×1024, 1440×960, 320×800 and
  1920×1080 passed 50/50. The preparation workspace also retained its
  browser-only autosave probe.
- Manual compact evidence for `prepare?lang=kk` is
  `output/playwright/qazfund-prepare-kk-after-mobile.png`; source wording,
  focusable controls, the collapsed workflow, and the browser-only boundary
  were visually inspected.
- Matched mobile before/after evidence is in
  `output/playwright/qazfund-home-before-393.png` and
  `output/playwright/qazfund-home-after-393.png`.
- At 393 px, opening the filter sheet exposes the collapsed topic control;
  `output/playwright/qazfund-topic-touch-393.png` records its 44 px target.

The generated acceptance JSON and screenshots remain deliberately ignored local
evidence; the committed ledger and craft/anti-generative audits describe their
scope and result. A production claim requires a separately authorised release
and a fresh browser run against the exact deployed SHA.
