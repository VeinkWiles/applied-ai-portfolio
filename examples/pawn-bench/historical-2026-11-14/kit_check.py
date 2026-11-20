#!/usr/bin/env python3
"""Checker for a modular character kit: one .glb with the base body cut into regions plus separate gear
pieces, and its .json manifest (written by pare_lib.write_kit).

  kit_check.py KIT.glb KIT.json [--kit male|female|male-hair|female-hair] [--script BUILD.py] [--previews PREFIX] [--max-tris 10000] [--max-surfaces 12]
               [--max-texture 512]

Checks:
  names     the manifest lists body regions head/torso/arms/legs/feet, the always-shown meshes and every
            expected gear piece; the .glb holds exactly those meshes, one surface each.
  covers    every piece has the right set and slot and names the body regions it hides. In a -hair kit the hair
            styles are pieces in the slot "hair", and head pieces that cover the whole head say "hides": ["hair"].
  rig       same bone names as the source body; every mesh skinned.
  texture   no texture over --max-texture px.
  body      the body meshes together against the source body: texture, UVs, vertex colour, skin weights
            and shape (the same tests as glb_check.py).
  seams     the body regions still meet edge to edge (no cracks): the open-edge vertices along each cut coincide.
  <piece>   each gear piece against its own source file, same tests (shape at whole-character scale).
  loadouts  every loadout (none or one piece per slot; a worn piece hides the regions it covers) is within
            --max-tris and --max-surfaces. Prints bare, each full set, the mix and the heaviest.
  script    no automatic re-skinning.
  previews  PREFIX_bare.png, PREFIX_ranger.png, PREFIX_knight.png, PREFIX_mix.png exist and show a character.

Sources are read from <home>/src/art-packs/quaternius/Source (override with the KIT_SOURCES variable).
"""
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb_check as gc

ROOT = os.environ.get("KIT_SOURCES", "<home>/src/art-packs/quaternius/Source")
BODY_DIR = "Universal Base Characters[Source]/Base Characters/Exports/Godot - UE/"
MP = "Modular Character Outfits - Fantasy[Source]/Exports/glTF (Godot-Unreal)/Modular Parts/"
REGIONS = ["head", "torso", "arms", "legs", "feet"]
SLOTS = {"hood": ("head", []), "helm": ("head", []), "body": ("body", ["torso"]), "arms": ("arms", ["arms"]),
         "legs": ("legs", ["legs"]), "boots": ("feet", ["feet"]), "feet": ("feet", ["feet"]), "pauldron": ("pauldron", [])}
# per kit: body source file, then piece -> source file. Set = the name before "_", slot and covers from SLOTS.
KITS = {
    "male": ("Regular_Male_FullBody.gltf", {
        "ranger_hood": "Male_Ranger_Head_Hood.gltf", "ranger_body": "Male_Ranger_Body.gltf", "ranger_arms": "Male_Ranger_Arms.gltf",
        "ranger_legs": "Male_Ranger_Legs.gltf", "ranger_boots": "Male_Ranger_Feet_Boots.gltf", "ranger_pauldron": "Male_Ranger_Acc_Pauldron.gltf",
        "knight_helm": "Male_Knight_Head_Armet.gltf", "knight_body": "Male_Knight_Body_Armor.gltf", "knight_arms": "Male_Knight_Arms.gltf",
        "knight_legs": "Male_Knight_Legs_Armor.gltf", "knight_feet": "Male_Knight_Feet_Armor.gltf", "knight_pauldron": "Male_Knight_Acc_Pauldron_Round.gltf"}),
    "female": ("Regular_Female_FullBody.gltf", {
        "ranger_hood": "Female_Ranger_Head_Hood.gltf", "ranger_body": "Female_Ranger_Body.gltf", "ranger_arms": "Female_Ranger_Arms.gltf",
        "ranger_legs": "Female_Ranger_Legs.gltf", "ranger_boots": "Female_Ranger_Feet.gltf", "ranger_pauldron": "Female_Ranger_Acc_Pauldrons.gltf",
        "knight_helm": "Female_Knight_Head_Armet.gltf", "knight_body": "Female_Knight_Body_Armor.gltf", "knight_arms": "Female_Knight_Arms.gltf",
        "knight_legs": "Female_Knight_Legs.gltf", "knight_feet": "Female_Knight_Feet.gltf", "knight_pauldron": "Female_Knight_Acc_Pauldrons_Round.gltf"}),
}
CHAR_EXTENT = 1.8  # metres: pieces are compared at the pixel size of a whole character, like glb_check.py does
MIX = ["knight_helm", "knight_body", "ranger_arms", "ranger_legs", "ranger_boots"]
# kits with hair: "<kit>-hair" = the same kit plus hair styles in the slot "hair" (piece -> source file).
# Head pieces that cover the whole head must then say "hides": ["hair"]. The mix preview wears the second style.
HAIR_DIR = "Universal Base Characters[Source]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/"
HAIR = {"male": {"hair_parted": "Male/Hair_SimpleParted.gltf", "hair_ponytail": "Male/Hair_Ponytail.gltf"},
        "female": {"hair_bob": "Female/Hair_Bob.gltf", "hair_ponytail": "Female/Hair_Ponytail_2.gltf"}}
