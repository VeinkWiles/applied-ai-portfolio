# Evidence index

This page lists the main public claims in this repository: what is claimed, where to read it, what backs it, when it was dated, what the limit is, and who it is attributed to.

Verification levels used here:

- **Public artifact** — the file or number is in this repository, or can be re-derived from a file that is.
- **Reported private evidence** — taken from a private repository, a local snapshot, or a lab notebook, and described here. The private tree is not in this repo.
- **Independently reproducible** — can be re-derived from stated inputs without trusting a private log.
- **Unverified** — no artifact is offered.

A line in a case-study header that says work is "verified in this repo" means the artifact is here. It is not a third-party badge, and it is not a claim that the private tests were re-run for this portfolio.

Private filesystem paths, credentials, and collaborator names are not listed.

Case-study stories keep attribution and limitations in their headers. Clock times, private issue and pull-request numbers, and naming history are collected here and in [examples/pawn-bench/RESULTS-SUMMARY.md](examples/pawn-bench/RESULTS-SUMMARY.md).

## Front page

| Claim | Where | Source | Level | Date | Limitation | Attribution |
|---|---|---|---|---|---|---|
| Building with AI tools since at least 10 January 2026 | [README](README.md), [D20 Forge](case-studies/d20-forge.md) | Private Vibecode changelog stamp `2026-01-11T00:29:47Z` (10 Jan 2026, 6:29 PM America/Chicago (CST)) | Reported private evidence | 10 Jan 2026 | "At least" is deliberate; a later gap until October is also recorded | Kevin, with agents in Vibecode |
| pawn-bench is the public, inspectable project; Nextimus, the trading runner, and D20 Forge are described from private sources | [README](README.md) | This repository's file set | Public artifact | 19 Nov 2026 | Private trees stay private | Kevin |
| Data analysis is mentioned only as a general skill | [README](README.md) | Statement of skill, no workplace case study | Public artifact (the sentence) | — | No supporting artifact is offered beyond the statement | Kevin |

## pawn-bench

