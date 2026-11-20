#!/usr/bin/env python3
"""Run the published stdlib checkers on the synthetic fixture.

This is not a pawn-bench task rerun. It does not use Quaternius packs,
a Nextimus checkout, Blender, or a model host.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(HERE))

from generate_fixture import generate  # noqa: E402
import glb_check as gc  # noqa: E402
import kit_check as kc  # noqa: E402

SEAM_REGIONS = {"body_torso", "body_legs"}


def run_glb_check(out_glb: Path, src_glb: Path, *extra: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(TOOLS / "glb_check.py"), str(out_glb), str(src_glb), *extra]
    return subprocess.run(cmd, text=True, capture_output=True)


def expect(ok: bool, proc: subprocess.CompletedProcess, label: str, must_contain: str | None = None) -> None:
    print(f"--- {label} (exit {proc.returncode}) ---")
    out = (proc.stdout or "") + (proc.stderr or "")
    print(out, end="" if out.endswith("\n") or not out else "\n")
    if ok and proc.returncode != 0:
        raise SystemExit(f"FAIL: {label}: expected success, got exit {proc.returncode}")
    if not ok and proc.returncode == 0:
        raise SystemExit(f"FAIL: {label}: expected checker failure, got exit 0")
    if must_contain and must_contain not in out:
        raise SystemExit(f"FAIL: {label}: output did not contain {must_contain!r}")


def main() -> int:
    paths = generate(HERE)
    print("Synthetic fixture generated (not Quaternius; not a bench rerun).")
    for k, p in paths.items():
        print(f"  {k}: {p.name} ({p.stat().st_size} bytes)")

    good = run_glb_check(paths["good"], paths["source"], "--max-tris", "20", "--max-surfaces", "6")
    expect(True, good, "glb_check good export under a 20-triangle cap", "ALL CHECKS PASS")

    tight = run_glb_check(paths["good"], paths["source"], "--max-tris", "4", "--max-surfaces", "6")
    expect(False, tight, "glb_check same export under a 4-triangle cap", "FAIL  budget")

    collapsed = run_glb_check(paths["collapsed"], paths["source"], "--max-tris", "20", "--max-surfaces", "6")
    expect(False, collapsed, "glb_check collapsed export vs source", "FAIL  shape")

    g_ok, bins_ok = gc.load(str(paths["seams_ok"]))
    ex_ok, tot_ok = kc.seam_share(g_ok, bins_ok, SEAM_REGIONS)
    share_ok = ex_ok / tot_ok if tot_ok else 0.0
    print(f"--- kit_check.seam_share on coincident regions: {ex_ok} of {tot_ok} ({share_ok:.0%}, need {kc.SEAM_MIN:.0%}) ---")
    if tot_ok <= 0 or share_ok < kc.SEAM_MIN:
        raise SystemExit(f"FAIL: coincident seam fixture should meet {kc.SEAM_MIN:.0%}, got {ex_ok}/{tot_ok}")

    g_bad, bins_bad = gc.load(str(paths["seams_cracked"]))
    ex_bad, tot_bad = kc.seam_share(g_bad, bins_bad, SEAM_REGIONS)
    share_bad = ex_bad / tot_bad if tot_bad else 0.0
    print(f"--- kit_check.seam_share on cracked regions: {ex_bad} of {tot_bad} ({share_bad:.0%}, need {kc.SEAM_MIN:.0%}) ---")
    if tot_bad > 0 and share_bad >= kc.SEAM_MIN:
        raise SystemExit(f"FAIL: cracked seam fixture should fall below {kc.SEAM_MIN:.0%}, got {ex_bad}/{tot_bad}")
    if tot_bad <= 0:
        raise SystemExit("FAIL: cracked seam fixture produced no seam vertices to score")

    unskinned = run_glb_check(paths["unskinned"], paths["source"], "--max-tris", "20", "--max-surfaces", "6")
    expect(False, unskinned, "glb_check missing skinning", "FAIL  skinned")

    surfaces = run_glb_check(paths["two_surfaces"], paths["source"], "--max-tris", "40", "--max-surfaces", "1")
    expect(False, surfaces, "glb_check surface limit (2 surfaces, max 1)", "FAIL  budget")

    corrupted = run_glb_check(paths["corrupted"], paths["source"], "--max-tris", "20", "--max-surfaces", "6")
    expect(False, corrupted, "glb_check corrupted input", "FAIL  input")

    def seam_case(label, path, should_pass):
        g, bins = gc.load(str(path))
        exact, total = kc.seam_share(g, bins, SEAM_REGIONS)
        share = exact / total if total else 0.0
        print(f"--- kit_check.seam_share {label}: {exact} of {total} ({share:.0%}, need {kc.SEAM_MIN:.0%}) ---")
        if total <= 0:
            raise SystemExit(f"FAIL: {label}: no seam vertices to score")
        if should_pass and share < kc.SEAM_MIN:
            raise SystemExit(f"FAIL: {label}: expected to meet {kc.SEAM_MIN:.0%}, got {exact}/{total}")
        if not should_pass and share >= kc.SEAM_MIN:
            raise SystemExit(f"FAIL: {label}: expected to fall below {kc.SEAM_MIN:.0%}, got {exact}/{total}")

    seam_case("threshold boundary at 85%", paths["seams_at_limit"], True)
    seam_case("threshold boundary below 85%", paths["seams_below_limit"], False)

    scratch = Path(tempfile.mkdtemp(prefix="pawn-fixture-"))
    # Invalid manifest: kit_check should fail in the names/manifest step without source art.
    bad_man = scratch / "synthetic_invalid_manifest.json"
    bad_man.write_text('{"not": "a kit manifest"}\n')
    man_proc = subprocess.run(
        [sys.executable, str(TOOLS / "kit_check.py"), str(paths["good"]), str(bad_man)],
        text=True, capture_output=True,
    )
    expect(False, man_proc, "kit_check invalid manifest", "FAIL  names")

    # Duplicate slot: kit_loadout refuses two pieces in the same slot.
    dup_man = scratch / "synthetic_dup_slot.json"
    dup_glb = paths["good"]
    dup_out = scratch / "synthetic_dup_slot_out.glb"
    dup_man.write_text(
        '{"body": {"head": "h", "torso": "fixture_body", "arms": "a", "legs": "l", "feet": "f"},'
        ' "always": ["eyes"],'
        ' "pieces": {'
        '  "ranger_boots": {"set": "ranger", "slot": "feet", "meshes": ["m1"], "covers": ["feet"]},'
        '  "knight_feet": {"set": "knight", "slot": "feet", "meshes": ["m2"], "covers": ["feet"]}'
        '}}\n'
    )
    dup_proc = subprocess.run(
        [sys.executable, str(TOOLS / "kit_loadout.py"), str(dup_glb), str(dup_man), str(dup_out),
         "ranger_boots,knight_feet"],
        text=True, capture_output=True,
    )
    dup_text = (dup_proc.stdout or "") + (dup_proc.stderr or "")
    print(f"--- kit_loadout duplicate slot (exit {dup_proc.returncode}) ---")
    print(dup_text, end="" if dup_text.endswith("\n") or not dup_text else "\n")
    if dup_proc.returncode == 0:
        raise SystemExit("FAIL: kit_loadout duplicate slot: expected a non-zero exit")
    if "at most one piece per slot" not in dup_text:
        raise SystemExit("FAIL: kit_loadout duplicate slot: message missing")

    # Canonical source-art variable, with KIT_SOURCES as a fallback alias.
    import os
    saved_q, saved_k = os.environ.get("QUATERNIUS_SOURCE"), os.environ.get("KIT_SOURCES")
    try:
        os.environ["QUATERNIUS_SOURCE"] = "/synthetic/source-location"
        os.environ.pop("KIT_SOURCES", None)
        if kc.source_art_root() != "/synthetic/source-location":
            raise SystemExit(f"FAIL: QUATERNIUS_SOURCE was not honored: {kc.source_art_root()}")
        os.environ.pop("QUATERNIUS_SOURCE", None)
        os.environ["KIT_SOURCES"] = "/synthetic/kit-alias"
        if kc.source_art_root() != "/synthetic/kit-alias":
            raise SystemExit(f"FAIL: KIT_SOURCES fallback was not honored: {kc.source_art_root()}")
        print("--- kit_check.source_art_root honors QUATERNIUS_SOURCE and KIT_SOURCES fallback ---")
    finally:
        if saved_q is None: os.environ.pop("QUATERNIUS_SOURCE", None)
        else: os.environ["QUATERNIUS_SOURCE"] = saved_q
        if saved_k is None: os.environ.pop("KIT_SOURCES", None)
        else: os.environ["KIT_SOURCES"] = saved_k

    print("ALL FIXTURE TESTS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
