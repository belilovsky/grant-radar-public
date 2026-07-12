# Taxonomy

Canonical taxonomy for `grant-radar`.

This document defines the controlled vocabulary used to classify opportunities, sources, eligibility, geography, and operational status.

The goal is to make ingestion deterministic, filtering stable, search useful, and scoring explainable.

## Design principles

- use small, explicit enums where possible
- preserve raw source text separately from normalized values
- separate primary classification from secondary tags
- allow unknown / unclassified states without breaking ingestion
- avoid source-specific labels in canonical fields

## Core entities

The taxonomy is applied to at least four layers:

- source
- opportunity
- run
- parser status

## Source taxonomy

### source_kind

Primary classification of the source itself.

Allowed values:

- `grants_portal`
- `accelerator_platform`
- `cloud_program`
- `donor_site`
- `multilateral_bank`
- `government_portal`
- `procurement_portal`
- `foundation_site`
- `corporate_program`
- `ngo_program`
- `un_agency`
- `university_program`
- `media_watch`
- `manual_feed`
- `other`

### source_scope

Geographic or jurisdictional scope of the source.

Allowed values:

- `country`
- `regional`
- `global`
- `mixed`

### source_access_type

How the data is obtained.

Allowed values:

- `html_static`
- `html_dynamic`
- `rss`
- `api`
- `pdf`
- `email`
- `manual`
- `mixed`

### source_priority

Operational importance of the source.

Allowed values:

- `tier_1`
- `tier_2`
- `tier_3`

### source_status

Current operational state.

Allowed values:

- `planned`
- `active`
- `paused`
- `broken`
- `deprecated`

## Opportunity taxonomy

### opportunity_type

Primary type of opportunity.

Allowed values:

- `grant`
- `accelerator`
- `cloud_credits`
- `tender`
- `rfp`
- `challenge`
- `competition`
- `fellowship`
- `scholarship`
- `technical_assistance`
- `partnership`
- `pilot_program`
- `training_program`
- `award`
- `other`

### funding_instrument

How value is delivered.

Allowed values:

- `cash_grant`
- `subsidy`
- `cost_reimbursement`
- `loan_guarantee`
- `preferential_financing`
- `leasing`
- `tax_benefit`
- `equity_free_program`
- `cloud_credits`
- `technical_support`
- `procurement_contract`
- `prize_money`
- `mixed`
- `unknown`

### opportunity_status

Lifecycle state of the opportunity.

Allowed values:

- `draft`
- `open`
- `upcoming`
- `closing_soon`
- `closed`
- `archived`
- `unknown`

### deadline_status

Computed deadline state.

Allowed values:

- `no_deadline_found`
- `deadline_future`
- `deadline_soon`
- `deadline_today`
- `deadline_passed`
- `rolling`
- `unknown`

Recommended threshold:

- `deadline_soon` = 14 calendar days or fewer

## Thematic taxonomy

### sector_primary

Exactly one preferred primary sector when possible.

Allowed values:

- `ai`
- `edtech`
- `govtech`
- `digital_public_infrastructure`
- `digital_skills`
- `civictech`
- `healthtech`
- `climatetech`
- `agritech`
- `fintech`
- `general_innovation`
- `other`

### sector_tags

Multi-value tags for secondary classification.

Allowed tags:

- `ai`
- `genai`
- `machine_learning`
- `edtech`
- `school_systems`
- `teacher_training`
- `student_support`
- `curriculum`
- `assessment`
- `higher_education`
- `govtech`
- `public_sector`
- `digital_identity`
- `payments`
- `interoperability`
- `procurement`
- `civictech`
- `anti_corruption`
- `digital_skills`
- `startup_support`
- `business_support`
- `domestic_support`
- `state_program`
- `preferential_financing`
- `leasing`
- `agrotech`
- `vettech`
- `ecotech`
- `agriculture`
- `livestock`
- `animal_health`
- `industry`
- `export`
- `trade`
- `investment`
- `private_equity`
- `venture`
- `science`
- `civil_society`
- `cloud_infrastructure`
- `research`
- `inclusion`
- `stem`
- `youth`
- `women_in_tech`
- `data_governance`
- `cybersecurity`

## Eligibility taxonomy

### applicant_type

Who can apply.

Allowed values:

- `for_profit`
- `nonprofit`
- `ngo`
- `university`
- `school`
- `government`
- `municipality`
- `individual`
- `consortium`
- `mixed`
- `unknown`

### stage_fit

Best-fit company or project stage.

Allowed values:

- `idea`
- `prototype`
- `pilot`
- `early_stage`
- `growth`
- `institutional`
- `mixed`
- `unknown`

### partner_requirement

Whether another entity is required.

Allowed values:

- `none`
- `nonprofit_required`
- `government_required`
- `university_required`
- `local_partner_required`
- `consortium_required`
- `recommended`
- `unknown`

