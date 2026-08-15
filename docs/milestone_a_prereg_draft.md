# Milestone A preregistration — DRAFT (not frozen; joint freeze required
# before any GPU spend)

## Question (neutral by design)

Does curriculum composition affect the probability, timing, or
persistence of transitions between competing behavioral strategies
after initial acquisition?

NOT preregistered as "structure-first causes reversals" — that would be
post-hoc overfitting to one organism (C1_L1_s3). A directional
prediction may be separately preregistered iff the graph derives one
before the runs.

## Operational definitions (to freeze)

Route state at checkpoint t: from held-out conflict utility-agreement
u(t): UTILITY-committed if u ≥ θ_U for ≥ k adjacent checkpoints;
CUE-committed if u ≤ 1−θ_U similarly; else UNCOMMITTED.
A REVERSAL requires: (1) prior commitment to one route, (2) subsequent
commitment to the other, (3) ID competence ≥ θ_ID throughout (ordinary
forgetting must not be mislabeled as switching), (4) transient
excursions shorter than k checkpoints do not break or create
commitment. Proposed exploratory values θ_U = 0.9, k = 2, θ_ID = 0.95
— DECLARED EXPLORATORY because they were chosen with seed 3 visible;
they will be applied unchanged to entirely new seeds, and the primary
analysis will additionally report sensitivity across a small
pre-declared grid (θ_U ∈ {0.85, 0.9}, k ∈ {2, 3}).

## Outcome measures (family, one primary)

Preserve full 21-checkpoint trajectories. Family: (a) transition count;
(b) time-to-first stable commitment; (c) probability of leaving a
committed state; (d) unstable-period duration; (e) final-vs-peak route
difference. PRIMARY: (c), probability of leaving a committed state,
per organism. The binary "reversal occurred" is reported descriptively,
not as the primary statistic.

## Competing explanations the design must separate

1. curriculum-specific instability effect;
2. ordinary seed-dependent stochasticity;
3. recency/interference from the phase immediately preceding the tail;
4. shared-tail composition causing reconsolidation/overwrite;
5. competence/optimization instability unrelated to route identity
   (ID-competence gate + no-cue tracking address this).

## Design sketch (to be compiled by the graph, then frozen)

Manipulate LATE-PHASE composition under matched early history (paired
inits, same multiset where the arm permits): e.g., arms varying the
final-30% mixture (baseline tail / P-heavier tail / W-reinserted tail /
interleaved tail), n seeds per arm set by a sequential plan with a
pre-declared stopping rule; exact paired permutation tests on the
primary; FDR handling for the secondary family.

## Closed-loop acceptance criterion (the point of Milestone A)

Using ONLY Phase A traces, derive a candidate developmental
relationship; preregister a curriculum manipulation and a predicted
held-out difference in stability dynamics; train new organisms; the
graph succeeds iff its preregistered prediction outperforms the
baseline-policy prediction on the primary measure. Success earns the
edge a promotion; failure weakens or removes it — either outcome is the
loop working.
