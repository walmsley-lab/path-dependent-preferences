# The Perturbation Ladder: how deeply did we change the organism?

*Adopted 2026-08-15 (ChatGPT handoff via Patrick, integrated by Claude).
This is a new experimental axis, orthogonal to the developmental-order axis.
It does not modify Phase A; Phase A's preregistered claims stay exactly as
frozen. Everything here is Phase B and beyond, plus a schema decision made
now so all interventions land in one comparable framework.*

**The core sentence:** we are not just asking whether a model's preference
can be changed. We are asking **how deeply** it has been changed —
expression, representation, causal mechanism, persistent weights, or
developmental trajectory — and what evidence distinguishes those
possibilities.

**The key terminology discipline:** a prompt does not perturb the weights.
It perturbs the model's current activation/state trajectory and therefore
its *expressed* behavior. Keeping behavior / activations / optimizer state /
weights / developmental history distinct is what makes the ladder a
scientific instrument instead of a metaphor.

## The six rungs (weakest/most reversible → deepest/most persistent)

| # | Rung | What varies | What's held fixed | Status in this repo |
|---|------|-------------|-------------------|---------------------|
| 1 | **Environmental** | the task/world presented (ID → conflict, no-cue, cue-only, altered payoffs, novel agents) | weights, context | **Built.** The eval-set suite *is* rung 1; `score_set` measures it. |
| 2 | **Contextual / persona** | in-context demonstrations or claims about an agent (congruent/incongruent/none) | weights | **Built & preregistered.** `score.py --context` (the contextual-dissociation protocol) is the first rung-2 experiment. |
| 3 | **Activation** | internal state during inference (steer/suppress λ-direction, amplify cue-direction, patch C1↔C2, ablate) | weights | **Partially built.** `steer_test` (α-sweep along the λ probe direction) exists; patching/ablation are Phase B. |
| 4 | **Optimizer-state** | Adam moments m, v (reset, transplant across curricula, swap while holding θ) | weights at transplant point | **Apparatus ready.** `trainstates` save θ+m+v+RNG at segment boundaries; `--resume_weights_from/--resume_opt_from` implement the crossed transplant (Phase B flagship B1). |
| 5 | **Weight** | θ itself (counter-training, corrective fine-tuning, weight transplant, editing) | — | Phase B / later. Must measure **persistence after the intervention is removed** — that is the defining question of this rung. |
| 6 | **Developmental** | the corpus/curriculum that grows a new organism (reorder W/P, move counterexamples, vary cue complexity, adaptive blocks) | init, data multiset (where applicable) | **Built — it is the main experiment.** C1/C2/C3 is a rung-6 intervention with the multiset held exactly fixed. |

Note the pleasant inversion: the *deepest* rung is the one we built first.
Phase A perturbs developmental history under maximal control; the ladder
now tells us which shallower perturbations to compare it against.

## Classify the *kind* of divergence, not just its magnitude

Every perturbation p gets a common diagnostic vector (all components
already computable with the existing harness):

```
d(p) = [ A_id, A_conflict, A_nocue, A_cueonly,   # behavioral (score_set)
         Δlogp margins,                           # decision strength
         D_λ, D_cue,                              # probe selectivities
         βU, βC,                                  # mechanism-competition regression
         persistence,                             # does it survive removal of p?
         specificity ]                            # do unrelated behaviors stay put?
```

Operational categories (defined by measurements, never by psychological
language):

- **Expression override** — behavior moves; λ stays decodable; effect
  vanishes when the context is removed. (The signature the preregistered
  dissociation protocol is designed to detect.)
- **Representation shift** — internal representations move *with* behavior.
- **Mechanism substitution** — another route becomes behaviorally/causally
  dominant while the previous route may remain represented (βU↓ βC↑ with
  D_λ stable would be the cleanest signature).
- **Persistent rewrite** — the change survives removal of the triggering
  context/intervention (rung ≥ 5 territory; must be shown, not assumed).
- **Developmental redirection** — the intervention changes what the model
  *later* learns or which route becomes dominant (rung 6; Phase A's
  dependent variable).

These labels are hypotheses about individual results, not guaranteed
clusters; whether real perturbations fall cleanly into them is itself an
empirical question.

## Schema decision (made now, so later work lands in one framework)

Perturbations become first-class objects wherever they are recorded:

```
Perturbation {
  type:        environmental | contextual | activation | optimizer | weight | developmental
  target:      what was manipulated (set name, direction, layer, segment, ...)
  strength:    dose (k demos, steering α, blocks reordered, ...)
  start_state: run_id + checkpoint (+ trainstate for rungs 4-5)
  end_state:   run_id + checkpoint after intervention (if any)
  measurements: d(p) components with provenance stamps
  persistence: measurements after removal of p (null where meaningless)
  provenance:  run_id, commit, timestamps  # numbers without a stamp do not exist
}
```

Existing artifacts (`score_*.json` context blocks, steer sweeps, the
planned B1 transplant outputs) should be *viewable* as instances of this
schema; a mechanical converter is enough — no rewrite of working code.

## The graph connection

Inferred-graph (Ĝ) edges already carry evidence types (behavioral /
representational / causal-use / causal-transfer). The ladder adds the
second annotation: **which perturbation rung produced the evidence, and
whether the effect persisted.** "Prompt context → choice (behavioral,
vanishes on removal)" and "λ-state → choice (activation patch, within
intervention window)" are different epistemic objects and must render
differently.

## Closed-loop extension (Stage 6 framing, unchanged but sharpened)

```
desired mechanism → perturb → measure divergence → classify failure mode
   → generate corrective experience → retrain → apply the SAME perturbation again
```

The controller's question upgrades from "is behavior right?" to "which
failure category does this perturbation expose, and did the corrective
curriculum close it?" — with the Goodhart guardrails of ROADMAP.md §Stage 6
unchanged (held-out audit sets, frozen policy, logged decisions).

## Near-term priorities (does NOT gate Phase A)

1. Contextual/persona perturbation via the existing dissociation protocol —
   already in the batch's final-checkpoint scoring.
2. Checkpoint-aligned λ/cue probe measurements before vs after context
   (probes currently run without context; the "λ still decodable under
   incongruent context" claim needs the with-context probe variant —
   small `score.py` extension, Phase B).
3. Persistence testing after context removal (trivially true for stateless
   forced-choice prompting — state that rather than measure it — but it
   becomes a real measurement for rungs 3-5).
4. One activation-level intervention beyond steering (a single
   C1→C2 activation patch at the decision token) in Phase B.
5. The optimizer/weight transplants already planned (B1).
6. The `Perturbation` schema converter, so every intervention can be
   compared in the same interface (workbench "perturbation depth" axis).
