# Local release verification — 29 October 2026

## Passed

- **55 Python tests**: the 46 existing research/financial/import tests plus 9 self-contained site/data-contract tests.
- **24 Node tests**, including three numeric scenario fixtures and **10,000 seeded parameter cases** independently checking market clearing, capacity feasibility and cost/demand comparative statics. Exact decimal token arithmetic, strict prompt-threshold equality, documented later-entry override precedence, unsupported schedule rejection, invalid values, last-good retention for 401/429/schema/offline failures, source policy gating and a cancelled 4 MiB stream are covered.
- Buildless static build and JavaScript syntax checks. The public build is copied only from `site/`; private Library inputs, original papers/reports and local financial datasets are excluded.
- Research transfer: verified readable local ZIP, exact size **20,667 bytes**, SHA256 **33ca51abe587c822b5da0e1dbde5ec0e9fecc9b8f7a1505726212810e6453897**, ZIP integrity and all four producer manifest checksums. Final study and contract 2026-10-29.2 replace earlier text versions.
- A bounded manual OpenRouter API refresh succeeded without credentials. Stored capture: **2026-10-29T06:37:34.324Z**, six selected model IDs. No descriptions, benchmark corpus or bulk raw response retained in public data.
- Real browser refresh also succeeded, showing a new capture time and six records while leaving unknown publication/effective dates null. This verifies an explicit current fetch, not a continuously streaming feed.
- Desktop Chrome visual check at the existing 1920-pixel viewport and phone check at **390×844**. Phone document width matched viewport (390 px); chart uses a separate mobile viewBox and has no horizontal overflow. Temporary viewport override reset.
- UI interactions: reference 100/100; binding-capacity preset 150.0 quantity index / 266.7 price index; observed AWS input gives 108.7 / 92.0 under default transmission; token workload arithmetic; source override tier; missing-cache unavailable behavior; reset; named presets; real refresh. Separate explicitly labelled temporary QA fixtures showed **STALE** and **UNAVAILABLE**, with scenario controls still functional.
- Screenshots were captured in this task for the desktop hero and phone hero/chart. They are QA evidence, not data observations.

## Limits and pending actions

- This is a **local release**. No public repository was created, remote push performed, Pages enabled or public deployment claimed while the specific publication approval is pending.
- Proposed dedicated destination: `carlos1980s/intelligence-economy-observatory`. No personal portfolio, Ludumina, Roblox/Studio or recording resources were changed.
- Remote CI is **unrun**, pending repository approval/push. Prepared CI runs the self-contained public tests; original private-input research integration tests were verified locally and are not falsely claimed as remote checks.
- Public API metadata access is not a blanket redistribution license. The final review supports selected factual OpenRouter API metadata with attribution, not descriptions, third-party benchmark data or corpus mirrors. Manual refresh is bounded to 15 seconds and 4 MiB; no recurring schedule is enabled.
- Artificial Analysis, Silicon Data and Ornn data feeds are absent. Their restricted public-dashboard/raw redistribution operations remain outside this release; there is no source-rights blocker for the scoped manual OpenRouter factual metadata indicator supported by the final review.
- No measured world useful-task volume, empirically identified demand curve, calibrated macro equilibrium, wages/GDP effect, audited task-performance dataset or contract valuation is claimed.
- Scenario sensitivities are not confidence/credible intervals. API top-provider changes are not silently treated as fixed-provider tariff inflation. Model aliases do not establish immutable quality.

## Commands

```sh
node --test tests/site.test.mjs
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
python3 -m http.server 8879 --bind 127.0.0.1 --directory site
```

A portable source/build bundle is tested again after extraction before handoff. The temporary QA and preview servers are stopped at final teardown. See `DEPLOYMENT.md` for the manual deployment route after approval.
