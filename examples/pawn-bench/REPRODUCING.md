# Reproducing pawn-bench from this public copy

This is an honest limit list, not a one-command quick start.

## What this folder is

A sanitized subset of the local harness: task prompts T1–T16, `run.sh`, `night-1114.sh`, agent and skill prompts, the checkers (`glb_check.py`, `kit_check.py`, `kit_loadout.py`, `pare_lib.py`), `gltf_stats.py`, `direct_agent.py`, and the four T4 log fixtures. A cleaned write-up of the 14 Nov 2026 overnight set is in [RESULTS-SUMMARY.md](RESULTS-SUMMARY.md). The scripts that ran that night are in [historical-2026-11-14/](historical-2026-11-14/); the current scripts are the fixed versions.

It does **not** include transcripts, raw `results/` files, `pawn-logs/`, handoff notes, Quaternius packs, or a Nextimus checkout.

## What you can run from this repository alone

- Read the tasks and the checkers.
- Run the [synthetic checker fixture](fixtures/): `python3 examples/pawn-bench/fixtures/test_checkers.py` from the repository root, or from this folder, `python3 fixtures/test_checkers.py`. That uses only the Python standard library. It does not need Blender, a model host, or any private tree. The meshes it builds are invented for the test. They are not Quaternius art and not a bench rerun.
- Run the mocked harness status tests: `bash examples/pawn-bench/fixtures/test_harness.sh`. Those tests invent a disposable git checkout and a fake `openclaw`; they do not call a model or open a private tree.
- `python3 -m py_compile` on the stdlib tools (`glb_check.py`, `kit_check.py`, `kit_loadout.py`, `gltf_stats.py`, `direct_agent.py`). `pare_lib.py` is a Blender `bpy` library and is not exercised here.

Pillow is optional. The fixture path does not need it. In the full checker, byte-identical source textures are compared with the standard library; recognizing a *resized* copy of a source texture uses Pillow if it is installed. Without Pillow, resized copies are not treated as a match.

A public GitHub Actions workflow, if present, runs only those syntax checks, the checker fixture, and the mocked harness status tests. It does not run `night-1114.sh` or any T-task against a real model.

## What a full task rerun needs (not in this repo)

- A **frozen Nextimus checkout** (`NEXTIMUS_PAWN`), with no remotes, at the revision the harness was written against. That tree is private. `run.sh` preflights that the path is a git work tree.
- **Quaternius Source packs** for T9–T16. The canonical variable is `QUATERNIUS_SOURCE`. `KIT_SOURCES` is a fallback alias that `kit_check.py` still honors. Those packs are [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). I bought the Source versions; I did not author the meshes, and they are not published here. `run.sh` preflights that the directory exists and passes `QUATERNIUS_SOURCE` into the kit checker.
- **Blender** for the art-pipeline tasks (the overnight set used 5.3.0).
- A **local model host**: LM Studio and an OpenClaw agent named `pawn` by default. The published `agent/SYSTEM.md` is the prompt that belongs in that external OpenClaw config; `run.sh` does not load the file itself on the OpenClaw path. `AGENT=direct` talks to LM Studio through `tools/direct_agent.py` and does load `agent/SYSTEM.md` by default. Alias `q36` is Qwen3.6 35B A3B MLX. Other aliases exist in `run.sh`; this page is not a vendor comparison.
- Optional `PAWN_LOGS` for preview or scene output.

Copy [../../.env.example](../../.env.example) and set the paths. **These scripts do not automatically load a `.env` file.** Export the variables in your shell, or run `set -a; . .env; set +a`. There are no API keys in this harness (`AGENT=direct` can read `LMS_API_KEY` or a local OpenClaw config at run time; nothing like that is stored in this repo).

Typical command, once those locals exist: `./run.sh T11 q36` from this folder. `night-1114.sh` is a wrapper for the 14 Nov 2026 overnight set only.

If a support file a given option needs is missing, `run.sh` now exits immediately with a message that names the file (the T4 log fixtures, `tools/direct_agent.py` for `AGENT=direct`, and `tools/gltf_stats.py` for T8–T12 reporting). Those files are included in this copy.

## What you still cannot reproduce from the public copy

- The 16/16 overnight table, byte for byte. The raw result files and the private lab notebook are not published. The cleaned summary is.
- Visual regrades (the T13 seam miss and the T11 3.6% shape miss) without the original exports and a reference to compare them to.
- T1–T7 Godot/GDScript tasks, which need the frozen game checkout and Godot, not only Python. T4 can use the published log fixtures, but the summarizer script the task asks the agent to write lives in the private game tree.

Infrastructure and provider errors are not scored as model failures; `run.sh` exits 75 for a persistent infra error and 124 for a timeout, distinct from a checker or agent failure (exit 1). Fix rounds, timeouts, and thinking level are optional `run.sh` settings, not defaults for the published 16/16 night (that set had 0 fix rounds, 0 infra failures, and 0 timeouts).
