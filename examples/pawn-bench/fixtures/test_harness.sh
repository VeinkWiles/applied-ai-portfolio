#!/usr/bin/env bash
# Mocked run.sh status tests. No Blender, no private trees, no model host.
# Coverage is by harness result, not a T-task rerun.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RUN_SH="$(cd "$HERE/.." && pwd)/run.sh"
PASS=0
FAIL=0

ok() { echo "PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "FAIL: $1"; echo "$2"; FAIL=$((FAIL+1)); }

# Build a disposable bench + git checkout + mock agent.
setup() {
  WORK=$(mktemp -d)
  mkdir -p "$WORK/bench/tools" "$WORK/bench/tasks" "$WORK/bench/fixtures" \
           "$WORK/game" "$WORK/source" "$WORK/bin"
  cp "$RUN_SH" "$WORK/bench/run.sh"
  chmod +x "$WORK/bench/run.sh"
  printf 'T13 mock task\n' > "$WORK/bench/tasks/T13.md"

  cat > "$WORK/bench/tools/kit_check.py" << 'PY'
#!/usr/bin/env python3
import os, sys
from pathlib import Path
state = Path(os.environ["MOCK_CHECK_STATE"])
remaining = int(state.read_text().strip() or "0")
if remaining > 0:
    state.write_text(str(remaining - 1))
    print("CHECKS FAILED")
    sys.exit(1)
print("ALL CHECKS PASS")
sys.exit(0)
PY
  chmod +x "$WORK/bench/tools/kit_check.py"

  git -C "$WORK/game" init -q
  git -C "$WORK/game" config user.name "Harness Test"
  git -C "$WORK/game" config user.email "harness-test@example.com"
  echo "mock nextimus checkout" > "$WORK/game/README"
  git -C "$WORK/game" add README
  git -C "$WORK/game" commit -q -m "init"
  git -C "$WORK/game" branch -M main

  cat > "$WORK/bin/openclaw" << 'SH'
#!/usr/bin/env bash
set -euo pipefail
mode="${MOCK_AGENT_MODE:-success}"
commit_outputs() {
  local repo="$NEXTIMUS_PAWN" asset=chr_male_kit_v001
  mkdir -p "$repo/art/scripts" "$repo/art/export" "$repo/art/previews"
  : > "$repo/art/scripts/build_${asset}.py"
  : > "$repo/art/export/${asset}.glb"
  : > "$repo/art/export/${asset}.json"
  : > "$repo/art/previews/${asset}_bare.png"
  : > "$repo/art/previews/${asset}_ranger.png"
  : > "$repo/art/previews/${asset}_knight.png"
  : > "$repo/art/previews/${asset}_mix.png"
  git -C "$repo" add art
  git -C "$repo" diff --cached --quiet || git -C "$repo" commit -q -m "mock outputs"
}
case "$mode" in
  fail) echo "agent failed"; exit 1 ;;
  missing) echo "agent finished without writing outputs"; exit 0 ;;
  timeout) echo "OpenClaw took too long to respond"; exit 1 ;;
  infra) echo "Provider foo is in cooldown"; exit 1 ;;
  success|repair|checker) echo "agent finished"; commit_outputs; exit 0 ;;
  *) echo "unknown MOCK_AGENT_MODE=$mode" >&2; exit 99 ;;
esac
SH
  chmod +x "$WORK/bin/openclaw"

  echo 0 > "$WORK/check_state"
}

run_case() {
  local name="$1" mode="$2" expect_exit="$3" expect_result="$4"
  local extra="${5:-}"
  setup
  echo 0 > "$WORK/check_state"
  if [ "$mode" = repair ]; then
    echo 1 > "$WORK/check_state"
  elif [ "$mode" = checker ]; then
    echo 99 > "$WORK/check_state"
  fi
  local log="$WORK/run.log" rc=0
  set +e
  env -u KIT_SOURCES \
    PATH="$WORK/bin:$PATH" \
    NEXTIMUS_PAWN="$WORK/game" \
    QUATERNIUS_SOURCE="$WORK/source" \
    MOCK_AGENT_MODE="$mode" \
    MOCK_CHECK_STATE="$WORK/check_state" \
    INFRA_WAIT=0 \
    INFRA_RETRIES=0 \
    $extra \
    bash "$WORK/bench/run.sh" T13 q36 >"$log" 2>&1
  rc=$?
  set -e
  local result=""
  result=$(grep -o 'result=[A-Z]*' "$log" | tail -1 | cut -d= -f2 || true)
  local summary
  summary="exit=$rc result=${result:-?} log=$(tail -5 "$log" | tr '\n' ' | ')"
  if [ "$rc" -eq "$expect_exit" ] && [ "$result" = "$expect_result" ]; then
    ok "$name ($summary)"
  else
    bad "$name (expected exit $expect_exit result $expect_result)" "$summary"$'\n'"$(tail -30 "$log")"
  fi
  rm -rf "$WORK"
}

echo "Running mocked harness status tests (no Blender, no private trees)."
run_case "agent failure" fail 1 FAIL "FIX=0"
run_case "missing outputs" missing 1 FAIL "FIX=0"
run_case "checker failure" checker 1 FAIL "FIX=0"
run_case "timeout" timeout 124 TIMEOUT "FIX=0"
run_case "infra failure" infra 75 INFRA "FIX=0"
run_case "success" success 0 PASS "FIX=0"
run_case "successful repair" repair 0 PASS "FIX=1"

echo "--- $PASS passed, $FAIL failed ---"
if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
echo "ALL HARNESS STATUS TESTS PASS"
exit 0