PART_KEYS = ["skinned", "texture", "materials", "look", "shape", "weights"]
# Gear pieces are cut much harder than a whole character, and the weight score compares each vertex with the
# nearest source vertex, so honest decimation scores 0.977-0.984 on arms (an automatic re-skin scores 0.95).
PIECE_WEIGHT_MIN = 0.97


SEAM_NEAR = 0.01   # metres: open-edge vertices of two regions this close belong to the same seam
SEAM_MIN = 0.85    # share of seam vertices that must sit exactly on the neighbouring region (reference build: 0.94)


def seam_share(g, bins, region_meshes):
    """(seam vertices that coincide with the neighbouring region, seam vertices). A seam vertex is an open-edge
    vertex of one body region within SEAM_NEAR of an open-edge vertex of another region. split_regions leaves
    them coincident; decimating a region afterwards moves them and opens cracks."""
    border = {}
    for node in g.get("nodes", []):
        if "mesh" not in node or node.get("name") not in region_meshes:
            continue
        verts = set()
        for prim in g["meshes"][node["mesh"]].get("primitives", []):
            pos = gc.read(g, bins, prim["attributes"]["POSITION"])
            idx = [i[0] for i in gc.read(g, bins, prim["indices"])]
            key = [(round(p[0], 4), round(p[1], 4), round(p[2], 4)) for p in pos]
            edges = {}
            for k in range(0, len(idx) - 2, 3):
                t = (key[idx[k]], key[idx[k + 1]], key[idx[k + 2]])
                for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                    if a != b:
                        e = (min(a, b), max(a, b))
                        edges[e] = edges.get(e, 0) + 1
            verts |= {v for e, c in edges.items() if c == 1 for v in e}
        border[node["name"]] = verts
    exact = total = 0
    for n, bv in border.items():
        others = set().union(*[v for m, v in border.items() if m != n]) if len(border) > 1 else set()
        cell = {}
        for q in others:
            cell.setdefault((round(q[0], 2), round(q[1], 2), round(q[2], 2)), []).append(q)
        for p in bv:
            if p in others:
                exact += 1; total += 1
                continue
            c = (round(p[0], 2), round(p[1], 2), round(p[2], 2))
            if any(sum((p[i] - q[i]) ** 2 for i in range(3)) <= SEAM_NEAR ** 2
                   for dx in (-0.01, 0, 0.01) for dy in (-0.01, 0, 0.01) for dz in (-0.01, 0, 0.01)
                   for q in cell.get((round(c[0] + dx, 2), round(c[1] + dy, 2), round(c[2] + dz, 2)), ())):
                total += 1
    return exact, total


