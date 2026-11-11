# Basketball Dashboard TODO

## Release gates
- [x] Scope confirmed: NCAA Division I men's basketball, 2026–27 (API season=2027).
- [ ] Ask Rad Sports Analytics explicitly whether public GitHub Pages downloadable JSON containing season-wide team/player aggregated totals, points, percentages, and names is permitted, and what size/format they consider a reasonable display versus bulk redistribution. Separately ask about season-wide normalized individual game logs (do NOT publish without written clarification).
- [x] Women's basketball excluded from this project; validate that API responses represent NCAA Division I men only.
- [ ] Verify exact API schemas with authenticated Actions CI; limit or mask response logging, validate fields and endpoint access.
- [ ] Review third-party trademarks, player identity, images, and attribution; no logos or photos now.
- [ ] Confirm exhibition and non-DI-opponent treatment; choose regular/postseason games and demonstrate consistent coverage.
- [ ] Determine current shared account-level quota with official provider usage endpoint and include football workflow, manual runs, pagination, retries, other consumers.

## Functional work after permission
- [ ] Replace synthetic data with approved minimal display-only aggregates; use explicit per-dataset rights review and validation checks.
- [ ] Add safe scheduled/manual GitHub Action and secret, Python fetcher, staged multi-file validation, last-success timestamp/last-attempt status, failure-safe publication.
- [ ] Validate fields for shot makes/attempts, possession definitions, player minutes; calculate missing as null and weighted shooting percentages from totals.
- [ ] Show team and player coverage/samples, staleness indicators; warn on season change and tiny samples.
- [ ] Upcoming matchup schedule, comparisons, recent form, transparent and backtested ranking algorithms.
- [ ] Add simple tracked workflow API-request counter, labeled as only this repository and not official provider counter.

- [x] Prepare manual, private, maximum-two-call API schema/coverage probe (`scripts/probe_api.py`, `.github/workflows/verify-api.yml`)
- [ ] Run the probe after the basketball repository and secret are configured; confirm HTTP 200, field paths, null rates and records
- [ ] Confirm free-tier access for both season stats endpoints using actual API responses
