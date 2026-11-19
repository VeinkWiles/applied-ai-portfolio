# paper-trading-runner

**Evidence:** Private, described. Prototype.  
**Where the evidence lives:** a private GitHub repository created 16 Nov 2026, 8:00 PM America/Chicago (CST). I have not copied the tree, the paper ledger, or any host configuration into this portfolio.

This is a standalone [Node.js](https://nodejs.org/) 24 runner for [Alpaca](https://alpaca.markets/) **paper** trading: a simulated brokerage account, not real money. It has a phone-first dashboard and optional push alerts. It was built, in a tight burst, under my name: about **26 commits** to `main` between 16 Nov 2026, 8:04 PM and 18 Nov 2026, 9:02 AM America/Chicago (CST), with **0 pull requests**. That process is looser than Nextimus, and I am not going to dress it up as the same pipeline.

Agents helped write and debug the code. I directed the work, including the safety rules that I care about most.

## Paper only, including when a key looks live

The first thing I want a reader to know is what this runner will not do.

- Secrets load from an uncommitted `state/.env`, not from the repo. The private repo's example file lists key *names* and empty values. I am not republishing a filled environment, a ledger, or a systemd unit.
- The config loader **refuses live Alpaca keys** whose id starts with `AK`. Paper keys are the only keys it is willing to use.
- A "going live" plan exists as a document and is explicit that real-money trading is **not built**. I am not presenting this as a production trading system, and I am not going to.

Those rails are the design. The rest of the runner — a paper engine, market hours, crypto plus stocks and ETFs, and a research tab — sits behind them. The research tab can pull news and watch public U.S. House filings and IPO / S-1 activity. I am describing that at a high level only; I am not publishing filing fixtures or any account state.

There is also a drafted instruction file for a local-LLM research and decision agent (a local Qwen model). A 17 Nov 2026 commit says that file is docs only and is not wired. I will not claim an autonomous trader that is not hooked up.

## What the mid-November commit trail actually shows

Because there are no issues or PRs, the review trail *is* the commit messages. They read like debugging notes, which is what they were: API 403 windows, PDF cross-reference streams, an OCR fallback for scanned filings, Telegram payload fixes, nickname matching. Almost every subject line repeats that the work is paper only.

The repo is documented as **zero npm dependencies**. Tests are plain Node `assert` files run in a loop over `tests/*.test.js`. The test tree is real — it includes fixtures — but I did not run it for this portfolio and I do not have a passing count I am willing to invent, so I am not putting a test number here.

What I will stand behind is the combination of a short, dense build, visible troubleshooting, and safety rules that fail closed on live credentials. That is the case study.
