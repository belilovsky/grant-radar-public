# QAZ.FUND language surface

QAZ.FUND uses `kk`, `ru`, and `en` as canonical locales on the public query
surface (`?lang=`). Legacy and provider spellings are accepted only at the
input boundary and are normalized before rendering or content lookup:

- Kazakh: `kk`, `kk-KZ`, `kz`, `kaz`, `kaz_Cyrl`, `kazakh`;
- Russian: `ru`, `ru-RU`, `rus`, `russian`;
- English: `en`, `en-US`, `eng`, `english`.

The dashboard, opportunity/funder pages, insights, source status, public
explanations, branded 404 and the noindex operator shell all expose the same
three locales. On a page with no reviewed Kazakh copy, a compact notice makes
the source-language fallback explicit. The source payload remains separate
from localized display fields. Missing localized content may use a source or
safe fallback, but that fallback must not be described as an editor-approved
translation. Source language and translation availability are data properties,
not a reason to mutate a source record.

The public insights page has curated Kazakh interface copy for its metrics and
charts. Opportunity descriptions and source excerpts remain in their published
language until a native-language editorial pass approves the corresponding
`raw.i18n.kk` fields.

The machine-readable contract is [`language-surface.json`](language-surface.json)
and is referenced from `docs/qazstack/consumer-contract.json`.

## Runtime readiness boundary

The public opportunity endpoint must be checked separately from the UI
dictionary contract. The aggregate-only runtime guard measures locale bucket
presence, source-language metadata and approval fields without printing item
text:

```bash
python3 scripts/check_public_translation_readiness.py
python3 -m pytest -q tests/test_public_translation_readiness.py
```

Missing `kk` content is reported as fallback/source behavior, never as an
approved translation. Remote write and automatic memory promotion remain
disabled until reviewer, quality and memory-eligibility metadata are explicit.
