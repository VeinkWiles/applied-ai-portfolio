#!/bin/bash
# Usage: <pawn-bench>/run.sh <T1..T16> <model alias>
# Optional env: THINK=low|medium|high   TIMEOUT=<seconds>   FIX=<rounds>   INFRA_WAIT=<s>   INFRA_RETRIES=<n>
#   AGENT=direct   talk to LM Studio through tools/direct_agent.py instead of OpenClaw (lmstudio models only;
#                  results are tagged <alias>-direct; transcripts in results/.sessions/)
#   NEXTIMUS_PAWN, QUATERNIUS_SOURCE (KIT_SOURCES is a fallback alias), PAWN_LOGS
# This script does not auto-load a .env file. Export the variables in your shell, or `set -a; . .env; set +a`.
set -u
# Control-c (or kill) stops the whole run, not just the current agent call. The handler runs once the
# call in progress has ended; it notes the interruption, cleans up, and re-raises the signal so a
# wrapping loop or `a; b` chain stops too.
stop_run() {
  [ -n "${out:-}" ] && echo "=== interrupted by signal $1; run stopped (not a graded result)" >> "$out"
  [ -n "${R:-}" ] && git -C "$R" checkout -q -f main 2>/dev/null
  [ -n "${pdir:-}" ] && rm -rf "$pdir"
  trap - INT TERM; kill -s "$1" $$
}
trap 'stop_run INT' INT
trap 'stop_run TERM' TERM
task="${1:-}"; m="${2:-}"
case "$m" in
  coder)  model="ollama/qwen3-coder:30B" ;;
  qwen9b) model="ollama/qwen3.5:9b" ;;
  oss20)  model="ollama/gpt-oss:20b" ;;
  lms9b)  model="lmstudio/qwen3.5-9b-mlx" ;;
  lms27b) model="lmstudio/qwen3.8-27b-mlx" ;;
  q36)    model="lmstudio/qwen3.6-35b-a3b-mlx" ;;
  qcn)    model="lmstudio/qwen3-coder-next-mlx" ;;
  laguna) model="lmstudio/laguna-xs-2.1-mlx" ;;
  oss120) model="lmstudio/gpt-oss-120b" ;;
  sonnet) model="anthropic/claude-sonnet-5" ;;
  *) echo "usage: run.sh <T1..T16> <model alias>"; exit 2 ;;
esac
B="$(cd "$(dirname "$0")" && pwd)"; R="${NEXTIMUS_PAWN:-<nextimus-pawn>}"
f="$B/tasks/$task.md"; [ -f "$f" ] || { echo "no task file $f"; exit 2; }
base=main; [ -f "$B/tasks/$task.base" ] && base=$(tr -d '[:space:]' < "$B/tasks/$task.base")
# Blender paring tasks: asset id and source file (the harness checker needs both)
asset=""; src=""; also=(); kitarg=male
# Canonical source-art path. KIT_SOURCES is accepted only as a fallback alias.
if [ -n "${QUATERNIUS_SOURCE:-}" ]; then
  Q="$QUATERNIUS_SOURCE"
elif [ -n "${KIT_SOURCES:-}" ]; then
  Q="$KIT_SOURCES"
else
  Q="<quaternius-source>"
