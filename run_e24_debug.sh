#!/bin/bash
# Calibration diagnostic: does Route A crystallize with 3x more optimization?
# 24-epoch W-heavy pilot + no-cue curve + train-vs-held-out acquisition plot.
set -e
python3 train.py --data data/gate_L0 --curriculum pilot_w_heavy_then_p \
    --seed 0 --outdir runs/debug_wheavy_e24 --epochs 24
for c in 020 040 060 080 100; do
  python3 score.py --run runs/debug_wheavy_e24 --data data/gate_L0 \
      --ckpt ckpt_$c.pt --sets eval_nocue 2>/dev/null | \
    python3 -c "import sys,json; print('CURVE24 $c nocue', json.load(sys.stdin)['sets']['eval_nocue']['acc_utility'])"
done
grep "choose?" data/gate_L0/pilot_w_heavy_then_p.txt > /tmp/wheavy_p_lines.txt
python3 plot_acquisition.py --run runs/debug_wheavy_e24 --data data/gate_L0 \
    --train_file /tmp/wheavy_p_lines.txt --eval_set eval_nocue \
    --title "Route A acquisition: utility (24-epoch W-heavy pilot)" \
    --out figures/route_a_acquisition.png
echo E24_COMPLETE
