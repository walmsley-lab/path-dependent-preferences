#!/bin/bash
# Calibration diagnostic: is Route A learnable WITHOUT the cue competing?
# Trains W-heavy-then-NONCUED-P (neutral verbs, utility answers) and traces
# the no-cue acquisition curve. Calibration only; never part of main runs.
set -e
python3 generate_world.py --level L0 --seed 0 --n_w 80000 --n_p 80000 \
    --n_p_nocue 80000 --outdir data/nocue_L0 > /dev/null
python3 train.py --data data/nocue_L0 --curriculum pilot_w_then_nocue_p \
    --seed 0 --outdir runs/debug_nocueP_e8 --epochs 8
for c in 020 040 060 080 100; do
  python3 score.py --run runs/debug_nocueP_e8 --data data/nocue_L0 \
      --ckpt ckpt_$c.pt --sets eval_nocue eval_id 2>/dev/null | \
    python3 -c "import sys,json; s=json.load(sys.stdin)['sets']; print('NOCUE_CURVE $c nocue', s['eval_nocue']['acc_utility'], 'id', s['eval_id']['acc_utility'])"
done
python3 debug_selfcheck.py --run runs/debug_nocueP_e8 \
    --file data/nocue_L0/pilot_w_then_nocue_p.txt
echo NOCUE_DEBUG_COMPLETE