fi
case "$task" in
  T8) asset=chr_ranger_male_pared_v001; src="$R/art/vendor/quaternius/character-outfits-fantasy/Male_Ranger.gltf" ;;
  T9) asset=chr_wizard_female_pared_v001; src="$Q/Modular Character Outfits - Fantasy[Source]/Exports/glTF (Godot-Unreal)/Outfits/Female_Wizard.gltf" ;;
  T10) asset=chr_wizard_female_full_v001; src="$Q/Modular Character Outfits - Fantasy[Source]/Exports/glTF (Godot-Unreal)/Outfits/Female_Wizard.gltf"
       also=(--also "$Q/Universal Base Characters[Source]/Base Characters/Exports/Godot - UE/Regular_Female_OnlyHead.gltf"
             --also "$Q/Universal Base Characters[Source]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Female/Hair_Long.gltf") ;;
  T11) asset=chr_knight_male_full_v001; src="$Q/Modular Character Outfits - Fantasy[Source]/Exports/glTF (Godot-Unreal)/Outfits/Male_Knight.gltf"
       also=(--skip Male_Knight_Head_Armet
             --also "$Q/Universal Base Characters[Source]/Base Characters/Exports/Godot - UE/Regular_Male_OnlyHead.gltf"
             --also "$Q/Universal Base Characters[Source]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Male/Hair_Balding.gltf"
             --also "$Q/Universal Base Characters[Source]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Male/Hair_Beard.gltf") ;;
  T12) asset=chr_knight_male_helm_v001; src="$Q/Modular Character Outfits - Fantasy[Source]/Exports/glTF (Godot-Unreal)/Outfits/Male_Knight.gltf"
       also=(--also "$Q/Universal Base Characters[Source]/Base Characters/Exports/Godot - UE/Regular_Male_OnlyHead.gltf"
             --also "$Q/Universal Base Characters[Source]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Male/Hair_Balding.gltf"
             --also "$Q/Universal Base Characters[Source]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Male/Hair_Beard.gltf") ;;
  T13) asset=chr_male_kit_v001; kitarg=male ;;
  T14) asset=chr_female_kit_v001; kitarg=female ;;
  T15) asset=chr_male_kit_v002; kitarg=male-hair ;;
  T16) asset=chr_female_kit_v002; kitarg=female-hair ;;
