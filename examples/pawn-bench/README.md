# pawn-bench (published subset)

This folder is a sanitized copy of the local harness: task prompts T1–T16, `run.sh`, `night-1114.sh`, agent and skill prompts, and the checkers.

It does **not** include transcripts, raw `results/` files, `pawn-logs/`, or handoff notes. For the 14 Nov 2026 overnight set, see [RESULTS-SUMMARY.md](RESULTS-SUMMARY.md). For what you can and cannot rerun from this copy, see [REPRODUCING.md](REPRODUCING.md). A [synthetic checker fixture](fixtures/) exercises the published checkers without private files, and [fixtures/test_harness.sh](fixtures/test_harness.sh) mocks harness exit status.

The scripts that ran on 14 Nov 2026 are kept unchanged in [historical-2026-11-14/](historical-2026-11-14/); the files in this folder are the current, fixed versions.

To point the scripts at your own checkouts, copy [../../.env.example](../../.env.example) and export `NEXTIMUS_PAWN`, `QUATERNIUS_SOURCE` (or the fallback alias `KIT_SOURCES`), and optionally `PAWN_LOGS`. The scripts do not auto-load a `.env` file. There are no API keys in this harness.
