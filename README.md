# College Basketball Dashboard — $0 prototype

An independent static, responsive dashboard patterned after a separate college football dashboard. **All current numbers are SYNTHETIC DEMONSTRATIONS, not actual NCAA statistics.** It does not use a basketball API key or spend API requests.

## What is ready
- Team and player sortable tables, searches, conference filtering, per-game/total player views, mobile layout, accessible button links.
- Tested basketball calculations, missing-data rules, explicit season and refresh status.
- Matchups placeholder, rights-review TODO, GitHub Pages-ready static files.

## Deployment
1. Create a *separate public* GitHub repository named `college-basketball-dashboard`. Do **not** upload any of this into `college-football-dashboard`.
2. Upload every file in this ZIP preserving its relative path. You can use GitHub **Add file → Create new file**, typing a path like `assets/app.js` or `tests/test_metrics.py`; GitHub creates the directories. For hidden paths type `.github/workflows/update-data.yml` into the new-file name input.
3. Open **Settings → Pages → Build and deployment → Deploy from a branch → main → / (root) → Save**.
4. Visit `https://YOUR-USERNAME.github.io/college-basketball-dashboard/` after Pages publishes.
5. **Do not add an API key** yet. This version does not use a provider. No Actions schedule runs until permissions and live format are approved.

## Rebuild demo data
From project root: `python scripts/build_demo.py`. Run tests: `python -m unittest discover -s tests -v`.

## Data source assessment (2026-11-11)
Candidate: https://collegebasketballdata.com/ — free tier 1,000 API calls/month shared with CollegeFootballData. Documented core endpoint examples include `/stats/team/season?season=2027&seasonType=regular` and `/stats/player/season?season=2027&seasonType=regular`; live access and response schemas must be tested with your key inside a private CI environment. `/stats/team/leaderboard` explicitly requires Patreon Tier 2, so we will calculate approved metrics ourselves. Provider's terms allow reasonable displays, independently derived analysis, private caching, but prohibit bulk public redistribution. Publishing season-wide public team/player JSON is **not yet approved**. Provider terms: https://collegebasketballdata.com/terms ; tiers: https://collegebasketballdata.com/api-tiers ; docs: https://api.collegebasketballdata.com/api/stats .

## Methodology
Season convention: ending year (2027 = 2026–27). Scope confirmed: NCAA Division I men's basketball, 2026–27 season (API season=2027). Regular-season and postseason inclusion, exhibitions, and non-D-I opponent handling require explicit validation before live publication. The demonstration models a fictional D-I-style league and includes **no real teams, player stats, or scores**. The live updater must validate game types, exhibitions, excluded opponents, total games, denominator coverage, and required fields before publishing.

For approved future data: PPG = points / games, raw offensive rating = 100 × points / possessions, raw defensive rating = 100 × opponent points / opponent possessions, eFG% = 100 × (FGM + 0.5 × 3PM) / FGA; TS% = 100 × points / (2 × (FGA + 0.44 × FTA)). 0 attempts gives missing, never 0%. 0.44 FT attempt weighting is approximate. Shooting percentages use combined makes and attempts, not an average of separate game percentages. Pace needs a consistent possession and regulation-minute convention. No opponent-adjusted values are claimed.

## Security
Public pages read only repository-approved JSON. No client API calls or credentials. Future secrets should go to **Settings → Secrets and variables → Actions**, not to files, logs, or chat. A live updater and scheduled workflow have deliberately not been enabled pending rights clearance.
