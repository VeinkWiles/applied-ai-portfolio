# Kevin Lewis

Green Bay, WI

GitHub: [VeinkWiles](https://github.com/VeinkWiles)

## For small business owners

I work in manufacturing and used to manage a retail store, so I know what a small business owner's day looks like. Everything in this repo comes down to three habits I'd bring to a shop: break a messy job into clear steps, check whether the AI actually got it right, and fix the process when it breaks instead of hiding the problem.

**Example:** My AI agents froze for hours because every instruction went through a Slack channel and the AI got buried in the whole chat history. I moved coordination to GitHub so each agent only sees its own task, and the freezes stopped. When one code review burned most of my AI subscription's usage limit, I put the expensive model on reviews only and a cheaper one on everything else.

## Technical overview

I build AI-assisted tools, automations, evaluations, and local-model setups for people and teams who need that work done but don't have the expertise or compute in-house. The public example in this repo is pawn-bench, where I ran a Qwen3.6 35B model in [LM Studio](https://lmstudio.ai/) through OpenClaw and wrote the harness that grades the result.

In pawn-bench, a kit that officially passed still had cracked seams. I added a measurable seam check, tightened a shape limit after another soft pass, and kept both misses in the totals.

## Run the public fixture

```bash
python3 examples/pawn-bench/fixtures/test_checkers.py
```

- [pawn-bench case study](case-studies/pawn-bench.md)
- [Code](examples/pawn-bench/)
- [Results](examples/pawn-bench/RESULTS-SUMMARY.md)

**Roles I'd fit:** AI workflow and agent operations, AI evaluation/QA, technical product and prototyping, and junior AI engineer.

**Also open to:** hands-on AI help for local small businesses — manufacturers, retail shops, and service firms — and community workshops on practical AI use.

## Projects

| Project | What it is | Evidence |
|---|---|---|
| [pawn-bench](case-studies/pawn-bench.md) | A local harness that grades coding and art agents on frozen Nextimus tasks. | Verified in this repo (harness, prompts, cleaned results, and selected previews) |
| [Nextimus](case-studies/nextimus.md) | A Godot 4.7.2 LAN graybox — a playable prototype with placeholder visuals — for a persistent, online Good-vs-Evil game. Spiritual successor to Xenimus, not a clone, and not a shipped MMO. | Private, described |
| [paper-trading-runner](case-studies/paper-trading-runner.md) | A Node 24 paper-trading runner with live-key refusal. Paper only; real-money trading is not built. | Private, described |
| [D20 Forge](case-studies/d20-forge.md) | A mobile d20 app (in-app name: Realms of Valor), built with Vibecode / Expo. Prototype (v0). | Private source, described. In-app screenshots verified in this repo. |

I own the concepts, the designs, and the decisions. Agents do most of the coding, debugging, and project-management work. The tools I actually use are SuperGrok, Claude Code, GPT Codex, Meta Muse, and that local Qwen3.6 35B A3B MLX model. I have been building with AI tools since at least 10 January 2026; the most concentrated work here is from September through November 2026. I also do data analysis as a general skill.

Evidence labels used throughout:

- **Verified in this repo** — the file or number is in this repository, or was read from a source that is copied here.
- **Private, described** — the work exists in a private repo or on a local machine. I describe it honestly and do not paste the private tree.
- **Prototype** — real code, not a shipped product.
- **Planned** — written down, not shown as finished.

The [evidence index](EVIDENCE.md) lists the main public claims with a source, a verification level, a date, a limitation, and attribution. A label here means an artifact exists or is honestly described; it is not a badge that a third party re-ran the work. Clock times, private issue and pull-request numbers, and naming history live there and in the pawn-bench [results summary](examples/pawn-bench/RESULTS-SUMMARY.md).

## What's in this repository

- [case-studies/](case-studies/) — four write-ups. Each opens with the same short header (problem, role, tools, outcome, evidence, limitations).
- [architecture/](architecture/) — how the Nextimus agent pipeline and the pawn-bench harness are put together, including diagrams that match that behavior.
- [examples/pawn-bench/](examples/pawn-bench/) — sanitized task prompts, harness scripts, and checkers, a [cleaned results summary](examples/pawn-bench/RESULTS-SUMMARY.md), an honest [reproduction guide](examples/pawn-bench/REPRODUCING.md), and a [synthetic checker fixture](examples/pawn-bench/fixtures/).
- [examples/camera-spec.md](examples/camera-spec.md) — the numeric camera call I wrote for Nextimus.
- [demos/](demos/) — Nextimus graybox stills, a graybox-vs-style-test comparison of the Good town square, five D20 Forge in-app screenshots, two pawn-bench stills from the 14 Nov 16/16 run, and three T15 Sword_Attack GIFs from the harness reference scene. No synthetic screenshots.
- [SECURITY.md](SECURITY.md) — what this repo excludes, and how to report a problem.

This repository is the public portfolio. The private projects it describes stay private.

## License

The original writing and harness files in this repository are [MIT](LICENSE). Third-party art used by pawn-bench and shown in those demos (Quaternius Source character packs, and Quaternius MegaKits in the Good-town style test) is [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/); I did not author those meshes or the source animation clips. The style-test fountain, lamp posts, and ground textures were built by Knight (my Claude-backed agent, directed by me) for that look test. Raw `.glb` / `.blend` files are not in this repository. D20 Forge screenshots include Kenney tiles ([CC0](https://creativecommons.org/publicdomain/zero/1.0/)) and character sprites from a commercially licensed pack I did not author; the raw sprite files are not in this repository.
