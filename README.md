# Kevin Lewis

Green Bay

GitHub: [VeinkWiles](https://github.com/VeinkWiles)

I design systems and then direct AI coding agents to implement, test, and iterate them. The work I can actually show here is a Godot multiplayer graybox, a local agent-evaluation harness, a paper-only trading runner, and an earlier mobile d20 project.

I have been building with AI tools since at least 10 January 2026. The most concentrated work in this portfolio is from September through November 2026.

I own the concepts, the designs, and the decisions. Agents do most of the coding, debugging, and project-management work. The tools I actually use are SuperGrok, Claude Code, GPT Codex, Meta Muse, and a local Qwen3.6 35B A3B MLX model running in [LM Studio](https://lmstudio.ai/) through OpenClaw.

I also do data analysis as a general skill.

## Projects

| Project | What it is | Evidence |
|---|---|---|
| [Nextimus](case-studies/nextimus.md) | A Godot 4.7.2 graybox for a persistent, online Good-vs-Evil game. Spiritual successor to Xenimus, not a clone. | Private, described |
| [pawn-bench](case-studies/pawn-bench.md) | A local harness that grades coding and art agents on frozen Nextimus tasks. | Verified in this repo (harness, prompts, cleaned results, and selected previews) |
| [paper-trading-runner](case-studies/paper-trading-runner.md) | A Node 24 paper-trading runner with live-key refusal. Paper only; real-money trading is not built. | Private, described |
| [D20 Forge](case-studies/d20-forge.md) | A mobile d20 app (in-app name: Realms of Valor), built with Vibecode / Expo. | Private source, described. Prototype (v0). In-app screenshots verified in this repo. |

Evidence labels used throughout:

- **Verified in this repo** — the file or number is in this repository, or was read from a source that is copied here.
- **Private, described** — the work exists in a private repo or on a local machine. I describe it honestly and do not paste the private tree.
- **Prototype** — real code, not a shipped product.
- **Planned** — written down, not shown as finished.

## What's in this repository

- [case-studies/](case-studies/) — four write-ups, each structured differently.
- [architecture/](architecture/) — how the Nextimus agent pipeline and the pawn-bench harness are put together.
- [examples/pawn-bench/](examples/pawn-bench/) — sanitized task prompts, harness scripts, and checkers, plus a [cleaned results summary](examples/pawn-bench/RESULTS-SUMMARY.md).
- [examples/camera-spec.md](examples/camera-spec.md) — the numeric camera call that went into Nextimus PR #287.
- [demos/](demos/) — two real Nextimus graybox stills from PR #287, a graybox-vs-style-test comparison of the Good town square, five real D20 Forge in-app screenshots, two pawn-bench stills from the 14 Nov 16/16 run, and three T15 Sword_Attack GIFs from the harness reference scene. No synthetic screenshots.
- [SECURITY.md](SECURITY.md) — what this repo excludes, and how to report a problem.

This is a local draft. It is not an invitation to treat any of the private projects as public.

## License

The original writing and harness files in this repository are [MIT](LICENSE). Third-party art used by pawn-bench and shown in those demos (Quaternius Source character packs, and Quaternius MegaKits in the Good-town style test) is [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/); I did not author those meshes or the source animation clips. The style-test fountain, lamp posts, and ground textures were built by Knight (my Claude-backed agent, directed by me) for that look test. Raw `.glb` / `.blend` files are not in this repository. D20 Forge screenshots include Kenney tiles ([CC0](https://creativecommons.org/publicdomain/zero/1.0/)) and character sprites from a commercially licensed pack I did not author; the raw sprite files are not in this repository.
