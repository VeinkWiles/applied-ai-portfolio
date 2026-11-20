#!/usr/bin/env python3
"""Count triangles, surfaces (mesh primitives) and bone names in a .gltf/.glb. Stdlib only.

Usage: gltf_stats.py FILE [--json]

A surface, in this checker, is one mesh primitive (one rendered material/group).
"""
import argparse
import json
import struct
import sys


def load(path):
    data = open(path, "rb").read()
    if data[:4] == b"glTF":
        n = struct.unpack_from("<I", data, 12)[0]
        return json.loads(data[20:20+n])
    return json.loads(data)


def stats(path):
    gltf = load(path)
    accessors = gltf.get("accessors", [])
    meshes = gltf.get("meshes", [])
    triangles = 0
    surfaces = 0
    materials = set()
    for node in gltf.get("nodes", []):
        if "mesh" not in node:
            continue
        for prim in meshes[node["mesh"]].get("primitives", []):
            if prim.get("mode", 4) != 4:
                continue
            surfaces += 1
            materials.add(prim.get("material"))
            if "indices" in prim:
                triangles += accessors[prim["indices"]]["count"] // 3
            else:
                triangles += accessors[prim["attributes"]["POSITION"]]["count"] // 3
    bones = []
    for skin in gltf.get("skins", []):
        bones += [gltf["nodes"][j].get("name", "") for j in skin.get("joints", [])]
    return {
        "file": path,
        "triangles": triangles,
        "surfaces": surfaces,
        "materials": len(materials),
        "mesh_nodes": sum(1 for n in gltf.get("nodes", []) if "mesh" in n),
        "bones": sorted(set(bones)),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help=".gltf or .glb")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = stats(args.file)
    if args.json:
        print(json.dumps(result))
    else:
        print(f"{result['file']}: {result['triangles']} triangles, {result['surfaces']} surfaces, {result['materials']} materials, {result['mesh_nodes']} mesh nodes, {len(result['bones'])} bones")


if __name__ == "__main__":
    main()