### commercial_eligibility

For commercial startup relevance.

Allowed values:

- `commercial_allowed`
- `commercial_limited`
- `commercial_not_allowed`
- `unknown`

## Geography taxonomy

### region_scope

Allowed values:

- `kazakhstan`
- `uzbekistan`
- `kyrgyzstan`
- `tajikistan`
- `turkmenistan`
- `central_asia_regional`
- `mena`
- `europe`
- `global`
- `other`

### central_asia_eligibility

Operational yes/no/maybe field.

Allowed values:

- `yes`
- `no`
- `unclear`

### country_mode

How geography is represented.

Allowed values:

- `single_country`
- `multi_country`
- `regional`
- `global`
- `unknown`

## Funding taxonomy

### amount_type

Allowed values:

- `fixed_amount`
- `range`
- `credits`
- `in_kind`
- `not_disclosed`
- `unknown`

### currency_code

Use ISO currency code when known.

Examples:

- `USD`
- `EUR`
- `GBP`
- `KZT`
- `UZS`
- `KGS`
- `TJS`
- `TMT`

If not parseable, store raw currency text separately.

## Language taxonomy

### language_primary

Allowed values:

- `en`
- `ru`
- `kk`
- `uz`
- `ky`
- `tg`
- `tr`
- `mixed`
- `other`
- `unknown`

## Normalization confidence

### parse_confidence

Allowed values:

- `high`
- `medium`
- `low`

### classification_confidence

Allowed values:

- `high`
- `medium`
- `low`

## Review workflow taxonomy

### review_status

Allowed values:

- `auto_accepted`
- `needs_review`
- `reviewed`
- `rejected`
- `archived`

### review_reason

Common values:

- `ambiguous_eligibility`
- `ambiguous_deadline`
- `duplicate_suspected`
- `unclear_amount`
- `weak_relevance`
- `important_source_low_confidence`
- `parser_anomaly`

## Deduplication taxonomy

### dedup_strategy

Allowed values:

- `url_exact`
- `canonical_url`
- `title_plus_source`
- `title_plus_deadline`
- `manual_merge`
- `unknown`

### duplicate_status

Allowed values:

- `unique`
- `duplicate_exact`
- `duplicate_probable`
- `merged`
- `unknown`

## Scoring taxonomy

### priority_bucket

Allowed values:

- `p1`
- `p2`
- `p3`

Suggested meaning:

- `p1` – direct fit and actionable now
- `p2` – relevant but partner-dependent or uncertain
- `p3` – weak fit or watchlist only

### urgency_bucket

Allowed values:

- `urgent`
- `this_week`
- `this_month`
- `later`
- `unknown`

## Run taxonomy

### run_status

Allowed values:

- `started`
- `success`
- `partial_success`
- `failed`
- `skipped`

### error_type

Common normalized values:

- `network_error`
- `parse_error`
- `schema_error`
- `auth_error`
- `rate_limit`
- `empty_result`
- `unexpected_markup`
- `unknown_error`

## Recommended raw vs normalized fields

Always preserve these pairs where possible:

- `deadline_raw` + `deadline_at`
- `amount_raw` + `amount_min` / `amount_max`
- `eligibility_raw` + normalized eligibility fields
- `source_country_raw` + normalized geography fields
- `status_raw` + `opportunity_status`

## Tagging rules

### Primary classification rules

- each opportunity gets exactly one `opportunity_type`
- each opportunity gets at most one `sector_primary`
- secondary tags go to `sector_tags`
- if unsure, use `other` or `unknown` rather than inventing values

### Naming rules

- use lowercase snake_case for all enums
- avoid spaces and punctuation in canonical values
- avoid source-branded terms in normalized fields
- keep source-specific wording in raw text fields only

## Minimal required fields for ingestion

Each opportunity should have at least:

- `title`
- `source_name`
- `source_url`
- `opportunity_type`
- `opportunity_status`
- `central_asia_eligibility`
- `scraped_at`
- `dedup_key`

## Example normalized record

```json
{
  "title": "Google for Startups Accelerator: Middle East, North Africa and Turkey",
  "source_name": "Google for Startups",
  "source_kind": "accelerator_platform",
  "opportunity_type": "accelerator",
  "funding_instrument": "equity_free_program",
  "sector_primary": "ai",
  "sector_tags": ["ai", "startup_support"],
  "commercial_eligibility": "commercial_allowed",
  "partner_requirement": "none",
  "region_scope": "central_asia_regional",
  "central_asia_eligibility": "yes",
  "opportunity_status": "open",
  "parse_confidence": "high",
  "classification_confidence": "high",
  "priority_bucket": "p1"
}
```

## Future extensions

Future taxonomy additions may include:

- beneficiary age group
- education level
- procurement method
- donor family
- SDG mapping
- responsible AI / safety tags
- multilingual search synonyms
