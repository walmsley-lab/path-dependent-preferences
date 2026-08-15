"""Figures and Table 1 from the batch's score_*.json files.

Reads runs/{cond}_{level}_s{seed}/score_ckpt_{pct}.json and produces:
  fig1_same_behavior          ID accuracy vs training %, by condition
  fig2_route_selection        conflict (utility-agreement) + cue-only (cue-
                              following) vs training %, by condition
  fig3_mechanism_competition  beta_U(t) and beta_C(t) by condition
  fig4_context_dissociation   accuracy under none/congruent/incongruent demos
  table1.md                   final-checkpoint summary, mean +/- sd across seeds
  paired_deltas.md            the preregistered primary statistic (per-seed
                              conflict-accuracy differences, C1 - C2)

Per-seed trajectories are drawn as thin lines; means are bold. Colors follow
the condition (fixed assignment, validated palette); identity is never
color-alone (direct labels + legend).

Usage: python analyze.py --level L0 [--runs runs --out figures]
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COND_COLORS = {"C1": "#1D6A96", "C2": "#B4452A", "C3": "#7A5FA8"}
COND_LABELS = {"C1": "C1 structure-first", "C2": "C2 choices-first",
               "C3": "C3 interleaved"}
INK, GRID = "#202428", "#e6e3da"

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "font.size": 10, "axes.titlesize": 11,
})


def load_runs(runs_dir, level):
    """-> {cond: {seed: {pct: report}}}"""
    out = {}
    for d in sorted(Path(runs_dir).glob(f"C*_{level}_s*")):
        m = re.match(rf"(C\d)_{level}_s(\d+)", d.name)
        if not m:
            continue
        cond, seed = m.group(1), int(m.group(2))
        for f in sorted(d.glob("score_ckpt_*.json")):
            pct = int(f.stem.split("_")[-1])
            out.setdefault(cond, {}).setdefault(seed, {})[pct] = json.loads(
                f.read_text())
    return out


def series(data, cond, extract):
    """-> (pcts, {seed: values}) for one metric across checkpoints."""
    per_seed = {}
    for seed, ckpts in data.get(cond, {}).items():
        pts = {}
        for pct, rep in ckpts.items():
            try:
                v = extract(rep)
            except (KeyError, TypeError):
                continue
            if v is not None:
                pts[pct] = v
        if pts:
            per_seed[seed] = pts
    pcts = sorted({p for s in per_seed.values() for p in s})
    return pcts, per_seed


def traj_panel(ax, data, extract, ylabel, conds, chance=None):
    ends = []
    for cond in conds:
        pcts, per_seed = series(data, cond, extract)
        if not per_seed:
            continue
        col = COND_COLORS[cond]
        for vals in per_seed.values():
            xs = sorted(vals)
            ax.plot(xs, [vals[x] for x in xs], color=col, alpha=0.25,
                    linewidth=0.9)
        means = [np.mean([v[p] for v in per_seed.values() if p in v])
                 for p in pcts]
        ax.plot(pcts, means, color=col, linewidth=2.2,
                label=COND_LABELS[cond])
        ends.append((cond, col, pcts[-1], means[-1]))
    # Direct end labels, dodged apart when trajectories converge.
    ends.sort(key=lambda e: e[3])
    ys = [e[3] for e in ends]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + 0.05)
    for (cond, col, x, y0), y in zip(ends, ys):
        ax.annotate(cond, (x, y0), xytext=(5, (y - y0) * 72 * 3.4 / 1.04),
                    textcoords="offset points", color=col, fontsize=9,
                    fontweight="bold", va="center")
    if chance is not None:
        ax.axhline(chance, color=INK, linewidth=0.8, linestyle=":",
                   alpha=0.5)
        ax.annotate("chance", (ax.get_xlim()[0], chance), xytext=(2, 3),
                    textcoords="offset points", fontsize=8, alpha=0.6)
    ax.set_xlabel("training progress (%)")
    ax.set_ylabel(ylabel)
    ax.set_ylim(-0.02, 1.02)


def save(fig, out, name):
    for ext in ("png", "pdf"):
        fig.savefig(Path(out) / f"{name}.{ext}", dpi=200,
                    bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {name}")


def final_metric(data, cond, extract):
    vals = []
    for seed, ckpts in data.get(cond, {}).items():
        if 100 in ckpts:
            try:
                v = extract(ckpts[100])
                if v is not None:
                    vals.append((seed, v))
            except (KeyError, TypeError):
                pass
    return dict(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True)
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default="figures")
    args = ap.parse_args()
    Path(args.out).mkdir(exist_ok=True)
    data = load_runs(args.runs, args.level)
    conds = [c for c in ("C1", "C2", "C3") if c in data]
    print(f"loaded conditions: {conds}, "
          f"seeds: { {c: sorted(data[c]) for c in conds} }")

    # Figure 1 — same behavior in-distribution.
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    traj_panel(ax, data, lambda r: r["sets"]["eval_id"]["acc_utility"],
               "ID accuracy", conds, chance=0.5)
    ax.set_title("In-distribution choices: conditions indistinguishable")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    save(fig, args.out, "fig1_same_behavior")

    # Figure 2 — route selection: conflict + cue-only.
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4), sharey=True)
    traj_panel(axes[0], data,
               lambda r: r["sets"]["eval_conflict"]["acc_utility"],
               "conflict set: utility-agreement", conds, chance=0.5)
    axes[0].set_title("Which route wins when they disagree?")
    traj_panel(axes[1], data,
               lambda r: r["sets"]["eval_cueonly"]["acc_cue"],
               "cue-only set: cue-following", conds, chance=0.5)
    axes[1].set_title("Pure shortcut reliance (utility ties)")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, args.out, "fig2_route_selection")

    # Figure 3 — mechanism-competition coefficients.
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4))
    for ax, key, title in [
            (axes[0], "beta_U", "utility coefficient  β$_U$(t)"),
            (axes[1], "beta_C", "cue coefficient  β$_C$(t)")]:
        for cond in conds:
            pcts, per_seed = series(
                data, cond, lambda r: r["sets"]["eval_conflict"][key])
            if not per_seed:
                continue
            col = COND_COLORS[cond]
            for vals in per_seed.values():
                xs = sorted(vals)
                ax.plot(xs, [vals[x] for x in xs], color=col, alpha=0.25,
                        linewidth=0.9)
            means = [np.mean([v[p] for v in per_seed.values() if p in v])
                     for p in pcts]
            ax.plot(pcts, means, color=col, linewidth=2.2,
                    label=COND_LABELS[cond])
        ax.axhline(0, color=INK, linewidth=0.8, alpha=0.4)
        ax.set_title(title)
        ax.set_xlabel("training progress (%)")
    axes[0].set_ylabel("OLS coefficient on Δlogp (conflict set)")
    axes[0].legend(frameon=False, fontsize=8)
    save(fig, args.out, "fig3_mechanism_competition")

    # Figure 4 — in-context dissociation (final checkpoint).
    ctx_conds = ("none", "congruent", "incongruent")
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    width = 0.25
    for i, cond in enumerate(conds):
        vals, errs = [], []
        for ctx in ctx_conds:
            per_seed = final_metric(
                data, cond, lambda r: r["context"][ctx]["acc_utility"])
            vals.append(np.mean(list(per_seed.values())) if per_seed else 0)
            errs.append(np.std(list(per_seed.values())) if per_seed else 0)
        x = np.arange(len(ctx_conds)) + (i - 1) * width
        ax.bar(x, vals, width * 0.92, yerr=errs, color=COND_COLORS[cond],
               label=COND_LABELS[cond], error_kw={"linewidth": 1})
    ax.set_xticks(range(len(ctx_conds)),
                  [f"{c} demos" for c in ctx_conds])
    ax.axhline(0.5, color=INK, linewidth=0.8, linestyle=":", alpha=0.5)
    ax.set_ylabel("no-cue accuracy (utility-agreement)")
    ax.set_title("Does immediate context override the trained preference?")
    ax.legend(frameon=False, fontsize=8)
    ax.set_ylim(0, 1.02)
    save(fig, args.out, "fig4_context_dissociation")

    # Table 1 + the preregistered primary statistic.
    metrics = {
        "final loss": None,   # from train_log, appended below
        "ID acc": lambda r: r["sets"]["eval_id"]["acc_utility"],
        "conflict acc": lambda r: r["sets"]["eval_conflict"]["acc_utility"],
        "no-cue acc": lambda r: r["sets"]["eval_nocue"]["acc_utility"],
        "cue-follow": lambda r: r["sets"]["eval_cueonly"]["acc_cue"],
        "W acc": lambda r: r.get("acc_w"),
        "λ selectivity": lambda r: max(
            (v["selectivity"] for k, v in r.get("probes", {}).items()
             if k.endswith("lambda_class")), default=None),
        "override rate": lambda r: r.get("context", {}).get("override_rate"),
    }
    rows = ["| Metric | " + " | ".join(COND_LABELS[c] for c in conds) + " |",
            "|---" * (len(conds) + 1) + "|"]
    for name, fn in metrics.items():
        cells = []
        for cond in conds:
            if name == "final loss":
                losses = []
                for d in Path(args.runs).glob(f"{cond}_{args.level}_s*"):
                    log = json.loads((d / "train_log.json").read_text())
                    losses.append(log[-1]["loss"])
                vals = dict(enumerate(losses))
            else:
                vals = final_metric(data, cond, fn)
            cells.append(f"{np.mean(list(vals.values())):.3f} ± "
                         f"{np.std(list(vals.values())):.3f}"
                         if vals else "—")
        rows.append(f"| {name} | " + " | ".join(cells) + " |")
    (Path(args.out) / "table1.md").write_text("\n".join(rows) + "\n")
    print("wrote table1.md")

    if "C1" in data and "C2" in data:
        c1 = final_metric(data, "C1",
                          lambda r: r["sets"]["eval_conflict"]["acc_utility"])
        c2 = final_metric(data, "C2",
                          lambda r: r["sets"]["eval_conflict"]["acc_utility"])
        deltas = {s: c1[s] - c2[s] for s in sorted(set(c1) & set(c2))}
        lines = ["# Preregistered primary statistic",
                 "Δᵢ = conflict accuracy, C1(i) − C2(i), final checkpoint", ""]
        lines += [f"- seed {s}: {d:+.3f}" for s, d in deltas.items()]
        if deltas:
            arr = np.array(list(deltas.values()))
            same = max((arr > 0).sum(), (arr < 0).sum())
            lines += ["", f"mean Δ = {arr.mean():+.3f}; "
                      f"{same}/{len(arr)} same sign; "
                      f"support requires ≥4/5 same sign and mean |Δ| ≥ 0.10"]
        (Path(args.out) / "paired_deltas.md").write_text("\n".join(lines) + "\n")
        print("wrote paired_deltas.md")


if __name__ == "__main__":
    main()
