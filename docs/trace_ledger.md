# The Trace Ledger: the research data contract

*Adopted 2026-08-15 (ChatGPT handoff via Patrick). Governing principle for
everything built from here on:*

> **Every expensive computation must either discriminate between
> hypotheses or contribute evidence to the formal graph.** If a technique
> produces no evidence record for or against a candidate formal
> relationship — "none, but it makes a cool visualization" — it does not
> belong in the critical path. We are not trying to interpret every
> neuron; we are trying to progressively compress developmental traces
> into experimentally justified formal structure.

## One accumulating artifact

Every experiment writes into the same compact record; every interactive
chapter and Lab instrument is a *view* over these objects:

```
ExperimentTrace {
  model / seed / curriculum        # which organism
  checkpoint                       # developmental age
  stimulus + intervention          # what was done (Perturbation schema,
                                   #   docs/perturbation_ladder.md)
  behavior                         # forced-choice outcomes, margins
  representations                  # probe reads (with controls)
  parameter_components             # decomposition attributions (L3+)
  causal_effects                   # steering / patching / ablation deltas
  provenance                       # run_id, commit, timestamps
}
DevelopmentalEvent   # a located transition (window, measures that moved)
CandidateVariable    # λ-like, cue-like, place-like, agent-identity, ...
CandidateEdge        # source, target, checkpoint(s), typed relation
EvidenceRecord       # what measurement, on which trace, supporting what
Intervention         # instance of the perturbation ladder
FormalGraph          # typed nodes/edges + evidence vectors (below)
```

**No single confidence score.** Each edge carries an evidence *vector*
`E(e) = (E_B, E_R, E_D, E_C, E_X)` — behavioral, representational,
developmental, causal, cross-run replication — displayed as the
measurements themselves plus a qualitative status from explicit criteria:
ASSOCIATED → REPRESENTED → DEVELOPMENTALLY ALIGNED → CAUSALLY SUPPORTED
(→ REPLICATED). Interventions promote or downgrade edges by *predicting*
an effect first and testing it; a failed prediction downgrades.

## Compute escalation (design law)

**Cheap measurements locate transitions. Expensive measurements explain
transitions.**

| Level | Operation | Run on |
|---|---|---|
| L0 | behavior/evals | every checkpoint |
| L1 | cheap probes / statistics | selected checkpoints |
| L2 | representation comparison | transition windows |
| L3 | parameter decomposition / interaction traces | few checkpoints × prompts |
| L4 | causal interventions | candidate mechanisms only |
| L5 | retraining / transplants | decisive hypotheses only |

A level unlocks the next only when cheaper evidence produced something
worth testing. This *adaptive experimental allocation* is itself a
methodological contribution — it is what makes eventual corpus-scale
analysis (the Observatory) plausible at all.

## How the next chapters map onto the ledger

- **Ch 6 — Watch development (L0):** the already-paid-for checkpoints ×
  the small diagnostic battery → developmental trajectories → *candidate
  transition regions*. Deep analysis then happens at ~6 checkpoints, not
  60.
- **Ch 7 — What appeared inside (L1):** cheap probes (λ, cue, place,
  agent identity, utility difference) over developmental time → emergence
  ordering. Edges drawn from this are labeled representational/temporal
  evidence, never causal structure.
- **Ch 8 — Follow the computation (L3):** borrow existing machinery
  (parameter-decomposition / attribution methods, e.g. Goodfire's
  component-interaction work; J-space/VPD-style analyses) rather than
  inventing our own stack — admitted only as producers of
  `candidate_edge` records with evidence attached. The research product
  is machine-readable candidates, not the visualization.
- **Ch 9 — Does it actually matter (L4):** ablation/steering/patching on
  candidate edges that survived 6–8, with directional predictions made in
  advance. Promotion/downgrade per the evidence-vector rules.
- **Ch 10 — What did childhood change (L5):** the crossed weights ×
  optimizer-state transplant matrix (apparatus already built; B1) —
  conceptually simple enough for the Expedition: *we raised two twins
  differently; now swap parts of their developmental state.*
  Distinguishes weights-carry-history / optimizer-carries-history /
  interaction / tail-erases-it.
- **Ch 11 — Formalize what survived:** the evidence graph rendered with
  per-edge vectors; the Act II reveal follows ("we knew what variables to
  look for — because we authored Matthew").

## Status

Schema is the contract as of 2026-08-15; nothing is implemented during
the Phase A batch beyond views over existing artifacts (score files,
probe suites, curricula, world specs are already ledger-shaped). First
implementation target after the batch: L0 trajectories over the fifteen
organisms' checkpoints, written as ExperimentTrace records.
