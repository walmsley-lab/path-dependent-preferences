# The Developmental Laboratory: architecture and data model

*Standing direction (Patrick, 2026-08-15): the workbench grows into an
interactive laboratory for observing model development, with the graph of
the synthetic world as the organizing object. Phase A is frozen and runs
independently; nothing here touches training methodology. This document is
the data model that lets today's experiment grow into that system without a
rebuild.*

## The narrative arc the UX serves

1. **The authored world** — a node/edge graph of agents, λ, payoffs,
   scenes, framing verbs, choices; latent vs observed marked; causal vs
   derived vs predictive-spurious edges typed; the Route-A/Route-B
   observational equivalence *visible in the graph structure*.
2. **Meet the organism** — the current guided workbench; sampling
   accumulates into sliceable behavioral portraits; developmental time
   exposed via checkpoint sliders, synchronized across C1/C2/C3.
3. **Descend** — organism → checkpoint → layer → token → representation;
   probes and geometry with evidence levels explicit.
4. **Intervene** — steering, patching, transplants; return immediately to
   the same behavioral question.
5. **Zoom back out** — G_authored beside Ĝ_learned, the evidence-backed
   hypothesis of what the model actually learned, changing as the
   checkpoint slider moves.
6. **Unlock the graph** — the reader authors a world; the graph becomes an
   executable experiment specification.
7. **Close the loop** — AUTHOR → COMPILE → ORDER → TRAIN → OBSERVE → PROBE
   → INTERVENE → INFER → RE-AUTHOR, eventually with a curriculum controller
   under Goodhart protections.

The symmetry to preserve: *at the start we know the world and not the
model; at the end we use what we learned about the model to change the
world.*

## The seven persistent objects

```
WorldSpec ──compile(seed,sizes)──▶ Corpus ──order(cond,seed)──▶ Curriculum
                                                                   │ train
                                                                   ▼
        InferredGraph ◀──infer(rules)── Measurements ◀──score/probe/intervene── Run
             │                                                     │
             └──── compare vs WorldSpec ──▶ discrepancies ──▶ re-author
```

**1. WorldSpec** — the declarative graph. Nodes are Variables
`{name, kind: latent|observed|derived, domain}`; edges are Relations
`{src, dst, type: causal|derived|predictive_spurious|constraint,
mechanism, realization}`. Constraints are first-class (this is what makes
the design an identification problem):
`equiv_on_train(RouteA, RouteB)`, `disagree_on(conflict_set)`.
*Today* `generate_world.py` is a hard-coded compiler of an implicit spec.
*Near-term:* the generator EMITS `world_spec.json` — the explicit graph it
already encodes — alongside every manifest. *Long-term:* the compiler
consumes the spec (spec-first), which is precisely what makes stage 6
possible without a rewrite.

**2. Corpus** — a deterministic compilation `Compile(spec, seed, sizes)`.
Identity = (spec_hash, seed, sizes). Already realized: data dirs with
manifests (agent assignments, generation stats, splits). Determinism is
load-bearing (seed-0/1 dataset reuse in the batch relied on it).

**3. Curriculum** — an ordering over a Corpus:
`Order(corpus, condition, seed)` with segment marks. Identity =
(corpus_hash, condition, seed). Already realized: curriculum files +
segment ranges in manifests.

**4. Run** — `Train(curriculum, arch, optimizer, exec_backend)`. Already
realized: run manifests (run_id, commit, hashes, config), checkpoint
series, boundary TrainStates (θ, m, v, RNG). The exec backend is recorded
so PERFORMANCE.md's two modes never blur scientific generations.

**5. Measurements** — append-only evidence atoms, in three explicitly
typed levels (never conflated):
- `Behavioral {run, ckpt, eval_set, metric, value, n, provenance}`
- `Representational {run, ckpt, probe: target×position×layer, acc,
  selectivity, provenance}`
- `Causal {run, ckpt, intervention {type, params, source_run?}, effect,
  provenance}`
Already realized in embryo: `score_ckpt_*.json` files ARE the behavioral +
representational store; steering output is the first causal record. The
formalization step is schema, not migration.

**6. InferredGraph (Ĝ)** — a **derived view, never stored as fact**:
`Ĝ(run, ckpt) = infer(measurements, rules)`. Every edge carries
`{claim, level: behavioral|representational|causal, sign, strength, ckpt,
condition, evidence: [measurement refs], confidence}`. λ-decodability and
λ-patching-changes-choices produce **different edge types** — the UI must
render that difference, not launder it. The inference `rules` are
themselves a versioned object, so Ĝ is auditable and recomputable; moving
the checkpoint slider recomputes Ĝ from the measurement store.

**7. Session/Notebook** — interaction provenance (already realized:
`interact.py save`, workbench sessions).

## Invariants (the actual architecture)

- **Append-only evidence; derived views recomputed.** Nothing downstream
  ever mutates upstream artifacts.
- **Every displayed value is a measurement reference** with provenance
  (run_id, commit, ckpt) — the UI is a pure function of the store.
- **Evidence levels are part of the type system**, not captions.
  behavioral → representational → causal is preserved in schemas, edge
  types, and rendering.
- **Identity by content hash + generative parameters** at every stage, so
  reuse (and cache) is safe and provenance is checkable.
- **The spec is executable, eventually.** Every near-term artifact is
  designed to survive the flip from code-first to spec-first compilation.

## Near-term build order (while Phase A runs; none of it blocks science)

1. `world_spec.json` emitter in the generator (explicit graph of the
   current world; the seed of stages 1, 5, 6).
2. "About this organism" drawer + run-manifest view (queued edits).
3. Aggregating behavioral portraits: an `/api/aggregate` over the existing
   score store, sliceable by agent/λ/scene/margin/condition/ckpt.
4. **Developmental timeline** (the biggest missing piece): checkpoint
   slider driving both a live same-scenario query and metric trajectories
   (route weight, ID, no-cue, cue-only, probes, βU/βC) from the store —
   synchronized C1/C2/C3 sliders.
5. Evidence-typed graph schema (this document) rendered read-only:
   G_authored first; Ĝ once inference rules v1 exist.
6. NOT yet: graph editor, corpus compiler UI, controller — abstractions
   before chrome.

The reproduction ladder threads through it: smallest verified organism →
inspect → larger experiments → eventually author your own world. Rung 6 of
the ladder eventually IS stage 6 of the arc.

## Performance (separate concern, same discipline)

See PERFORMANCE.md: semantics-preserving throughput now (profiling,
caching, cross-run parallelism, BF16/compile behind the numerical-
equivalence harness); dynamics-changing knobs are Phase-B experiments;
update-grouping (batch/accumulation) is intervention space. Profiling runs
post-batch or on the idle Lightning T4 — never against the live frozen
batch. Target: **scientifically interpretable experiments per GPU-hour.**
