#!/usr/bin/env python3
"""Write one loadout of a modular kit as its own .glb, for viewing (Quick Look, Blender, Godot).

  kit_loadout.py KIT.glb KIT.json OUT.glb [piece,piece,...]

The kit .glb holds every body region and every gear piece at once; it is a parts bin, not a character.
This copies it and keeps only the meshes one loadout shows: eyes and eyebrows, the worn pieces (at most one
per slot), and the body regions no worn piece covers. A worn piece that hides a slot (a hood or closed helm
hides hair) keeps that slot's piece out. No piece list = the bare body.
"""
import argparse
import json
import struct
import sys


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("kit_glb", help="kit .glb (parts bin)")
    parser.add_argument("manifest", help="kit .json manifest")
    parser.add_argument("out_glb", help="output .glb for this loadout")
    parser.add_argument("pieces", nargs="?", default="", help="comma-separated piece names; empty = bare body")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    worn = [w for w in args.pieces.split(",") if w]
    man = json.load(open(args.manifest))
    slots = {}
    for w in worn:
        if w not in man["pieces"]:
            sys.exit(f"no piece {w!r}; pieces: {sorted(man['pieces'])}")
        s = man["pieces"][w]["slot"]
        if s in slots:
            sys.exit(f"{w} and {slots[s]} are both {s}-slot pieces; a loadout wears at most one piece per slot")
        slots[s] = w
    hidden = {s for w in worn for s in man["pieces"][w].get("hides", [])}
    seen = [w for w in worn if man["pieces"][w]["slot"] not in hidden]
    covered = {r for w in seen for r in man["pieces"][w]["covers"]}
    show = set(man["always"]) | {m for r, m in man["body"].items() if r not in covered} | {m for w in seen for m in man["pieces"][w]["meshes"]}
    data = open(args.kit_glb, "rb").read()
    n = struct.unpack_from("<I", data, 12)[0]
    g = json.loads(data[20:20 + n])
    rest = data[20 + n:]
    for node in g["nodes"]:
        if "mesh" in node and node.get("name") not in show:
            del node["mesh"]
            node.pop("skin", None)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    with open(args.out_glb, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + len(rest)))
        f.write(struct.pack("<I4s", len(js), b"JSON"))
        f.write(js)
        f.write(rest)
    print(f"kit_loadout: wrote {args.out_glb} showing {sorted(show)}")


if __name__ == "__main__":
    main()
