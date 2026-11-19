---
name: blender-rigged-pare
description: Reduce a rigged, skinned glTF character or outfit (one source file or several: outfit + head + hair) to a triangle and surface budget in headless Blender while keeping its skeleton, skin weights, textures and vertex colours; then check the export before reporting. Use for any "pare", "decimate", "merge parts", "assemble a character" or "character budget" job on vendor .gltf/.glb files.
---

# Paring a rigged character in Blender (headless)

The job: fewer triangles and fewer surfaces, **same character**. It has to look the same (textures, vertex colours), move the same (skin weights and skeleton), and pass the checker. A file that only hits the numbers is not done.

## Use the house tools. Don't write Blender mechanics yourself.

Three tools in `<pawn-bench>/tools/` do the fragile parts. They are tested on Blender 5.3 with these assets.

1. **`pare_lib.py`**: the build library. Your build script is a short plan that calls it.
2. **`render_preview.py`**: renders the preview from the exported .glb.
3. **`glb_check.py`**: the checker.

A complete build script looks like this:

```python
import sys
sys.path.insert(0, "<pawn-bench>/tools")
import pare_lib as pl

SOURCES = ["/abs/path/outfit.gltf"]            # one file, or several that share a skeleton
OUT = "<nextimus-pawn>/art/export/<asset>.glb"

pl.start()
pl.load(SOURCES)               # imports everything onto ONE armature, folds duplicate materials
pl.split_by_material()         # every mesh now has exactly one material
pl.report()                    # table: mesh name, triangles, material, colour layers
pl.decimate("Some_Big_Part", 0.4)        # optional: cut a part harder first (the task may say which)
merged = pl.merge_by_material("chr_name") # one merged mesh per material = fewest surfaces
pl.fit_budget(10000, protect=[merged["MI_Eyes"]])   # scale the rest down until the total fits
pl.report()
pl.export(OUT)
pl.shrink_textures(OUT, 512)   # ASSETS.md: textures at most 512 px a side
```

What the library gives you (read its docstring once: `sed -n 1,40p tools/pare_lib.py`):
- `load(paths)`: one or several sources; checks they share bone names; leaves one armature.
- `remove([names])`: drop a part the task says to leave out; pass `--skip <name>` to the checker for each.
- `split_by_material()`, `merge(new_name, [names])`, `merge_by_material(prefix)`: merge only joins parts with the same material, and it adds a white colour layer where one is missing so nothing turns black.
- `decimate(name, ratio)`, `fit_budget(max_tris, protect=[names])`.
- `report()`, `tris()`, `meshes()`, `material_of(name)`, `export(path)`, `shrink_textures(path, 512)`.
- It raises `PareError` with the reason instead of exporting something wrong. Read the message; it tells you what to change in your plan.

Your decisions are the plan: which sources, which parts to cut harder, how to group if `merge_by_material` doesn't suit the surface budget, what to protect. Mesh names come from `pl.report()`; don't guess them.

If the library truly can't do something the task needs, say so in your report. Don't replace it with your own join, split, material or export code.

## Workflow

1. **Read the task** for the sources, the budget, the asset name and the exact output paths.
2. **Write the build script** (above) to the path the task names. It must rebuild from the sources every time it runs.
3. **Run it headless with a log outside the repo:**
   `blender --background --python <script> > <pawn-logs>/<asset>.build.log 2>&1`
   then read only the lines that matter: `grep -E "pare_lib|PareError|Traceback|Error" <log>`.
4. **Render the preview from the exported .glb:**
   `blender --background --python <pawn-bench>/tools/render_preview.py -- <your .glb> <preview .png> 512`
5. **Run the checker** (Self-check, below).
6. **Look at the preview** with the image/read tool if it lets you. Every part present, colours as in the source, nothing black that isn't black in the source.
7. **Commit** the script, the .glb and the preview, by exact path (never `git add -A`). Run `git status` first and restore anything you didn't mean to change.

## Self-check (required before you say done)

```
python3 <pawn-bench>/tools/glb_check.py <your .glb> <source .gltf> [--also <extra source> ...] --max-tris <N> --max-surfaces <M> --preview <your preview .png> --size 512 --max-texture 512 --script <your build script>
```

