# Act I experimental program: from traces to a tested formalization

*Adopted 2026-08-15 (ChatGPT handoff via Patrick). Governs the next arc,
after the demonstration freeze. The central question is no longer "does
curriculum order change the final learned strategy?" but:*

> **What changed, when did it change, where is that difference
> represented, is it causally used, and does moving the implicated state
> move the learned strategy?**

We are not doing probes, tracing, interventions and transplantation
because they are interesting techniques. **We are building and validating
an evidence-to-formalization compiler. The little social world is its
unit test.**

## The escalation ladder (extends docs/trace_ledger.md)

**Escalation law: use the cheapest instrument capable of falsifying the
current hypothesis.** Discovering *where to look* and *earning a
mechanistic claim* are different activities and must never be conflated.

- **L0 — Behavior: locate the phenomenon.** Every organism × checkpoint ×
  the cheap diagnostic sets, with uncertainty across seeds. Output:
  candidate developmental windows (when do curricula first become
  behaviorally distinguishable; do transitions reproduce; does
  divergence persist, reverse, or emerge during the common tail). Do NOT
  interpret internals yet. The seed-0 curves show why endpoint
  comparison is lossy — behavior rises, dips, and changes during the
  shared tail; the other seeds decide what is real.
- **L1 — Representation: what became available.** Cheap probes across
  the 21 checkpoints for variables we KNOW exist in the authored world
  (λ, utility quantities, cue/wording, scene, Δself/Δother). The product
  is a representation × layer × developmental-time tensor: where does λ
  first become decodable; does curriculum change the when/where/how
  strongly; do representation changes precede or follow behavioral
  transitions; do curricula converge internally during the tail even
  when behavior does not. Decodable ≠ used — a probe upgrades to
  REPRESENTED, never to mechanism.
- **L2 — Trace: candidate computational routes.** Use established
  tracing/decomposition machinery (do not invent a stack). Move from "λ
  decodable around L3" toward candidate paths (agent → λ-rep →
  utility-computation → choice, versus scene+wording → cue-rep →
  choice). **The authored graph supplies hypotheses and evaluation
  ground truth; it must never be forced onto the model.** The trace
  earns whatever graph it produces — essential discipline for Act II,
  where no authored graph exists.
- **L3 — Intervention: does it matter?** Only on components/windows
  nominated by L1/L2, cheapest adequate intervention first (ablation →
  steering → patching → targeted counterfactuals). The standard is
  **predicted intervention**, not generic degradation: state the
  direction implied by the candidate formalization, then test it.
  "Destroying a component makes the network worse" is weak; "steering
  the candidate λ-representation up shifts choice toward own-outcome
  maximization, as predicted" is what hardens a dashed edge to solid.
- **L4 — Developmental carrier: what carries history?** The crossed
  developmental transplant: exchange the implicated state between
  differently-raised organisms before/during the common tail and ask
  whether developmental fate transfers. What "state" means (θ, optimizer
  moments, activation state, a parameter subspace, an adapter-like
  delta) is decided by what L2/L3 implicate — not in advance because the
  metaphor is attractive. Mandatory controls: random-component
  transplant, magnitude-matched perturbation, same-curriculum
  transplant, unrelated-layer transplant.
- **L5 — Candidate mechanism.** Only after behavior + representation +
  trace + intervention + developmental evidence agree, derive the
  mechanism graph — as automatically as practical, consuming the trace
  ledger. The formalizer's job: **find the smallest candidate structure
  consistent with the evidence actually earned.** It must be
  structurally unable to convert correlations into causal arrows.
- **L6 — Falsification / prediction.** The candidate mechanism must
  predict something not used to derive it (the internal analogue of the
  withheld field notes and the chapter-4 disagreement): generate or
  select a new intervention where competing mechanism hypotheses predict
  different outcomes; run it; update. The loop —
  OBSERVE → LOCALIZE → PROBE → TRACE → FORMALIZE CANDIDATES → DERIVE
  DISCRIMINATING INTERVENTION → INTERVENE → UPDATE EVIDENCE ↺ —
  matters more than any particular method.

## Hierarchical replication

Seed 0 nominates hypotheses. The full 15-organism batch establishes
which phenomena deserve investigation. Expensive mechanistic work runs
on a deliberately selected subset first, then targeted replication on
held-out organisms. Ledger statuses keep exploratory work from quietly
becoming confirmatory: **exploratory → candidate → causally supported →
replicated.**

## What success looks like for Act I

Not reverse-engineering the whole 10.9M-parameter transformer. Bounded
and defensible:

1. Experience order reproducibly changes developmental trajectories.
2. We identify when those trajectories diverge.
3. We identify internal representations associated with the competing
   strategies.
4. Targeted interventions move behavior in predicted ways.
5. Ideally, a crossed developmental manipulation transfers part of the
   path-dependent phenotype.
6. The system automatically derives a compact candidate formalization
   from those measurements.
7. That formalization predicts the outcome of a new discriminating
   experiment.
8. The prediction survives replication.

Then we have earned Act II — the same loop with one luxury removed: in
Act I we can measure whether our instruments recover a structure we
know; in Act II we can't. Don't optimize for impressive interpretability
pictures. Optimize for recovering a small formal structure from traces,
testing it, falsifying it where possible, and knowing exactly what
evidence earned every edge.

## UI corollary (implemented in the Lab)

The workflow should teach the method: behavioral trajectory → interesting
window → probe matrix (representation × layer, humanized, honest
rounding; raw values in provenance only) → developmental emergence
(when/where a representation appeared, per curriculum) → CANDIDATE SITE →
the locked causal instrument. Established/not-established stated on
every representation result. No floating-point leakage in the reading
layer. The UI is a view over the ledger, never a replacement for it.

## Visual instruments plan (2026-08-15 addendum — build order, not built)

Before formalization, intermediate visualizations that generate candidate
mechanistic edges from traces (borrowing the *patterns* of J-space/
Jacobian-lens, parameter-decomposition attribution graphs, and circuit
tracing — all treated as candidate-generators to be tested by
perturbation, never as automatic truth; our simplification: the
developmental dimension is the star):

1. **Developmental activation atlas** — layer × age grid where each cell
   is a *location in the developmental trace*: click → scenario, state,
   λ/cue selectivity, behavior at that age, neighbors, provenance.
   Side-by-side organisms: "where did their internal paths diverge?"
   (Partially exists: the emergence view is the read-only skeleton; the
   full 21-age resolution and cell inspection arrive with the batch's
   probe schedule.)
2. **Representation trajectories** — the constellation animated through
   checkpoints (birth: mixed cloud → when does λ structure appear → does
   the tail collapse or preserve it), always labeled exploratory.
   (Partially exists: per-age constellation with color-by; animation and
   age-scrubbing next.)
3. **Execution trace for one decision** — the small-model attribution
   graph: one familiar conflict case, candidate internal contributors
   between input and choice, each edge labeled attribution-only / probe
   support / intervention-pending, hardening only via patching. Requires
   L3 attribution machinery — the first Goodfire/circuit-tracing borrow.
4. **C1 vs C2 difference map** — where paired organisms differ unusually
   strongly *relative to within-condition seed variability*: "where did
   childhood leave a detectable scar?" Click a hot region → probe →
   trace → intervention. **Gated on the batch** (needs seed variability
   to normalize against); the single-pair version would overclaim.

Sequencing: 2 (cheap, artifacts exist) → 1 (needs batch probe schedule)
→ 3 (needs attribution) → 4 (needs seeds). No new training compute; all
consume stored traces; every view writes/reads typed claims, not just
pixels.
