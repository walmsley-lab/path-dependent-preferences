#!/bin/bash
# Rung 1 of the reproduction ladder: the ENTIRE pipeline at toy scale.
# Generates a tiny world, verifies launch invariants, trains a 0.1M-param
# model for ~21 steps, scores it, and self-checks on its own training lines.
# Runs on CPU in ~2-3 minutes. SUCCESS = mechanical integrity: every stage
# runs, every artifact appears, provenance is stamped. Accuracies at ~chance
# are EXPECTED at this scale — learnability is rung 2's job.
set -e
PY="${PY:-python3}"

echo "== [1/5] invariant tests"
$PY test_generator.py > /dev/null && echo "   17 invariants PASS"

echo "== [2/5] generate toy world"
$PY generate_world.py --level L0 --seed 0 --n_w 1500 --n_p 1500 \
    --outdir data/smoke > /dev/null && echo "   data/smoke written"

echo "== [3/5] preflight launch invariants"
$PY preflight.py data/smoke --check-init --seed 0 | tail -1

echo "== [4/5] train tiny model (C1 curriculum, ~21 steps)"
$PY train.py --data data/smoke --curriculum curriculum_C1 --seed 0 \
    --outdir runs/smoke --d_model 64 --layers 2 --heads 2 --batch 16 \
    2>&1 | tail -1

echo "== [5/5] score + self-check"
$PY score.py --run runs/smoke --data data/smoke --ckpt ckpt_100.pt \
    --sets eval_id eval_conflict > /dev/null
$PY debug_selfcheck.py --run runs/smoke --file data/smoke/curriculum_C1.txt
$PY - <<'EOF'
import json
r = json.load(open("runs/smoke/score_ckpt_100.json"))
m = json.load(open("runs/smoke/run_manifest.json"))
assert "acc_utility" in r["sets"]["eval_id"], "scoring output malformed"
assert m.get("run_id") and m.get("git_commit"), "provenance stamp missing"
print(f"   score artifacts + provenance OK (run_id {m['run_id']})")
EOF

echo
echo "SMOKE PASS — pipeline mechanically verified end to end."
echo "Near-chance accuracy at this scale is expected and correct."
echo "Next rung: bash run_nocue_debug.sh (GPU, ~15 min) shows real learning."