esac
# Time limits. A main turn that hits its limit is a FAIL and ends the run (no fix rounds).
# Fix rounds get a short limit of their own: a fix that needs longer is starting over.
limit="${TIMEOUT:-2400}"; [ -n "$asset" ] && limit="${TIMEOUT:-2700}"
fixlimit="${FIX_TIMEOUT:-1200}"; ask_limit="$limit"
agent="${AGENT:-openclaw}"
case "$agent" in
  openclaw) ;;
  direct) case "$model" in lmstudio/*) ;; *) echo "AGENT=direct only works with lmstudio models"; exit 2 ;; esac ;;
  *) echo "AGENT must be openclaw or direct"; exit 2 ;;
esac
# Preflight: fail fast with a clear message rather than a mid-run traceback.
# These scripts do not auto-load .env; the variables have to be in the environment.
if [ ! -d "$R/.git" ]; then
  echo "preflight: NEXTIMUS_PAWN is not a git checkout: $R"
  echo "Export NEXTIMUS_PAWN. This script does not auto-load .env (see .env.example)."
  exit 2
fi
case "$task" in
  T9|T10|T11|T12|T13|T14|T15|T16)
    if [ ! -d "$Q" ]; then
      echo "preflight: QUATERNIUS_SOURCE is not a directory: $Q"
      echo "Export QUATERNIUS_SOURCE (KIT_SOURCES is a fallback alias). This script does not auto-load .env (see .env.example and REPRODUCING.md)."
      exit 2
    fi
    export QUATERNIUS_SOURCE="$Q"
    ;;
esac
if [ "$agent" = direct ] && [ ! -f "$B/tools/direct_agent.py" ]; then
  echo "preflight: AGENT=direct needs tools/direct_agent.py, which is not in this checkout. See REPRODUCING.md."
  exit 2
fi
if [ "$task" = T4 ]; then
  for fx in suite-pass suite-fail playtest-pass playtest-script-error; do
    if [ ! -f "$B/fixtures/$fx.log" ]; then
      echo "preflight: T4 needs fixtures/$fx.log, which is not in this checkout. See REPRODUCING.md."
      exit 2
    fi
  done
fi
tag="$m${THINK:+-think-$THINK}"; [ "$agent" = direct ] && tag="$tag-direct"
stamp=$(date +%Y%m%d-%H%M%S); branch="pawn/$task-$tag-$stamp"
out="$B/results/$task-$tag-$stamp.txt"; mkdir -p "$B/results" "${PAWN_LOGS:-$B/pawn-logs}"
git -C "$R" checkout -q -f main || exit 1
git -C "$R" clean -q -fd -e '*.uid' || exit 1
git -C "$R" checkout -q -b "$branch" "$base" || exit 1
# Split the task into parts on "=== NEXT ===" (multi-turn tasks); same session for every part.
pdir="$B/results/.parts-$stamp"; mkdir -p "$pdir"
awk -v d="$pdir" 'BEGIN{n=1} /^=== NEXT ===$/{n++; next} {print > (d "/part" n ".md")}' "$f"
nparts=$(ls "$pdir" | wc -l | tr -d ' ')
echo "Branch for this run (already checked out): $branch" >> "$pdir/part1.md"
echo "running $task on $model ($nparts part(s), limit ${limit}s, fix rounds ${fixlimit}s each) ... (output: $out)"
# Infra errors are not model failures. When the whole reply is an OpenClaw provider error
# (provider cooldown, failed preflight compaction), ask() waits INFRA_WAIT seconds (default 90)
# and retries, up to INFRA_RETRIES times (default 3). Returns 0 ok, 1 nonzero exit, 2 infra error persisted, 3 session full, 4 time limit reached.
infra_pat='Provider [A-Za-z0-9_-]+ is in cooldown|Auth profile "[^"]+" is temporarily unavailable|All models failed \(|Preflight compaction required but failed|^HARNESS: provider unreachable'
# A full session (OpenClaw's mislabelled overflow "The request took too long", or the direct harness's
# budget stop) isn't retried in place: ask() returns 3 and a fix round moves to a fresh session.
full_pat='^HARNESS: context (budget reached|full)|The request took too long\. Check the conversation'
timeout_pat='^OpenClaw took too long to respond|^HARNESS: time limit'
infra=0; infra_fail=0; last_rc=0; full=0; mainfull=0; timed_out=0
ask() { # ask <session-key> <message-file>; appends the reply to $out
  local key="$1" msg="$2" try=0 tmp t_ask; tmp=$(mktemp)
  while :; do
    t_ask=$(date +%s)
    if [ "$agent" = direct ]; then
      PYTHONDONTWRITEBYTECODE=1 python3 "$B/tools/direct_agent.py" --model "${model#lmstudio/}" --session "$B/results/.sessions/$key" \
        --workdir "$R" --timeout "$ask_limit" --message-file "$msg" > "$tmp" 2>&1
    else
      openclaw agent --agent pawn --session-key "$key" ${THINK:+--thinking "$THINK"} --model "$model" --timeout "$ask_limit" --message-file "$msg" > "$tmp" 2>&1
    fi
    last_rc=$?; cat "$tmp" >> "$out"
    if [ "$(wc -c < "$tmp" | tr -d " ")" -lt 2000 ] && grep -q -E "$infra_pat" "$tmp"; then
      try=$((try+1)); infra=$((infra+1))
      [ "$try" -gt "${INFRA_RETRIES:-3}" ] && { rm -f "$tmp"; return 2; }
      echo "=== infra error (not a model failure); waiting ${INFRA_WAIT:-90}s, retry $try:" >> "$out"
      sleep "${INFRA_WAIT:-90}"; continue
    fi
    if grep -q -E "$timeout_pat" "$tmp" || [ $(( $(date +%s) - t_ask )) -ge "$ask_limit" ]; then rm -f "$tmp"; return 4; fi
    if grep -q -E "$full_pat" "$tmp"; then full=$((full+1)); rm -f "$tmp"; return 3; fi
    rm -f "$tmp"; [ "$last_rc" -eq 0 ]; return $?
  done
}
start=$(date +%s); code=0; : > "$out"
for i in $(seq 1 "$nparts"); do
  [ "$nparts" -gt 1 ] && echo "=== part $i reply:" >> "$out"
  ask "bench-$task-$tag-$stamp" "$pdir/part$i.md"; c=$?
  [ $c -eq 2 ] && { infra_fail=1; code=75; echo "=== infra error persisted; run aborted (not graded as a model failure)" >> "$out"; break; }
  [ $c -eq 4 ] && { timed_out=1; code=124; echo "=== main turn hit the ${limit}s time limit: FAIL, no fix rounds" >> "$out"; break; }
  [ $c -eq 3 ] && mainfull=1
  [ $c -ne 0 ] && code=$last_rc
  echo >> "$out"
done
# Fix loop: the harness runs the task's checker itself. On a failure it sends the checker
# output back into the same session, up to FIX rounds (default 2 for every task with an asset id, T8–T16; 0 otherwise).
fix="${FIX:-0}"; [ -n "$asset" ] && fix="${FIX:-2}"; rounds=0
harness_check() { # prints the checker report; exit 0 only if everything passes
  case "$task" in
    T8|T9|T10|T11|T12)
      ok=0
      for p in art/scripts/build_${asset}.py art/export/${asset}.glb art/previews/${asset}_threequarter.png; do
        git -C "$R" cat-file -e "HEAD:$p" 2>/dev/null || { echo "NOT COMMITTED or MISSING: $p"; ok=1; }
      done
      python3 "$B/tools/glb_check.py" "$R/art/export/${asset}.glb" "$src" --preview "$R/art/previews/${asset}_threequarter.png" --size 512 --max-texture 512 --script "$R/art/scripts/build_${asset}.py" ${also[@]+"${also[@]}"} 2>&1 || ok=1
      return $ok ;;
    T13|T14|T15|T16)
      ok=0
      for p in art/scripts/build_${asset}.py art/export/${asset}.glb art/export/${asset}.json art/previews/${asset}_bare.png art/previews/${asset}_ranger.png art/previews/${asset}_knight.png art/previews/${asset}_mix.png; do
        git -C "$R" cat-file -e "HEAD:$p" 2>/dev/null || { echo "NOT COMMITTED or MISSING: $p"; ok=1; }
      done
      python3 "$B/tools/kit_check.py" "$R/art/export/${asset}.glb" "$R/art/export/${asset}.json" --script "$R/art/scripts/build_${asset}.py" --previews "$R/art/previews/${asset}" --kit "$kitarg" 2>&1 || ok=1
      return $ok ;;
    *) return 0 ;;
  esac
}
fixkey="bench-$task-$tag-$stamp"
ask_limit="$fixlimit"
while [ "$rounds" -lt "$fix" ] && [ "$infra_fail" -eq 0 ] && [ "$timed_out" -eq 0 ]; do
  report=$(harness_check) && break
  rounds=$((rounds+1))
  { echo "The harness ran the checker on your work and it FAILED. Its output:"; echo; echo "$report"; echo
    echo "Fix every FAIL line and anything NOT COMMITTED, rebuild, run the checker yourself until it prints ALL CHECKS PASS, commit on the same branch, and report again. Don't rename files; use the exact paths in the task."; } > "$pdir/fix$rounds.md"
  echo "=== harness check failed; fix round $rounds:" >> "$out"; echo "$report" >> "$out"; echo "=== fix round $rounds reply:" >> "$out"
  fresh_fix() { # run this fix round in a fresh session that gets the task text plus the checker report
    fixkey="bench-$task-$tag-$stamp-fix"
    { echo "You are continuing an earlier attempt at this task. Its files are in the repo on the branch named below (they may be uncommitted); inspect them before changing anything."
      echo; cat "$pdir"/part*.md; echo; cat "$pdir/fix$rounds.md"; } > "$pdir/fix$rounds-fresh.md"
    echo "=== $1; fix round $rounds runs in fresh session $fixkey:" >> "$out"
    ask "$fixkey" "$pdir/fix$rounds-fresh.md"; c=$?
  }
  if [ "$mainfull" -eq 1 ] && [ "$fixkey" = "bench-$task-$tag-$stamp" ]; then
    # The main turn already ended on a full session (seen 11-10: going back into it cost 74 minutes
    # for an empty reply). Don't touch it again.
    fresh_fix "main session ended full"
  else
    ask "$fixkey" "$pdir/fix$rounds.md"; c=$?
    if { [ $c -eq 2 ] || [ $c -eq 3 ]; } && [ "$fixkey" = "bench-$task-$tag-$stamp" ]; then
      fresh_fix "original session unavailable"
    fi
  fi
  [ $c -eq 2 ] && { infra_fail=1; code=75; echo "=== infra error persisted; fix rounds stopped" >> "$out"; break; }
  [ $c -eq 4 ] && { timed_out=2; code=124; echo "=== fix round $rounds hit the ${fixlimit}s time limit; fix rounds stopped" >> "$out"; break; }
  [ $c -ne 0 ] && code=$last_rc
  echo >> "$out"
done
end=$(date +%s)
{
  echo; echo "=== bench task=$task model=$model agent=$agent think=${THINK:-default} exit=$code seconds=$((end-start)) fix_rounds=$rounds branch=$branch base=$base infra_retries=$infra infra_fail=$infra_fail session_full=$full timed_out=$timed_out"
  echo "=== commits:"; git -C "$R" log --oneline "$base"..HEAD
  echo "=== uncommitted:"; git -C "$R" status --short | grep -v '\.uid$'
} >> "$out"
git -C "$R" diff "$base" > "$out.diff" 2>/dev/null
suite() { # run the rule suite with a 5-minute cap; summarize
  ( cd "$R" && perl -e 'alarm shift; exec @ARGV' 300 godot --headless --path . res://tests/run.tscn > "$out.tests.log" 2>&1 ); echo "rule tests exit $?"
  grep -c '^ok:' "$out.tests.log" | sed 's/^/ok lines: /'
  grep -n -E 'ALL TESTS PASSED|[0-9]+ FAILED|SCRIPT ERROR|^FAIL' "$out.tests.log" | grep -v timeout_hang | head -15
}
section() { sed -n "/^-- $1/,/^--/p" "$out.tests.log" | head -${2:-14}; }
verify_fail=0
{
  echo "=== verify:"
  case "$task" in
    T1) echo "(read-only: check answers by hand; files changed:)"; git -C "$R" status --short | grep -v '\.uid$' ;;
    T2) suite; section "xp table shape" 12; echo "files changed vs base:"; git -C "$R" diff --stat "$base" | tail -5 ;;
    T3) suite; section "xp progress" 12; echo "files changed vs base:"; git -C "$R" diff --stat "$base" | tail -5 ;;
    T4)
      for fx in suite-pass suite-fail playtest-pass playtest-script-error; do
        v=$(perl -e 'alarm shift; exec @ARGV' 30 python3 "$R/tools/godot_log_summary.py" "$B/fixtures/$fx.log" 2>&1 | head -1)
        perl -e 'alarm shift; exec @ARGV' 30 python3 "$R/tools/godot_log_summary.py" "$B/fixtures/$fx.log" > /dev/null 2>&1; c=$?
        echo "$fx: $v (exit $c)"
        case "$fx" in
          suite-pass|playtest-pass) [ "$c" -eq 0 ] || verify_fail=1 ;;
          suite-fail|playtest-script-error) [ "$c" -ne 0 ] || verify_fail=1 ;;
        esac
      done ;;
    T5)
      suite; section "level cap from data"
      echo "LEVEL_CAP left in scripts/ and tests/: $(grep -rn 'LEVEL_CAP' "$R/scripts" "$R/tests" 2>/dev/null | grep -v '\.uid' | wc -l | tr -d ' ')"
      python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print('xp.json level_cap:', d.get('level_cap'))" "$R/data/xp.json" 2>&1
      echo "files changed vs base:"; git -C "$R" diff --stat "$base" | tail -6 ;;
    T6)
      python3 - "$R/tests/run.gd" "$B/tasks/T6.hidden.gd" <<'PY'
import sys
p, h = sys.argv[1], sys.argv[2]
s = open(p).read(); hidden = open(h).read()
anchor = "\t_test_old_save_migrates()\n"
if anchor in s:
    s = s.replace(anchor, anchor + "\t_test_hidden_old_save_fields()\n", 1)
    print("hidden test inserted")
else:
    print("ANCHOR MISSING: hidden test not called")
open(p, "w").write(s.rstrip("\n") + "\n" + hidden)
PY
      suite; section "hidden: old save missing fields" 10
      echo "files changed vs base:"; git -C "$R" diff --stat "$base" HEAD | tail -5 ;;
    T7)
      suite
      python3 - "$R/data/xp.json" "$R/tests/run.gd" <<'PY'
import json, sys, re
d = json.load(open(sys.argv[1])); k = d.get("kill_xp", {})
print("cave_shaman:", k.get("cave_shaman"), " cave_lurker:", k.get("cave_lurker"))
t = open(sys.argv[2]).read()
print("run.gd lines mentioning cave_shaman:", len([l for l in t.splitlines() if "cave_shaman" in l]),
      " mentioning cave_lurker:", len([l for l in t.splitlines() if "cave_lurker" in l]),
      " stale 90 check:", bool(re.search(r"cave_shaman[^\n]*\b90\b", t)))
for l in t.splitlines():
    if "cave_shaman" in l or "cave_lurker" in l: print("  >", l.strip()[:160])
PY
      echo "commits on branch: $(git -C "$R" rev-list --count "$base"..HEAD)" ;;
    T8|T9|T10|T11|T12)
      g="$R/art/export/${asset}.glb"
      for p in art/scripts/build_${asset}.py art/export/${asset}.glb art/previews/${asset}_threequarter.png; do
        if git -C "$R" cat-file -e "HEAD:$p" 2>/dev/null; then echo "committed: $p ($(wc -c < "$R/$p" | tr -d ' ') bytes)"; elif [ -f "$R/$p" ]; then echo "NOT committed: $p"; verify_fail=1; else echo "MISSING: $p"; verify_fail=1; fi
      done
      if [ -f "$g" ]; then
        if [ ! -f "$B/tools/gltf_stats.py" ]; then
          echo "verify: tools/gltf_stats.py is not in this checkout; cannot print mesh stats. See REPRODUCING.md."
          verify_fail=1
        else
          python3 "$B/tools/gltf_stats.py" "$g" || verify_fail=1
        fi
        python3 "$B/tools/glb_check.py" "$g" "$src" --preview "$R/art/previews/${asset}_threequarter.png" --size 512 --max-texture 512 --script "$R/art/scripts/build_${asset}.py" ${also[@]+"${also[@]}"} || verify_fail=1
      else
        verify_fail=1
      fi ;;
    T13|T14|T15|T16)
      for p in art/scripts/build_${asset}.py art/export/${asset}.glb art/export/${asset}.json art/previews/${asset}_bare.png art/previews/${asset}_ranger.png art/previews/${asset}_knight.png art/previews/${asset}_mix.png; do
        if git -C "$R" cat-file -e "HEAD:$p" 2>/dev/null; then echo "committed: $p ($(wc -c < "$R/$p" | tr -d ' ') bytes)"; elif [ -f "$R/$p" ]; then echo "NOT committed: $p"; verify_fail=1; else echo "MISSING: $p"; verify_fail=1; fi
      done
      if [ -f "$R/art/export/${asset}.glb" ] && [ -f "$R/art/export/${asset}.json" ]; then
        QUATERNIUS_SOURCE="$Q" python3 "$B/tools/kit_check.py" "$R/art/export/${asset}.glb" "$R/art/export/${asset}.json" --script "$R/art/scripts/build_${asset}.py" --previews "$R/art/previews/${asset}" --kit "$kitarg" || verify_fail=1
      else
        verify_fail=1
      fi ;;
  esac
} >> "$out" 2>&1
# Final task result, computed after verification. Infrastructure and timeout
# stay distinct and take precedence over a model or checker failure.
if [ "${infra_fail:-0}" -eq 1 ]; then
  result=INFRA
  code=75
elif [ "${timed_out:-0}" -ne 0 ]; then
  result=TIMEOUT
  code=124
elif [ "${verify_fail:-0}" -ne 0 ]; then
  result=FAIL
  code=1
elif [ "${code:-0}" -ne 0 ]; then
  result=FAIL
else
  result=PASS
  code=0
fi
echo "=== result=$result exit=$code" >> "$out"
git -C "$R" checkout -q -f main
rm -rf "$pdir"
tail -20 "$out"
exit "$code"
