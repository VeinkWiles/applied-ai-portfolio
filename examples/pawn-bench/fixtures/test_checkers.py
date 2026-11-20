#!/usr/bin/env python3
"""Run the published stdlib checkers on the synthetic fixture.

This is not a pawn-bench task rerun. It does not use Quaternius packs,
a Nextimus checkout, Blender, or a model host.
"""
from __future__ import annotations

import subprocess
import sys
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

    print("ALL FIXTURE TESTS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
