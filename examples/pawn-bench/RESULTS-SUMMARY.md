# pawn-bench results summary (cleaned)

**Evidence:** Verified against the private lab notebook `RESULTS.md` for the `night-1114.sh` set. Transcripts, raw `results/` files, preview paths, and handoff notes are not included.

Times below are America/Chicago (CST). The private lab notebook summarized this set as 00:20–02:54; the first raw result file starts at 12:13 AM, and that is the time used here. The model alias `q36` is Qwen3.6 35B A3B MLX, run through LM Studio and OpenClaw, with house library `tools/pare_lib.py`, on Blender 5.3.0.

## Overnight set — 14 Nov 2026, 12:13 AM–2:54 AM

| | |
|---|---|
| Script | `night-1114.sh` |
| Result | **16/16 PASS first try** |
| Fix rounds | 0 |
| Infrastructure failures | 0 |
| Timeouts | 0 |
| Knight tasks T11–T12 | 4/4, 72–88 seconds per run |
| Kit tasks T13–T16 (three runs each) | 12/12, 483–1,067 seconds per run |

This is one model, one night, one machine. It is not a leaderboard.

## Cumulative `q36` + house-library totals

These totals include earlier runs, not only the overnight set.

| Task | Passes | What the miss was |
|---|---|---|
| T11 (knight) | 5/6 | Earlier run regraded by eye: armour was visibly rougher than the reference at a 3.6% shape error, after the limit was tightened from 4% to 3%. |
| T12 (knight, helmet on) | 3/3 | — |
| T13 (male kit) | 7/8 | Earlier run was a harness PASS, then regraded: the body was split after decimation and seams cracked (48% coincident seam vertices vs. about 94% on the reference). A seams rule (≥85%) was added afterward. |
| T14 (female kit) | 4/4 | — |
| T15 (male hair kit) | 4/4 | — |
| T16 (female hair kit) | 4/4 | — |

Still true as of that notebook entry: no kit run had yet exercised a harness fix round. Models also had a habit of leaving eyebrows at source density, which was noted and not turned into an automatic failure for this summary.

The 16 runs are three passes of T13–T16 (12 kit runs) followed by T11, T12, T11, T12 (4 knight runs), matching `night-1114.sh`. This set does not include T1–T7. I am not inventing per-task timings beyond the ranges in the notebook summary above.
