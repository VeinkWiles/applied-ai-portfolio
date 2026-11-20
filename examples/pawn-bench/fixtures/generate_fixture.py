#!/usr/bin/env python3
"""Build tiny synthetic GLB files for the published pawn-bench checkers.

These meshes are invented for the fixture. They are not Quaternius art, not
Nextimus assets, and not a pawn-bench task rerun. See README.md in this folder.
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _png_rgb(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _pack(fmt: str, rows) -> bytes:
    return b"".join(struct.pack("<" + fmt, *row) for row in rows)


def _box(xmin, ymin, zmin, xmax, ymax, zmax, skip=()):
    # 24 verts so each face has its own UVs; 12 triangles when all faces are kept.
    # skip is a set of face names: +z -z -x +x +y -y. Used to leave an open seam.
    faces_all = (
        ((xmin, ymin, zmax), (xmax, ymin, zmax), (xmax, ymax, zmax), (xmin, ymax, zmax)),  # +z
        ((xmax, ymin, zmin), (xmin, ymin, zmin), (xmin, ymax, zmin), (xmax, ymax, zmin)),  # -z
        ((xmin, ymin, zmin), (xmin, ymin, zmax), (xmin, ymax, zmax), (xmin, ymax, zmin)),  # -x
        ((xmax, ymin, zmax), (xmax, ymin, zmin), (xmax, ymax, zmin), (xmax, ymax, zmax)),  # +x
        ((xmin, ymax, zmax), (xmax, ymax, zmax), (xmax, ymax, zmin), (xmin, ymax, zmin)),  # +y
        ((xmin, ymin, zmin), (xmax, ymin, zmin), (xmax, ymin, zmax), (xmin, ymin, zmax)),  # -y
    )
    names = ("+z", "-z", "-x", "+x", "+y", "-y")
    faces = tuple(f for n, f in zip(names, faces_all) if n not in skip)
    pos, uv, col, jnt, wgt, idx = [], [], [], [], [], []
    for face in faces:
        base = len(pos)
        for i, p in enumerate(face):
            pos.append(p)
            uv.append(((i == 1 or i == 2), (i == 2 or i == 3)))
            col.append((1.0, 1.0, 1.0))
            jnt.append((0, 0, 0, 0))
            wgt.append((1.0, 0.0, 0.0, 0.0))
        idx.extend((base, base + 1, base + 2, base, base + 2, base + 3))
    return pos, uv, col, jnt, wgt, idx


def _write_glb(path: Path, meshes: list[dict], bone_name: str = "root") -> None:
    """meshes: list of {name, pos, uv, col, jnt, wgt, idx}."""
    blob = bytearray()
    views = []
    accessors = []

    def add(data: bytes, target: int | None, ctype: int, typ: str, count: int, extra=None):
        if len(blob) % 4:
            blob.extend(b"\x00" * (4 - len(blob) % 4))
        off = len(blob)
        blob.extend(data)
        view = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        vi = len(views)
        views.append(view)
        acc = {"bufferView": vi, "componentType": ctype, "count": count, "type": typ}
        if extra:
            acc.update(extra)
        accessors.append(acc)
        return len(accessors) - 1

    gl_meshes = []
    mesh_nodes = []
    for m in meshes:
        pos, uv, col, jnt, wgt, idx = m["pos"], m["uv"], m["col"], m["jnt"], m["wgt"], m["idx"]
        xs, ys, zs = [p[0] for p in pos], [p[1] for p in pos], [p[2] for p in pos]
        i_pos = add(_pack("fff", pos), 34962, 5126, "VEC3", len(pos),
                    {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]})
        i_uv = add(_pack("ff", uv), 34962, 5126, "VEC2", len(uv))
        i_col = add(_pack("fff", col), 34962, 5126, "VEC3", len(col))
        i_idx = add(_pack("H", [(i,) for i in idx]), 34963, 5123, "SCALAR", len(idx))
        attributes = {
            "POSITION": i_pos, "TEXCOORD_0": i_uv, "COLOR_0": i_col,
        }
        if not m.get("unskinned"):
            i_jnt = add(_pack("HHHH", jnt), 34962, 5123, "VEC4", len(jnt))
            i_wgt = add(_pack("ffff", wgt), 34962, 5126, "VEC4", len(wgt))
            attributes["JOINTS_0"] = i_jnt
            attributes["WEIGHTS_0"] = i_wgt
        prim = {"attributes": attributes, "indices": i_idx, "material": 0, "mode": 4}
        primitives = [prim]
        if m.get("extra_primitive"):
            primitives.append(dict(prim))
        gl_meshes.append({"name": m["name"], "primitives": primitives})
        node = {"name": m["name"], "mesh": len(gl_meshes) - 1}
        if not m.get("unskinned"):
            node["skin"] = 0
        mesh_nodes.append(node)

    ibm = (
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1,
    )
    i_ibm = add(_pack("f", [(v,) for v in ibm]), None, 5126, "MAT4", 1)
    png = _png_rgb(8, 8, (40, 120, 200))
    if len(blob) % 4:
        blob.extend(b"\x00" * (4 - len(blob) % 4))
    img_off = len(blob)
    blob.extend(png)
    img_view = len(views)
    views.append({"buffer": 0, "byteOffset": img_off, "byteLength": len(png)})

    skinned = any(not m.get("unskinned") for m in meshes)
    joint_index = len(mesh_nodes)
    nodes = mesh_nodes + ([{"name": bone_name}] if skinned else [])
    g = {
        "asset": {"version": "2.0", "generator": "applied-ai-portfolio synthetic fixture (not Quaternius)"},
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": views,
        "accessors": accessors,
        "images": [{"name": "T_Fixture_BaseColor", "mimeType": "image/png", "bufferView": img_view}],
        "samplers": [{}],
        "textures": [{"sampler": 0, "source": 0}],
        "materials": [{
            "name": "fixture",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.0,
                "roughnessFactor": 1.0,
            },
        }],
        "meshes": gl_meshes,
        "nodes": nodes,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "scene": 0,
    }
    if skinned:
        g["skins"] = [{"name": "armature", "joints": [joint_index], "inverseBindMatrices": i_ibm}]
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    bin_chunk = bytes(blob)
    bin_chunk += b"\x00" * ((4 - len(bin_chunk) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(bin_chunk)
    path.write_bytes(
        struct.pack("<4sII", b"glTF", 2, total)
        + struct.pack("<I4s", len(js), b"JSON")
        + js
        + struct.pack("<I4s", len(bin_chunk), b"BIN\x00")
        + bin_chunk
    )


def _seam_strips(n: int, n_shifted: int, shift: float = 0.005):
    """Two open edge strips that meet at y=0.5, with n vertices along the cut.

    The first n_shifted lower-strip vertices are moved down by `shift` metres
    (inside SEAM_NEAR, so they still count as seam vertices, but they are not
    coincident). 17/20 = 85% sits on the published SEAM_MIN; 16/20 is below it.
    """
    def strip(name, y_inner, seam_y, n_shifted=0):
        pos, uv, col, jnt, wgt, idx = [], [], [], [], [], []
        for i in range(n):
            x = -0.3 + 0.6 * (i / (n - 1))
            y_s = seam_y - (shift if i < n_shifted else 0.0)
            for y, u in ((y_s, 0.0), (y_inner, 1.0)):
                pos.append((x, y, 0.0))
                uv.append((i / (n - 1), u))
                col.append((1.0, 1.0, 1.0))
                jnt.append((0, 0, 0, 0))
                wgt.append((1.0, 0.0, 0.0, 0.0))
        for i in range(n - 1):
            a = 2 * i
            idx.extend((a, a + 1, a + 2, a + 1, a + 3, a + 2))
        return {"name": name, "pos": pos, "uv": uv, "col": col, "jnt": jnt, "wgt": wgt, "idx": idx}

    return [strip("body_torso", 0.6, 0.5, 0), strip("body_legs", 0.4, 0.5, n_shifted)]



def generate(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir or HERE)
    out_dir.mkdir(parents=True, exist_ok=True)
    src_pos, src_uv, src_col, src_jnt, src_wgt, src_idx = _box(-0.4, 0.0, -0.2, 0.4, 1.0, 0.2)
    source = {
        "name": "fixture_body",
        "pos": src_pos, "uv": src_uv, "col": src_col, "jnt": src_jnt, "wgt": src_wgt, "idx": src_idx,
    }
    paths = {}
    paths["source"] = out_dir / "synthetic_source.glb"
    _write_glb(paths["source"], [source])
    paths["good"] = out_dir / "synthetic_good.glb"
    _write_glb(paths["good"], [source])

    # Same silhouette, but much smaller — should fail the shape check.
    cpos, cuv, ccol, cj, cw, cidx = _box(-0.05, 0.0, -0.05, 0.05, 0.2, 0.05)
    paths["collapsed"] = out_dir / "synthetic_collapsed.glb"
    _write_glb(paths["collapsed"], [{
        "name": "fixture_body",
        "pos": cpos, "uv": cuv, "col": ccol, "jnt": cj, "wgt": cw, "idx": cidx,
    }])

    # Two body regions that meet on y=0.5. Each leaves that face open so the
    # shared perimeter is an open edge, which is what seam_share measures.
    torso = _box(-0.3, 0.5, -0.15, 0.3, 1.0, 0.15, skip=("-y",))
    legs = _box(-0.3, 0.0, -0.15, 0.3, 0.5, 0.15, skip=("+y",))
    paths["seams_ok"] = out_dir / "synthetic_seams_ok.glb"
    _write_glb(paths["seams_ok"], [
        {"name": "body_torso", "pos": torso[0], "uv": torso[1], "col": torso[2], "jnt": torso[3], "wgt": torso[4], "idx": torso[5]},
        {"name": "body_legs", "pos": legs[0], "uv": legs[1], "col": legs[2], "jnt": legs[3], "wgt": legs[4], "idx": legs[5]},
    ])
    # Shift the legs 5 mm down so the shared edge no longer coincides.
    shifted = _box(-0.3, -0.005, -0.15, 0.3, 0.495, 0.15, skip=("+y",))
    paths["seams_cracked"] = out_dir / "synthetic_seams_cracked.glb"
    _write_glb(paths["seams_cracked"], [
        {"name": "body_torso", "pos": torso[0], "uv": torso[1], "col": torso[2], "jnt": torso[3], "wgt": torso[4], "idx": torso[5]},
        {"name": "body_legs", "pos": shifted[0], "uv": shifted[1], "col": shifted[2], "jnt": shifted[3], "wgt": shifted[4], "idx": shifted[5]},
    ])

    # Same good box, but the mesh is not skinned.
    unskinned = dict(source)
    unskinned["unskinned"] = True
    paths["unskinned"] = out_dir / "synthetic_unskinned.glb"
    _write_glb(paths["unskinned"], [unskinned])

    # Two primitives on one mesh, for the surface-limit check.
    two_surf = dict(source)
    two_surf["extra_primitive"] = True
    paths["two_surfaces"] = out_dir / "synthetic_two_surfaces.glb"
    _write_glb(paths["two_surfaces"], [two_surf])

    # 20 coincident seam pairs; shift some lower verts by 5 mm (inside SEAM_NEAR, not exact).
    paths["seams_at_limit"] = out_dir / "synthetic_seams_at_limit.glb"
    _write_glb(paths["seams_at_limit"], _seam_strips(20, n_shifted=3))
    paths["seams_below_limit"] = out_dir / "synthetic_seams_below_limit.glb"
    _write_glb(paths["seams_below_limit"], _seam_strips(20, n_shifted=4))

    paths["corrupted"] = out_dir / "synthetic_corrupted.glb"
    paths["corrupted"].write_bytes(b"this is not a glTF or glB file")
    return paths


if __name__ == "__main__":
    paths = generate()
    for k, p in paths.items():
        print(f"{k}: {p.name} ({p.stat().st_size} bytes)")
