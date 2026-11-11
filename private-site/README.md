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
