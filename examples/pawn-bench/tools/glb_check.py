#!/usr/bin/env python3
"""Check a pared-down skinned character against its source glTF. Python 3 stdlib only.

Usage: glb_check.py OUTPUT.glb SOURCE.gltf [--max-tris 10000] [--max-surfaces 6] [--max-materials N]
                   [--preview PREVIEW.png] [--size 512] [--script BUILD.py] [--also SOURCE2.gltf ...]
                   [--max-texture 512] [--skip SOURCE_NODE ...] [--json]

--skip leaves a source part out of the comparison by node name (repeatable), for a part the task says
to drop (a helmet that would hide the face).
--also adds another source file (repeatable) when the output is assembled from several sources
(outfit + head + hair). All checks then compare against the sources taken together.

Checks:
  budget    triangles and surfaces (mesh primitives) within the limits
  bones     the same set of bone names as the source
  skinned   every mesh is skinned (has a skin, JOINTS_0 and WEIGHTS_0)
  texture   every surface uses a base colour texture, and each base colour image is one of the
            source's base colour images: byte-identical, or a resized copy of it (compared as
            32x32 thumbnails; needs optional Pillow). Without Pillow, only byte-identical
            source images count; resized copies are not recognized. With --max-texture N, no embedded image (colour,
            normal, roughness) may have a side longer than N pixels.
  materials surfaces use at most --max-materials materials (default: the number of distinct
            base colour images in the source, 2 for the Ranger: outfit + skin)
  look      each output vertex keeps the look of its source vertex: the same base colour
            image (by content), UVs within 0.01, and the same vertex colour (COLOR_0, which
            multiplies the texture; missing = white). Joining a part that has no colour attribute
            onto one that has fills it with black, which renders as a black face, hair or pauldron. Catches skin painted with the outfit
            texture and broken UVs. Needs 97% of matched vertices.
  weights   skin weights still match the source: for each output vertex, the nearest
            source vertex (within 2 cm) and the overlap of their per-bone weights.
            Kept weights score ~0.99 after decimation; needs 0.98.
  shape     the visible surface of the source is still there. Source and output are drawn as
            depth maps from the front, back, left, right and top (rest pose, 128 px); a source
            pixel is "missing" if the output has nothing there or its surface lies more than
            4 cm behind. At most 3% may be missing in any view (good runs score 1 to 2.5%). Catches deleted or unexported
            parts (missing sleeves) and heavy over-decimation; removing hidden faces is fine.
  script    (with --script) the build script doesn't re-skin: no ARMATURE_AUTO (automatic
            weights) outside comments. Bone heat often fails on this mesh and leaves most
            weights in place, so the weights check alone can miss it.
  preview   (with --preview) the PNG exists at exactly that path, is SIZE x SIZE, and shows the
            textured character: it covers at least 2% of the image in colours that differ from
            the background, at most 60% of those pixels are near-black, and their mean
            saturation is at least 0.12 (an untextured grey render is about 0.05; steel armour is about 0.2).
Exit code 0 when every check passes, 1 otherwise.
"""
import argparse, json, math, os, struct, sys

CT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
WEIGHT_MIN = 0.98   # mean weight overlap needed (kept weights ~0.99; one 11-09 auto re-skin 0.95; rigid ~0.81)
NEAR = 0.02         # metres
UV_TOL = 0.01       # UV distance counted as "same UV"
COLOR_TOL = 0.15    # per-channel difference allowed between output and source vertex colour (COLOR_0)
LOOK_MIN = 0.97     # per source texture: share of its matched vertices that must keep image and UV
IMAGE_NAMES = {}
IMAGE_BYTES = {}
THUMB_TOL = 8.0     # mean per-channel difference (0-255) allowed between a resized texture and its source
DARK_MAX = 0.60     # preview: share of character pixels that may be near-black
SAT_MIN = 0.12      # preview: mean saturation of character pixels


def load(path):
    data = open(path, "rb").read()
    if data[:4] == b"glTF":
        n = struct.unpack_from("<I", data, 12)[0]
        g = json.loads(data[20:20 + n])
        off = 20 + n
        ln = struct.unpack_from("<I", data, off)[0]
        return g, [data[off + 8:off + 8 + ln]]
    g = json.loads(data)
    base = os.path.dirname(path)
    return g, [open(os.path.join(base, b["uri"]), "rb").read() for b in g.get("buffers", [])]


