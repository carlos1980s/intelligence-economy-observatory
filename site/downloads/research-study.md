# Measuring the economy of useful intelligence

## Main conclusion

A defensible live website can track **offered compute and model prices**, benchmark-constrained technical performance, and separately measured adoption. It cannot currently display an empirically identified world supply curve, demand curve, or equilibrium for useful intelligence from those public series alone. The missing objects are task-standardized output, utilization and deployable capacity, buyers' willingness to pay, and credible variation separating demand from supply.

The recommended first release therefore has two visibly different layers: an observed indicators dashboard, and an explicitly conditional equilibrium experiment. The second layer answers “what would happen under these assumptions?” It does not claim “this is the measured intelligence economy.” This distinction is the central research finding, not an incidental disclaimer.

Research cutoff: 29 October 2026. Public sources were verified during this research pass. No paid datasets, account creation, private customer data, or outreach were used. The companion `implementation_contract.json` specifies formulas, data handling and release tests. `observed_price_examples.json` contains six directly retrieved factual price examples. These cloud-local artifacts are not automatically present on a separate computer.

## What the unit must mean

Let a task cell j specify domain, difficulty, input distribution, output rubric, quality threshold, permitted tools, maximum latency, supervision regime, and tolerated failure risk. Let q_jt count independently accepted completions of that cell during year t. The economic object is initially a vector q_t, not a scalar benchmark score. A correct code patch, a reliable invoice extraction and a useful scientific conjecture are not intrinsically commensurable.

Choose and publish a reference basket b_j of successful completions. Its cost is C_t(b) = sum_j b_j c_jt, where c_jt is the all-in expected cost of an accepted completion at fixed task specifications. A fixed-basket price index is P_t = 100 C_t(b)/C_0(b). Its inverse is a narrowly defined measure of useful completions per dollar for this particular basket. This does not establish a universal cardinal scale of intelligence.

For reporting aggregate output, a reference-price quantity index can be I_t = 100 sum_j v_j0 q_jt / sum_j v_j0 q_j0. The weights v_j0 must be disclosed and sensitivity-tested. They may be reference expenditure or value weights; they are not “intrinsic intelligence.” If instead the object is the number of complete, rigid baskets deliverable, it is bounded by min_j(q_jt/b_j). These are different aggregators and should never be swapped silently.

A task quality frontier is also not a supply curve. Plotting each available model's benchmark score against token price describes product differentiation and the available menu. It provides neither quantities firms would supply at each price nor buyers' marginal willingness to pay.

### Cost measurement

For a task cohort, estimate c_j as total attributable resource cost divided by independently accepted completions. Include all billed tokens, retries, tool calls, orchestration, human setup/review/correction, integration costs allocated over an explicit horizon, and expected loss from residual failures. Keep private cost and social externalities separate. Independent audit is essential: an assistant saying it succeeded is not outcome verification.

The shortcut “price per attempt divided by success probability” is valid only under the stated repeat-until-success policy, stable attempt costs, and appropriate assumptions about dependence and error detection. In realistic workflows, use the empirical cohort ratio and cluster uncertainty by underlying task and customer. Correlated failures and mistaken acceptances cannot be repaired by treating every retry as an independent Bernoulli draw.

Tokens are billing units, not task units. Tokenizers differ; reasoning changes output length; caches, context tiers and batch service change prices; tool use and review change total costs. A fixed 3:1 input/output token-price blend is useful as a declared offered-price convention, but it must not be called a fixed-quality task price.

## What primary research establishes

