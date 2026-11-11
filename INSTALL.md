# Manual GitHub instructions

## Create the repo
GitHub → + → New repository → name `college-basketball-dashboard` → Public → Create repository. No need to clone the football repo.

## Add files
Upload the extracted file contents with **Add file → Upload files**. If dragging folders fails, use **Add file → Create new file**, enter the *full relative path* in the filename box (for example `assets/style.css`, `scripts/metrics.py`, `tests/test_metrics.py`, or `data/teams.json`), paste its complete contents and select **Commit changes**. Repeat for each file. You can upload separate files in groups where GitHub supports that.

## Enable free Pages
Settings → Pages → Build and deployment → Deploy from a branch → main and /(root) → Save. Check Actions/Pages build completion and then browse the URL. No paid account or API key required.

## Verification
Check the Team Stats and Player Stats buttons, type into search, select conference, switch per-game vs totals, and resize your browser. Synthetic stats will always be labeled. Real data updates are not enabled.

## Scope and rights checkpoint
Confirmed: NCAA Division I men's basketball, 2026–27 (API season 2027). The demo may be published as labeled synthetic data. Do not turn on live data publication or a schedule until permission for the actual public JSON format is confirmed. See `PROVIDER_PERMISSION_REQUEST.md` for a ready-to-send clarification request.

## Optional private live API field verification (manual, two calls maximum)
Only after creating the new basketball repository, obtain your own free CBBD API key. In the **basketball** repository, go to Settings → Secrets and variables → Actions → New repository secret, name it `CBBD_API_KEY`, and paste the key. Never paste the key in a chat, file, commit, or screenshot.

Open Actions → **Verify CBBD fields privately** → Run workflow. The workflow requests only `season=2027&team=Duke` for the team and player season stats endpoints. It outputs HTTP status, record counts, and field paths with null counts; it does **not** save raw records, player names, or credentials. This costs up to **two** requests from the shared football/basketball monthly quota. A successful 200 does not itself authorize public redistribution. The action does not schedule refreshes or publish live data.

To share results for analysis, copy only the **Verify CBBD fields privately** step output. Do not share secrets or any raw response data.
