# Private dashboard delivery: security contract

**Status: design only. No real dataset has been deployed.**

The public GitHub Pages build serves synthetic demo files. Never commit real
provider season datasets to this repository, GitHub Pages, public build artifacts,
or public CI logs. The existing Cloudflare preview must be verified independently.

## Required request flow

1. An authorized viewer opens the private Cloudflare hostname over HTTPS.
2. Cloudflare Access (or an equivalent verified server-side access policy) checks
   the viewer **before** returning the HTML, JavaScript, or JSON.
3. The dashboard fetches `/data/teams.json` and `/data/players.json` from the
   **same protected origin**. The existing relative URLs can then remain intact.
4. Every data URL must independently reject an unauthenticated request, including
   direct links, HEAD requests, and query-string variations. Do not rely on a
   client-side password form or JavaScript to protect JSON.
5. Disable public caching of private JSON: use `Cache-Control: private, no-store`.
   Confirm Cloudflare cache rules, worker routes, and any custom domains do not
   expose the content outside the protected hostname.
6. The authenticated site must not fall back to public GitHub Pages real data.
   If approved private data is unavailable, show a clear unavailable state.
7. Validate an authorized session and a separate unauthenticated session for
   each endpoint. Verify no public Pages URL, artifact, or source map contains
   real records.

## Data preparation

Use `scripts/check_private_bundle.py SOURCE_DIR` to validate a permitted local
export. Use `scripts/stage_private_bundle.py SOURCE_DIR NEW_PRIVATE_DEST_DIR` to
stage outside the repository. These commands **do not upload or publish**.

The JSON contract is `schemaVersion: 1`, `season: 2027`, `demo: false`,
`approvedForPrivateDisplay: true`, nonempty `generatedAt`, `scope`, and
`source`, and an array of rows. The approval field is a human assertion, **not**
independent evidence of provider permission. Do not set it without verifying
rights and approved audience/usage.

Keep unresolved team game-count records out of the approved team export.
Player-team membership, coverage, and data completeness need their own checks.
The 3+ games filter is a viewing control, not a source-validation rule.

## Go/no-go checks

- [ ] Provider terms or written permission cover the specific private display,
      caching, number of viewers, and any redistribution involved.
- [ ] NCAA Division I men's 2026–27 scope and opponent/game eligibility verified.
- [ ] Cloudflare Access policy covers **all** `/data/*` routes and the site.
- [ ] Unauthenticated direct JSON requests return 401/403 or an Access challenge
      with no provider data in the response body.
- [ ] Authorized JSON requests succeed on the private origin.
- [ ] No public GitHub Pages, Git history, Actions artifacts, logs, or caches
      contain real data or API credentials.
- [ ] Private JSON responses cannot be cached publicly.
- [ ] Fail-closed behavior verified when a dataset is absent or invalid.

**No deployment should occur until all checks are satisfied.**
