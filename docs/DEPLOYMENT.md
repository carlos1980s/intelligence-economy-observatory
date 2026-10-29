# Deployment route and boundaries

Proposed dedicated destination: `carlos1980s/intelligence-economy-observatory`. Do not modify the existing personal portfolio, Ludumina or unrelated repositories.

The build is static and requires no new credentials, secrets, account or paid service. GitHub Pages is the prepared route after public creation/publication approval. `.github/workflows/pages.yml` deploys only by manual dispatch; it does not enable any recurring collection. Existing GitHub authentication is used only by the operator, never shipped to the browser/build.

Steps after the requested scope is approved:

1. Create/reuse the dedicated approved repository and push exact reviewed source.
2. Open implementation review as a draft PR if a base branch exists; retain exact head SHA.
3. Verify GitHub CI for that SHA. Site tests are self-contained; legacy private-input integration tests run locally.
4. Enable Pages only within the authorized repository if available at no added cost. Choose GitHub Actions as build source.
5. Manually dispatch the deployment workflow for the reviewed ref, verify the deployment result and literal URL, then test desktop/phone behavior at that URL.

Private repositories may require an eligible plan for Pages, and publication scope is a separate decision. Do not change visibility, account permissions or incur charges to work around a limitation. While approval is pending, local verification and the reviewed static artifact are the available preview.

The `site/data/source-policy.json` automation gate is not a user preference toggle. The final reviewed policy permits only bounded user-initiated factual metadata retrieval supported by the official Models API overview; it does not authorize bulk corpus redistribution or schedules. There is no refresh schedule. A future approved refresh must preserve exact IDs, tiers, source/reference/retrieval dates and last-good data; 401/429/schema failures cannot create fake prices or trigger account creation.
