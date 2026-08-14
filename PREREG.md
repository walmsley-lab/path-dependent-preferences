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

- Shortcut learnable: P-only pilot >80% on cue-isolation set.
- Utility learnable: W-heavy-then-P pilot >80% on no-cue utility set.
- No runaway dominance: interleaved pilot's conflict-set behavior not >90% aligned with either single route.
- Selection rule: lowest level in L0 → L1 → L2 passing all three criteria. If none passes, no launch; the calibration is the result.
- All levels' gate results are preserved and reported as calibration data.
- λ-decodability diagnostic (5-fold CV on probe data) recorded per pilot; persona-dissociation analysis is contingent on λ being decodable.
- Smoke budget: ~20% of main-run tokens.

## Design constants (frozen at launch)

- Conditions: C1 structure-first, C2 choices-first, C3 interleaved; identical examples, counts, per-seed initialization, optimizer, steps.
- Controls: flat LR after warmup; identical final-10% tail segment across conditions.
- Seeds: 5 per condition, paired across conditions.
- Model: ______ layers, d_model ______, ______ params (fill at freeze).
- Cue complexity level (from balance gate): L__ — definition: ______ (fill at freeze).
- Training tokens per run: ______ (fill at freeze).

## Exclusion / failure rules (decided now, before data)

- A run is excluded only for infrastructure failure (crash, NaN loss, corrupted checkpoint) — never for its results. Excluded runs are reported.
- If >1 seed-pair is lost in the primary contrast, rerun the lost pairs before analysis rather than proceeding at n<4.
- No checkpoint selection: the final checkpoint is the endpoint, fixed here.

## Secondary analyses (exploratory, labeled as such in the report)

1. W-competence at final checkpoint, Acc_W(C1) vs. Acc_W(C2) — qualifies the primary result as mechanism-selection (equal W) vs. acquisition (unequal W).
2. No-cue-set and paraphrase-set accuracy by condition.
3. Probe trajectories (utility, λ, cue) with control-task selectivity; AULC comparisons.
4. Persona-dissociation: expressed choice vs. probe-recovered λ under conflicting personas.
5. C3 (interleaved) positioning relative to C1/C2.
6. If run: causal steering along the λ direction; plasticity under counter-training.

## What we will not claim

- No "critical period" language without the timing-sweep controls (equal exposure counts and equal post-introduction steps).
- No "the model knows/believes/hides" phrasing; probe results are linear decodability with selectivity.
- Novelty phrased as "to our knowledge," never "first ever / nobody has."
