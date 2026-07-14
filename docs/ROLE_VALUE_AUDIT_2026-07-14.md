# QAZ.FUND role and public-value audit – 2026-07-14

## Purpose

This pass evaluates QAZ.FUND as a daily working tool, not as a technical
demonstration. The review covers five perspectives: analyst, journalist,
editor, lawyer, and public-sector employee.

The common job is simple: find an opportunity, understand whether it deserves
attention, preserve the evidence, and hand the result to another person without
losing the source or the remaining verification work.

## What was unclear

The catalog already supported saved filters, shareable URLs, CSV export,
calendar export, local workflow stages, funder profiles, source status, and
public detail pages. Several of those capabilities were hidden behind internal
labels such as “Collections”, “My work”, and “Export”. The first screen also
repeated audience presets already available in the catalog instead of exposing
the tasks people return to every day.

The product therefore looked narrower than it was. A new visitor could find a
card but might not discover how to turn it into a reproducible selection,
working brief, deadline calendar, or review handoff.

## Role map

| Role | Main question | Useful output | Required caution |
|---|---|---|---|
| Analyst | What is available and how can I reproduce the result? | Filtered URL, structured fields, CSV | A relevance score is a ranking heuristic, not a program rating |
| Journalist | What can I safely report and cite? | Copyable working brief, official URL, source profile | Record the date of the actual source check |
| Editor | Which statements are confirmed and which still need checking? | Clean summary plus explicit verification list | Do not turn inferred eligibility into a factual claim |
| Lawyer | Which conditions determine participation? | Applicant, jurisdiction, deadline, documents, submission route | QAZ.FUND is not a legal opinion and does not confirm eligibility |
| Public-sector employee | How do I prepare and circulate a Kazakhstan-focused note? | Reproducible selection, CSV, calendar, official source | Procurement documents and amendments remain authoritative |

## Implemented changes

1. The first-screen quick start is now task-based: find support, check a
   program, review deadlines, open Kazakhstan support, or open procurement.
2. The three product statements now describe concrete outputs: a reproducible
   filtered link, a working brief, and table/calendar export.
3. Working tools are named by outcome: saved items, saved filters, shared
   results, CSV table, deadline calendar, and workspace backup.
4. The methodology section now contains a compact role guide for all five
   perspectives.
5. Each public opportunity page can copy a structured working brief containing
   only fields already present in the card and links to the official source and
   application route.
6. Each detail page now states the verification boundary for eligibility,
   current terms, procurement documents, and publication or internal handoff.

## QazStack opportunities

The cheapest useful additions are already supported locally and should remain
product features for now:

- saved, shareable filter state;
- CSV and iCalendar export;
- deterministic Kazakhstan and Central Asia relevance;
- source freshness and structured status;
- localized content cleanup;
- public OpenAPI, `llms.txt`, and discovery metadata.

The next platform-level candidates are narrow contracts, not new screens:

- shared evidence metadata: source, checked time, status, and limitation;
- reusable report export for a saved selection;
- Kazakhstan entity and region normalization;
- source-change notifications after a real notification channel exists.

Do not add accounts, alerts, a legal eligibility verdict, or generated evidence
until storage, ownership, delivery, and audit history are implemented.

## Editorial and legal boundary

QAZ.FUND is a navigator and working index. It does not award funding, accept
applications, confirm eligibility, or replace current official terms. This is
especially important for procurement, where the current documentation, lots,
qualification requirements, attachments, amendments, and portal state may
change after a card is indexed.

Official references used for this review:

- [Current Kazakhstan public procurement law](https://adilet.zan.kz/rus/docs/Z2400000106)
- [Unified procurement portal](https://zakup.gov.kz/)
- [Kazakhstan public-service register](https://egov.kz/cms/ru/articles/register_public_services)

## Deferred decisions

- Email or messenger alerts require a real delivery and consent model.
- Legal or eligibility scoring requires an approved legal methodology and
  versioned source evidence.
- Cross-opportunity comparison should be added only when field coverage is
  high enough to avoid comparing missing values as facts.
- Automatically generated press or service notes need an editorial review and
  provenance contract before public release.

## Validation target

- A first-time user can reach a useful result from a task button.
- The exact result set can be shared as a URL.
- A card produces a copyable brief without inventing missing values.
- The brief contains the official source and a clear verification caveat.
- RU and EN present the same product logic.
- Existing filters, saved work, exports, source status, and public pages remain
  functional on desktop and mobile.
