# Public data provenance contract

Version: `provenance.v1`  
Introduced: 2026-08-04

QAZ.FUND publishes a small provenance profile inside every public opportunity
payload as `raw.provenance`. The same profile is present in the full JSON API,
the compact dashboard response, NDJSON export and opportunity detail API.

The profile is a trust signal, not a legal eligibility decision. A direct link
to an official page is labelled `sourced`; it is not silently promoted to
`verified`.

## Fields

| Field | Meaning |
| --- | --- |
| `schema_version` | Version of this contract. |
| `source` | Adapter/source identifier. |
| `source_url` | Direct public page used by the record. |
| `evidence_state` | QazStack evidence state: `sourced`, `verified`, `archival`, `compiled` or `unlinked`. |
| `evidence_basis` | Public reasons for the state, without source HTML. |
| `observed_at` | Time at which the record was observed by the parser. This is not a verification claim. |
| `last_verified_at` | Explicit source or editorial check timestamp, only when supplied by the adapter. It is never copied from `observed_at`. |
| `source_language` | Best available language of the original source content. |
| `source_language_basis` | `explicit`, `detail` or `record_languages`. |
| `status` | Normalized source/lifecycle status, or `unknown`. |
| `deadline_confidence` | `supported`, `reported` or `unknown`. |
| `amount_confidence` | `supported`, `reported` or `unknown`. |
| `missing_metadata` | Trust metadata that still needs a source or editorial addition. |

## Confidence rules

- `supported` means the adapter retained source-level evidence such as a raw
  deadline/amount, policy or explicit source field.
- `reported` means the normalized field exists but no separate source-level
  evidence was retained.
- `unknown` means the field is absent or cannot be tied to a source-level
  signal.

The profile never generates a deadline, amount, status or language through an
LLM. The parser may infer a display language from a single record language only
as `source_language_basis=record_languages`; this remains metadata, not a
translation approval.

## Consumer rules

Consumers should:

1. show the direct source link next to the user-facing action;
2. show `observed_at` and `last_verified_at` as different facts;
3. treat `unknown` confidence as a request to check the source;
4. preserve `schema_version` and `missing_metadata` in downstream archives;
5. avoid converting `sourced` into a claim that the program is open, eligible or
   likely to award funding.

QazPipe may transport this profile as public provenance. QazLake may archive it
with the public record. QazCompute may use it as a feature envelope, but the
profile itself is not a decision-ready eligibility result.

Для истории изменений нормализованных публичных полей используется отдельный
контракт [`HISTORY_CONTRACT.md`](HISTORY_CONTRACT.md). `observed_at` в истории
означает момент обнаружения изменения и не заменяет `last_verified_at`.
