# Acts II and III: the Observatory and the Foundry

*Adopted 2026-08-15 (ChatGPT architectural handoff via Patrick). This is
architecture for what comes AFTER the controlled experiment — recorded now
so today's objects grow into it instead of dead-ending. Nothing here is
built during the sprint beyond a mocked transition; Phase A remains the
scientific priority and is not destabilized.*

## The three environments

| Act | Environment | Ground truth | Purpose |
|---|---|---|---|
| I | **The Laboratory** | authored — we wrote it | validate the instruments (Path-Dependent Preferences is this) |
| II | **The Observatory** | unknown — real/naturalistic corpora | infer developmental-structure hypotheses and experimentally test them |
| III | **The Foundry** | n/a — engineering | express sufficiently supported computations as executable formal abstractions; eventually lower onto alternative hardware |

The Act I → Act II transition line (frozen): **"Until now, we knew the
world because we built it. Real corpora come without a map."**

## The most important architectural rule: there is not one graph

Three fundamentally different objects, which must never quietly collapse
into one supposedly "causal" graph:

- **G_C — Corpus Graph.** What structure does the training material
  *appear* to contain? Nodes: concepts, entities, skills, propositions,
  procedures, latent candidate variables. Edges: co-occurs / predicts /
  entails / composes / appears-prerequisite / introduced-before /
  semantically-depends / instance-of. These are hypotheses extracted from
  data, never claims about neural computation. Every inferred edge carries
  provenance and epistemic status.
- **G_D — Development Graph.** The Corpus Graph proposes; the
  **Developmental Mapper** tests through training interventions. For a
  candidate A→B: train `A then B` / `B then A` / interleaved / `B without
  A` / `A→B→A` under controls (same init, same examples where possible,
  same token budget, same optimizer, multiple seeds, checkpoints
  preserved), and measure whether exposure to A changes acquisition,
  sample efficiency, generalization, retention, forgetting, robustness,
  strategy selection, or representational emergence of B. An edge here
  means: *experience with A changes the subsequent acquisition/retention/
  generalization/mechanism-selection associated with B.* **The C1/C2
  experiment is the first working example of the Developmental Mapper** —
  that conceptual connection is load-bearing.
- **G_M — Mechanism Graph.** What computation actually formed inside the
  learner — from behavioral diagnostics, checkpoint trajectories, probes,
  activation geometry, steering/patching/ablation, eventually
  circuit-level analysis. The existing discipline binds: behavior ≠
  representation ≠ causal use ≠ developmental explanation; a successful
  probe must not create a causal edge; behavioral agreement with the
  utility route does not establish that the network implements the
  authored utility equation.

In the Laboratory there is additionally **G_authored** — the generating
graph, a *privileged ground-truth object that exists only because the
world is synthetic*. It is the calibration target: hide it, and ask
whether G_C/G_D/G_M pipelines recover it (ROADMAP "inverse problem").

**The scientific payoff is comparing the graphs.** Toggle CORPUS /
DEVELOPMENT / MECHANISM / OVERLAY; disagreement is itself a result. The
interface surfaces structural anomalies (corpus says A→B→C; development
says removing B changes nothing; mechanism implicates latent Z) and
offers "Design discriminating experiment →" rather than reconciling
automatically.

## Evidence display rules

**No invented confidence scores.** Never `causal evidence: 0.62` unless a
statistically principled method makes the number meaningful. Expose the
measurements themselves (conflict effect in pp, C1/C2 contrast, probe R²
with selectivity control, steering Δlogit, patching effect, seed
replication count), and assign a **qualitative epistemic status from
explicit criteria**: OBSERVED / PREDICTIVE / ORDER-SENSITIVE /
REPRESENTED / CAUSALLY SUPPORTED / REPLICATED. Every status answers "why
does this edge have this status?" by opening its evidence.

## Graph data-model requirements (bind on anything built from now on)

