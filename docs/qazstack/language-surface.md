# QAZ.FUND language surface

QAZ.FUND uses `kk`, `ru`, and `en` as canonical locales on the public query
surface (`?lang=`). Legacy and provider spellings are accepted only at the
input boundary and are normalized before rendering or content lookup:

- Kazakh: `kk`, `kk-KZ`, `kz`, `kaz`, `kaz_Cyrl`, `kazakh`;
- Russian: `ru`, `ru-RU`, `rus`, `russian`;
- English: `en`, `en-US`, `eng`, `english`.

The dashboard, opportunity/funder pages, public explanations, branded 404 and
the noindex operator shell all expose the same three locales. The source
payload remains separate from localized display fields. Missing localized
content may use a source or safe fallback, but that fallback must not be
described as an editor-approved translation. Source language and translation
availability are data properties, not a reason to mutate a source record.

The machine-readable contract is [`language-surface.json`](language-surface.json)
and is referenced from `docs/qazstack/consumer-contract.json`.
