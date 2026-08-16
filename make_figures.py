"""Paper figures from the provenance-stamped batch artifacts.

Figure 1 — the identification problem (four graph objects, and why one
           generic "knowledge graph" cannot hold them)
Figure 2 — experimental design (one multiset, three deals, paired inits,
           21 checkpoints, four diagnostic sets)
Figure 3 — developmental trajectories, all 15 organisms (THE figure)
Figure 4 — mechanistic evidence: probes, steering dose-response,
           ablation controls, and the failed patching test

Reads only stored artifacts; writes figures/fig{1..4}_*.png.
Usage:  python make_figures.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

R = Path("batch_results/runs")
OUT = Path("figures")
OUT.mkdir(exist_ok=True)

INK, FADED, RULE = "#26241d", "#6f6a5c", "#cfc9b6"
UTIL, CUE, MIX, GREEN = "#1D6A96", "#B4452A", "#7A5FA8", "#1e4d38"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "font.size": 9, "axes.edgecolor": RULE, "axes.labelcolor": INK,
    "xtick.color": FADED, "ytick.color": FADED, "text.color": INK,
    "axes.titlesize": 10, "axes.spines.top": False,
    "axes.spines.right": False})


def box(ax, x, y, w, h, text, style="solid", color=INK, fs=8):
    ls = {"solid": "-", "dashed": "--", "dotted": ":"}[style]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                linewidth=1.1, edgecolor=color,
                                facecolor="white", linestyle=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=color, zorder=5)


def arrow(ax, p0, p1, color=INK, style="-", label=None, fs=7):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>",
                                 mutation_scale=11, linewidth=1.1,
                                 color=color, linestyle=style,
                                 shrinkA=2, shrinkB=2))
    if label:
        ax.text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + .022, label,
                ha="center", fontsize=fs, color=color)


# ---------------------------------------------------------------- fig 1
def fig1():
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax in axes:
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[0]
    ax.set_title("G_generator — how the world was actually built\n"
                 "(privileged ground truth)", loc="left")
    box(ax, .02, .70, .22, .13, "agent")
    box(ax, .02, .44, .22, .13, "λ  (latent)", style="dashed")
    box(ax, .34, .44, .26, .13, "utility[o]")
    box(ax, .70, .44, .26, .13, "choice")
    box(ax, .70, .12, .26, .13, "framing_class[o]")
    box(ax, .34, .12, .26, .13, "scene")
    arrow(ax, (.13, .70), (.13, .58))
    arrow(ax, (.24, .50), (.34, .50))
    arrow(ax, (.60, .50), (.70, .50), label="argmax")
    arrow(ax, (.83, .44), (.83, .26), color=CUE)
    arrow(ax, (.60, .18), (.70, .18), color=CUE)
    ax.text(.02, .01, "the generator assigns wording FROM the choice —\n"
                      "the planted route is not causal in the world",
            fontsize=7.5, color=CUE)

    ax = axes[1]
    ax.set_title("G_observational — what the corpus offers a learner\n"
                 "(two predictors, indistinguishable on training data)",
                 loc="left")
    box(ax, .02, .68, .40, .13, "λ + payoffs", color=UTIL)
    box(ax, .02, .20, .40, .13, "scene + wording", color=CUE)
    box(ax, .52, .68, .44, .13, "utility_prediction", color=UTIL)
    box(ax, .52, .20, .44, .13, "cue_prediction", color=CUE)
    box(ax, .52, .44, .44, .13, "choice")
    arrow(ax, (.42, .74), (.52, .74), color=UTIL)
    arrow(ax, (.42, .26), (.52, .26), color=CUE)
    arrow(ax, (.74, .68), (.74, .58), color=UTIL, style=":")
    arrow(ax, (.74, .33), (.74, .43), color=CUE, style=":")
    ax.text(.02, .03,
            "training constraint (machine-verified):\n"
            "utility_prediction(x) = cue_prediction(x) = choice(x)  ∀x∈train\n"
            "dotted = predictive, not causal in the world",
            fontsize=7.5, color=FADED)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_identification.png", dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------- fig 2
def fig2():
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("Experimental design — one multiset, three deals, "
                 "paired initializations", loc="left")
    ax.text(.005, .86, "2.4M rendered lines\n1.2M structure · 1.2M choice",
            fontsize=8, color=INK, va="top")
    rows = [("C1", [("structure", .45, UTIL), ("choices", .45, CUE),
                    ("tail", .10, FADED)]),
            ("C2", [("choices", .45, CUE), ("structure", .45, UTIL),
                    ("tail", .10, FADED)]),
            ("C3", [("interleaved", .90, MIX), ("tail", .10, FADED)])]
    for i, (name, segs) in enumerate(rows):
        y = .55 - i * .17
        ax.text(.005, y + .035, name, fontsize=9, color=GREEN, weight="bold")
        x = .07
        for label, frac, color in segs:
            w = frac * .60
            ax.add_patch(plt.Rectangle((x, y), w, .075, facecolor=color,
                                       alpha=.72, edgecolor="white"))
            if w > .07:
                ax.text(x + w / 2, y + .037, label, ha="center",
                        va="center", fontsize=7.5, color="white")
            x += w
    ax.text(.70, .60, "× 5 paired seeds\n(identical init within seed,\n"
                      "hash-verified)", fontsize=8, va="top")
    ax.text(.70, .38, "21 checkpoints / organism\nθ, m, v, RNG preserved\n"
                      "at phase boundaries", fontsize=8, va="top")
    ax.text(.70, .16, "diagnostics: ID · conflict ·\nno-cue · cue-only",
            fontsize=8, va="top")
    ax.text(.07, .06, "identical final 10% tail in every condition — "
                      "same deck, different deal", fontsize=7.5, color=FADED)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_design.png", dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------- fig 3
def traj(run):
    xs, ys = [], []
    for p in sorted((R / run).glob("score_ckpt_*.json")):
        s = json.loads(p.read_text())["sets"]["eval_conflict"]
        xs.append(int(p.stem.split("_")[-1]))
        ys.append(s["acc_utility"])
    return xs, ys


def fig3():
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    titles = {"C1": "C1 · structure first", "C2": "C2 · choices first",
              "C3": "C3 · interleaved"}
    for ax, cond in zip(axes, ["C1", "C2", "C3"]):
        ax.axhline(.5, color=RULE, linestyle="--", linewidth=.8)
        for seed in range(5):
            run = f"{cond}_L1_s{seed}"
            xs, ys = traj(run)
            outlier = (cond == "C1" and seed == 3)
            ax.plot(xs, ys, linewidth=2.2 if outlier else 1.1,
                    color=CUE if outlier else GREEN,
                    alpha=1.0 if outlier else .45, zorder=5 if outlier else 2)
            if outlier:
                ax.annotate("C1 seed 3\nmastery → collapse →\n"
                            "transient recovery → reversal",
                            xy=(95, .215), xytext=(30, .12), fontsize=7.5,
                            color=CUE,
                            arrowprops=dict(arrowstyle="->", color=CUE,
                                            linewidth=.9))
        ax.set_title(titles[cond], loc="left")
        ax.set_xlabel("developmental age (%)")
        ax.set_xlim(0, 100); ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("conflict: agreement with the utility rule")
    axes[0].text(3, .53, "chance", fontsize=7, color=FADED)
    fig.suptitle("Developmental trajectories, all 15 organisms — "
                 "14 converge utility-side; one reverses late",
                 x=.005, ha="left", fontsize=10.5)
    fig.tight_layout(rect=[0, 0, 1, .93])
    fig.savefig(OUT / "fig3_trajectories.png", dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------- fig 4
def fig4():
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.2))

    # (a) held-out-agent probe generalization
    ax = axes[0]
    labels, vals = [], []
    for run, lab in [("C2_L1_s0", "C2"), ("C3_L1_s0", "C3")]:
        p = Path("runs") / run / "evidence_probe_generalization.json"
        if not p.exists():
            continue
        ev = json.loads(p.read_text())
        best = max(v["heldout_agent_selectivity"]
                   for row in ev["layers"].values()
                   for k, v in row.items() if "lambda" in k)
        labels.append(lab); vals.append(best)
    ax.bar(labels, vals, color=UTIL, width=.5)
    ax.axhline(0, color=RULE)
    ax.set_ylim(0, 1.05); ax.set_ylabel("selectivity")
    ax.set_title("(a) λ recoverable on\nHELD-OUT agents", loc="left")

    # (b) steering dose-response
    ax = axes[1]
    for run, lab, color in [("C2_L1_s0", "C2 @L2", UTIL),
                            ("C3_L1_s0", "C3 @L3", GREEN)]:
        p = Path("runs") / run / "evidence_steering.json"
        if not p.exists():
            continue
        ev = json.loads(p.read_text())
        for key, ls, c in [("candidate", "-", color),
                           ("control_layer", "--", FADED),
                           ("random_direction", ":", CUE)]:
            sw = ev["sweeps"][key]
            sw = sw.get("alphas", sw)
            a = sorted(float(k) for k in sw)
            y = [sw[str(k)]["acc_utility"] for k in a]
            ax.plot(a, y, ls, color=c, linewidth=1.6 if key == "candidate"
                    else 1.0, label=f"{lab}" if key == "candidate" else None)
    ax.set_xlabel("steering α"); ax.set_ylim(0, 1.02)
    ax.set_title("(b) steering: candidate site\nvs controls (dashed/dotted)",
                 loc="left")
    ax.legend(frameon=False, fontsize=7)

    # (c) ablation with controls
    ax = axes[2]
    names, cand, rand, ctrl = [], [], [], []
    for run, lab in [("C2_L1_s0", "C2"), ("C3_L1_s0", "C3")]:
        p = Path("runs") / run / "evidence_ablation.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())["utility_agreement_drop"]
        names.append(lab); cand.append(d["candidate_lambda"])
        rand.append(d["random_direction"]); ctrl.append(d["control_layer_lambda"])
    x = range(len(names))
    ax.bar([i - .25 for i in x], cand, .25, label="v_λ @ candidate",
           color=UTIL)
    ax.bar(list(x), rand, .25, label="random @ candidate", color=FADED)
    ax.bar([i + .25 for i in x], ctrl, .25, label="v_λ @ control layer",
           color=CUE)
    ax.set_xticks(list(x)); ax.set_xticklabels(names)
    ax.axhline(0, color=RULE)
    ax.set_ylabel("drop in utility-agreement")
    ax.set_title("(c) ablation: causal dependence,\nbut NOT unique "
                 "localization", loc="left")
    ax.legend(frameon=False, fontsize=6.5)

    # (d) the failed patching test
    ax = axes[3]
    rows, y = [], 0
    for run, lab in [("C2_L1_s0", "C2←C3"), ("C3_L1_s0", "C3←C2")]:
        p = Path("runs") / run / "evidence_patching.json"
        if not p.exists():
            continue
        ev = json.loads(p.read_text())
        au = ev.get("audit", {}).get("per_example", {})
        for age, a in au.items():
            rows.append((f"{lab} · age {int(age)}%",
                         a["candidate"]["on_disputed_items_sides_with_donor"],
                         a["mismatched"]["on_disputed_items_sides_with_donor"]))
    ypos = range(len(rows))
    ax.barh([i + .18 for i in ypos], [r[1] for r in rows], .32,
            color=UTIL, label="candidate patch")
    ax.barh([i - .18 for i in ypos], [r[2] for r in rows], .32,
            color=FADED, label="mismatched control")
    ax.axvline(.5, color=RULE, linestyle="--", linewidth=.8)
    ax.set_yticks(list(ypos)); ax.set_yticklabels([r[0] for r in rows],
                                                  fontsize=7)
    ax.set_xlim(0, 1); ax.set_xlabel("sides with donor on disputed items")
    ax.set_title("(d) patching: predicted transfer\nNOT observed", loc="left")
    ax.legend(frameon=False, fontsize=6.5, loc="lower right")

    fig.suptitle("Mechanistic evidence — two organisms, single seed, "
                 "post-hoc: what the instruments support and what they refute",
                 x=.005, ha="left", fontsize=10.5)
    fig.tight_layout(rect=[0, 0, 1, .90])
    fig.savefig(OUT / "fig4_mechanism.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4()
    for p in sorted(OUT.glob("fig*.png")):
        print("wrote", p)
