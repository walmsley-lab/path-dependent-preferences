# Preregistration — Post-Acquisition Strategy Stability (Phase B)

**Status: FROZEN pending joint sign-off. No training runs may begin
until the sign-off line at the end of this document is completed.**
Written 2026-08-16, before any Phase B training. Phase A artifacts
(commit 8de3c010) are the only data that informed this document.

## 1. Motivation and what Phase A does and does not establish

Phase A tested whether curriculum order determines final strategy
preference; its preregistered endpoint criterion was not met. Applying
the operational definitions in §3 to the Phase A checkpoint record
retrospectively identifies post-commitment declines in 3 of 15 runs
(C1: 2/5, C2: 0/5, C3: 1/5), one of which proceeds to full alignment
with the competing rule.

Phase A provides **essentially no evidence about differential rates
between conditions**: the C1-versus-C2 contrast (2/5 vs 0/5) has a
Fisher exact p of 0.44, and the pooled contrast used in earlier drafts
(1/5 vs 0/10) gives p = 0.33. These numbers establish a base rate worth
planning around, not an effect. Phase B is therefore the first genuine
test of the differential-rate hypothesis, not a confirmation of it.

## 2. Hypotheses

- **H0 (null):** transition probability does not differ between
  structure-first (C1) and choices-first (C2) curricula.
- **H1:** transition probability is higher under C1 than C2.
- **H2:** transition probability is higher under C2 than C1.

The test is two-sided. H1 is the direction suggested by Phase A, and is
named to make the direction-agnostic analysis explicit rather than to
privilege it.

## 3. Operational definitions (frozen)

Let u(t) be conflict-set agreement with the utility rule at checkpoint t
and a(t) in-distribution accuracy at t.

- **Committed** at t: u ≥ 0.90 for three consecutive checkpoints
  beginning at t.
- **Transition** at t' > t: after commitment, u < 0.80 for three
  consecutive checkpoints beginning at t', **with a ≥ 0.95 throughout
  those checkpoints**. The competence gate ensures degradation of
  general task ability is not classified as strategy change.
- **Full crossing:** a transition whose final-checkpoint u < 0.50
  (alignment with the competing rule).
- Transient excursions shorter than three checkpoints neither create
  nor break commitment.

**Threshold provenance.** These thresholds were selected with Phase A
trajectories visible and are therefore exploratory in origin. They are
frozen here before new data collection. The primary analysis reports
sensitivity across the pre-declared grid: commitment threshold ∈ {0.85,
0.90}, persistence k ∈ {2, 3}, competence gate ∈ {0.90, 0.95}. On Phase
A data the classification is identical at all four commitment/k
combinations (C1 2/5, C2 0/5, C3 1/5), which is evidence of stability
of the definition but not of the phenomenon.

## 4. Design

Two arms, C1 and C2, identical to Phase A in architecture (6 layers,
d=384, 6 heads, 10.9M parameters), corpus construction, cue level (L1),
single-pass training, and checkpoint schedule (21 per run). C3 is not
run in Phase B; the primary contrast is the pure order reversal.

**n = 25 runs per arm (50 runs total).** Seeds 0–24; within each seed
index, C1 and C2 begin from identical initial parameters (weight-hash
verified), preserving the paired-initialization design. Phase A seeds
are not reused.

**Sample size justification.** With Fisher's exact test at one-sided
α = 0.05 and the Phase A base rate (p_C1 = 0.40, p_C2 = 0.05), n = 25
per arm gives 82% power (simulation, 6,000 trials). Under conservative
assumptions (p_C1 = 0.30, p_C2 = 0.05) power falls to 57%, and under
pessimistic assumptions (0.25 vs 0.10) to 19%. We accept this: n = 25
is the largest arm size that fits the available budget (50 runs ≈ 33
GPU-hours ≈ $28 on one L4), and we preregister that a null result at
this n will be reported as **inconclusive for small effects** rather
than as evidence of no difference.

**Stopping rule.** One interim analysis after 12 runs per arm, at
α = 0.005; final analysis at 25 per arm, at α = 0.048 (approximately
preserving overall α = 0.05 under a two-look O'Brien-Fleming-style
spending function). The interim look may stop for efficacy only, never
for futility, and never to extend n.

## 5. Endpoints

**Primary:** transition rate per arm (binary per run, §3), compared by
Fisher's exact test.

**Secondary family** (reported with Benjamini-Hochberg FDR control at
q = 0.10, and never used to declare the primary result):

1. D_max = max over checkpoints of (a(t) − u(t)), the competence-gated
   dissociation;
2. time from first commitment to transition, among transitioning runs;
3. probability of leaving a committed state within the final 25% of
   training;
4. maximum drawdown from peak u, reported alongside D_max because the
   two dissociate — Phase A drawdown is largest in C2, where it
   reflects competence degradation rather than strategy change;
5. final-checkpoint u (the Phase A primary), for continuity.

**Paired analyses.** Because initializations are paired by seed index,
secondary continuous measures are additionally analyzed by exact paired
permutation test over sign flips (n = 25 pairs; minimum attainable
two-sided p = 2⁻²⁴).

## 6. Competing explanations the design must separate

1. curriculum-specific instability;
2. seed-level stochasticity (addressed by n and pairing);
3. interference from the phase immediately preceding the tail;
4. shared-tail composition effects (identical across arms, so held
   constant rather than tested here);
5. optimization instability unrelated to strategy (addressed by the
   competence gate and by reporting loss curves).

Explanations 3 and 4 are **not** separable within this design; they
require the tail-composition arms deferred to Phase B-2. This
preregistration therefore tests differential rate, not mechanism.

## 7. Prospective prediction (the closed-loop criterion)

Derived from Phase A traces alone, before Phase B data exist:

> **Prediction P1.** The transition rate under C1 will exceed the rate
> under C2, with a difference of at least 15 percentage points.

P1 is recorded here so that Phase B constitutes a prospective test of a
relationship inferred from prior trajectories rather than a description
of them. If P1 is confirmed under §5, the corresponding developmental
edge is promoted from candidate to supported. If it is disconfirmed, the
edge is weakened or removed, and that outcome is reported with equal
prominence.

## 8. Analysis code and blinding

Analysis code implementing §3 and §5 is written and committed **before**
Phase B training begins, and is run unmodified on the resulting
artifacts. Any deviation is reported as a deviation. Run identifiers,
commit hash, and timestamps accompany every reported value.

## 9. Deviations register

*(Append-only. Any departure from this protocol is recorded here with
its date, reason, and effect on interpretation.)*

— none —

## Sign-off

Frozen by: ______________________  Date: ____________

No Phase B training run may begin before this line is completed.
