# Protected basketball dashboard (not deployed)

This is a **preparatory scaffold**, not a live private website. The existing GitHub Pages dashboard remains public and contains fictional data only.

## Design
- One shared password, no individual accounts. Server-side Worker checks a signed, seven-day HttpOnly cookie.
- Worker protects HTML, JavaScript, CSS and JSON, including direct requests to /data/*.json.
- Static asset allowlist is built into private-site/site with fictional data only. Never commit real CBBD records to the repository or the generated site directory.
- When PRIVATE_DATA KV is configured, the Worker serves private team, player, and schedule JSON from KV instead of demo files.
- Password and signing key must be Worker secrets. API credentials remain separate in GitHub Actions.
- No live API requests are performed by the Worker or visitors.

## Setup (requires your Cloudflare account)
1. Install Node.js and run `python private-site/build_site.py`.
2. From `private-site`, run `npx wrangler login`, then `npx wrangler secret put ACCESS_PASSWORD` and `npx wrangler secret put SESSION_SECRET` (use a long random signing secret).
3. Run `npx wrangler deploy`; verify incorrect passwords are rejected, correct password grants access, and direct /data/teams.json requests without the cookie show the password gate.
4. For real data, create a private KV namespace, configure its ID in wrangler.toml, and use a **separate, authorized private updater** to write validated JSON to keys `teams`, `players`, `schedule`. That updater is NOT implemented yet. Validate the provider's data-use terms before sharing data.

## Security limitations
A common password can be forwarded. There is no individual revocation, per-user identity, or rate limiting in this scaffold; configure Cloudflare rate limiting/WAF before real data deployment. Shared-password protection is not a substitute for provider redistribution permissions. Existing public GitHub Pages is not password-protected.


## Full-coverage updater (draft PR; not deployed)
The existing live password-protected Cloudflare Worker remains separate from this draft. The offline tools are `fetch_season_snapshot.py`, `normalize_season_snapshot.py`, `validate_full_coverage.py`, and `api_budget.py`. No scheduled live fetch, production publication, or secret setup is enabled by this PR.

**Provider permissions:** CollegeBasketballData.com's Terms of Use (effective August 12, 2026) allow private caching, scheduled polling, reasonable factual display, and independently created analyses, but prohibit standalone datasets, bulk downloads, substitute APIs, and giving visitors direct/programmatic access to stored raw responses. See https://collegebasketballdata.com/terms . Restrict visitors to reasonable dashboard views and derived rankings; do not expose raw provider snapshots or broad export endpoints. API credentials must remain server-side. Player/team trademarks and likeness rights are separate.

**Quota:** The documented free tier includes 1,000 requests per month shared with CollegeFootballData. Our provisional quota guard reserves 500 for football and 100 as a safety margin, limiting a basketball refresh to 12 calls; these are local policy defaults, not provider limits. Never infer the live remaining balance from a manually typed value in production: query account usage or use a conservatively maintained shared counter before enabling scheduled fetches. Dashboard page views must use cached Cloudflare KV and never trigger provider calls.

**Coverage:** Season `2027` means 2026–27. The normalizer currently requires an explicitly supplied verified D-I team count (at least 300) and rejects incomplete/mismatched data. The actual season directory must establish the count; do not guess it or label a 24-team pilot full coverage. The normalizer currently expects dashboard-style field names and will reject a provider response with different keys. A documented field-by-field provider mapping is still required before production. Do not substitute missing statistics with zero.

**Release gate:** Before publication, confirm provider response shapes and the required statistics, implement the mapping, check full team/player coverage and reasonableness, verify permitted presentation, add secret-backed authenticated publication with rollback/atomic-read behavior, and pass CI. Never commit real provider records, local raw snapshots, API keys, or Cloudflare tokens. Keep PR #36 draft until these checks are complete.
