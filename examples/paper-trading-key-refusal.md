# Paper-trading safety rails (described)

**Evidence:** Private, described. Taken from a review of the private `paper-trading-runner` repo on 18 Nov 2026, America/Chicago, including `src/config.js` and the "going live" commit. This is not a source listing, and it is not a promise that a later private revision is identical.

What the reviewed code and commits established:

- Secrets are loaded only from an uncommitted `state/.env`. They are not logged by the config file that was reviewed.
- Alpaca key IDs that start with `AK` (live keys) are refused. The runner is paper-only.
- The default dashboard bind is localhost. A dashboard token is part of the example environment names; no filled token belongs in a public repo.
- A 16 Nov 2026, 8:18 PM America/Chicago (CST) commit records a going-live plan and states that real-money trading is not built.

I am not copying `state/.env.example` from that repo into this one, because even empty key names sit next to a trading stack I am not publishing here. The empty placeholders in this portfolio's own [`.env.example`](../.env.example) are only for rerunning the published pawn-bench harness.