def read(g, bins, i):
    a = g["accessors"][i]
    bv = g["bufferViews"][a["bufferView"]]
    buf = bins[bv.get("buffer", 0)]
    fmt = CT[a["componentType"]]
    size = struct.calcsize("<" + fmt)
    n = NC[a["type"]]
    stride = bv.get("byteStride", size * n)
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    norm = a.get("normalized", False) and fmt in "BH"
    scale = {"B": 255.0, "H": 65535.0}.get(fmt, 1.0)
    out = []
    for k in range(a["count"]):
        v = struct.unpack_from("<" + fmt * n, buf, start + k * stride)
        out.append(tuple(x / scale for x in v) if norm else v)
    return out


def summary(g):
    tris = surfaces = 0
    for node in g.get("nodes", []):
        if "mesh" not in node:
            continue
        for prim in g["meshes"][node["mesh"]].get("primitives", []):
            if prim.get("mode", 4) != 4:
                continue
            surfaces += 1
            idx = prim.get("indices")
            tris += (g["accessors"][idx]["count"] if idx is not None else g["accessors"][prim["attributes"]["POSITION"]]["count"]) // 3
    bones = set()
    for s in g.get("skins", []):
        bones |= {g["nodes"][j].get("name", "") for j in s.get("joints", [])}
    return tris, surfaces, bones


