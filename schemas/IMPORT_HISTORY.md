# Real provider-history import contract

Use the documented schema and CLI; new providers do not require model-code edits. Admission does not automatically make a representative market index.

## Input 1: normalized quote CSV

Use **exactly** the header in `outputs/quotes.csv`. The machine-readable row contract is `schemas/quotes.schema.json`; CSV numeric fields are parsed to their indicated JSON types. `gpu_index.data.Quote.validate()` enforces runtime units, terms, dates, positive rates, required descriptors and provenance. A quote describes a complete rentable instance hour. Host bundle, GPU memory/device count and interconnect must be explicit. Canonicalize descriptors consistently from cited sources; do not label an unknown interconnect as verified.

Each row requires provider/category, region, GPU/memory, host bundle, GPU count, interconnect, OS/tenancy, commitment/duration, currency/unit/rate, availability evidence, URL/SHA256/hash scope, observation/publication/effective dates, effective month, launch date, license/rights note, evidence/freshness, instance, SKU and rate code. A provider lacking SKU/rate codes may use an immutable source-native service/rate identifier in those fields with its meaning documented; never use a mutable display name alone. The prototype does not derive market shares from listing counts.

For monthly model import, evidence must be `OBSERVED`, freshness `verified_capture`, launch date nonempty and no later than effective date, GPU memory/interconnect known, source-rights manifest qualified and category hyperscaler/neocloud. Quote listing evidence does not establish capacity; the separate availability field must retain that limitation. Endpoint rows can be valid observed-index inputs while failing stricter monthly-model admission.

Run the inventory first:

```sh
python3 -m gpu_index eligibility provider_quotes.csv --out eligibility
# With the source manifest after its terms have actually been reviewed:
python3 -m gpu_index eligibility provider_quotes.csv --rights source_rights.json --out eligibility
```

`data_eligibility.csv` gives deterministic `quote_id`s and record exclusions. IDs hash the complete normalized quote with canonical numeric types. Changing price, dates or provenance changes the quote ID. `configuration_id` instead hashes service-cell descriptors, excluding prices/dates; it preserves multiple bundles of the same architecture.

## Input 2: explicit anchor bindings CSV

Exactly two columns:

```csv
quote_id,anchor_quote_id
<inventory quote ID>,<inventory AWS quote ID>
```

The anchor must be a qualified AWS row in the **same effective month**, with identical canonical GPU, per-device memory, GPU count, interconnect, OS, commitment/duration, currency and unit. Host/provider differences remain in the source cells and must be economically qualified before creating the bindings. This version deliberately offers no automatic cross-memory, quality or host-bundle adjustment. AWS can anchor itself. A matched AWS anchor is a model conditioning variable, not independent validation or proof of one-for-one transmission.

No placeholder zero prices, pre-launch hardware, unverified refreshes, forward filling, approximate GPU-name matching or silent term conversions. Import one on-demand/spot/term-duration segment at a time. A comparison of distinct terms needs separate imports/models and labels.

## Input 3: source-rights manifest JSON

Keyed by exact provider name. Start from `source_rights.example.json`. Required per provider: `local_research_allowed` true only after actual qualification, `terms_source_url`, `checked_date`, and an explanatory note. This is a factual source-policy record, not a grant of rights or external publication approval. The bundled example is intentionally unapproved. Preserve restrictive terms and leave unresolved providers ineligible.

## Import and fit

```sh
python3 -m gpu_index import-history provider_quotes.csv \
  --bindings anchor_bindings.csv --rights source_rights.json --out imported
python3 -m gpu_index financial-lab --panel imported/monthly_panel.json \
  --as-of 2026-10-28T23:59:59Z --out imported_validation
```

Outputs: `monthly_panel.json` and source/hash/license-preserving `lineage.csv`. `provider_history.schema.json` documents the derived panel. Natural logs are used for prices and anchors. The importer requires at least one consecutive monthly pair; the comparison needs at least 12 initial months plus eligible test observations. Two endpoints are not expanded into monthly history. Passing these gates does not by itself qualify global aggregation or real model promotion.

At every rolling origin, rental training rows and last-price conditioning inputs must have own **and anchor** publication dates before the target month. Target-month anchor price is an explicitly supplied conditional scenario, so the tests do not forecast future AWS policy. Held-out providers contribute no fitted rental changes, but their already-known last price may be used. Financial features use the end of the previous month, with no future acceptance/filing information.

Raw `fit` accepts the simpler experimental JSON API documented in README, including labelled synthetic fixtures. Use the import path for real data: that experimental API alone does not certify provenance or source rights.
