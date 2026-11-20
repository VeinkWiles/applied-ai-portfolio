# Reproducing pawn-bench from this public copy

This is an honest limit list, not a one-command quick start.

## What this folder is

A sanitized subset of the local harness: task prompts T1–T16, `run.sh`, `night-1114.sh`, agent and skill prompts, and the checkers (`glb_check.py`, `kit_check.py`, `kit_loadout.py`, `pare_lib.py`). A cleaned write-up of the 14 Nov 2026 overnight set is in [RESULTS-SUMMARY.md](RESULTS-SUMMARY.md).

It does **not** include transcripts, raw `results/` files, `pawn-logs/`, handoff notes, Quaternius packs, or a Nextimus checkout.

## What you can run from this repository alone

- Read the tasks and the checkers.
- Run the [synthetic checker fixture](fixtures/): `python3 examples/pawn-bench/fixtures/test_checkers.py` from the repository root, or from this folder, `python3 fixtures/test_checkers.py`. That uses only the Python standard library. It does not need Blender, a model host, or any private tree. The meshes it builds are invented for the test. They are not Quaternius art and not a bench rerun.
- `python3 -m py_compile` on the three stdlib checkers (`glb_check.py`, `kit_check.py`, `kit_loadout.py`). `pare_lib.py` is a Blender `bpy` library and is not exercised here.

A public GitHub Actions workflow, if present, runs only those syntax checks and the fixture test. It does not run `run.sh`, `night-1114.sh`, or any T-task.

## What a full task rerun needs (not in this repo)

- A **frozen Nextimus checkout** (`NEXTIMUS_PAWN`), with no remotes, at the revision the harness was written against. That tree is private.
- **Quaternius Source packs** for T8–T16 (`QUATERNIUS_SOURCE` / `KIT_SOURCES`). Those packs are [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). I bought the Source versions; I did not author the meshes, and they are not published here.
- **Blender** for the art-pipeline tasks (the overnight set used 5.3.0).
- A **local model host**: LM Studio and OpenClaw by default, or the direct LM Studio path `run.sh` already supports. Alias `q36` is Qwen3.6 35B A3B MLX. Other aliases exist in `run.sh`; this page is not a vendor comparison.
- Optional `PAWN_LOGS` for preview or scene output. Copy [../../.env.example](../../.env.example) and set the paths. There are no API keys in this harness.

Typical command, once those locals exist: `./run.sh T11 q36` from this folder. `night-1114.sh` is a wrapper for the 14 Nov 2026 overnight set only.

## What you still cannot reproduce from the public copy

- The 16/16 overnight table, byte for byte. The raw result files and the private lab notebook are not published. The cleaned summary is.
- Visual regrades (the T13 seam miss and the T11 3.6% shape miss) without the original exports and a reference to compare them to.
- T1–T7 Godot/GDScript tasks, which need the frozen game checkout and Godot, not only Python.

Infrastructure and provider errors are not scored as model failures. Fix rounds, timeouts, and thinking level are optional `run.sh` settings, not defaults for the published 16/16 night (that set had 0 fix rounds, 0 infra failures, and 0 timeouts).
