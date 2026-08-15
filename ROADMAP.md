# Research roadmap: from scalar λ to cultivated computational character

*The lifespan plan beyond the sprint. Phase A (the preregistered ordering
experiment) stays untouched; everything here builds on it. The endpoint:*
**can we specify a desired computational character, cultivate it through
developmental training, inspect its formation, formally test its invariants,
intervene when it diverges, and verify the resulting mechanism rather than
merely its outputs?**

**The three axes.** The program has three independent knobs, and we
deliberately do not scale them simultaneously:

- **developmental complexity** — λ world → multi-trait θ → hierarchical
  personas → richer language → larger/pretrained models (the six stages);
- **perturbation depth** — world → prompt/persona → activations →
  optimizer state → weights → curriculum
  ([docs/perturbation_ladder.md](docs/perturbation_ladder.md));
- **evidential strength** — behavior → representation → causal
  involvement → developmental explanation → candidate causal abstraction
  (the evidence ladder; near-constitutional: no level automatically
  establishes the next).

The next several experiments keep the model tiny and the world simple
while descending in evidential depth; then one latent variable is added
with everything else controlled; only much later does model scale move.
That is how modest compute yields a lot of science.

**Scope discipline (keep this visible):** what we are building sits
somewhere between an interactive paper, a developmental-interpretability
testbed, a synthetic-world generator, and an experimental laboratory for
learned computation — *and we earn that one rung at a time.* The vision
determines what infrastructure we preserve and how future experiments are
organized. It is never permission to broaden the claims of the experiment
currently running.

A distinction runs through every stage and should be measured, not assumed:

> behavioral equivalence ≠ representational equivalence ≠ mechanistic
> equivalence ≠ developmental equivalence.

Two agents can make the same choices yet encode persona differently; encode
the same information yet causally use different circuitry; implement the same
mechanism yet have arrived by different histories. The current experiment
isolates the last two; later stages give each inequality its own instrument
(behavior batteries / probes / steering & ablation / authored history).

## The six stages

1. **Scalar ground truth (now).** Fixed λ per agent; validate whether order
   selects utility-vs-cue mechanism. Status: apparatus built, calibration in
   progress.
2. **Multidimensional persona.** Entry point (per 2026-08-15 discussion):
   TWO traits first — θ = (λ, ρ) with ρ = risk preference over stated
   stochastic payoffs — some situations identify λ, some ρ, some both,
   keeping ground truth visualizable and counterfactuals exhaustive before
   scaling to the full vector. Question upgrade: does developmental history
   change how the model *factorizes* a person? Full design below.
3. **Hierarchical persona.** Traits become *derived*: a latent utility whose
   expression varies systematically with relationship, uncertainty, prior
   cooperation. Question: do different curricula produce different
   *factorizations* of the same behavior?
4. **Context/persona dissociation at scale.** Contradictory demonstrations,
   system-like instructions, role information, changed circumstances — measure
   what moves behaviorally vs. what stays representationally stable, and
   characterize hysteresis and recoverability after temporary persona shifts.
5. **Provenance and causal mechanism.** Training history → emergence
   trajectory → representation → parameter/circuit → behavior: probes, timed
   emergence, steering, ablations, SAE/parameter decomposition (SPD/VPD)
   around divergence checkpoints.
6. **Closed-loop cultivation.** Interpretability becomes a training
   instrument, not post-hoc microscopy. Design below.

## Stage 2 concrete design: the five-trait world

Each agent gets an authored trait vector **θ = (λ, ρ, r, δ, c)**:

| Trait | Meaning | Behavioral instrument |
|---|---|---|
| λ | self/other weighting | payoff-split choices (current design) |
| ρ | risk tolerance | options with stated stochastic payoffs ("gains 4 shells or loses 2, equal chance") — U penalizes variance: −ρ·Var |
| r | reciprocity | repeated-partner scenarios; effective other-weight becomes λ + r·(partner cooperated last time) |
| δ | temporal discounting | now-vs-later payoffs ("2 tokens now or 5 after the market closes") — δᵗ weighting |
| c | rule-compliance | posted norms ("the village rule says split evenly"); c gates whether the rule overrides utility |

Utility: `U = Σ_t δᵗ · [ λ_eff·E[Δself_t] + (1−λ_eff)·E[Δother_t] − ρ·Var_t ]`,
overridden by the posted rule with probability governed by c;
`λ_eff = clip(λ + r·recip_t)`.

**Design principles carried over from Stage 1:** ground truth stays authored
and integer-exact where possible; every record carries full probe labels; a
three-way split with held-out surface forms; per-seed trait assignment,
demographically counterbalanced; invariant tests before anything trains.

