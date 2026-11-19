"""House library for paring rigged glTF characters in headless Blender 5.3.

Use these functions instead of writing the Blender mechanics yourself. Every Blender call in
here comes from a bench run that passed the checker. Objects are always addressed by NAME,
so nothing breaks when a join or split replaces an object.

    import sys
    sys.path.insert(0, "<pawn-bench>/tools")
    import pare_lib as pl

    pl.start()
    pl.load([OUTFIT_GLTF, HEAD_GLTF, HAIR_GLTF])   # one or more sources -> ONE armature
    pl.remove("Some_Helmet")                       # optional: a part the task says to leave out
    pl.split_by_material()                         # every mesh ends up with exactly one material
    pl.report()                                    # table: name, triangles, material, colour layers
    pl.merge("outfit", ["Female_Wizard_Body", "Female_Wizard_Legs", ...])  # same material only
    # or: pl.merge_by_material("chr")              # one merged mesh per material, automatically
    pl.decimate("outfit", 0.5)                     # optional: your own ratio for one object
    pl.fit_budget(10000, protect=["Eyes"])         # scales the rest down until the total fits
    pl.export("/abs/path/out.glb")                 # meshes + the armature
    pl.shrink_textures("/abs/path/out.glb", 512)   # textures to at most 512 px a side
    pl.report()

Modular kits (a body cut into regions plus separate gear pieces in one .glb) also use rename(),
decimate_to(), split_regions() and write_kit(); see their docstrings.

Rules the library enforces (it raises an error with the reason instead of exporting something wrong):
  - merge() only joins parts that use the same material; the result has one material = one surface.
  - parts without a colour layer get a white one before a join, so nothing turns black.
  - the source materials are kept as imported (base colour, normal map, roughness); duplicates
    created by importing several files (MI_X.001) are folded into the first one (MI_X).
  - no re-skinning anywhere: vertex groups and the Armature modifier are kept.
"""
import re

import bpy

HELPERS = ("Icosphere", "Cube")


class PareError(Exception):
    pass


# ── small helpers ─────────────────────────────────────────────────────────────
def meshes():
    """Names of the character's mesh objects, sorted."""
    return sorted(o.name for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith(HELPERS))


def _obj(name):
    o = bpy.data.objects.get(name)
    if o is None or o.type != "MESH":
        raise PareError(f"no mesh object named {name!r}; current meshes: {meshes()}")
    return o


def armature():
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if len(arms) != 1:
        raise PareError(f"expected exactly one armature, found {[a.name for a in arms]}")
    return arms[0]


def tris(name=None):
    """Triangle count of one mesh, or of all meshes."""
    names = [name] if name else meshes()
    return sum(max(0, len(p.vertices) - 2) for n in names for p in _obj(n).data.polygons)


def material_of(name):
    """Name of the single material a mesh uses (after split_by_material)."""
    o = _obj(name)
    used = {p.material_index for p in o.data.polygons}
    mats = {o.data.materials[i].name for i in used if i < len(o.data.materials) and o.data.materials[i]}
    if len(mats) != 1:
        raise PareError(f"{name} uses {sorted(mats) or 'no'} materials; run split_by_material() first")
    return mats.pop()


def _deselect_all():
    for o in bpy.context.scene.objects:
        o.select_set(False)


def _only(o):
    _deselect_all()
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def _point_at_armature(o, arm):
    for mod in list(o.modifiers):
        if mod.type == "ARMATURE":
            o.modifiers.remove(mod)
    mod = o.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm
    o.parent = arm


def _single_slot(o, mat):
    """Make `mat` the only material slot of o (all its faces already use it)."""
    for p in o.data.polygons:
        p.material_index = 0
    o.data.materials.clear()
    o.data.materials.append(mat)


def _white_colour_layer(o):
    me = o.data
    if not any(c.name == "Color" for c in me.color_attributes):
        ca = me.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="CORNER")
        for loop in me.loops:
            ca.data[loop.index].color = (1.0, 1.0, 1.0, 1.0)


