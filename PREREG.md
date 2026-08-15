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
- Pilot sizes (AMENDED — see Calibration log): pilots use the main-run architecture at **main-run per-family exposure** (n_w = n_p = 80,000 lines, single pass), because the gate's question is whether each route is learnable *at the exposure the main experiment provides*.

## Calibration log (append-only)

**Calibration v1 — 2026-08-15, FAILED both hard gates (preserved in `calibration/`).**
Run at the originally specified ~20% token budget (gate_n = 16,000/family) on all three cue levels. Results: gate 1 (cue-follow) 46–53% and gate 2 (no-cue utility) 49–54% at every level — chance; target 3 trivially passed at chance; λ-probe selectivity 0.20–0.53 across levels. Per the frozen rule, **no launch** (hard gates are never overridable).
*Diagnosis:* run manifests show pilots received only **39–61 optimizer steps** (final training loss ~1.3, down from 5.1 — template structure learned, task answers not). The 20%-budget rule under-specified optimization by an order of magnitude; the result is uninformative about route learnability at the exposure the main experiment provides, and uninformative about the order hypothesis.
*Amendment (v2):* pilot corpus raised to main-run per-family exposure (80,000 lines/family, single pass; P-only ≈ 175 steps, W-heavy ≈ 350). Conflict construction, gate thresholds, selection rule, and all main-experiment constants are untouched. `eval_id` added to every pilot's scored sets as a learned-anything diagnostic. If v2 also fails the hard gates with converged training losses, the finding is that a route is not learnable at main-run exposure, and the next amendment must raise the *main* token budget itself (not just the pilots').

*Interpretation note (appended after review):* v1 is calibration evidence, not a mistake to erase — at the original pilot budget (39–61 optimizer updates, unconverged), neither route generalizes; we amended pilot exposure before testing the preregistered ordering hypothesis. The gate demonstrated its value: without it, 15 models would have trained into near-chance conflict behavior, and optimization failure could have been misread as developmental path dependence. This goes in the methodology section regardless of v2's outcome.

**Calibration v3 — 2026-08-15, sizing from measured acquisition curves (both diagnostics complete, recorded BEFORE gate v3 runs).**
Route B (8-epoch P-only): held-out cue-following flat at chance until ~55% of 1,430 steps, then near-vertical to 100%; train-line accuracy had risen to ~85% first — *partial-memorization phase followed by sharp generalization transition*; 80% crossing ≈ 850–1,150 steps; final |Δlogp| ≈ 7.4.
Route A, non-cued (8-epoch, Lightning): learnable without cue competition — gradual, noisy climb to 0.84 no-cue at 2,850 steps; train self-check only 0.81 at |Δlogp| ≈ 1.8.
Route A, cued (24-epoch, GCP): crystallizes WITH the cue present — no-cue 0.54→0.79→0.84 across 6,839 steps; 80% crossing ≈ 2,400 steps; train saturates 100% by ~2,700 steps while held-out plateaus ~0.80–0.86 (persistent generalization gap). Verdict per the pre-fixed table: **acquisition-timescale asymmetry, not hard interference.** The preregistered gate instruments are unchanged — the cued gate-2 pilot passes honestly at adequate exposure. Corpus resized as recorded in Design constants; no thresholds, selection rules, or eval constructions touched.

*Sizing rule made explicit (before v3 results):* the single-pass endpoint is placed **well inside the stable acquisition region**, not at the first threshold graze — main-run/W-heavy exposure ≈ 4,300 steps ≈ 63% of the diagnostic trajectory (stable plateau holds from ~50% onward); P-only ≈ 2,700 steps ≈ 2.3–3.2× Route B's crossing. This de-sensitizes the gate to checkpoint noise around the 0.78–0.85 wobble.

*Headline calibration fact (preserved for interpretation, recorded before the main batch):* the routes have **qualitatively different isolated learning dynamics and different generalization ceilings** — Route A: train and held-out rise together from ~20–25% of training, gradual acquisition, asymptote ≈ 0.85; Route B: train rises first (partial memorization to ~85%), long flat held-out phase, abrupt generalization snap, asymptote ≈ 1.00. Consequences fixed in advance: (a) "shortcut" and "easy-to-acquire-first" are not synonyms — B's eventual rule is simpler but its acquisition is *later*; (b) "both >80%" does NOT mean the mechanisms are equally learnable — B has the higher isolated ceiling; (c) therefore, if all conditions end cue-dominated, B's intrinsic generalization advantage is a plausible explanation and must be weighed against a path-dependence null; conversely, if structure-first history preserves Route A *despite* B's isolated advantage, the order effect is stronger than a naive reading would suggest.

**Gate v3 OUTCOME — 2026-08-15 07:35 UTC, commit 2abed0d, provenance-stamped (archived: `calibration/gate_v3_results.json`).**

| | Gate 1 cue-follow (>0.80, HARD) | Gate 2 no-cue (>0.80, HARD) | Target 3 dominance (<0.90) | λ-probe selectivity |
|---|---|---|---|---|
| L0 | 1.000 ✅ | 0.578 ❌ | 0.9925 ❌ (cue-dominant) | 0.45 |
| L1 | 0.825 ✅ | 0.9425 ✅ | 0.980 ❌ (utility-dominant) | 0.70 |
| L2 | 0.5225 ❌ | 0.9975 ✅ | 0.975 ❌ (utility-dominant: 0.975/0.025) | 0.53 |

Code's mechanical verdict: **NO LEVEL PASSED** — independently confirmed by hand against the frozen rule. L0 fails hard gate 2 (out, never overridable). L2 fails hard gate 1 — a calibration finding in its own right: the two-feature conjunction cue is *not learnable from choices alone* at this exposure (0.5225 ≈ chance), so L2 offers no two-route race. **L1 is the only level passing both hard gates**, failing only calibration target 3, in the utility direction.