Typed nodes and typed edges; per-edge provenance (runs, commits,
timestamps); evidence class (which of the three graphs it belongs to and
which measurement kinds support it); links to the experiments that
produced it; and room for **temporal/context annotations** — because
developmental structure may not be a DAG. Facilitation, interference,
recency, forgetting, consolidation, revisitation, plasticity windows, and
context dependence are all live possibilities (the inverted mini already
warns us); an edge may eventually read "A facilitates later B" or "A→B→A
is superior to A→B" with timing/budget annotations. The long-term object
is closer to a *developmental program* than a static prerequisite DAG. Do
not architect that possibility away.

## The editable graph (the loop, unchanged but placed)

Unlock order per experience_script.md: the reader inherits our graph,
edits it (nodes, edges, ordering constraints, planted shortcuts,
diagnostics), and "TEST THIS HYPOTHESIS" compiles the change into paired
curricula, trains organisms, runs diagnostics, and returns evidence to
the graph. CORPUS → PROPOSE → DESIGN → GENERATE → TRAIN → OBSERVE →
PROBE → INTERVENE → COMPARE GRAPHS → REFINE → RETRAIN.

## The formalization gate (epistemically separate from mechanism discovery)

A convincing mechanism graph is not an executable formal specification:

```
candidate mechanism → causally supported abstraction → executable surrogate
  → equivalence testing → formal computational specification
  → hardware-independent IR → hardware lowering → physical implementation
```

Formal methods enter concretely at equivalence testing: for transformer M
and executable abstraction F, define equivalence over a specified domain
(e.g. ∀x ∈ D_diagnostic: choice_F(x) = choice_M(x), or bounded
approximation criteria for distributions/internal variables).
**Understanding eventually has to survive an attempt to rebuild the
computation** — a far stronger test than drawing an interpretable graph.
Clicking "Formalize" must never imply interpretability results have been
proven into a computation.

**The final dragon:** the neuromorphic compiler. Future targets: SNN,
event-driven digital, FPGA, memristive/reservoir, hybrids. And the
closing scene to preserve: **Matthew asks the question again** — the same
harness (ID, conflict, no-cue, counterfactuals) run against (1) the
original transformer, (2) the extracted executable abstraction, (3) the
neuromorphic implementation.

## Corpus scaling strategy (preserve in roadmap)

1. Synthetic known worlds (current).
2. Richer synthetic worlds (multiple latent traits, interactions,
   multiple shortcuts).
3. Semi-synthetic structured corpus (naturalistic content with
   known/annotated relationships).
4. Bounded real corpus (a textbook, course, codebase, formal domain —
   expert evaluation feasible).
5. Heterogeneous corpus (does the methodology survive ambiguity and
   scale?).
6. Pretraining-scale investigation — only if earlier stages establish the
   measurements mean anything.

Arbitrary-corpus causal formalization is not solved and we do not pretend
otherwise.

## The central research question (one sentence)

Can we experimentally discover how the structure and order of experience
shape learned computation, turn that understanding into a manipulable
developmental model, and eventually use it to deliberately cultivate and
re-express computation?

Path-Dependent Preferences establishes the first experimentally
controlled rung. If our instruments cannot distinguish mechanisms in a
world whose truth we already know, we stop and improve the instruments.
If they work, we earn the right to make the world harder — then to remove
the ground-truth graph entirely (the Observatory) — and only after
reconstruction-and-validation works do we face the final question: did we
understand the computation well enough to build it somewhere else?

## Built during the sprint (deliberately minimal)

- This document; three-graph distinction cross-referenced from
  laboratory_architecture.md, expedition_design.md, ROADMAP.md.
- The Expedition's mocked Act II portal: the transition line, a CONCEPT
  three-layer graph with a disagreement example, PENDING stamp — nothing
  functional.
- G_authored explicitly labeled as the privileged synthetic-world object
  in the interfaces.
- Everything else stays roadmap.
