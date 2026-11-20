# D20 Forge

**Problem:** Build a mobile d20 game I could actually play, with party, adventure, and inventory, as an early AI-assisted project.  
**Role:** I owned the design, the prompts, and the decisions about what belonged in v0. Agents in Vibecode did the implementation.  
**Tools:** Vibecode / Expo / React Native (the 6 Oct 2026 snapshot pins `expo` at 54.0.22).  
**Outcome:** A v0 prototype, in-app name Realms of Valor, with in-app screenshots in this repo.  
**Evidence:** Private source, described. Prototype (the in-app version is labeled v0). In-app screenshots verified in this repo. Dates and stack verified in local snapshots on 19 Nov 2026, America/Chicago. The application code was not copied into this repository.  
**Limitations:** This is a v0 prototype, not a production mobile app. There is no `test` script, and I did not run lint or typecheck for this portfolio, so I have no passing count to quote. The source stays private.

D20 Forge is the earliest project in this portfolio I can date from the work itself, not just from a note. I built it in [Vibecode](https://www.vibecodeapp.com/) as a mobile d20 app. The Expo `app.json` name is **Realms of Valor**; a later handoff also calls the Vibecode project OpenD20 Forge.

## When I actually started

The Vibecode changelog in the snapshots I opened begins with an agent change at `2026-01-11T00:29:47Z`. That is **10 Jan 2026, 6:29 PM America/Chicago (CST)** — the same evening I wrote the "D20 Forge Notes" document (9:40–10:52 PM CST that night), and a little earlier.

The same changelog then goes quiet after 11 Jan 2026, 2:13 AM CST, and picks up again on 3 Oct 2026. The last stamp on the v0 snapshot is `2026-10-11T17:21:34Z`, or **11 Oct 2026, 12:21 PM America/Chicago (CDT)**. File mtimes on the trees are mostly export times, and there is no git history. A Prisma migration folder named `20251003235745_init` looks like 3 Oct 2025, but the app package is still called `template-app-53`, so I am treating that as a Vibecode template stamp, not as my start date.

That is why this portfolio says I have been building with AI tools since at least January 2026, not "for over a year." Ten January 2026 is after 19 Nov 2025.

## What is in the snapshots

The stack is Expo / React Native. The 6 Oct 2026 `package.json` pins `expo` at **54.0.22**; the README in that tree still says SDK 53. Navigation is Expo Router. State is Zustand with AsyncStorage. Styling is NativeWind. I used bun. There is a Hono / Prisma / SQLite backend with better-auth, documented for future cloud sync and login, not as the heart of the local game.

The 11 Oct 2026 handoff calls the rules an **OGL 3.5 / Pathfinder hybrid**. The app README is more specific about what that means in the build: mechanics from the d20 [SRD](https://en.wikipedia.org/wiki/System_Reference_Document) (System Reference Document) under the Open Game License 1.0a, with no Product Identity — no Golarion, no official unique names. The in-app title is original.

Those snapshots already contain a lot of the game, not just a shell: a party of up to four, a ten-step character creator, a character sheet, level-up (including adding a class), an Adventure tab for exploration, combat, inventory, a shop, a quest board, and a dice tab. The data side has the seven SRD races, eleven core classes, 35 skills, and a 272-spell SRD 3.5 list, with a subset actually wired to combat or to location effects such as Light and Detect Magic. Places like Haven, the Whispering Woods, and the Forgotten Crypt have danger tiers and skill challenges. By the v0 tree there are also Kenney Tiny Town and Tiny Dungeon tiles (CC0, per the handoff) and location maps.

The January notes' backlog — battle map, town NPCs, day/night, more of the bestiary — is no longer a fair picture of the October snapshots. Some of that landed; some of it is still design in the v0 roadmap. I am not going to pretend the October tree was a finished commercial app. The handoff itself labels that snapshot **v0**.

## Tests, licenses, and what I am not publishing

The mobile scripts include `lint` and `typecheck`. There is no `test` script. `jest` is in the dependencies, almost certainly from the template; I found no `*.test.ts` files. `testParty.ts` is seed data, not a test harness. I did not run lint or typecheck for this portfolio, so I have no passing count to quote.

The README says the application code is **proprietary** and the game content is under **OGL 1.0a**. Oryx Ultimate Fantasy sprites are commercially licensed; they are not in this repository. I also did not copy `.env` files, a local SQLite dev database, or the source tree itself.

## What the app looks like

These are iPhone screenshots of the running v0 app (in-app title **Realms of Valor**). I cropped off the iOS status bar and the "App Store" back label, stripped EXIF/GPS, and resized them for the web. Map tiles are [Kenney](https://kenney.nl/) Tiny Town / Tiny Dungeon (**CC0**). Character portraits are from a commercially licensed sprite pack; I did not author those sprites, and the raw sprite files are not in this repository.

![D20 Forge party roster](../demos/d20-forge-party.jpg)

*Party tab, scrolled down, showing two test parties of up to four. Visible here: three members of the level-2 test party I played up from level 1 (Clera, Human Cleric 2; Merla, Elf Wizard 2; Grukk, Human Barbarian 2, placeholder initial — Bram is the fourth member of that party, seen in the Haven, Woods, and Inventory stills) and two members of a separate level-5 test party (Bram, Human Fighter 5, and a second Clera at Cleric 5).*

![D20 Forge, Haven Village](../demos/d20-forge-haven-village.jpg)

*Adventure tab, Haven Village. The party bar, a Kenney-tiled village map, and actions to rest at the inn, visit the shop, or open the quest board.*

![D20 Forge, Whispering Woods](../demos/d20-forge-woods.jpg)

*Adventure tab, Whispering Woods, danger 3. The same four-member level-2 test party as the Haven and Inventory stills (Bram, Clera, Merla, and Grukk), a Kenney-tiled forest map, and explore / hunt actions.*

![D20 Forge party inventory](../demos/d20-forge-inventory.jpg)

*Party Inventory, with Grukk's list expanded: falchion in both hands, hide armor equipped, plus everyday gear. Party purse 455 gp.*

![D20 Forge spells and recent events](../demos/d20-forge-spells-events.jpg)

*Adventure tab, scrolled down: travel back to Haven or into the Test Shaft, a Cast a Spell list (Light, Detect Magic, Read Magic on Clera and Merla), and a recent-events log that includes completing "The Test Shaft."*

Agents in Vibecode (the changelog is a long list of agent changes, and the handoff notes Opus as the model in use there) did the implementation. I owned the design, the prompts, and the decisions about what belonged in v0.