def base_images(g, bins, base_dir=None):
    """{material index: md5 of its base colour image bytes}; also fills IMAGE_NAMES {md5: name}"""
    import hashlib
    out = {}
    for mi, m in enumerate(g.get("materials", [])):
        bc = m.get("pbrMetallicRoughness", {}).get("baseColorTexture")
        if not bc:
            continue
        im = g["images"][g["textures"][bc["index"]]["source"]]
        if "bufferView" in im:
            bv = g["bufferViews"][im["bufferView"]]
            data = bins[bv.get("buffer", 0)][bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
        elif base_dir is not None and "uri" in im:
            data = open(os.path.join(base_dir, im["uri"]), "rb").read()
        else:
            continue
        out[mi] = hashlib.md5(data).hexdigest()
        IMAGE_NAMES.setdefault(out[mi], im.get("name") or os.path.splitext(im.get("uri", "?"))[0])
        IMAGE_BYTES[out[mi]] = data
    return out


def thumb(data):
    """32x32 RGB thumbnail bytes of an image, or None without Pillow."""
    try:
        import io
        from PIL import Image
        return Image.open(io.BytesIO(data)).convert("RGB").resize((32, 32), Image.BOX).tobytes()
    except Exception:
        return None


def image_size(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    try:
        import io
        from PIL import Image
        return Image.open(io.BytesIO(data)).size
    except Exception:
        return None


def skinned_vertices(g, bins, images=None):
    """[(position, {bone name: weight}, uv, base image md5)] for every skinned vertex."""
    images = images or {}
    out = []
    for node in g.get("nodes", []):
        if "mesh" not in node or "skin" not in node:
            continue
        joints = [g["nodes"][j].get("name", "") for j in g["skins"][node["skin"]]["joints"]]
        for prim in g["meshes"][node["mesh"]].get("primitives", []):
            at = prim["attributes"]
            if "JOINTS_0" not in at or "WEIGHTS_0" not in at:
                continue
            pos, jn, wt = read(g, bins, at["POSITION"]), read(g, bins, at["JOINTS_0"]), read(g, bins, at["WEIGHTS_0"])
            uvs = read(g, bins, at["TEXCOORD_0"]) if "TEXCOORD_0" in at else [None] * len(pos)
            # COLOR_0 multiplies the base colour; a missing attribute means white
            cols = [c[:3] for c in read(g, bins, at["COLOR_0"])] if "COLOR_0" in at else [(1.0, 1.0, 1.0)] * len(pos)
            img = images.get(prim.get("material"))
            for p, js, ws, uv, col in zip(pos, jn, wt, uvs, cols):
                total = sum(ws) or 1.0
                d = {}
                for j, w in zip(js, ws):
                    if w > 0:
                        d[joints[int(j)]] = d.get(joints[int(j)], 0.0) + w / total
                out.append((p, d, uv, img, col))
    return out


def weight_overlap(out_verts, src_verts):
    """(mean weight overlap with the nearest source vertex, unmatched count,
    {source image of the nearest source vertex: [kept, total]}) where kept = the output vertex has
    the same image and a UV within UV_TOL of some source vertex within NEAR"""
    cell = NEAR
    grid = {}
    for p, d, uv, img, col in src_verts:
        grid.setdefault((math.floor(p[0] / cell), math.floor(p[1] / cell), math.floor(p[2] / cell)), []).append((p, d, uv, img, col))
    scores = []
    unmatched = 0
    groups = {}
    for p, d, uv, img, col in out_verts:
        c = (math.floor(p[0] / cell), math.floor(p[1] / cell), math.floor(p[2] / cell))
        best, bimg, bd, look = None, None, NEAR * NEAR, False
        ok_img = ok_uv = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for q, e, quv, qimg, qcol in grid.get((c[0] + dx, c[1] + dy, c[2] + dz), ()):
                        dist = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
                        if dist < bd:
                            best, bimg, bd = e, qimg, dist
                        if not look and dist < NEAR * NEAR and img is not None and img == qimg:
                            ok_img = True
                            if uv is not None and quv is not None and abs(uv[0] - quv[0]) <= UV_TOL and abs(uv[1] - quv[1]) <= UV_TOL:
                                ok_uv = True
                                if max(abs(col[i] - qcol[i]) for i in range(3)) <= COLOR_TOL:
                                    look = True
        if best is None:
            unmatched += 1
            continue
        gr = groups.setdefault(bimg, [0, 0, 0, 0]); gr[0] += look; gr[1] += 1; gr[2] += ok_img; gr[3] += ok_uv
        scores.append(sum(min(w, best.get(b, 0.0)) for b, w in d.items()))
    n = len(scores)
    return (sum(scores) / n if n else 0.0), unmatched, groups


SHAPE_RES = 128
SHAPE_TOL = 0.04    # metres the output surface may sit behind the source surface
SHAPE_MAX = 0.03    # share of source pixels that may be missing in any one view
SHAPE_HOLE = 0.20   # metres: output this far behind means the view goes through an opening, see shape_check
SHAPE_MIN_PIXELS = 300  # a view where the source covers fewer pixels (an arm seen end-on) is scored as if it covered this many
SHAPE_VIEWS = {"front": (0, 1, 2, 1), "back": (0, 1, 2, -1), "right": (2, 1, 0, 1), "left": (2, 1, 0, -1), "top": (0, 2, 1, 1)}


def mesh_triangles(g, bins):
    out = []
    for node in g.get("nodes", []):
        if "mesh" not in node:
            continue
        for prim in g["meshes"][node["mesh"]].get("primitives", []):
            if prim.get("mode", 4) != 4:
                continue
            pos = read(g, bins, prim["attributes"]["POSITION"])
            idx = [i[0] for i in read(g, bins, prim["indices"])] if prim.get("indices") is not None else list(range(len(pos)))
            for k in range(0, len(idx) - 2, 3):
                out.append((pos[idx[k]], pos[idx[k + 1]], pos[idx[k + 2]]))
    return out


def depth_map(tris, view, lo, scale):
    u, v, w, sgn = SHAPE_VIEWS[view]
    res, buf = SHAPE_RES, {}
    for t in tris:
        x = [(p[u] - lo[u]) * scale for p in t]; y = [(p[v] - lo[v]) * scale for p in t]; z = [p[w] * sgn for p in t]
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-12:
            continue
        for py in range(max(0, int(min(y))), min(res - 1, int(max(y))) + 1):
            cy = py + 0.5
            for px in range(max(0, int(min(x))), min(res - 1, int(max(x))) + 1):
                cx = px + 0.5
                a = ((y[1] - y[2]) * (cx - x[2]) + (x[2] - x[1]) * (cy - y[2])) / d
                b = ((y[2] - y[0]) * (cx - x[2]) + (x[0] - x[2]) * (cy - y[2])) / d
                c = 1 - a - b
                if a < -0.01 or b < -0.01 or c < -0.01:
                    continue
                zz = a * z[0] + b * z[1] + c * z[2]
                k = py * res + px
                if k not in buf or zz > buf[k]:
                    buf[k] = zz
    return buf


def shape_check(g, bins, st, min_extent=0.0):
    """{view: share of the source's visible pixels that the output is missing}; st = source triangles"""
    ot = mesh_triangles(g, bins)
    lo = [min(p[i] for t in st for p in t) for i in range(3)]
    hi = [max(p[i] for t in st for p in t) for i in range(3)]
    # min_extent keeps the pixel size of a whole character when only one small piece is compared (kit_check.py)
    scale = (SHAPE_RES - 1) / max([hi[i] - lo[i] for i in range(3)] + [min_extent])
    out = {}
    for view in SHAPE_VIEWS:
        sd, od = depth_map(st, view, lo, scale), depth_map(ot, view, lo, scale)
        miss = 0
        for k, z in sd.items():
            if k not in od:
                miss += 1  # nothing there at all: lost silhouette
            elif od[k] < z - SHAPE_TOL and od[k] >= z - SHAPE_HOLE:
                miss += 1  # surface pushed back a little: over-decimated
            elif od[k] < z - SHAPE_HOLE:
                # the output is far behind here: the view goes through an opening to something well below. If a
                # neighbouring pixel has the surface, a thin rim (a boot top seen from above) only moved sideways by
                # under a pixel; otherwise the part is really gone.
                px, py = k % SHAPE_RES, k // SHAPE_RES
                near = any(od.get((py + dy) * SHAPE_RES + px + dx, -1e9) >= z - SHAPE_TOL
                           for dy in (-1, 0, 1) for dx in (-1, 0, 1) if 0 <= px + dx < SHAPE_RES and 0 <= py + dy < SHAPE_RES)
                miss += 0 if near else 1
        out[view] = round(miss / max(SHAPE_MIN_PIXELS, len(sd)), 3)
    return out


def png_pixels(path):
    """Decode an 8-bit RGB/RGBA/grey PNG (non-interlaced) with the stdlib. Returns (w, h, rows of pixel tuples)."""
    import zlib
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    pos, idat, w = 8, b"", None
    while pos < len(data):
        ln, typ = struct.unpack_from(">I4s", data, pos)
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        pos += 12 + ln
    if depth != 8 or interlace:
        raise ValueError("only 8-bit, non-interlaced PNGs are supported")
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * bpp
    prev = bytearray(stride)
    rows = []
    i = 0
    for _ in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append([tuple(line[k:k + min(bpp, 3)]) for k in range(0, stride, bpp)])
        prev = line
    return w, h, rows


def preview_check(path, size):
    if not os.path.isfile(path):
        return False, f"missing: {path}"
    try:
        w, h, rows = png_pixels(path)
    except Exception as e:
        return False, f"unreadable: {e}"
    if (w, h) != (size, size):
        return False, f"{w}x{h}, expected {size}x{size}"
    bg = rows[0][0]
    total = changed = dark = 0
    sat = 0.0
    for row in rows[::2]:
        for px in row[::2]:
            total += 1
            if sum(abs(px[k] - bg[k]) for k in range(len(bg))) > 30:
                changed += 1
                rgb = px if len(px) == 3 else (px[0],) * 3
                if 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2] < 40:
                    dark += 1
                hi, lo = max(rgb), min(rgb)
                sat += (hi - lo) / hi if hi else 0.0
    frac = changed / total
    if frac < 0.02:
        return False, f"{w}x{h}, character covers {frac:.1%} of the image (need 2%): blank, or the camera misses the character; render it from the .glb with tools/render_preview.py"
    dk, st = dark / changed, sat / changed
    ok = dk <= DARK_MAX and st >= SAT_MIN
    return ok, (f"{w}x{h}, character covers {frac:.1%}; near-black {dk:.0%} (max {DARK_MAX:.0%}), "
                f"saturation {st:.2f} (min {SAT_MIN:.2f})" + ("" if ok else ": too dark or washed out; render it from the .glb with tools/render_preview.py instead of your own render code"))


def script_check(path):
    if not os.path.isfile(path):
        return False, f"missing: {path}"
    hits = [f"line {i}" for i, l in enumerate(open(path, errors="replace").read().splitlines(), 1)
            if "ARMATURE_AUTO" in l and not l.strip().startswith("#")]
    return (not hits), ("no automatic re-skinning" if not hits else
                        "uses ARMATURE_AUTO (automatic weights) at " + ", ".join(hits) + "; keep the source weights instead")


def check(out_path, src_path, max_tris=10000, max_surfaces=6, preview=None, size=512, script=None, max_materials=None, also=(),
          max_texture=None, skip=(), only=(), shape_extent=0.0):
    g, bins = load(out_path)
    if only:  # kit_check.py: look at just these output meshes
        for node in g.get("nodes", []):
            if "mesh" in node and node.get("name") not in only:
                node.pop("mesh", None)
    # every source: (gltf, buffers, {material index: image md5}); sources are read first so their image names win
    sources = []
    for sp in [src_path] + list(also):
        sg, sbins = load(sp)
        for node in sg.get("nodes", []):  # parts the task leaves out
            if node.get("name") in skip:
                node.pop("mesh", None)
        sources.append((sg, sbins, base_images(sg, sbins, os.path.dirname(sp))))
    src_image_set = {h for _, _, im in sources for h in im.values()}
    imgs = base_images(g, bins)
    # a resized copy of a source texture counts as that texture
    resized, src_thumbs = [], None
    for mi, h in list(imgs.items()):
        if h in src_image_set:
            continue
        t = thumb(IMAGE_BYTES[h])
        if t is None:
            continue
        if src_thumbs is None:
            src_thumbs = {sh: thumb(IMAGE_BYTES[sh]) for sh in src_image_set}
        for sh, st in src_thumbs.items():
            if st is not None and sum(abs(a - b) for a, b in zip(t, st)) / len(t) <= THUMB_TOL:
                imgs[mi] = sh
                resized.append(IMAGE_NAMES.get(sh, sh))
                break
    tris, surfaces, bones = summary(g)
    src_bones = set()
    for sg, _, _ in sources:
        src_bones |= summary(sg)[2]
    r = {"file": out_path, "triangles": tris, "surfaces": surfaces}
    r["budget"] = tris <= max_tris and surfaces <= max_surfaces

    r["bones"] = bones == src_bones
    r["bone_count"] = len(bones)

    unskinned = []
    for node in g.get("nodes", []):
        if "mesh" not in node:
            continue
        prims = g["meshes"][node["mesh"]].get("primitives", [])
        if "skin" not in node or any("JOINTS_0" not in p["attributes"] or "WEIGHTS_0" not in p["attributes"] for p in prims):
            unskinned.append(node.get("name", "?"))
    r["skinned"] = not unskinned
    r["unskinned_meshes"] = unskinned

    mats = g.get("materials", [])
    textured = {i for i, m in enumerate(mats) if m.get("pbrMetallicRoughness", {}).get("baseColorTexture")}
    used = [p.get("material") for n in g.get("nodes", []) if "mesh" in n for p in g["meshes"][n["mesh"]].get("primitives", [])]
    r["untextured_surfaces"] = sum(1 for m in used if m not in textured)
    foreign = sorted({mats[m].get("name", "?") for m in set(used) if m in imgs and imgs[m] not in src_image_set})
    r["foreign_texture_materials"] = foreign
    r["resized_textures"] = sorted(set(resized))
    sizes = []
    for im in g.get("images", []):
        if "bufferView" in im:
            bv = g["bufferViews"][im["bufferView"]]
            sz = image_size(bins[bv.get("buffer", 0)][bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]])
            if sz:
                sizes.append((max(sz), im.get("name", "?")))
    r["largest_texture"] = max(sizes) if sizes else None
    r["max_texture"] = max_texture
    too_big = sorted(n for s_, n in sizes if max_texture and s_ > max_texture)
    r["oversized_textures"] = too_big
    r["texture"] = bool(textured) and all(m in textured for m in used) and not foreign and not too_big

    limit = max_materials if max_materials is not None else len(src_image_set)
    r["material_count"] = len(set(used))
    r["max_materials"] = limit
    r["materials"] = r["material_count"] <= limit

    src_verts, src_tris = [], []
    for sg, sbins, sim in sources:
        src_verts += skinned_vertices(sg, sbins, sim)
        src_tris += mesh_triangles(sg, sbins)
    overlap, unmatched, groups = weight_overlap(skinned_vertices(g, bins, imgs), src_verts)
    r["weight_overlap"] = round(overlap, 3)
    r["weights_unmatched_vertices"] = unmatched
    r["weights"] = overlap >= WEIGHT_MIN
    r["look_by_texture"] = {IMAGE_NAMES.get(k, str(k)): {"kept": round(v[0] / v[1], 3), "vertices": v[1],
                                                         "image_ok": round(v[2] / v[1], 3), "uv_ok": round(v[3] / v[1], 3)}
                            for k, v in sorted(groups.items(), key=lambda kv: -kv[1][1])}
    r["look"] = bool(groups) and all(v[0] / v[1] >= LOOK_MIN for v in groups.values())

    r["shape_missing"] = shape_check(g, bins, src_tris, shape_extent)
    r["shape"] = max(r["shape_missing"].values()) <= SHAPE_MAX

    keys = ["budget", "bones", "skinned", "texture", "materials", "look", "shape", "weights"]
    if script:
        r["script"], r["script_detail"] = script_check(script)
        keys.append("script")
    if preview:
        r["preview"], r["preview_detail"] = preview_check(preview, size)
        keys.append("preview")
    r["ok"] = all(r[k] for k in keys)
    return r


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("output", help="exported .glb")
    parser.add_argument("source", help="source .gltf / .glb")
    parser.add_argument("--max-tris", type=int, default=10000)
    parser.add_argument("--max-surfaces", type=int, default=6)
    parser.add_argument("--max-materials", type=int, default=None)
    parser.add_argument("--preview", default=None, help="preview PNG to check")
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--script", default=None, help="build script to scan")
    parser.add_argument("--also", action="append", default=[], help="extra source file (repeatable)")
    parser.add_argument("--max-texture", type=int, default=None)
    parser.add_argument("--skip", action="append", default=[], help="source node to leave out (repeatable)")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        r = check(
            args.output,
            args.source,
            args.max_tris,
            args.max_surfaces,
            args.preview,
            args.size,
            args.script,
            args.max_materials,
            args.also,
            args.max_texture,
            args.skip,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, struct.error) as exc:
        print(f"FAIL  input: could not read or parse a mesh file ({type(exc).__name__}: {exc})")
        print("CHECKS FAILED")
        sys.exit(1)
    if args.json:
        print(json.dumps(r))
    else:
        yn = lambda b: "PASS" if b else "FAIL"
        print(f"{yn(r['budget'])}  budget: {r['triangles']} triangles, {r['surfaces']} surfaces")
        print(f"{yn(r['bones'])}  bones: {r['bone_count']} names, same set as source: {r['bones']}")
        print(f"{yn(r['skinned'])}  skinned: unskinned meshes: {', '.join(r['unskinned_meshes']) or 'none'}")
        print(f"{yn(r['texture'])}  texture: surfaces without a base colour texture: {r['untextured_surfaces']}; materials whose image isn't a source base colour image: {', '.join(r['foreign_texture_materials']) or 'none'}"
              + (f"; largest texture {r['largest_texture'][0]} px" if r["largest_texture"] else "")
              + (f" (max {r['max_texture']})" if r["max_texture"] else "")
              + (f"; over the limit: {', '.join(r['oversized_textures'])}: run tools/shrink_textures.py on the .glb" if r["oversized_textures"] else ""))
        print(f"{yn(r['materials'])}  materials: {r['material_count']} used (max {r['max_materials']})")
        lk = "; ".join(f"{k} {v['kept']:.1%} of {v['vertices']}" for k, v in r["look_by_texture"].items())
        print(f"{yn(r['look'])}  look: vertices that keep their source texture, UV and vertex colour, per source texture: {lk} (need {LOOK_MIN:.0%} each)")
        for k, v in r["look_by_texture"].items():
            if v["kept"] < LOOK_MIN:  # say which of the three parts fails; measured, not guessed
                if v["image_ok"] < LOOK_MIN:
                    why = f"only {v['image_ok']:.1%} of these vertices are on this texture: faces were moved to another material"
                elif v["uv_ok"] < LOOK_MIN:
                    why = f"texture right, but only {v['uv_ok']:.1%} have the source UV: UVs changed (decimating after joining parts, or a decimate that ignores UV seams, does this; decimate each part before joining)"
                else:
                    why = f"texture and UV right ({v['uv_ok']:.1%}), but only {v['kept']:.1%} have the source vertex colour (COLOR_0): compare the exported COLOR_0 with the source; don't just fill it with white if the source isn't white"
                print(f"      {k}: {why}")
        sm = r["shape_missing"]; worst = max(sm, key=sm.get)
        print(f"{yn(r['shape'])}  shape: source surface missing from the output, by view: " + ", ".join(f"{k} {v:.1%}" for k, v in sm.items())
              + f" (max {SHAPE_MAX:.0%})" + ("" if r["shape"] else f": geometry is missing or over-decimated, worst seen from the {worst}; check that every part is in the export"))
        if "script" in r:
            print(f"{yn(r['script'])}  script: {r['script_detail']}")
        if "preview" in r:
            print(f"{yn(r['preview'])}  preview: {r['preview_detail']}")
        print("ALL CHECKS PASS" if r["ok"] else "CHECKS FAILED")
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
