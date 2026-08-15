# Preregistration — Path-Dependent Preferences

**Status: DRAFT — freeze and commit before launching the full 15-run batch. After the batch launches, this file is append-only (corrections logged, never silently edited).**

Date frozen: _______ (fill at freeze)
Frozen by: Patrick Walmsley

## Primary hypothesis

When identical training evidence admits both a utility mechanism (Route A) and a surface-cue shortcut (Route B), the developmental ordering of experience affects which mechanism the trained model uses.

## Primary contrast and endpoint

- **Contrast:** C1 (structure-first) vs. C2 (choices-first).
- **Sole primary endpoint:** conflict-set accuracy (agreement with the utility answer) at the **final checkpoint**.
- **Headline statistic:** paired per-seed differences Δᵢ = Acc_conflict,C1(i) − Acc_conflict,C2(i), i = 1…5, reported individually. Supporting: Wilcoxon signed-rank on the pairs, effect size.
- **Support** = all (or 4/5) Δᵢ same sign with mean |Δ| ≥ 10 percentage points. **Null** = mixed signs or mean |Δ| < 10 pp. Anything between is reported as inconclusive, not spun.

## Balance-gate criteria (fixed BEFORE training any cue variant)

- HARD gate 1 — shortcut learnable: P-only pilot >80% cue-following on the cue-only (exact utility-tie) set.
- HARD gate 2 — utility learnable: W-heavy-then-P pilot >80% on no-cue utility set.
- Calibration target 3 — no runaway dominance: interleaved pilot's conflict behavior <90% aligned with either single route. **Pre-authorized overrides (the only permitted ones, written before any gate run):**
  - Override A: target 3 fails at a level, BUT the mini-C1/C2 pilot at that level shows ≥10 pp conflict-set separation in the expected direction → proceed at that level, reporting the dominance figure.
  - Override B: every level fails target 3 with the SAME route dominant → proceed at the level with weakest dominance, reporting dominance as a headline constraint on the design.
  - No other overrides. A failed hard gate (1 or 2) is never overridable.
- Diagnostic 4 — λ-probe selectivity >15 pp over shuffle control in ≥1 pilot; contextual-dissociation analysis is contingent on λ decodability.
- Optional gate 5 — an instruction-following pilot passes held-out persona instructions >70% → unlocks the conditional prompted-persona module (two extra runs); otherwise that module is not run.
- Selection rule: lowest level in L0 → L1 → L2 passing gates 1–2 and target 3. If none passes, no launch; the calibration is the result.
- All levels' gate results are preserved and reported as calibration data.
- Pilot sizes: P-only = 800 P; W-heavy = 1200 W + 400 P in two blocks; interleaved = 800 W + 800 P shuffled. Pilots use the main-run architecture at ~20% token budget.

## Evaluation and scoring (frozen)

- Primary scoring: forced-choice log-probability, logp("1") vs logp("2") at the answer position. Free generation only for report sanity panels.
- Eval sets: ID, conflict, no-cue (randomized neutral-verb assignment), cue-only (exact utility ties), surface-generalization (held-out nouns; renamed from "paraphrase"), W-heldout-names. Probe-test uses held-out template T2.

## Contextual-dissociation protocol (replaces prompted persona as primary)

- k=4 in-context demo lines per query (same agent, neutral verbs, disjoint demo pool), conditions: congruent / incongruent / none, on 200-item no-cue and 200-item conflict subsets.
- override_rate = anti-utility choice rate under incongruent demos − no-demo baseline.
- probe_persistence = λ-probe selectivity with demos ÷ selectivity without.
- Feasibility gate: incongruent demos must shift behavior ≥15 pp; otherwise reported as a behavioral null, no further analysis time spent.
- Prompted-persona variant runs only if optional gate 5 passes.

## Design constants (frozen at launch)

- Conditions: C1 structure-first, C2 choices-first, C3 interleaved; identical examples, counts, per-seed initialization, optimizer, steps.
- Controls: flat LR after warmup; identical final-10% tail segment across conditions.
- **Epoch rule: single-pass training on unique examples sized to the full token budget** — W→P happens once; "developmental history" means one history. (Fallback only if compute forces it: one curriculum sequence repeated identically per epoch, which redefines the intervention as (W→P)ⁿ and must be recorded here.)
- Seeds: 5 per condition, paired across conditions; hard floor 3.
- Model: decoder-only, 6 layers, d_model 384, 6 heads, MLP 4×, **block 320** (fits k=4 demos + query), dropout 0.0 (~11M params); word-level tokenizer over the controlled vocabulary.
- Per-seed agent→λ assignment (sex counterbalanced each seed); assignment recorded in each data manifest.
- Phase boundaries aligned to training-block boundaries; segment→block ranges in run manifests.
- Corpus: n_w = n_p = 80,000 unique lines per run (~8M tokens, single pass) unless the gate calibrates otherwise; final numbers recorded here at freeze.
- Secondary analyses additionally include: Δlogp (continuous log-odds) everywhere; conflict accuracy stratified by exact |ΔU| (no floor on the primary set); per-checkpoint mechanism-competition regression Δlogp = βU·ΔU + βC·cue + ε with βU(t), βC(t) trajectories by condition.
- Mini-C1/C2 pilot (2 paired seeds, gate scale) precedes the batch; interpreted asymmetrically — positive effect builds confidence, null does not abort.
- Optimizer: AdamW, lr 3e-4 constant after 200-step warmup, weight decay 0.1, grad clip 1.0, batch 64 sequences.
- Token budget: ~20M per run (~1250 steps); checkpoints at init + every 5%; probes scored at {20, 40, 60, 80, 100}%.
- Cue complexity level (from balance gate): L__ — definition: ______ (fill at freeze).
- Cue framing: the cue is a socially meaningful verb class; trained from scratch, its semantics are defined entirely by its statistical role in the corpus; verb–payoff decorrelation is enforced by construction and audited by invariant test.

## Exclusion / failure rules (decided now, before data)

- A run is excluded only for infrastructure failure (crash, NaN loss, corrupted checkpoint) — never for its results. Excluded runs are reported.
- If >1 seed-pair is lost in the primary contrast, rerun the lost pairs before analysis rather than proceeding at n<4.
- No checkpoint selection: the final checkpoint is the endpoint, fixed here.

## Secondary analyses (exploratory, labeled as such in the report)

1. W-competence at final checkpoint, Acc_W(C1) vs. Acc_W(C2) — qualifies the primary result as mechanism-selection (equal W) vs. acquisition (unequal W).
2. No-cue-set and paraphrase-set accuracy by condition.
3. Probe trajectories (utility, λ, cue) with control-task selectivity, at TWO preregistered positions — the first agent-name token ("is preference encoded at identity introduction?") and the final decision token ("or only assembled at decision time?"); AULC comparisons. No other probe positions or pooling schemes without labeling them post hoc.
4. Persona-dissociation: expressed choice vs. probe-recovered λ under conflicting personas.
5. C3 (interleaved) positioning relative to C1/C2.
6. If run: causal steering along the λ direction; plasticity under counter-training.

## What we will not claim

- No "critical period" language without the timing-sweep controls (equal exposure counts and equal post-introduction steps).
- No "the model knows/believes/hides" phrasing; probe results are linear decodability with selectivity.
- Novelty phrased as "to our knowledge," never "first ever / nobody has."