Report **the checker's numbers**, not your script's, and paste its output into your report.
- Every line PASS and `ALL CHECKS PASS`: you may report `RESULT: done`.
- Any FAIL: read the line under it. The checker says what it measured (wrong texture, wrong UV, wrong vertex colour, missing geometry). Change your plan and rebuild.

## Rules

- **Never change the asset to satisfy the checker.** Don't brighten, recolour or rebuild materials, don't edit textures, don't add lights or emission, don't touch `render_preview.py` or `glb_check.py`. If a check fails and your plan is right, report it.
- **Three strikes.** If the same check has failed three times, stop. Report `RESULT: partial`, the failing line, and what you tried. Don't keep trying variations.
- **Never re-skin.** No `ARMATURE_AUTO`, no automatic or envelope weights.
- **Never touch the armature or the source files.**
- **Use the exact file names the task gives.**
- **Budget by plan, not by nudging.** `fit_budget` hits the triangle budget for you. Use `decimate` only for deliberate choices (a part the task says to cut first, a hidden layer).
- If a shape check fails after `fit_budget`, one part was cut too hard: lower the cut on visible parts and cut bulky hidden ones harder, or protect the small visible part.

## Modular kits (a body cut into regions plus separate gear pieces)

Some tasks ask for a kit instead of one finished character: one .glb that holds the base body cut into region meshes and every gear piece as its own mesh, plus a .json manifest. The game shows a loadout by showing the worn pieces and hiding the body regions they cover. Nothing is merged across pieces.

Extra library functions for this:
- `rename(old, new)`: give a mesh its final name.
- `decimate_to(name, triangles)`: decimate one mesh to about that many triangles.
- `split_regions(body_mesh, "body")`: cuts the body by skin weights into `body_head`, `body_torso`, `body_arms`, `body_legs`, `body_feet` and returns `{region: mesh name}`. Decimate the body **before** this call, never after: decimating a region afterwards opens cracks between regions.
- `write_kit(json_path, body, always, pieces)`: writes the manifest and prints the budget of the bare body, each full set and the heaviest loadout. Read that line. If it says OVER BUDGET, lower some targets and rebuild.

The pattern:

```python
pl.start(); pl.load([BODY] + GEAR_FILES); pl.split_by_material(); pl.report()
pl.decimate("<body mesh>", 0.5)
body = pl.split_regions("<body mesh>", "body")
pl.rename("Eyes", "body_eyes")
pl.decimate_to("<gear mesh>", 1500); pl.rename("<gear mesh>", "knight_body")     # once per gear mesh
pieces = {"knight_body": {"set": "knight", "slot": "body", "meshes": ["knight_body"], "covers": ["torso"]}}
pl.write_kit(OUT[:-4] + ".json", body, ["body_eyes", "body_eyebrows"], pieces)
pl.export(OUT); pl.shrink_textures(OUT, 512)
```

Budget by plan: a loadout is the always-shown meshes, the body regions no worn piece covers, and one piece (or none) per slot. So the heaviest loadout is about: always-shown + head region + for each slot the larger of (its heaviest piece, the body region that slot covers). Pick triangle targets that add up under the budget with a little room, because `decimate_to` lands near its target, not on it.

A piece that comes as several meshes with one material (a body plus belts): `decimate_to` each, then `merge("<piece name>", [names])`. A piece with two materials stays two meshes, both listed under that piece in the manifest.

Previews of a kit are per loadout: `blender --background --python .../render_preview.py -- <kit .glb> <png> 512 kit=<kit .json> wear=<piece,piece,...>` (`wear=` with nothing after it renders the bare body). The checker for kits is `tools/kit_check.py`; the task gives the exact command.

Hair in a kit: each hair style is a piece in the slot `hair` (`"set": "hair", "slot": "hair", "covers": []`). A head piece that covers the whole head gets `"hides": ["hair"]` in its manifest entry, so the hair is not drawn (and not counted) while it is worn. Size a hair style no heavier than the head pieces and the budget of the heaviest loadout stays the same.
