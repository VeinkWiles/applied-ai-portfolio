# pawn-bench (published subset)

This folder is a sanitized copy of the local harness: task prompts T1–T16, `run.sh`, `night-1114.sh`, agent and skill prompts, and the checkers.

It does **not** include transcripts, raw `results/` files, `pawn-logs/`, or handoff notes. For the 14 Nov 2026 overnight set, see [RESULTS-SUMMARY.md](RESULTS-SUMMARY.md). For what you can and cannot rerun from this copy, see [REPRODUCING.md](REPRODUCING.md). A [synthetic checker fixture](fixtures/) exercises the published checkers without private files.

To point the scripts at your own checkouts, copy [../../.env.example](../../.env.example) and set `NEXTIMUS_PAWN`, `QUATERNIUS_SOURCE`, and optionally `PAWN_LOGS`. There are no API keys in this harness.