**Override adjudication (frozen text applied):** Override B requires all levels to fail target 3 with the SAME dominant route — L0 is cue-dominant while L1/L2 are utility-dominant → **Override B unavailable.** **Override A is the live path, at L1:** proceed only if the mini-C1/C2 pilot at L1 shows ≥10 pp conflict-set separation in the expected direction.

**Override-A mini interpretation rule (fixed NOW, before the minis run):** 2 paired seeds (0, 1), C1 vs. C2 at L1, full calibrated scale, single pass, identical to main-run configuration. Expected direction: Δ = Acc_conflict-utility(C1) − Acc_conflict-utility(C2) **> 0** (structure-first more utility-governed). Support for Override A = both seeds' Δ same sign in the expected direction AND mean Δ ≥ 10 pp. Anything else → Override A fails → no launch; the calibration story (including the striking L0-vs-L1 dominance flip under identical interleaved exposure) is the sprint result.

**Override-A mini OUTCOME — 2026-08-15 (archived: `calibration/minis_L1_results.txt`).**
Seed 0: C1 = 0.710, C2 = 0.965 (Δ = −0.255). Seed 1: C1 = 0.435, C2 = 0.955 (Δ = −0.520). Mean Δ = −0.3875. **OVERRIDE_A: NOT SUPPORTED** per the frozen directional rule — correctly applied, no launch authorized by this gate.
*Scientific reading, recorded with the verdict:* the minis show a **large, seed-consistent order effect in the direction OPPOSITE to the frozen expectation** — choices-first (C2) is strongly utility-governed; structure-first (C1) is substantially more cue-reliant and higher-variance. The directional expectation derived from the first-mover/gradient-starvation toy mapping is **rejected at calibration**: the toy assumed the choice readout exists during the early phase to capture margins, but choices exist only in P. Candidate mechanism consistent with the data: **interference/recency** — the middle phase degrades the first phase's route, the final phase's route arrives fresh, and the 430-step identical tail (< Adam's β₂ horizon, as flagged in THEORY.md §6) does not equalize. Note: the preregistered PRIMARY support criterion (§Primary) is and was **direction-agnostic** ("all/4-of-5 Δᵢ same sign, mean |Δ| ≥ 10 pp"); only this override gate was directional.

**AMENDMENT — APPROVED by Patrick, 2026-08-15, before any main-batch outcome exists.**

*Original admission criterion, quoted verbatim from this document:* "Override A: target 3 fails at a level, BUT the mini-C1/C2 pilot at that level shows ≥10 pp conflict-set separation **in the expected direction** → proceed at that level" and "Support for Override A = both seeds' Δ same sign **in the expected direction (C1 > C2)** AND mean Δ ≥ 10 pp."

**The original admission criterion FAILED.** It is not described as having "basically passed."

*Amendment:* before any main-batch outcomes were generated, we elected to proceed because both paired calibration seeds exhibited substantial effects in the opposite direction (−25.5 pp, −52.0 pp). The original directional prediction is recorded as **falsified**. The main-batch endpoint, analysis, sample size, conditions, seeds, and decision criteria are **unchanged** (the primary support rule was always direction-agnostic: same-sign Δᵢ, mean |Δ| ≥ 10 pp).

*Constraints attached to the approval:*
1. **The minis are calibration evidence only.** Their two seeds are never folded into the five-seed confirmatory analysis.
2. **Mechanism is unresolved and stays that way in the record.** Interference/recency is one *hypothesis generated by the surprising result*, alongside differential acquisition rates, optimizer-state effects, gradient starvation, phase-specific representation change, and interactions. The trajectories and Phase-B interventions discriminate; no narrative may pre-commit.
3. **The falsification stays prominent.** The eventual narrative distinguishes: (a) preregistered broad question — can order alone select among behaviorally equivalent solutions?; (b) directional theoretical prediction — structure-first should preferentially preserve utility; (c) mini-pilot observation — strong order separation, opposite direction; (d) status — directional prediction falsified, mechanism unresolved. No retrofitting into "we predicted path dependence all along."
- **"Same exposure" means same evidence for the route under test, not same total optimizer updates.** Gate 1's operational question: can Route B be learned from the same 80k P lines the main run provides? (W lines carry no cue evidence.) Gate 2's: can Route A be learned given the same W machinery + P evidence the main run provides? The interleaved pilot is the joint, main-run-like check. Both line counts AND realized optimizer steps/token counts are reported for v1 and v2 from run manifests.
- **W-heavy composition, corrected record:** the original prereg text ("1200 W + 400 P") never matched the implemented pilot builder, which has always used the full generated pools — v1 actually ran 16k W + 16k P; v2 runs 80k W then 80k P. This makes the W-heavy pilot deliberately the *most Route-A-favorable arrangement* (C1-like, minus the tail mix) — correct for a learnability gate: if the most favorable arrangement cannot learn utility, the route is dead. Pilot data is disjoint from main-run data and pilot results only gate; they never enter the analysis.
- **Selection stays mechanical:** hard gates >80%, then the existing target-3 rule, lowest passing level. Training curves are inspected diagnostically only; they are not a tuning surface and do not influence level selection.

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
- Corpus (CALIBRATED at v3, superseding 80,000): **n_w = n_p = 1,200,000 unique lines per run** (~90M tokens, ~4,300 optimizer steps, single pass) — sized from the measured acquisition curves so both routes' 80% crossings clear with margin (Route B ≈ 850–1,150 steps; Route A ≈ 2,400 steps; P-only pilot ≈ 2,700 steps; W-heavy pilot/main runs ≈ 4,300). Partner-name pool widened 4→8 to keep task spaces comfortably larger than the corpus.
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
