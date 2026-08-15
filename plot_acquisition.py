"""Train-vs-held-out acquisition curves across a run's checkpoints.

Distinguishes grokking (train saturates long before held-out jumps) from
ordinary delayed acquisition (both rise together). One figure, two lines.

Usage:
  python plot_acquisition.py --run runs/debug_ponly_e8 --data data/gate_L0 \
      --train_file data/gate_L0/pilot_p_only.txt --eval_set eval_cueonly \
      --out figures/route_b_acquisition.png
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from score import load_run, forced_choice, load_set
from train import pick_device

INK = "#202428"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--train_file", required=True)
    ap.add_argument("--eval_set", default="eval_cueonly")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--out", default=None)
    ap.add_argument("--title", default=None)
    args = ap.parse_args()
    dev = pick_device("auto")

    tr_lines = [l for l in open(args.train_file).read().splitlines()
                if l.endswith(("Option 1", "Option 2"))][:args.n]
    tr_prompts = [l.rsplit(" A: Option", 1)[0] for l in tr_lines]
    tr_ans = np.array([int(l[-1]) for l in tr_lines])

    ev = load_set(args.data, args.eval_set)[:args.n]
    key = "cue_answer" if args.eval_set == "eval_cueonly" else "utility_answer"
    ev_prompts = [r["prompt"] for r in ev]
    ev_ans = np.array([r[key] for r in ev])

    pcts, tr_acc, ev_acc = [], [], []
    for ck in sorted(Path(args.run).glob("ckpt_*.pt")):
        pct = int(ck.stem.split("_")[1])
        model, stoi, cfg = load_run(args.run, ck.name, dev)
        d_tr = forced_choice(model, stoi, tr_prompts, dev, cfg["block"])
        d_ev = forced_choice(model, stoi, ev_prompts, dev, cfg["block"])
        pcts.append(pct)
        tr_acc.append(float((np.where(d_tr > 0, 1, 2) == tr_ans).mean()))
        ev_acc.append(float((np.where(d_ev > 0, 1, 2) == ev_ans).mean()))
        print(f"ckpt {pct:3d}%  train {tr_acc[-1]:.3f}  heldout {ev_acc[-1]:.3f}")

    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.plot(pcts, tr_acc, color="#1D6A96", linewidth=2, marker="o",
            markersize=3, label="training lines (answers stripped)")
    ax.plot(pcts, ev_acc, color="#B4452A", linewidth=2, marker="s",
            markersize=3, label=f"held-out ({args.eval_set})")
    ax.axhline(0.5, color=INK, linewidth=0.8, linestyle=":", alpha=0.5)
    ax.set_xlabel("training progress (%)")
    ax.set_ylabel("forced-choice accuracy")
    ax.set_ylim(0.35, 1.02)
    ax.set_title(args.title or
                 "Grokking would show train saturating far ahead of held-out")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    out = args.out or f"{args.run}/acquisition.png"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
