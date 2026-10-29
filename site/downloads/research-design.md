# Intelligence Economy Observatory — research design

Version 2026-10-29.2. Working research interface, not a fitted macroeconomic equilibrium. The completed independent study is preserved in research-study.md; this design implements its observed-versus-conditional distinction.

## Economic object

I denotes a fixed-quality basket of successful cognitive tasks per year. A valid empirical unit must define tasks, basket weights, acceptance criteria, latency, reliability and risk tolerance. Tokens, benchmark scores and GPU-hours alone do not identify I.

The website plots annual useful-task quantity and price as **indices**, reference scenario = 100. Neither the absolute worldwide task volume nor a dollar price of intelligence is identified.

Demand can change through substitution, greater use within existing activities, and newly viable activities. Integration, oversight, human labor and risk are real adoption costs. The compact curve is reduced form and does not separately estimate these mechanisms.

Supply depends on model efficiency, rental or ownership costs, productive utilization and deployable capacity. Announced projects, GPU TDP, total data-center electricity and listings are not equivalent to available inference capacity.

## Conditional scenario

q_d(p)=A p^(−epsilon)

q_s(p)=min[K, B(p/c)^eta]

c=(R/100)^rho

A: demand scale; epsilon: positive demand elasticity; B: supply productivity/scale; eta: positive supply elasticity; K: deliverable annual basket capacity. All are assumed. R is a selected observed GPU input tariff index or an explicit scenario value; rho is assumed input-cost pass-through. c is a scenario shifter, not measured marginal cost.

Unconstrained p_u=(A/B)^[1/(epsilon+eta)] × c^[eta/(epsilon+eta)] and q_u=A p_u^(−epsilon). If q_u≤K, this is the equilibrium. If capacity binds, q*=K and p*=(A/K)^(1/epsilon). Marginal cost at capacity is c(K/B)^(1/eta). Any positive gap is a conditional scarcity rent per unit, not measured company profit.

A=B=c=1 with K≥1 produces q=p=1, displayed as 100. This is a normalization, not calibration to observed world activity. Both chart axes begin at zero. The scenario range varies A, B and K ±20% over eight corners. It is not a confidence or credible interval.

The older linear example with I=100 and p=1 was hypothetical and is not used as a calibration target.

## Offered token prices

Six exact incumbent OpenRouter model IDs are selected as examples, not a representative market basket. Each record retains model ID, canonical slug, service variant, tier, pricing overrides, source, capture/retrieval time, raw-response hash and unknown metadata. Base prompt/completion fields are USD per token; multiplying by 1,000,000 gives displayed per-million rates.

The calculator is a declared text input/output workload. Cache-read pricing is used only when observed; missing cache prices make a cached workload unavailable. Qualified prompt-tier overrides apply only when prompt length strictly exceeds the threshold. Scheduled time/day rates are excluded until an explicit request schedule is defined. These are top-provider offered catalog rates: routing/provider changes can alter a listing without a tariff change. The catalog created date means added to OpenRouter, never price effective. Provider route, geography, tokenizer and reasoning settings missing from the supplied capture stay unknown. No record is treated as a quality-comparable fixed task basket.

Displayed token charges exclude unmeasured separately billed reasoning, tool fees, human labor, retries and success rates. Billed completion tokens must not have their included reasoning counted a second time. A 3:1 input/output blend is a convention, not equal task work across tokenizers. Batch/free/routes are not silently mixed. API output prices are never added to GPU input prices as independent components of supply cost.

## Historical GPU comparison

The AWS five-cell matched on-demand list-tariff basket is 100 in October 2024 and 84.59609438567942 in October 2026, a 15.4039056% decline. Cells are H100, A100 40 GB, A10G, T4 and L4 with exact instance definitions, Linux/shared/us-east-1 terms, equal baseline expenditure. This is a one-provider bundled tariff comparison, not verified capacity, transaction prices or a global compute market.

Laspeyres = 100 Σ p_it q_i0 / Σ p_i0 q_i0, with q_i0 proportional to 1/p_i0. Missing cells cannot silently drop or reweight. The eight-model extension is a separate sensitivity, not a revision. No interpolated monthly path or pre-launch history is invented.

## Freshness and rights

Observed capture/retrieval time differs from publication/effective dates. Unknown dates remain null. Model creation dates never backfill price history. Stored captures are labelled snapshots and become stale after seven days. Failed source attempts retain dated last-good data; unavailable data stay unavailable.

OpenRouter public metadata was accessible without a key, but no general redistribution license was verified. Only selected factual fields and attribution are included. The final source review verified the official Models API overview supports production metadata integration. Bounded user-initiated retrieval of selected factual rates is enabled; descriptions, third-party benchmark data and bulk mirrors remain excluded. No recurring job is enabled. The full metadata response and descriptions are excluded from the public repository.

Artificial Analysis raw data/public dashboard integration is omitted because its Data Platform Terms sections 2.3–2.5 restrict relevant uses without reviewed permission. Silicon Data and Ornn remain contextual sources, not licensed public feeds.

## Identification and wider economy

Public prices alone do not identify demand elasticity, total quantities or useful intelligence. Price and usage are jointly determined; regressing one on the other is not an identified demand curve without valid variation or instruments. Task benchmarks, randomized price/offer variation, transaction quantities and adoption costs are future research inputs.

The scenario is partial equilibrium. Wages, incomes, capital investment, product demand, labor complementarity and substitution, distribution and general-equilibrium feedback are outside the curve. Do not interpret producer scarcity rents as social welfare, GDP, OpenAI contract value or realizable trading profit.

NVIDIA, Broadcom and neocloud filings are indirect optional challengers. Earlier code implements acceptance-date-aware features and regularized comparisons on synthetic rental fixtures. Those experiments are not an observed market backcast or a calibrated current equilibrium.

Census BTOS changed its AI adoption question in November 2025, from producing goods/services to any business function. Exact questionnaire/reference-period breaks must be qualified before combining histories. Adopter share is not adoption intensity or a task-demand quantity. BLS wage/inflation context requires a verified series and remains outside task-demand identification.

## Primary sources

- OpenRouter model API: https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties
- OpenRouter terms: https://openrouter.ai/terms
- AWS public price files: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-the-aws-price-list-bulk-api-fetching-price-list-files-manually.html
- AWS archived Oct 2026 regional tariff file: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/20261027193004/us-east-1/index.csv
- Census BTOS: https://www.census.gov/hfp/btos/data
- Federal Reserve adoption note: https://www.federalreserve.gov/econres/notes/feds-notes/monitoring-ai-adoption-in-the-u-s-economy-20260403.html
- Artificial Analysis terms: https://artificialanalysiscdn.com/legal/ProDataPlatformTerms.pdf
