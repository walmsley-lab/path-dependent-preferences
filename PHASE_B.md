# Phase B: the causal decomposition program

*Runs only after Phase A completes and only if its artifacts justify it.
Phase A stays frozen; nothing here touches the preregistered design.
Escalation spine: existence → persistence → mediation → localization →
causal use → causal transfer → deliberate control. Kill criteria live in
THEORY.md §9; the evidence-level ladder (behavioral / representational /
causal-use / causal-transfer) governs what each result may claim.*

## Infrastructure status (verified, 2026-08-15)

- **Transplant-ready:** `train.py` saves full training state (model weights
  + Adam m/v + step + all RNG) at every segment boundary and final step;
  `--resume_weights_from` / `--resume_opt_from` implement crossed
  continuation and are smoke-tested (crossed C1-weights × C2-optimizer at
  the common tail-start step runs and records provenance).
- **Transplant point:** phase-boundary steps differ by condition, but the
  **tail-start step is identical across C1/C2/C3** — the canonical crossed-
  transplant point needs no interpolation.
- **Optimizer ablations ready:** `--optimizer {adamw, sgd, sgd_momentum}`.
- **Trajectories reconstructable without retraining:** weight checkpoints
  every 5%; βU/βC + conflict/ID/no-cue/cue-only scored per checkpoint in the
  batch; probes at {20,40,60,80,100}% and re-runnable on any saved
  checkpoint; train-line accuracy computable post-hoc from checkpoints +
  curriculum files (`plot_acquisition.py`); Δlogp margins stored.
- **Route weight is continuous everywhere:** conflict agreement and βU−βC
  are the behavioral estimators of w ∈ [0,1]; no analysis code buckets
  models into binary mechanisms.

## Prioritized interventions

| # | Experiment | Question it answers | Kills which attack | Compute |
|---|---|---|---|---|
| B1 | **Crossed weights × Adam-state transplant** at tail-start (2×2, common continuation, paired seeds) | What carries the history — representations or optimizer memory? | "it's just Adam bookkeeping" / "it's just weights" | ~8 runs × tail-length ≈ 1 GPU-hr |
| B2 | **Adam-state reset** at tail-start (cheap sibling of B1) | Is optimizer memory necessary for persistence? | optimizer-mediation | ~4 runs × tail ≈ 0.5 hr |
| B3 | **SGD replication** of C1/C2 (2–3 paired seeds) | Does the order effect survive without optimizer moments? | "Adam artifact" (THEORY P-refs; Sweeney 2026) | ~6 full runs ≈ 1.5 hr |
| B4 | **Extended-tail / hysteresis test** (tail ×2, ×4) | Transient interference vs. developmental lock-in; washout timescale | "it would wash out" | ~6 part-runs ≈ 1 hr |
| B5 | **η / gradient-accumulation scaling** (η/2 & 2×steps; accumulation ×4) | Noncommutativity-mediated vs. starvation-mediated (THEORY P3 discriminator) | mechanism ambiguity | ~8 runs ≈ 2 hr |
| B6 | **λ/cue-direction steering, differential by condition** (implemented: `score.py --steer`) | Causal reliance, not just decodability | "probe is correlational" | minutes |
| B7 | **Layerwise C1↔C2 activation patching** at agent-token and decision-token positions | Where does divergence become causally instantiated? (2D map: layer × position) | "no localized mechanism" — noting a distributed-mechanism null is NOT a mechanism-difference null | ~1 hr analysis |
| B8 | **Early/late window swaps** (swap equal-sized curriculum windows) | First-mover capture vs. uniform sensitivity (THEORY P2-adjacent) | "any window would do" | ~6 runs ≈ 1.5 hr |
| B9 | **Gradient-starvation diagnostic:** βU-growth in C2 vs. isolated pilot at matched W-exposure (THEORY P1) | Is the losing route's learning suppressed by residual capture? | starvation-story unfalsifiability | analysis only |
| B10 | **Representation geometry** (spectral rank, participation ratio, CKA, subspace overlap) — strictly direction-neutral and exploratory | Does order produce reproducible geometry differences covarying with w? | — (exploratory; no "lower rank = compositional" assumption) | analysis only |
| B11 | More paired seeds; second model size (~30M); alternate cue realization | seed-fluke / scale-artifact / cue-family artifact | ~1 GPU-day |
| B12 | Pretrained small open-weight replication (ordered fine-tuning) | "from-scratch toy only"; forming vs. recruiting representations | ~1 GPU-day |

**Sequencing rule:** B1–B3 before interpretability depth (B6, B7, B10) —
"what carries the history" precedes "where does it act." B4/B5 slot in
whenever GPUs are idle; B9 is free with existing artifacts. B11/B12 gate on
the core effect existing.

**Theory hooks:** B1↔THEORY §6 (Markov mediation; tail < β₂ horizon);
B4↔P2 (log-slow washout predicted by margin starvation; toy corollary
predicts C1's commitment outlasts C2's); B5↔P3 (the two-theory
discriminator); B9↔P1; the persistence-asymmetry corollary makes B4
*directional*, not just existence-testing.

## Explicitly not in Phase B until the above resolve

SAE/VPD decomposition (needs a localized target first — B7's output);
formalization beyond THEORY.md; multi-trait persona worlds (ROADMAP Stage
2); closed-loop curriculum control (ROADMAP Stage 6).
