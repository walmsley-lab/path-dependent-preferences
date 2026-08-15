"""Diagnostic: score a trained model on its OWN training P lines (answers
stripped, forced-choice). Distinguishes "never learned the answer mapping"
from "learned it but eval distribution/scoring is broken".

Usage: python debug_selfcheck.py --run runs/debug_ponly_e8 \
           --file data/gate_L0/pilot_p_only.txt
"""

import argparse

import numpy as np

from score import load_run, forced_choice
from train import pick_device


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--ckpt", default="ckpt_100.pt")
    ap.add_argument("--n", type=int, default=400)
    a = ap.parse_args()
    dev = pick_device("auto")
    model, stoi, cfg = load_run(a.run, a.ckpt, dev)
    lines = [l for l in open(a.file).read().splitlines()
             if l.endswith(("Option 1", "Option 2"))][:a.n]
    prompts = [l.rsplit(" A: Option", 1)[0] for l in lines]
    ans = np.array([int(l[-1]) for l in lines])
    d = forced_choice(model, stoi, prompts, dev, cfg["block"])
    pred = np.where(d > 0, 1, 2)
    print(f"TRAIN_SELF_CHECK acc: {float((pred == ans).mean()):.4f} "
          f"n: {len(lines)} mean|dlogp|: {float(np.abs(d).mean()):.3f}")


if __name__ == "__main__":
    main()
