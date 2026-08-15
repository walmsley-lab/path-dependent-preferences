# Path-Dependent Preferences

**Does learning order select the mechanism behind a model's preferences?**

Apart Research [Digital Minds Research Sprint](https://apartresearch.com/sprints/digital-minds-research-sprint-2026-08-14-to-2026-08-16), Aug 14–16 2026 · Track 5 (The Assistant Persona & Model Identity).

Two models can see exactly the same evidence and make exactly the same
ordinary choices, yet learn different reasons for making them. We ask whether
the *order* of experience determines which reason wins.

## The experiment in three pictures

**1 — Two developmental histories.** Small transformers train from scratch on
an artificial resource world with two task families: world-modeling (W:
ownership, outcomes, totals, comparisons) and choices (P: a named agent with a
latent utility weight λ picks between two actions with explicit payoffs).
Every condition sees the **same examples, same counts, same initialization,
same steps** — only the order differs (W→P, P→W, or interleaved), single
pass, flat learning rate, identical final-10% tail.

**2 — Two equally valid solutions.** In every training choice, the
λ-consistent action also carries a correlated framing cue, so training data is
solved equally well by a **utility mechanism** (parse payoffs → compute
λ-weighted trade-off) or a **shortcut** (follow the cue). Both routes give
identical training loss; the equivalence class is the design.

**3 — The diagnostic conflict.** Held-out evaluations force the routes apart:
a **conflict set** where cue and utility disagree, a **no-cue set** (utility
only), a **cue-only set** (exact utility ties — integer-exact — so only the
cue carries signal), plus W-competence and surface-generalization checks.
Behavior on the conflict set reveals which route governs. Linear probes (with
control-task selectivity, two preregistered positions) track what stays
decodable; in-context counter-evidence tests whether immediate context changes
expressed choices while the developmental preference remains decodable
underneath.

Because we author the training histories and define λ mathematically, we have
**causal ground truth** — the thing studies of frontier-model preferences
cannot have.

## Status

- [x] Preregistration drafted ([PREREG.md](PREREG.md)) — freezes before the batch launches
- [x] Generator + 16 invariant tests (route equivalence, conflict disagreement,
      split disjointness, curriculum multiset/tail identity, cue–payoff
      decorrelation, …)
- [x] Training/eval/probing/steering harness, smoke-verified end-to-end
- [ ] Balance gate (the first experiment: are both routes independently learnable?)
- [ ] 15-run batch (3 orderings × 5 paired seeds) + analysis

## Reproduce

```bash
python test_generator.py                                   # invariants must pass
python run_batch.py --stage gate                           # balance gate, L0→L2
# freeze the selected cue level + constants in PREREG.md, then:
python run_batch.py --stage batch --level <Lx> --seeds 0 1 2 3 4
python analyze.py --level <Lx>                             # figures + Table 1
```

`preflight.py` verifies the design invariants (same multiset, identical tails,
paired initialization) and refuses the launch on violation. Runs write full
manifests: git commit, dataset/vocab/init SHA-256, config, versions.

## Repository map

| File | Role |
|---|---|
| [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) | Full design, controls, outcome matrix, related work |
| [PREREG.md](PREREG.md) | Frozen hypotheses, endpoints, gate criteria, exclusion rules |
| [generate_world.py](generate_world.py) | World, cue levels L0–L2, eval sets, curricula, pilots |
| [test_generator.py](test_generator.py) | 16 invariant tests encoding the design guarantees |
| [train.py](train.py) / [preflight.py](preflight.py) | Single-pass curriculum trainer; executable launch invariants |
| [score.py](score.py) | Forced-choice Δlogp, βU/βC regression, probes, steering, context test |
| [run_batch.py](run_batch.py) / [colab_run.ipynb](colab_run.ipynb) | Orchestration, cloud bootstrap |
| [analyze.py](analyze.py) | Figures 1–4, Table 1, preregistered paired-Δ report |
| [technical-writing-guide.md](technical-writing-guide.md) | Reporting standards the writeup follows |

Design refined through adversarial review rounds across multiple AI systems;
decision log in the plan. Built with [Claude Code](https://claude.com/claude-code).