| Claim | Where | Source | Level | Date | Limitation | Attribution |
|---|---|---|---|---|---|---|
| 14 Nov 2026 overnight set is three passes of T13–T16 then four knight runs of T11/T12, 16/16 PASS first try, 0 fix rounds, 0 infra failures, 0 timeouts, 12:13 AM–2:54 AM America/Chicago (CST) | [case study](case-studies/pawn-bench.md), [RESULTS-SUMMARY](examples/pawn-bench/RESULTS-SUMMARY.md), [night-1114.sh](examples/pawn-bench/night-1114.sh) | Published wrapper script; private lab notebook and raw result files, re-opened 19 Nov 2026. The notebook line said 00:20–02:54; the first raw result file starts at 12:13 AM, and that is the time used here | Public artifact (script shape); reported private evidence (outcome and clock times) | 14 Nov 2026 | One model, one machine, one night, after the tighter rules. Not a generalized benchmark | q36 under the harness; Kevin (operator) |
| Knight runs 4/4 in 72–88 s; kit runs 12/12 in 483–1,067 s | Same pages | Raw overnight result files, re-opened 19 Nov 2026 | Reported private evidence | 14 Nov 2026 | Ranges, not a per-run public log | q36 |
| Cumulative q36 + house-library totals: T11 5/6, T12 3/3, T13 7/8, T14–T16 4/4. The two misses are earlier eye-regrades | [case study](case-studies/pawn-bench.md), [RESULTS-SUMMARY](examples/pawn-bench/RESULTS-SUMMARY.md) | Private lab notebook, re-opened 19 Nov 2026 | Reported private evidence | as of 14 Nov 2026 | Visual regrades mean the cumulative rate is not a frozen metric | Kevin (regrade); q36 (runs) |
| T13 seam false-positive: harness PASS in 667 s, 48% coincident vs about 94% on the reference; ≥85% rule added; next run 93%. That run is the miss in 7/8 | [case study](case-studies/pawn-bench.md#seam-false-positive) | Private result file and notebook (667 s, 48%, 93%); published `kit_check.py` has `SEAM_MIN = 0.85` and a comment that the reference share is 0.94 | Reported private evidence (the run); public artifact (the threshold in code) | 11 Nov 2026 | The 48% figure was measured in the regrade; the original checker had no seam test | Kevin (caught it and kept the miss); agent (the run) |
| T11 shape limit 4% → 3% after a passing run at 3.6%; that run is the miss in 5/6 | [case study](case-studies/pawn-bench.md#shape-limit) | Private notebook (3.6% run and the change); published `glb_check.py` has `SHAPE_MAX = 0.03` | Reported private evidence (the run); public artifact (the current cap) | 11 Nov 2026 | — | Kevin (threshold); agent (the run) |
| T11/T12 budget: at most 10,000 triangles and 6 surfaces. Four source figures about 25,200 + 4,800 + 1,700 + 1,000 add to 32,700 (T12, helmet on); T11 brief calls the starting total about 31,000 after the helmet is removed | [case study](case-studies/pawn-bench.md), [T11](examples/pawn-bench/tasks/T11.md), [T12](examples/pawn-bench/tasks/T12.md) | Published task briefs | Public artifact | — | The source figures are the brief's "about" values, not a fresh mesh count from this repo | Quaternius (sources); Kevin (brief) |
| T13–T16: every loadout at most 10,000 triangles and 12 surfaces; T15 brief lists Knight arms 9,144 and Ranger boots 9,172 | [case study](case-studies/pawn-bench.md), [T15](examples/pawn-bench/tasks/T15.md) | Published task briefs | Public artifact | — | — | Quaternius / Kevin |
| Overnight checker totals, including T11/T12 all at 9,847 triangles / 4 surfaces, and the T15 02:22 AM mix at 8,623 / 9 with heaviest 9,995 | [case study](case-studies/pawn-bench.md) | Raw overnight result files, re-opened 19 Nov 2026. T11 and T12 sharing 9,847 is in all four files | Reported private evidence | 14 Nov 2026, 02:48–02:54 AM America/Chicago (CST) | Raw files stay private; the table is a cleaned extract | q36 / checkers |
| T15 reference GIFs: `kit_scene` recorded 6,759, 9,460, 9,552, and 8,862 triangles for bare, full Knight, full Ranger, and a mix. These are the 12 Nov reference kit, not the 14 Nov agent export | [case study](case-studies/pawn-bench.md), [demos](demos/README.md) | Private scene log, re-opened 19 Nov 2026; published GIFs are 960×540, 19 frames, 80 ms/frame (12.5 fps), under 1 MB | Reported private evidence (the four counts); public artifact (the GIFs and frame timing) | 12 Nov 2026 | Do not read the GIFs as overnight agent output | Harness reference kit; Quaternius (meshes and clips) |
| Quaternius Source packs are CC0 1.0; Kevin bought the Source versions and did not author the meshes | [README](README.md), case study, [REPRODUCING](examples/pawn-bench/REPRODUCING.md) | Public CC0 license; purchase is stated | Public artifact (license); reported private evidence (purchase) | — | Packs are not in this repo | Quaternius (art); agents (paring and loadout); Kevin (tasks) |
| Synthetic fixture and mocked harness status tests | [fixtures](examples/pawn-bench/fixtures/) | Generated `.glb` files, `test_checkers.py`, and `test_harness.sh`, run locally 19 Nov 2026 | Public artifact; independently reproducible | 19 Nov 2026 | Not a bench rerun; not Quaternius. Does not run `pare_lib.py` or a real model | Kevin (fixture); published checkers and `run.sh` |

## Nextimus

| Claim | Where | Source | Level | Date | Limitation | Attribution |
|---|---|---|---|---|---|---|
| Godot 4.7.2 graybox, version 0.1.0; spiritual successor to Xenimus, not a clone; no Xenimus names, spells, towns, or assets | [case study](case-studies/nextimus.md) | Private repo review, 18 Nov 2026 | Reported private evidence | as of 18 Nov 2026 | LAN graybox, not a shipped MMO | Kevin, with a human collaborator and agents |
| Repo started 20 Sep 2026; work through PR #320, merged 14 Nov 2026, 9:38 PM America/Chicago (CST) | [case study](case-studies/nextimus.md) | Private GitHub metadata, 18 Nov 2026 review | Reported private evidence | 20 Sep–14 Nov 2026 | — | Kevin (merges) |
| As of 18 Nov 2026: 156 pull requests, 145 merged, 18 open issues | [case study](case-studies/nextimus.md) | GitHub search on that date, recorded as search results, not an audited inventory | Reported private evidence | 18 Nov 2026, America/Chicago (CST) | Not re-counted later | mixed; humans merge |
| Camera spec: ortho 7.25 m, 50° / 72°, 30 m back, feet-centered, 1.25× visual scale; 1.81 m bench Knight becomes about 2.26 m; walk speed stayed 7.5 m/s | [camera spec](examples/camera-spec.md), [case study](case-studies/nextimus.md) | Kevin's 12 Nov 2026 design note and PR #287 | Public artifact (the numbers in this repo); reported private evidence (the note and the PR) | 12 Nov 2026, 11:44 AM America/Chicago (CST) | — | Kevin (spec); Claude Code (PR #287); Kevin (merge) |
| Ground spans 4.73 m / 3.81 m ahead-behind and 6.44 m left-right; character about 20% / 10% of screen height | [camera spec](examples/camera-spec.md) | Derived from 7.25 m ortho size, 50°/72°, 16:9, 1.25× | Independently reproducible | 12 Nov 2026 | Relies on those stated assumptions | Kevin |
| PR #287 merged 12 Nov 2026, 9:03 PM America/Chicago (CST). The agent-written PR reports 44 of 44 scenarios in 458 s at `--playtest-speed=4` on a later head. That suite was not re-run for this portfolio | [case study](case-studies/nextimus.md) | Private PR #287, re-read 19 Nov 2026 | Reported private evidence | 12 Nov 2026 | Quoted from the PR, not a fresh log | Claude Code (PR text); Kevin (merge, and the quote-not-rerun caveat) |
| Graybox stills are 1920×1080 captures from PR #287 | [demos](demos/README.md) | Published PNGs are 1920×1080 | Public artifact | 12 Nov 2026 | Godot-reported 7.25 m is from the PR, not from image metadata | Nextimus graybox (programmer art) |
| Good-town style test, 23 Oct 2026, 3:36 PM America/Chicago (CDT), commit `55194db`, issue #92, PR #108, built by Knight (Claude-backed, directed by Kevin). Kits are Quaternius MegaKits (CC0). Knight built the fountain, lamp posts, and ground textures | [case study](case-studies/nextimus.md), [demos](demos/README.md) | Private commit and issue, re-read 19 Nov 2026 | Reported private evidence | 23 Oct 2026 | Git author is Kevin Lewis, consistent with the agent committing under his config. Not a pawn-bench T-task | Knight, directed by Kevin; Quaternius (kits) |
| Style-test brief (issue #92) specified 48 × 48 m. Issue #289 describes a later 24 × 24 m playable square and asks for a further shrink, still open in the issue | [case study](case-studies/nextimus.md) | Private issues #92 and #289. Numbers only; the repo is private, so there are no links | Reported private evidence | 22 Oct 2026 (#92); 12 Nov 2026 (#289) | Issue #289 was still open when read | Kevin (direction) |
| Pipeline: issue → branch → PR → Bishop review → human merge. Agents do not merge. Play-like-a-player signed 13 Oct 2026. PRs #303–#317 split the sim in ten parts. Networking is ENet on a LAN, not DTLS-hardened | [pipeline](architecture/nextimus-pipeline.md) | Private process docs and PR history, 18 Nov 2026 | Reported private evidence | Oct–Nov 2026 | Describes the intended loop | Bishop (review); humans (merge); Rook / Knight / Codex (implementation) |

## paper-trading-runner

| Claim | Where | Source | Level | Date | Limitation | Attribution |
|---|---|---|---|---|---|---|
| Node 24 Alpaca **paper** runner; about 26 commits to `main` between 16 Nov 2026, 8:04 PM and 18 Nov 2026, 9:02 AM America/Chicago (CST); 0 pull requests | [case study](case-studies/paper-trading-runner.md) | Private repo review, 18 Nov 2026 | Reported private evidence | 16–18 Nov 2026 | "About 26" is a paged list | Kevin (direction); agents (implementation) |
| Refuses live Alpaca keys whose id starts with `AK`; real-money trading is not built | [case study](case-studies/paper-trading-runner.md), [safety note](examples/paper-trading-key-refusal.md) | Private config review and a 16 Nov 2026, 8:18 PM CST "going live" commit | Reported private evidence | 16–18 Nov 2026 | Code is not published, so this cannot be re-run from the portfolio | Kevin (safety rule) |
| Tests exist but were not run for this portfolio; no passing count is quoted | [case study](case-studies/paper-trading-runner.md) | Honest omission | Reported private evidence (that tests exist) | 18 Nov 2026 | — | Kevin |
| No dashboard screenshots or ledger in this repo | [demos](demos/README.md) | Absence of those files | Public artifact | — | — | Kevin |

## D20 Forge

| Claim | Where | Source | Level | Date | Limitation | Attribution |
|---|---|---|---|---|---|---|
| v0 mobile d20 prototype, in-app name Realms of Valor, Vibecode / Expo | [case study](case-studies/d20-forge.md) | Private snapshots, 19 Nov 2026; screenshots in [demos](demos/) | Reported private evidence (source); public artifact (screenshots) | snapshots through 11 Oct 2026 | Not a production mobile app | Kevin (design); Vibecode agents (implementation) |
| Changelog starts 10 Jan 2026, 6:29 PM America/Chicago (CST); quiet after 11 Jan 2026, 2:13 AM CST; resumes 3 Oct 2026; last v0 stamp 11 Oct 2026, 12:21 PM America/Chicago (CDT) | [case study](case-studies/d20-forge.md) | Private changelog in the snapshots | Reported private evidence | Jan and Oct 2026 | No git history; most file mtimes are export times | Vibecode agents / Kevin |
| A Prisma folder named `20251003235745_init` is treated as a template stamp, not the start date | [case study](case-studies/d20-forge.md) | Package still named `template-app-53` | Reported private evidence | — | Conservative on purpose | template, not Kevin's start date |
| Expo pin 54.0.22; the snapshot README still says SDK 53. Party of up to four; 10-step creator; 7 races, 11 classes, 35 skills, 272-spell SRD list | [case study](case-studies/d20-forge.md) | Private `package.json` and app README | Reported private evidence | Oct 2026 snapshots | Counts are from that README, not re-counted from source arrays here | Kevin / SRD |
| In-app stills: Kenney tiles (CC0); commercially licensed character sprites Kevin did not author. Party-tab frame is scrolled down and shows two test parties of up to four (a level-2 party played up from level 1, and a separate level-5 test party). Haven, Woods, and Inventory show the four-member level-2 party. Danger 3 and 455 gp are visible on those stills | [case study](case-studies/d20-forge.md), [demos](demos/README.md) | Published JPEGs, 660×1354, EXIF/GPS stripped | Public artifact | processed 19 Nov 2026 | Raw sprites are not in this repo | Kevin (screenshots); Kenney (tiles); commercial sprite pack (portraits); Vibecode agents (the app) |
| No `test` script; lint/typecheck were not run for this portfolio | [case study](case-studies/d20-forge.md) | Private package scripts | Reported private evidence | 19 Nov 2026 | No passing count is quoted | Kevin |

## Dates, issue numbers, and naming (audit trail)

These details were moved out of the main case-study stories so the narratives can stay readable. They are still part of the public record.

| Item | Detail | Level |
|---|---|---|
| Overnight window | 14 Nov 2026, 12:13 AM–2:54 AM America/Chicago (CST). The private notebook said 00:20–02:54; the first raw result file starts at 12:13 AM | Reported private evidence |
| T11 / T12 still times | Published T11 still is the 02:51 AM run; published T15 mix still is the 02:22 AM run. T11/T12 raw files start 02:48–02:52 AM | Reported private evidence |
| Nextimus repo span | Started 20 Sep 2026; work through PR #320, merged 14 Nov 2026, 9:38 PM America/Chicago (CST) | Reported private evidence |
| Nextimus counts on 18 Nov 2026 | 156 pull requests, 145 merged, 18 open issues (search results that day, not a later recount) | Reported private evidence |
| Camera PR | PR #287 (issue #284), merged 12 Nov 2026, 9:03 PM America/Chicago (CST). Spec note written 12 Nov 2026, 11:44 AM CST | Reported private evidence |
| Style-test commit | 23 Oct 2026, 3:36 PM America/Chicago (CDT), commit `55194db`, issue #92, PR #108 | Reported private evidence |
| Town size issues | Issue #92: original 48 × 48 m brief. Issue #289: later 24 × 24 m playable square, further shrink still open. Numbers only; no private-repo links | Reported private evidence |
| "Play like a player" | Signed 13 Oct 2026. Sim split in PRs #303–#317 | Reported private evidence |
| D20 start and gap | Changelog starts 10 Jan 2026, 6:29 PM CST; quiet after 11 Jan 2026, 2:13 AM CST; resumes 3 Oct 2026; last v0 stamp 11 Oct 2026, 12:21 PM CDT | Reported private evidence |
| D20 naming | In-app name Realms of Valor; Expo `app.json` uses that name; a later handoff also calls the Vibecode project OpenD20 Forge; package still named `template-app-53` | Reported private evidence |
| Paper runner burst | About 26 commits to `main` between 16 Nov 2026, 8:04 PM and 18 Nov 2026, 9:02 AM America/Chicago (CST); private repo created 16 Nov 2026, 8:00 PM CST; 0 pull requests | Reported private evidence |