# ── pipeline steps ────────────────────────────────────────────────────────────
def start():
    """Empty scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load(paths):
    """Import one or more .gltf/.glb files and leave ONE armature that every mesh is skinned to.
    All files must have the same bone names."""
    if isinstance(paths, str):
        paths = [paths]
    for p in paths:
        bpy.ops.import_scene.gltf(filepath=p)
    for o in list(bpy.data.objects):  # importer helper shapes
        if o.type == "MESH" and o.name.startswith(HELPERS):
            bpy.data.objects.remove(o)
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if not arms:
        raise PareError("no armature in the imported files")
    keep = arms[0]
    bones = sorted(b.name for b in keep.data.bones)
    for extra in arms[1:]:
        if sorted(b.name for b in extra.data.bones) != bones:
            raise PareError(f"{extra.name} has different bone names from {keep.name}; these sources don't share a skeleton")
    for name in meshes():
        _point_at_armature(_obj(name), keep)
    for extra in arms[1:]:
        data = extra.data
        bpy.data.objects.remove(extra)
        if data.name in bpy.data.armatures:
            bpy.data.armatures.remove(data)
    # fold duplicate materials (MI_X.001 -> MI_X)
    for name in meshes():
        o = _obj(name)
        for i, m in enumerate(o.data.materials):
            if m is None:
                continue
            base = bpy.data.materials.get(re.sub(r"\.\d{3}$", "", m.name))
            if base is not None and base is not m:
                o.data.materials[i] = base
    print(f"pare_lib: loaded {len(paths)} file(s): {len(meshes())} meshes, {tris()} triangles, 1 armature with {len(bones)} bones")


def remove(names):
    """Delete meshes the task says to leave out (for example a helmet that would hide the face).
    Tell the checker too: --skip <name> for each one."""
    if isinstance(names, str):
        names = [names]
    for n in names:
        bpy.data.objects.remove(_obj(n))
    print(f"pare_lib: removed {names}; {len(meshes())} meshes, {tris()} triangles left")


def split_by_material():
    """Split every mesh that uses more than one material; afterwards each mesh has exactly one."""
    for name in meshes():
        o = _obj(name)
        if len({p.material_index for p in o.data.polygons}) < 2:
            continue
        before = set(meshes())
        _only(o)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="MATERIAL")
        bpy.ops.object.mode_set(mode="OBJECT")
        _deselect_all()
        pieces = [name] + sorted(set(meshes()) - before)
        for piece in pieces:
            po = _obj(piece)
            used = {p.material_index for p in po.data.polygons}
            if len(used) != 1:
                raise PareError(f"split of {name} left {piece} with {len(used)} materials")
            mat = po.data.materials[used.pop()]
            _single_slot(po, mat)
            new = f"{name}__{re.sub(r'[^A-Za-z0-9]+', '_', mat.name)}"
            po.name = new
            po.data.name = new
    arm = armature()
    for name in meshes():
        o = _obj(name)
        _single_slot(o, bpy.data.materials[material_of(name)])
        _point_at_armature(o, arm)


def merge(new_name, names):
    """Join meshes that share one material into a single mesh called new_name (one surface)."""
    names = list(names)
    if not names:
        raise PareError("merge() needs at least one mesh name")
    mats = {material_of(n) for n in names}
    if len(mats) != 1:
        raise PareError(f"merge({new_name!r}) mixes materials {sorted(mats)}; merge only parts with the same material, "
                        f"one merged mesh per material")
    mat = bpy.data.materials[mats.pop()]
    expected = sum(tris(n) for n in names)
    if any(len(_obj(n).data.color_attributes) for n in names):
        for n in names:  # a part without a colour layer would be filled with black by the join
            _white_colour_layer(_obj(n))
    first = _obj(names[0])
    if len(names) > 1:
        _deselect_all()
        for n in names:
            _obj(n).select_set(True)
        bpy.context.view_layer.objects.active = first
        bpy.ops.object.join()
    merged = _obj(names[0])  # the active object of the join survives under its own name
    merged.name = new_name
    merged.data.name = new_name
    _single_slot(merged, mat)
    _point_at_armature(merged, armature())
    _deselect_all()
    got = tris(new_name)
    if got != expected:
        raise PareError(f"merge({new_name!r}): expected {expected} triangles, got {got}")
    return new_name


def merge_by_material(prefix="part"):
    """Join all meshes that share a material: one merged mesh (one surface) per material.
    The simplest grouping that always fits a surface budget >= the number of materials.
    Returns {material name: merged mesh name}."""
    groups = {}
    for n in meshes():
        groups.setdefault(material_of(n), []).append(n)
    out = {}
    for mat, names in sorted(groups.items()):
        out[mat] = merge(f"{prefix}_{re.sub(r'[^A-Za-z0-9]+', '_', mat)}", names)
    return out


def decimate(name, ratio):
    """Collapse-decimate one mesh to about ratio x its triangles (0 < ratio < 1)."""
    if not 0.0 < ratio < 1.0:
        return tris(name)
    o = _obj(name)
    before = tris(name)
    _only(o)
    mod = o.modifiers.new(name="Decimate", type="DECIMATE")
    mod.ratio = ratio
    bpy.context.view_layer.update()
    bpy.ops.object.modifier_apply(modifier=mod.name)
    _deselect_all()
    after = tris(name)
    if after >= before:
        raise PareError(f"decimate({name!r}, {ratio:.3f}) did not reduce the mesh ({before} -> {after})")
    return after


def fit_budget(max_tris, protect=()):
    """Decimate every mesh not in `protect` by the same ratio until the total is <= max_tris.
    Call decimate() first on parts you want cut harder (boots, hidden layers); protect small
    parts that must stay crisp (eyes)."""
    protect = set(protect)
    for _ in range(6):
        total = tris()
        if total <= max_tris:
            break
        fixed = sum(tris(n) for n in meshes() if n in protect)
        free = total - fixed
        if free <= 0:
            raise PareError("fit_budget: every mesh is protected and the total is over budget")
        ratio = max(0.05, (max_tris * 0.985 - fixed) / free)
        if ratio >= 1.0:
            raise PareError("fit_budget: protected parts alone exceed the budget")
        for n in meshes():
            if n not in protect:
                decimate(n, ratio)
    if tris() > max_tris:
        raise PareError(f"fit_budget: still {tris()} triangles after 6 passes (budget {max_tris})")
    print(f"pare_lib: fit_budget -> {tris()} triangles (budget {max_tris})")
    return tris()


# ── modular kits (body split into regions + separate gear pieces) ─────────────
# which body region a bone belongs to; bones not listed (arms, hands, fingers) are "arms"
REGIONS = {"head": ("Head", "neck_"), "torso": ("root", "pelvis", "spine_", "clavicle_"),
           "legs": ("thigh_",), "feet": ("calf_", "foot_", "ball_")}
REGION_ORDER = ("head", "arms", "legs", "feet", "torso")


def _bone_region(bone):
    for region, prefixes in REGIONS.items():
        if bone.startswith(prefixes):
            return region
    return "arms"


def _face_regions(o):
    """Region of every polygon: the region whose bones carry the most weight on its vertices."""
    by_group = {g.index: _bone_region(g.name) for g in o.vertex_groups}
    vert = []
    for v in o.data.vertices:
        acc = {}
        for g in v.groups:
            r = by_group.get(g.group)
            if r is not None and g.weight > 0:
                acc[r] = acc.get(r, 0.0) + g.weight
        vert.append(acc)
    out = []
    for p in o.data.polygons:
        acc = {}
        for vi in p.vertices:
            for r, w in vert[vi].items():
                acc[r] = acc.get(r, 0.0) + w
        out.append(max(sorted(acc), key=acc.get) if acc else "torso")
    return out


def rename(old, new):
    """Give a mesh its final name."""
    if new in bpy.data.objects:
        raise PareError(f"rename: an object named {new!r} already exists")
    o = _obj(old)
    o.name = new
    o.data.name = new
    return new


def decimate_to(name, target_tris):
    """Decimate one mesh to about target_tris triangles (does nothing if it is already at or under)."""
    now = tris(name)
    if now <= target_tris:
        return now
    return decimate(name, target_tris / now)


def split_regions(name, prefix="body"):
    """Cut a body mesh into region meshes by skin weights: <prefix>_head, _torso, _arms, _legs, _feet.
    legs = thighs; feet = calves and feet (boots reach the knee); arms include the hands.
    No face is deleted and no vertex moves, so the regions together are still the whole body with no gaps.
    Decimate the body BEFORE calling this (decimating the regions afterwards opens cracks between them).
    Returns {region: mesh name}."""
    expected = tris(name)
    mat = bpy.data.materials[material_of(name)]
    present = set(_face_regions(_obj(name)))
    todo = [r for r in REGION_ORDER if r in present]
    out = {}
    for r in todo[:-1]:
        o = _obj(name)
        before = set(meshes())
        _only(o)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        fr = _face_regions(o)
        for p in o.data.polygons:
            p.select = fr[p.index] == r
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.separate(type="SELECTED")
        bpy.ops.object.mode_set(mode="OBJECT")
        _deselect_all()
        new = sorted(set(meshes()) - before)
        if len(new) != 1:
            raise PareError(f"split_regions: separating {r} from {name} made {len(new)} new meshes (expected 1)")
        out[r] = rename(new[0], f"{prefix}_{r}")
    out[todo[-1]] = rename(name, f"{prefix}_{todo[-1]}")
    arm = armature()
    for n in out.values():
        _single_slot(_obj(n), mat)
        _point_at_armature(_obj(n), arm)
    got = sum(tris(n) for n in out.values())
    if got != expected:
        raise PareError(f"split_regions({name!r}): expected {expected} triangles in total, got {got}")
    print("pare_lib: split_regions -> " + ", ".join(f"{n} {tris(n)}" for n in out.values()))
    return out


def kit_loadouts(body, always, pieces):
    """Every loadout of a kit: none or one piece per slot. A worn piece hides the body regions it covers and
    the pieces in the slots it hides ("hides": ["hair"] on a hood or closed helm).
    Returns [(triangles, surfaces, [worn piece names])], heaviest first."""
    import itertools
    count = {n: tris(n) for n in meshes()}
    slots = {}
    for pname, p in sorted(pieces.items()):
        slots.setdefault(p["slot"], []).append(pname)
    rows = []
    for combo in itertools.product(*[[None] + v for v in slots.values()]):
        worn = [c for c in combo if c]
        hidden = {s for c in worn for s in pieces[c].get("hides", [])}
        seen = [c for c in worn if pieces[c]["slot"] not in hidden]
        covered = {r for c in seen for r in pieces[c]["covers"]}
        shown = list(always) + [m for r, m in body.items() if r not in covered] + [m for c in seen for m in pieces[c]["meshes"]]
        rows.append((sum(count[m] for m in shown), len(shown), worn))
    return sorted(rows, key=lambda r: -r[0])


def write_kit(path, body, always, pieces, max_tris=10000, max_surfaces=12):
    """Write the kit manifest (.json) and print the loadout budget.
      body   = {"head": "body_head", "torso": ..., "arms": ..., "legs": ..., "feet": ...}   (from split_regions)
      always = ["body_eyes", "body_eyebrows"]                                              (never hidden)
      pieces = {"knight_body": {"set": "knight", "slot": "body", "meshes": ["knight_body"], "covers": ["torso"]}, ...}
    A piece may also have "hides": [slot, ...]: while it is worn, the piece in each of those slots is not drawn
    (a hood or closed helm hides the "hair" slot; a circlet would not). Hair styles are pieces in the slot "hair".
    Every mesh in the scene must be listed exactly once. Returns (triangles, surfaces) of the heaviest loadout;
    it does not raise when that is over budget, so check the printed line and re-plan."""
    import json
    listed = list(body.values()) + list(always) + [m for p in pieces.values() for m in p["meshes"]]
    if sorted(listed) != meshes():
        raise PareError(f"write_kit: the manifest must list every mesh exactly once; not listed: {sorted(set(meshes()) - set(listed))}; "
                        f"listed but missing or repeated: {sorted(m for m in set(listed) if m not in meshes() or listed.count(m) > 1)}")
    for pname, p in pieces.items():
        bad = [r for r in p["covers"] if r not in body]
        if bad:
            raise PareError(f"write_kit: {pname} covers unknown regions {bad}; regions: {sorted(body)}")
        slots = {q["slot"] for q in pieces.values()}
        bad = [s for s in p.get("hides", []) if s not in slots]
        if bad:
            raise PareError(f"write_kit: {pname} hides unknown slots {bad}; slots: {sorted(slots)}")
    rows = kit_loadouts(body, always, pieces)
    worst_t = rows[0]
    worst_s = max(rows, key=lambda r: r[1])
    bare = next(r for r in rows if not r[2])
    json.dump({"body": body, "always": list(always), "pieces": pieces,
               "triangles": {n: tris(n) for n in meshes()}}, open(path, "w"), indent=1)
    print(f"pare_lib: kit bare body: {bare[0]} triangles, {bare[1]} surfaces")
    for s in sorted({p["set"] for p in pieces.values()}):
        full = [n for n, p in sorted(pieces.items()) if p["set"] == s]
        r = next((r for r in rows if sorted(r[2]) == full), None)  # None: a set with two pieces in one slot (hair styles)
        if r is not None:
            print(f"pare_lib: kit full {s}: {r[0]} triangles, {r[1]} surfaces")
    print(f"pare_lib: kit heaviest loadout: {worst_t[0]} triangles (max {max_tris}) wearing {worst_t[2]}; "
          f"most surfaces: {worst_s[1]} (max {max_surfaces})"
          + ("" if worst_t[0] <= max_tris and worst_s[1] <= max_surfaces else "  <-- OVER BUDGET"))
    print(f"pare_lib: wrote {path}")
    return worst_t[0], worst_s[1]


def shrink_textures(path, max_px=512):
    """Shrink the textures inside an exported .glb to at most max_px a side (ASSETS.md: 512).
    Runs tools/shrink_textures.py with the system python3 (it needs Pillow, which Blender's Python lacks).
    Call it right after export()."""
    import os
    import subprocess
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shrink_textures.py")
    r = subprocess.run(["python3", tool, path, str(max_px)], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        raise PareError(f"shrink_textures failed: {r.stderr.strip()[-400:]}")


def report():
    """Print one line per mesh: triangles, material, colour layers, skinning. Returns the rows."""
    rows = []
    for n in meshes():
        o = _obj(n)
        used = sorted({o.data.materials[p.material_index].name for p in o.data.polygons
                       if p.material_index < len(o.data.materials) and o.data.materials[p.material_index]})
        rows.append((n, tris(n), used, [c.name for c in o.data.color_attributes], len(o.vertex_groups),
                     any(m.type == "ARMATURE" for m in o.modifiers)))
    print(f"pare_lib report: {len(rows)} meshes, {tris()} triangles, {sum(len(r[2]) for r in rows)} surfaces, "
          f"{len({m for r in rows for m in r[2]})} materials")
    for n, t, mats, cols, vg, arm in rows:
        print(f"  {n:44s} {t:6d} tris  mat={','.join(mats):28s} colour_layers={cols}  vertex_groups={vg}  armature_mod={arm}")
    return rows


def export(path):
    """Export every mesh plus the armature to a .glb. Fails if a mesh is unskinned or has several materials."""
    arm = armature()
    for n in meshes():
        o = _obj(n)
        material_of(n)
        if not len(o.vertex_groups) or not any(m.type == "ARMATURE" for m in o.modifiers):
            raise PareError(f"{n} is not skinned (vertex groups: {len(o.vertex_groups)})")
    _deselect_all()
    for n in meshes():
        _obj(n).select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_extras=False)
    print(f"pare_lib: exported {path}: {len(meshes())} meshes, {tris()} triangles")