**The identification problem deepens deliberately:** single tasks cannot
reveal single traits (a selfish-looking choice may be low λ, high ρ, or rule
compliance) — only the *battery* identifies θ. Eval sets include per-trait
isolation sets (other traits neutralized by construction) and cross-trait
conflict sets (e.g., reciprocity vs. rule; discounting vs. risk). The Stage-1
question then upgrades: does developmental order change **which factorization
of θ** the model learns — five separable directions vs. entangled
behavioral clusters? Measured via probe geometry across traits
(dimensionality, separability, layer/time stability), causal steering per
trait direction, and cross-context generalization of each trait.

## Stage 6 concrete design: the closed-loop curriculum controller

**Target:** a mechanism specification **M\***, not an output distribution.
Example (Stage-1 vocabulary): βU ≥ 0.8·βU_max with βC ≈ 0; λ-probe
selectivity above threshold at the agent token; steering response ≥ x pp per
unit α; W-competence ≥ 95%; persona-consistency invariants hold.

**Loop:**
```
train k steps → checkpoint → diagnostic vector d_t →
compare d_t to M* → controller π(d_t) selects next data block →
train k steps → …
```

- **Diagnostic vector d_t:** (βU, βC, per-trait probe selectivities, steering
  causal response, W-competence, ID accuracy, persona-consistency score) — all
  already computable with the Stage-1 harness at checkpoint speed.
- **Controller π:** starts as a transparent rule/bandit over a fixed menu of
  block types (more W; more no-cue P; counter-cue examples; per-trait
  isolation batches; interleave-ratio changes). No differentiating through
  interpretability at first. Objective (measured, not differentiated):
  `J = L_behavior + α·L_mechanism + β·L_robustness + γ·L_persona-consistency`.
- **Goodhart guardrails (non-negotiable):** the controller sees only its
  diagnostic sets; final evaluation uses held-out audit sets the controller
  never touches; the controller policy is frozen before the run
  (a prereg for the *curriculum*, mirroring PREREG.md for the experiment);
  every decision logged with its triggering diagnostics.
- **Baselines:** fixed-order curricula (C1/C2/C3) and random-policy
  controller — the claim "closed-loop cultivation beats open-loop order"
  needs its own controls.

**The formal layer** (where the Abbott-style formalization thread lands):
specify as machine-checkable properties — what constitutes the intended
persona state; which behavioral invariants must hold; which contexts are
*legitimately* preference-changing; which mechanisms count as equivalent
implementations; which interventions must causally move outputs; which
transformations must leave the persona invariant. Then auto-generate
adversarial/counterexample scenarios against the specification, in the spirit
of hardware verification — except the object under specification is a learned
computational/persona structure.

## The interactive workbench thread (runs through every stage)

The world is authored, so both the corpus and the models are *inspectable
by design*: any agent's complete developmental biography is reconstructable
(every fact, every choice, every curriculum position), and any checkpoint
is interrogatable in the world's own language. `interact.py` is the first
instrument — REPL interrogation, counterfactual re-rendering of a single
scenario, C1/C2 side-by-side, λ-probe readouts beside behavior. Planned
maturation (J-Lens-inspired): its `export` output (session grids of
scenario × model × checkpoint responses + probe reads) feeds a browser
explorer where a reader can grapple with the model as it develops between
checkpoints — scrub the training slider, watch the route-weight and probe
geometry move, ask the same question of every developmental stage. The
explorer runs on precomputed real data (no backend), so it can ship as a
static page beside the paper. As Stage 2+ worlds add trait vectors, the
same instrument grows trait-by-trait probes and per-trait counterfactuals.

## Sequencing and dependencies

Stage 2 needs only the Stage-1 generator extended (new templates + trait
sampler + battery eval sets) and is worth building as soon as Phase A/B
results land. Stage 3–4 reuse Stage-2 infrastructure. Stage 5 rides on
wherever behavioral divergence is localized in time. Stage 6 needs Stages 2
and 5 (a mechanism spec presupposes mechanism measurement) plus the formal
layer; a minimal Stage-6 prototype on the *scalar* world (M* = "utility
route wins") is feasible earlier and would be the first demonstration that
interpretability-in-the-loop curriculum control works at all.

## The perturbation axis (added 2026-08-15)

Orthogonal to the six stages: every intervention on an organism sits on a
six-rung **perturbation ladder** — environmental → contextual/persona →
activation → optimizer-state → weight → developmental — ordered by depth
and persistence, with a common diagnostic vector and operational divergence
categories (expression override / representation shift / mechanism
substitution / persistent rewrite / developmental redirection). Phase A is
a rung-6 intervention; the eval suite is rung 1; the preregistered
contextual-dissociation protocol is rung 2; B1's crossed transplant is
rung 4. Full spec: [docs/perturbation_ladder.md](docs/perturbation_ladder.md).
The Stage-6 controller inherits its failure-mode vocabulary from this
ladder: perturb → classify divergence → corrective curriculum → re-perturb.