The task-based framework distinguishes displacement from the creation of new human tasks. It gives a reason to model substitution, complementarity and changing task composition separately rather than treating an occupational wage bill as demand for AI. [Acemoglu and Restrepo, 2019](https://www.nber.org/papers/w25684).

For existing tasks and first-order changes, aggregate productivity accounting can connect the economic share of affected tasks to task-level cost savings. This is an accounting approximation under stated assumptions, not a way to obtain an entire market demand curve, and it is especially incomplete for new products, research feedback and major reallocations. [Acemoglu, The Simple Macroeconomics of AI](https://economics.mit.edu/sites/default/files/2024-10/The%20Simple%20Macroeconomics%20of%20AI.pdf).

Actual measured productivity effects vary by workflow. The published customer-support study reports a 15% average improvement in issues resolved per hour, with substantial heterogeneity. That is a workflow-specific estimate, not a universal task multiplier. [Brynjolfsson, Li and Raymond, QJE 2025](https://doi.org/10.1093/qje/qjae044). METR's early-2025 randomized study found a 19% increase in completion time for experienced maintainers in its particular sample; its February 2026 update explains why selection and changing experimental participation complicate later comparisons. This is evidence for measuring outcomes and human overhead, not a current claim that AI generally makes coding slower. [METR study](https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf), [2026 design update](https://metr.org/blog/2026-02-24-uplift-update/).

The 2026 Journal of Economic Perspectives article on the inference market documents horizontal and vertical differentiation, rapid entry and changing market shares. That supports a task/model/provider panel rather than one unqualified scalar market. [Demirer, Fradkin and Tadelis, JEP 2026](https://ftp.aeaweb.org/articles?id=10.1257/jep.20261506).

The related December 2025 working paper, with Sida Peng, reports a preferred provider–model–day token-demand elasticity of −1.11, standard error 0.22, using model-by-date and provider-by-model fixed effects. It studies open models and acknowledges that automated routing may generate some price responsiveness. This is preliminary, short-run, platform-specific substitution evidence, **not** an estimate of world demand for useful tasks. Its variation does not eliminate every provider-level supply, reliability or routing confound. It can inform a labeled sensitivity discussion, but not silently set a calibrated macro elasticity. [Working paper, section 7 and table 2](https://demirermert.github.io/Papers/Demirer_LLM_demand.pdf).

Recent quality-adjusted-price research is useful methodological evidence but not a ready-made ground truth. An August 2026 preprint fits benchmark-based latent quality and shows sensitivity to benchmark validity and token-versus-task units. Its public release contains upstream Artificial Analysis material, so its own open-license label does not by itself establish all upstream redistribution rights. The dashboard should not ingest it wholesale without provenance and rights review or treat its latent scale as measured useful intelligence. [Zhu, 2026 preprint](https://arxiv.org/abs/2608.29843), [data description](https://huggingface.co/datasets/louisyzhu/price-of-intelligence/blob/main/README.md?code=true).

## Estimating supply without confusing inputs with outputs

### Four distinct objects

1. **Rental offer price**: dollars per instance-hour or GPU-hour for a precisely specified contract.
2. **Technical efficiency**: task-appropriate successful work per GPU-hour or joule at fixed quality and latency.
3. **Deliverable capacity**: installed, powered, connected and operational systems available to the target workload, with utilization and allocation constraints.
4. **Economic supply**: useful output offered at each delivered-task price, including opportunity cost, congestion, uncertainty and market structure.

None can substitute for all four. Rental prices are themselves upstream equilibrium prices; they are not automatically exogenous supply shocks. Vendor revenue or share price is further removed from a physical output unit. Hardware shipments and booked data-center projects are flows or plans, not the installed and usable inference stock.

### Engineering accounting

For hardware/system h serving task j, a simplified unit cost is

c_jh = (hourly rental charge + nonduplicated hourly overhead)/(u_h g_jh s_jh) + variable tools + human review + residual expected loss.

Here g is attempts per active system-hour under the relevant workload, s is audited success probability, and u is productive utilization of paid clock time. If g already counts accepted completions, do not multiply by success again. If the rental charge includes electricity and capital recovery, do not add them again. An owned-hardware calculation instead uses a clearly specified capital-user-cost/depreciation model, power, maintenance, networking, site costs and residual value. Neither is the same as short-run marginal cost.

Published MLCommons inference results can help estimate matched technical performance, but version, benchmark, division, system, model, accuracy target, scenario and latency conditions must match. Its power results refer to measured whole-system AC consumption for the accompanying benchmark; GPU thermal design power and power-supply ratings are not measured system energy. Results may be corrected or invalidated, so commit/version and change-log checks are necessary. [MLCommons benchmark documentation](https://mlcommons.org/benchmarks/inference-datacenter/). Derived cost-per-task metrics are the dashboard author's analysis, not official benchmark results; follow the benchmark's results messaging and attribution rules. [Messaging policy](https://github.com/mlcommons/policies/blob/master/MLPerf_Results_Messaging_Guidelines.adoc).

For annual capacity, a hardware constraint is sum_j x_jh <= H_y N_h u_h, where x is system-hours, N is installed matching systems, and H_y is the actual year's hours. A separately defined energy constraint is sum_jh e_jh q_jh <= E_inference. Facility electricity, IT electricity and accelerator electricity must be distinct. A model using facility capacity must include PUE, average load, downtime, non-AI workloads and the training/inference split exactly once. Missing allocations are assumptions, not observations.

A serious supply model minimizes the cost of producing b_j I over model/system allocations subject to GPU memory, system-hours, energy, regional latency, network and review-labor constraints. Its cost function C(I) yields a conditional marginal-cost schedule. If aggregate quantities of installed hardware and usable power are unknown, the schedule remains partially identified even with excellent engineering throughput data.

### Energy evidence boundary

Berkeley Lab's data-center work is bottom-up estimation with future scenarios, not a live meter for inference capacity. The current Lab page identifies a 2025 update and reports a 2030 scenario range of 9.5–15.3% of U.S. electricity, superseding use of the older 2024 projection as the latest outlook. These are all-data-center electricity scenarios, not world useful-intelligence supply. The update's eScholarship full-text page presented a browser verification block in this research pass; the official Lab summary is accessible. [Berkeley Lab](https://eta.lbl.gov/data-centers).

EIA electricity prices can be a regional input-cost proxy, but average retail industrial/commercial tariffs are not necessarily data-center contract rates. Monthly electricity data and downloadable files are public; the API requires a free registration/key. No registration was performed. [EIA data](https://www.eia.gov/electricity/data.php), [API documentation](https://www.eia.gov/opendata/documentation.php).

## Estimating demand rather than renaming adoption

Demand for task j should include four channels: replacement of existing workflows, more intensive use in those workflows, genuinely new activities, and R&D/investment demand. Add households, firms and government explicitly. Nonmarket household value is not a wage bill; government procurement is not unconstrained private willingness to pay; scientific research is often a distribution of future payoffs rather than immediate labor savings.

A buyer k adopts or expands if expected task benefit exceeds all-in cost, switching/integration costs, risk and constraints. Existing human cost can inform a comparator, but it is not a guaranteed willingness-to-pay ceiling for quality improvements or new activity, and it is not equal to supplier revenue. Savings can accrue to users rather than model suppliers. Workflow bottlenecks, required human complements and falling output prices can reduce monetizable gains.

A useful micro specification is

q_jkt = D_j(p_jt, p_-j,t, quality_jt, latency_jt, wages_kt, income_kt, output_demand_kt, integration_stock_kt, risk_kt).

The extensive margin is who adopts; the intensive margin is accepted tasks per adopter; the task-composition margin is which activities occur. A firm using AI once and a firm executing millions of useful workflows both count as one adopter in a binary rate. Surveys, traffic and token counts cannot be converted into aggregate useful-task output without these bridges.

### Empirical identification ladder

- **Best within scope:** randomized price/credit offers or exogenous access constraints with consent, measuring accepted output, total spend and outside options. None is undertaken for this release.
- **Potential observational design:** provider-model-task panels with plausibly exogenous cost shifts, fixed effects, dynamic responses and explicit exclusion restrictions. Hardware-price movements are not automatically valid instruments, because expected demand also affects them.
- **Descriptive only:** correlate price, token volume or adoption. It cannot identify a structural slope when quality, supply, routing and demand change together.
- **Structural calibration:** fit task-specific substitution and outside-option behavior to observed moments, publish identification diagnostics and estimate uncertainty. It must distinguish within-provider, within-model and market-wide elasticities.
- **Partial identification:** if willingness-to-pay or quantity denominators are missing, report bounds or scenario sets instead of a single estimated curve.

A platform's own share may rise when it captures competitors' traffic even if total market demand is unchanged. Survey sampling, selection into a provider, and changing classifiers can all mimic adoption growth. Tokens used for failed attempts or longer reasoning can increase while useful output remains constant. These are reasons to retain separate measures, not merge them into an opaque “demand index.”

### Public demand evidence

Census BTOS supplies a broad U.S. business adoption indicator, not task volume. A November 2025 wording change broadened the question from production of goods/services to any business function. Histories must be split at the actual questionnaire period, with the break visible. The official data/download pages are JavaScript-driven; current XLSX URLs should be resolved from the official download UI rather than guessed. [Census downloads](https://www.census.gov/hfp/btos/data_downloads), [Federal Reserve discussion of the break](https://www.federalreserve.gov/econres/notes/feds-notes/monitoring-ai-adoption-in-the-u-s-economy-20260403.html).

The Bick–Blandin–Deming/Harvard GenAI Adoption Tracker offers an important separate worker/household lens. At retrieval its August 2026 cards reported 60.8% of working-age adults using generative AI, 40.5% of employed respondents using it for work, 5.3% of total work hours spent using it, and 2.1% of total work hours reported saved. Preserve those denominators and the survey definitions. Self-reported time savings are not experimentally identified productivity, and the cards are not a demand elasticity. [Primary tracker and methodology](https://www.genaiadoptiontracker.com/).

Anthropic's Economic Index gives task and collaboration composition on its own services, including a June 2026 release. Its Hugging Face metadata identifies an MIT license; pin the exact release/commit and preserve applicable notices and upstream source terms. The platform's users and machine-classified outcomes are not representative of the entire economy. Use composition evidence, not a direct population expansion factor or independent audit of task success. [Anthropic index](https://www.anthropic.com/economic-index), [dataset and releases](https://huggingface.co/datasets/Anthropic/EconomicIndex/tree/main).

O*NET supplies occupational task descriptions; BLS provides employment and wages; BEA provides interindustry links. Task importance/frequency scores are not automatically time shares. Occupation-to-industry crosswalks must not duplicate workers. Compensation is not identical to wages, and wage exposure is not AI expenditure. O*NET specifies attribution and modification notices under CC BY 4.0; BLS offers a no-registration v1 API; BEA's API requires registration. Public downloads remain available for versioned, lower-frequency research. [O*NET](https://www.onetcenter.org/database.html), [BLS API](https://www.bls.gov/developers/home.htm), [BEA input-output tables](https://www.bea.gov/industry/input-output-accounts-data), [BEA API](https://apps.bea.gov/API/docs/index.htm).

## General equilibrium and dynamic feedback

A complete model makes task demand depend on wages, income, output prices and capital investment, while supply depends on capacity investment, power and technical progress. Labor substitution changes incomes and task prices; complementarity and new tasks may increase labor demand elsewhere. Lower final-goods prices alter demand; R&D can improve future model capability; expanding data centers raises demand for power and capital. Training is an investment input to future capability, not interchangeable with current inference output.

An implementable extension starts with industry task shares and the BEA input-output structure, adds household income and consumption, capital accumulation, a model-development sector and constrained inference supply, then clears goods, labor and capital markets. A fixed Leontief inverse is an accounting baseline, not general equilibrium once input shares, prices and production methods change. Gross-output and intermediate-input effects must be reconciled to avoid counting the same AI service at each production stage.

For a one-period dashboard, clearly fix the omitted prices/incomes and call the curve partial-equilibrium and conditional. Do not label consumer surplus as GDP, API revenue as social value, or the area under a scenario curve as measured welfare. Long-run innovation and new-task demand are scenario mechanisms until identified.

Rebound also requires careful units. If an efficiency improvement reduces energy per accepted task by factor a and price falls proportionally, an isoelastic demand with absolute elasticity epsilon gives energy proportional to a^(1−epsilon). That simple result assumes full pass-through, fixed task composition and no other constraints. Token expenditure growth, provider share switching and new product quality are not direct evidence of energy rebound.

## What can be live now

### Verified during this pass

**AWS official static price files.** A direct unauthenticated GET succeeded for `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/index.json`. It reported publication time 2026-10-28T18:03:52Z and current version `20261028180352`. Follow the published version and region paths, then filter the precommitted product basket. The public-file route is distinct from authenticated AWS API operations. AWS says these prices are informational and omit Spot; service pricing pages govern discrepancies. [Public-file documentation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-the-aws-price-list-bulk-api-fetching-price-list-files-manually.html), [scope and caveats](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html).

**OpenRouter model metadata.** A direct unauthenticated GET of `https://openrouter.ai/api/v1/models` succeeded at 2026-10-29T06:16:50Z, returning 457 text-output rows (the default modality filter). That is an endpoint observation, not a guarantee of continued unauthenticated service or a statement about the total market. The raw file hash is stored in the companion observations. Example input/output USD per million token rates were 0.15/0.60 for `openai/gpt-4o-mini`, 0.30/2.50 for `google/gemini-2.5-flash`, and 0.10/0.32 for `meta-llama/llama-3.3-70b-instruct`. These are offered base prices, not standardized task costs. [API endpoint](https://openrouter.ai/api/v1/models), [documentation](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties).

OpenRouter credits/platform fees, taxes and optional services sit outside a simple token-rate comparison. Provider routing can also change the actual rate, latency or cache behavior. The production parser must retain exact model IDs, canonical versions and context-price overrides. The default catalog reports top-provider prices, so provider changes must be visible. Time/day-dependent price overrides require a fixed request schedule or exclusion; context thresholds use a strict greater-than comparison. [Model metadata conventions](https://openrouter.ai/docs/guides/overview/models). [Pricing explanation](https://openrouter.ai/pricing).

### Rights and access are separate questions

Publicly readable is not synonymous with openly redistributable. OpenRouter's documentation explicitly supports production integration of freely available metadata, while its general terms reserve rights in its materials; this is not a blanket corpus-redistribution license. For the first public release, prefer an attributed narrow factual price indicator and links, and do not publish its full descriptive corpus or a bulk mirror. Any broader redistribution requires an explicit rights decision. [OpenRouter terms](https://openrouter.ai/terms).

Artificial Analysis's API requires an account/key and attribution. Its August 2026 Data Platform Terms restrict raw-data distribution and customer-facing use, with separate provisions for charts, brief citations, derived outputs and competitive products. A free API key is **not** sufficient authorization to expose its JSON in a public GitHub dashboard. Leave a future adapter disabled behind a reviewed-rights gate. [API reference](https://artificialanalysis.ai/api-reference/), [current platform terms](https://artificialanalysiscdn.com/legal/ProDataPlatformTerms.pdf).

Silicon Data offers useful standardized GPU-rental series and separates provider segments. Its public H100 page at retrieval showed a dated value of $2.90/GPU-hour for 28 October 2026, but a FAQ on the same page still stated $2.53. This illustrates why a dated series must outrank undated marketing text and why parsing should detect conflicts. Its documentation distinguishes portal/API access tiers; no no-key redistribution grant was verified. Cite it as a cross-check, not an unlicensed live feed or a global useful-intelligence price. [Dated H100 page](https://www.silicondata.com/products/silicon-index/h100), [API/access documentation](https://docs.silicondata.com/introduction).

## The honest first-release curve

Use normalized price p and quantity q, with reference values 1 displayed as 100:

q_D(p) = A p^(−epsilon)

q_S(p) = min[K, B (p/c)^eta]

A is demand scale, epsilon a positive absolute demand elasticity, B supply scale/productivity, eta a positive supply elasticity, K deliverable capacity and c a cost shifter. All are assumptions except the explicitly observed input used to construct c. The shape is a convenient local scenario family, not a recovered structural law; increasing returns and strategic markups may require a different family.

The unconstrained equilibrium is

p_u = (A/B)^[1/(epsilon+eta)] c^[eta/(epsilon+eta)], q_u = A p_u^(−epsilon).

If q_u <= K, use that point. Otherwise q* = K and p* = (A/K)^(1/epsilon). At the capacity limit, price can exceed marginal resource cost c(K/B)^(1/eta); the difference is a conditional scarcity rent. Do not force demand to equal marginal cost when capacity binds.

Reference defaults A=B=c=1, epsilon=eta=1, K=1.5 yield q=p=1. Those defaults are a normalization, not calibration. Set c = (AWS fixed-basket index/100)^rho, with rho an explicit assumed pass-through parameter. The user can see how live rental-price changes would affect the model **if** the other assumptions held. Do not treat an API output price and a GPU rental input as independent additive cost measures.

The x axis must read “Useful-task basket quantity index — scenario”; the y axis “Price per useful-task basket index — scenario.” State that no absolute global task volume or dollar-per-task level has been measured. The observed price panels retain their own real units. Draw the scenario capacity constraint, mark the reference point, and show source dates beside observed inputs.

Use named sensitivity presets, not a fake confidence interval. Sampling confidence intervals, causal-estimation uncertainty, calibration ranges and unconstrained structural uncertainty are different. A parameter slider is not a posterior distribution. Do not assign probabilities to arbitrary scenarios.

## Data engineering and validation

Every observation needs source URL, source ID, retrieved timestamp, reference period, publication/effective dates where known, unit/currency, population, geography, version, evidence class and raw hash. Unknown dates stay null. Model creation time is not a price-change date. Preserve release vintages for historical backtests; a later revised observation must not leak into an earlier information set.

Maintain a fixed basket across time. For matched prices, L_t = 100 sum_i q_i0 p_it / sum_i q_i0 p_i0. If an item disappears, disclose lost coverage and halt that index or launch a separately labeled matched-sample result; do not quietly replace or reweight. New models enter an explicitly separate frontier panel or a documented chain-link bridge. Price differences caused by a provider/channel, hardware, context, batch, quality or latency change are not pure price changes.

Refresh a cached snapshot at a modest rate, keep the last successful observation, and display “stale” with its real date after failure. A daily scheduled attempt does not mean the underlying source updates daily. Never manufacture a smooth history from two snapshots. Store parser versions, rejected rows, deduplication rules and coverage diagnostics. Keep credentials server-side; do not open accounts to make a nonessential adapter work.

Minimum mathematical tests: normalization; interior equilibrium; binding capacity; comparative statics; unit invariance; positive finite inputs; reproducibility; monotonicity over a wide parameter grid; no silent extrapolation through zero; and scarcity rent only when the constraint binds. Data tests include exact identity/tier matching, Decimal arithmetic for prices, missing-item detection, schema-change failure, stale-state UI, future-date rejection, Census wording breaks, and reference-period-versus-retrieval-date separation. The companion contract supplies concrete numeric fixtures.

Economic validation must go beyond code tests: independently reproduce a small audited sample; compare alternate task weights and outcome rubrics; test hardware-performance transfer out of sample; validate demand against actual accepted-task quantities when available; and report model misspecification separately from sampling noise. A synthetic rental test cannot validate a global historical price model. Financial company variables may enter a lagged forecasting/calibration experiment, but not replace observed rental prices or physical capacity.

## Research roadmap and stopping boundary

The first release is complete when authorized publication has a reproducible observed-price pipeline, visibly separate scenario controls, provenance and stale-state behavior, and passing mathematical/data tests. It need not wait for an impossible claim of a measured world equilibrium.

The next research milestone would be a small, stable task basket with independently scored outcomes and measured all-in cost across model/provider configurations. That requires a separately authorized evaluation budget or supplied logs; it is not silently included in this no-paid-data pass. A subsequent milestone needs representative transaction/usage panels and a credible price-identification strategy. Only after those bridges should the website offer calibrated macro quantity or welfare estimates.

The useful conclusion today is narrower and stronger: **compute prices, offered token prices, benchmark performance, adoption and useful economic output are related but distinct. A live dashboard earns trust by showing their connections as explicit, testable hypotheses rather than collapsing them into one invented measured curve.**
