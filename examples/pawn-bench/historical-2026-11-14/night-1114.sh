#!/bin/bash
# Overnight reliability set, 2026-11-14: three passes over the four kit tasks, then the two knights.
# Runs are independent; a failed run does not stop the set. Summary at the end and in results/night-1114.summary.txt
cd "$(cd "$(dirname "$0")" && pwd)" || exit 1
S=results/night-1114.summary.txt; : > "$S"
for i in 1 2 3; do
  for t in T13 T14 T15 T16; do
    ./run.sh "$t" q36 > /dev/null 2>&1
    f=$(ls -t results/$t-q36-*.txt | head -1)
    echo "$(date +%H:%M) pass $i $t $(grep -o 'seconds=[0-9]* fix_rounds=[0-9]*' "$f") $(grep -o 'infra_fail=[0-9]* session_full=[0-9]* timed_out=[0-9]*' "$f") $(tail -1 "$f")" | tee -a "$S"
  done
done
for t in T11 T12 T11 T12; do
  ./run.sh "$t" q36 > /dev/null 2>&1
  f=$(ls -t results/$t-q36-*.txt | head -1)
  echo "$(date +%H:%M) knight $t $(grep -o 'seconds=[0-9]* fix_rounds=[0-9]*' "$f") $(tail -1 "$f")" | tee -a "$S"
done
echo "=== done $(date +%H:%M)"; cat "$S"
