#!/bin/bash
# Override-A test at L1 (PREREG: Gate v3 outcome section): mini-C1/C2,
# 2 paired seeds, full calibrated scale. Interpretation rule frozen in
# PREREG.md BEFORE this script's first run.
set -e
S0=data/gate_L1
S1=data/mini_L1_seed1

[ -f $S1/manifest.json ] || python3 generate_world.py --level L1 --seed 1 \
    --n_w 1200000 --n_p 1200000 --outdir $S1
python3 preflight.py $S1 --check-init --seed 1

for pair in "0 $S0" "1 $S1"; do
  set -- $pair; seed=$1; d=$2
  for c in C1 C2; do
    r=runs/mini_${c}_L1_s$seed
    if [ ! -f $r/ckpt_100.pt ]; then
      python3 train.py --data $d --curriculum curriculum_$c --seed $seed \
          --outdir $r &
    fi
  done
  wait
done

for seed in 0 1; do
  d=$S0; [ $seed -eq 1 ] && d=$S1
  for c in C1 C2; do
    python3 score.py --run runs/mini_${c}_L1_s$seed --data $d \
        --ckpt ckpt_100.pt --sets eval_conflict eval_id eval_nocue eval_cueonly
  done
done

python3 - <<'EOF'
import json
acc = {}
for seed in (0, 1):
    for c in ("C1", "C2"):
        r = json.load(open(f"runs/mini_{c}_L1_s{seed}/score_ckpt_100.json"))
        acc[(c, seed)] = r["sets"]["eval_conflict"]["acc_utility"]
deltas = []
for seed in (0, 1):
    d = acc[("C1", seed)] - acc[("C2", seed)]
    deltas.append(d)
    print(f"MINI seed {seed}: C1={acc[('C1',seed)]:.4f} "
          f"C2={acc[('C2',seed)]:.4f} delta={d:+.4f}")
mean_d = sum(deltas) / len(deltas)
support = all(x > 0 for x in deltas) and mean_d >= 0.10
print(f"MINI mean delta: {mean_d:+.4f}")
print(f"OVERRIDE_A: {'SUPPORTED' if support else 'NOT SUPPORTED'} "
      "(rule: both deltas > 0 and mean >= 0.10; frozen in PREREG.md)")
EOF
echo MINIS_COMPLETE