def part_detail(r, weight_min=None):
    weight_min = gc.WEIGHT_MIN if weight_min is None else weight_min
    """One line of measured numbers for a body or piece check."""
    lk = "; ".join(f"{k} {v['kept']:.1%} of {v['vertices']}" for k, v in r["look_by_texture"].items())
    sm = r["shape_missing"]
    bits = [f"{r['triangles']} triangles, {r['surfaces']} surfaces",
            f"look {lk or 'no vertex matches the source'} (need {gc.LOOK_MIN:.0%})",
            f"shape missing at worst {max(sm.values()):.1%} ({max(sm, key=sm.get)}; max {gc.SHAPE_MAX:.0%})",
            f"weights {r['weight_overlap']:.3f} (need {weight_min})"]
    why = []
    if not r["skinned"]:
        why.append("unskinned: " + ", ".join(r["unskinned_meshes"]))
    if not r["texture"]:
        why.append("texture is not this source's texture (or missing)" + (f": {', '.join(r['foreign_texture_materials'])}" if r["foreign_texture_materials"] else ""))
    if not r["materials"]:
        why.append(f"{r['material_count']} materials, the source has {r['max_materials']}")
    for k, v in r["look_by_texture"].items():
        if v["kept"] < gc.LOOK_MIN:
            if v["image_ok"] < gc.LOOK_MIN:
                why.append(f"{k}: only {v['image_ok']:.1%} of its vertices are on this texture (wrong mesh in this piece, or faces moved to another material)")
            elif v["uv_ok"] < gc.LOOK_MIN:
                why.append(f"{k}: only {v['uv_ok']:.1%} keep the source UV (decimated too hard, or decimated after a join)")
            else:
                why.append(f"{k}: only {v['kept']:.1%} keep the source vertex colour")
    if not r["shape"]:
        why.append("shape: geometry missing or over-decimated; give this part more triangles")
    if not r["weights"]:
        why.append("skin weights differ from the source (never re-skin)")
    return "; ".join(bits) + ("" if not why else "\n      " + "\n      ".join(why))


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        sys.exit(2)
    glb, man_path = a[0], a[1]
    opt = lambda name, d: a[a.index(name) + 1] if name in a else d
    max_tris, max_surf, max_tex = int(opt("--max-tris", 10000)), int(opt("--max-surfaces", 12)), int(opt("--max-texture", 512))
    script, prefix = opt("--script", None), opt("--previews", None)
    kit = opt("--kit", "male")
    hair = kit.endswith("-hair")
    kit = kit[:-5] if hair else kit
    if kit not in KITS:
        print(f"--kit must be one of {sorted(KITS)}, or one of those with -hair added")
        sys.exit(2)
    BODY_SRC = BODY_DIR + KITS[kit][0]
    PIECES = {n: (n.split("_")[0],) + SLOTS[n.split("_")[1]] + (MP + src,) for n, src in KITS[kit][1].items()}
    mix = list(MIX)
    if hair:
        PIECES.update({n: ("hair", "hair", [], HAIR_DIR + src) for n, src in HAIR[kit].items()})
        mix = [sorted(HAIR[kit])[1]] + [m for m in MIX if PIECES[m][1] != "head"]
    ok_all = True

    def line(ok, name, text):
        nonlocal ok_all
        ok_all = ok_all and ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {text}")

    for p in (glb, man_path):
        if not os.path.isfile(p):
            print(f"FAIL  files: missing {p}\nCHECKS FAILED")
            sys.exit(1)
    g, bins = gc.load(glb)
    try:
        man = json.load(open(man_path))
        body, always, pieces = man["body"], list(man["always"]), man["pieces"]
        for p in pieces.values():
            p["set"], p["slot"], list(p["meshes"]), list(p["covers"])
    except Exception as e:
        print(f"FAIL  names: the manifest is not what pare_lib.write_kit writes ({type(e).__name__}: {e})\nCHECKS FAILED")
        sys.exit(1)

    # names
    count, surf = {}, {}
    for node in g.get("nodes", []):
        if "mesh" in node:
            prims = [p for p in g["meshes"][node["mesh"]].get("primitives", []) if p.get("mode", 4) == 4]
            n = node.get("name", "?")
            surf[n] = surf.get(n, 0) + len(prims)
            count[n] = count.get(n, 0) + sum(g["accessors"][p["indices"]]["count"] // 3 for p in prims)
    listed = list(body.values()) + always + [m for p in pieces.values() for m in p["meshes"]]
    problems = []
    if sorted(body) != sorted(REGIONS):
        problems.append(f"body regions are {sorted(body)}, expected {sorted(REGIONS)}")
    if not always:
        problems.append("'always' is empty (the eyes and eyebrows belong there)")
    if sorted(pieces) != sorted(PIECES):
        problems.append(f"missing pieces: {sorted(set(PIECES) - set(pieces)) or 'none'}; unexpected pieces: {sorted(set(pieces) - set(PIECES)) or 'none'}")
    if sorted(listed) != sorted(count):
        problems.append(f"meshes in the .glb but not in the manifest: {sorted(set(count) - set(listed)) or 'none'}; "
                        f"in the manifest but not in the .glb (or listed twice): {sorted(m for m in set(listed) if m not in count or listed.count(m) > 1) or 'none'}")
    multi = sorted(n for n, s in surf.items() if s != 1)
    if multi:
        problems.append(f"meshes with more than one surface: {multi}")
    line(not problems, "names", f"{len(count)} meshes, {len(pieces)} gear pieces" if not problems else "; ".join(problems))
    if problems:  # the rest needs a sound manifest
        print("CHECKS FAILED")
        sys.exit(1)

    wrong = [f"{n}: set/slot/covers are {pieces[n]['set']}/{pieces[n]['slot']}/{sorted(pieces[n]['covers'])}, expected {s}/{sl}/{cv}"
             for n, (s, sl, cv, _) in PIECES.items() if (pieces[n]["set"], pieces[n]["slot"], sorted(pieces[n]["covers"])) != (s, sl, cv)]
    if hair:
        wrong += [f"{n}: \"hides\" is {sorted(pieces[n].get('hides', []))}, expected {['hair'] if sl == 'head' else []}"
                  " (a hood or closed helm hides the hair slot; nothing else hides a slot)"
                  for n, (_, sl, _, _) in PIECES.items() if sorted(pieces[n].get("hides", [])) != (["hair"] if sl == "head" else [])]
    line(not wrong, "covers", "every piece has its set, slot, covered regions" + (" and hidden slots" if hair else "") if not wrong else "; ".join(wrong))

    # body and pieces against their sources
    results = {}
    rb = gc.check(glb, os.path.join(ROOT, BODY_SRC), 10 ** 9, 999, max_texture=max_tex, only=list(body.values()) + always)
    results["body"] = rb
    line(rb["bones"] and not [n for n in g.get("nodes", []) if "mesh" in n and "skin" not in n], "rig",
         f"{rb['bone_count']} bone names, same set as the source body: {rb['bones']}")
    big = rb["oversized_textures"]
    line(not big, "texture", f"largest texture {rb['largest_texture'][0] if rb['largest_texture'] else '?'} px (max {max_tex})"
         + ("" if not big else f"; over the limit: {', '.join(big)}: call pl.shrink_textures on the .glb"))
    line(all(rb[k] for k in PART_KEYS), "body", part_detail(rb))
    ex, tot = seam_share(g, bins, set(body.values()))
    line(tot > 0 and ex / tot >= SEAM_MIN, "seams", f"{ex} of {tot} seam vertices between body regions still meet ({ex / max(1, tot):.0%}, need {SEAM_MIN:.0%})"
         + ("" if tot > 0 and ex / tot >= SEAM_MIN else ": the regions have cracks between them. A region was decimated after split_regions; decimate the whole body mesh before the split and don't decimate body_* meshes afterwards"))
    for n, (_, _, _, src) in PIECES.items():
        r = gc.check(glb, os.path.join(ROOT, src), 10 ** 9, 999, max_texture=max_tex, only=pieces[n]["meshes"], shape_extent=CHAR_EXTENT)
        r["weights"] = r["weight_overlap"] >= PIECE_WEIGHT_MIN
        line(all(r[k] for k in PART_KEYS), n, part_detail(r, PIECE_WEIGHT_MIN))

    # loadouts
    slots = {}
    for n in sorted(pieces):
        slots.setdefault(pieces[n]["slot"], []).append(n)
    rows = []
    for combo in itertools.product(*[[None] + v for v in slots.values()]):
        worn = [c for c in combo if c]
        hidden = {s for c in worn for s in pieces[c].get("hides", [])}
        seen = [c for c in worn if pieces[c]["slot"] not in hidden]
        covered = {r for c in seen for r in pieces[c]["covers"]}
        shown = always + [m for r, m in body.items() if r not in covered] + [m for c in seen for m in pieces[c]["meshes"]]
        rows.append((sum(count[m] for m in shown), len(shown), worn))
    find = lambda want: next(r for r in rows if sorted(r[2]) == sorted(want))
    bare, mix = find([]), find(mix)
    full = {s: find([n for n in pieces if pieces[n]["set"] == s]) for s in sorted({p["set"] for p in pieces.values()}) if s != "hair"}
    heavy, most = max(rows), max(rows, key=lambda r: r[1])
    text = (f"{len(rows)} loadouts; bare {bare[0]} triangles / {bare[1]} surfaces; "
            + "; ".join(f"full {s} {r[0]} / {r[1]}" for s, r in full.items())
            + f"; mix {mix[0]} / {mix[1]}; heaviest {heavy[0]} triangles (max {max_tris}) wearing {', '.join(heavy[2])}; most surfaces {most[1]} (max {max_surf})")
    over = heavy[0] > max_tris or most[1] > max_surf
    if over:
        per = {sl: max([count[body[r]] for n in v for r in pieces[n]["covers"]] + [sum(count[m] for m in pieces[n]["meshes"]) for n in v]) for sl, v in slots.items()}
        text += "\n      heaviest choice per slot: " + ", ".join(f"{sl} {t}" for sl, t in per.items()) + f"; always shown: {sum(count[m] for m in always) + count[body['head']]}"
    line(not over, "loadouts", text)

    if script:
        ok, detail = gc.script_check(script)
        line(ok, "script", detail)
    if prefix:
        for name in ("bare", "ranger", "knight", "mix"):
            ok, detail = gc.preview_check(f"{prefix}_{name}.png", 512)
            line(ok, f"preview {name}", detail)
    print("ALL CHECKS PASS" if ok_all else "CHECKS FAILED")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
