# Intelligence Economy Observatory

A buildless, responsive research website separating observed AI input prices from an explicitly conditional market for useful intelligence. No framework, tracking, API key or paid service is required.

## Run and test

```sh
python3 -m http.server 8879 --bind 127.0.0.1 --directory site
node --test tests/site.test.mjs
python3 -m unittest discover -s tests -p test_site.py -v
python3 tools/build_site.py
```

Open `http://127.0.0.1:8879`. `dist/` is the deployable static output. Node 22+ and Python 3.11+ use only their standard libraries. No package install is necessary.

## Evidence and model

- Observed: six selected factual OpenRouter offered-price records with capture/retrieval timestamps and exact IDs; historical AWS matched tariff evidence.
- Derived: declared token-workload charges and the AWS fixed-basket input index.
- Scenario: normalized demand/supply equilibrium, elasticities, capacity, input-cost transmission and eight-corner sensitivity envelope.
- Not identified: global task quantities, empirical demand elasticity, a dollar price of intelligence, general-equilibrium wages/GDP effects and a measured global market equilibrium.

The reference scenario is q=p=1, displayed as 100. That is a unit normalization, not empirical calibration. The supplied AWS comparison remains 100 → 84.596094 between October 2024 and October 2026. Optional use of that input-price change does not make demand or capacity observed.

Stored prices are **snapshots, not streaming live data**. Unknown publication/effective dates stay null. After seven days, the UI marks a capture stale. Cache/context tiers remain distinct; missing conditional prices produce an unavailable state.

The final source-specific review supports bounded, user-initiated OpenRouter factual API metadata refresh: its official overview describes freely available metadata designed for production integration. Public endpoint access is not a general redistribution license. Only selected factual fields and attribution are shipped, never the full response or model descriptions. No scheduled collection exists. Artificial Analysis, Silicon Data and Ornn feeds are not shipped. See `site/data/source-policy.json` and [research design](site/downloads/research-design.md).

## Publication and source scope

The public build contains only `site/`. Original Library PDFs, DOCX, research CSVs and local output files remain outside the public repository/build through explicit exclusions. Earlier `gpu_index/` estimators and local tests remain for research continuity; their full integration tests require the original locally authorized inputs. CI intentionally runs the self-contained site/data-contract tests instead of claiming those private-data checks were repeated remotely.

`.github/workflows/pages.yml` is a **manual** deployment route. Creating/enabling a public repository or publishing Pages requires the authorized publication scope; no account/security settings or paid services should be changed. CI runs on source changes and uploads a seven-day static-build artifact, with no data refresh job.

See [deployment notes](docs/DEPLOYMENT.md). The independent deep study is preserved in `docs/RESEARCH_STUDY.md` and downloadable from the site. Its central finding constrains the implementation: offered prices, technical performance, adoption and useful output remain distinct; no speculative curve is labelled empirical.
