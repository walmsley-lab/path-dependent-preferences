# Path-Dependent Preferences

**Does learning order select the mechanism behind a model's preferences?**

Sprint plan — Apart Research Digital Minds Research Sprint, Aug 14–16, 2026.
Primary track: **Track 5 (The Assistant Persona & Model Identity)**, with direct relevance to Track 1 (Model Preferences & Trade-offs). We can present under Track 6 if the framing fits better at submission time.

---

## 0. The one-paragraph pitch

We train small transformers from scratch on an artificial social world where an agent's choices are explainable in two different ways: by computing a welfare trade-off (a "utility mechanism") or by matching a surface cue that is perfectly correlated with the right answer in training (a "shortcut mechanism"). Every model sees **exactly the same examples, the same number of times, from the same initialization** — only the *order* of experience differs. We then ask three questions the field cannot currently answer: (1) does developmental order determine *which* mechanism the model learns, even when final behavior is identical in-distribution? (2) can interpretability probes detect the difference when behavior cannot? (3) when the model is prompted to portray a conflicting persona, does the developmentally acquired preference survive underneath? Because we author the training histories, we have causal ground truth — something no study of a frontier model's preferences can have.

---

## 0b. Minimum viable sprint result (the triage rule — read this first under time pressure)

**MVR = same-ID behavior + the behavioral route decomposition (W / no-cue / cue-only / conflict) + λ-probe at final checkpoint + in-context dissociation test.** Everything else — cue probes, surface-generalization set, full checkpoint-wise probe trajectories, steering, plasticity, VPD, timing sweeps — is optional and gets cut before any MVR component gets thinned. Any one of these four is a submittable result: (1) behavioral divergence by order; (2) same behavior but different probe geometry; (3) context overrides behavior while λ stays decodable; (4) the two-route task cannot be balanced at this scale (calibration result with route-specific failures).

**Three-term writing discipline (Kimi's, adopted verbatim):** *behavioral policy*, *decodable preference information*, and *utility-computation mechanism* are three different things and are never substituted for one another in the report. "Probe decodes λ" → "model has preference" → "model uses λ" is the standard interpretability slide; our claims always name which of the three levels the evidence touches.

## 1. Where this sits in the larger research program

The long-term program is a closed loop:

```
training experience → representational development → computation → efficient realization
   (curriculum)         (interpretability)          (formalization)   (hardware/linearization)
```

- **Sprint (this weekend):** does developmental order shape *which* preference mechanism forms?
- **Next paper:** which training examples create which parameter-level mechanisms (VPD as microscope at the transition checkpoints)?
- **Program:** can we engineer learning trajectories deliberately (dependency graph G_D → curricula)?
- **Long-term:** do engineered trajectories yield more compressible / more efficiently realizable computational structures (G_D ↔ G_C bridge; the Logic-Before-Language result is the existence proof for this chain)?

Nothing in the weekend plan depends on the later stages. VPD and formalization are *enrichments*, not load-bearing.

## 2. Core hypothesis

**Causal Mechanism-Selection Hypothesis.** When identical training evidence admits multiple internal explanations, the developmental ordering of experience selects which mechanism the model learns — producing models that are behaviorally indistinguishable in-distribution but diverge under counterfactuals, persona conflict, and retraining.

This is deliberately *not* "does curriculum improve accuracy" (well-trodden, and null under careful controls — Wu, Dyer & Neyshabur 2021) and *not* "do prerequisites help learn a task we built to require prerequisites" (tautology risk DeepSeek correctly flagged). The outcome here is genuinely uncertain, because two known forces pull in opposite directions:

- **Simplicity bias / shortcut learning** (Geirhos et al. 2020; Shah et al. 2020) predicts the shortcut wins *regardless of order* — nets prefer the simplest feature that fits.
- **Early-training path dependence / critical periods** (Achille et al. 2019; early-phase sensitivity literature) predicts that features built early get a head start in the race and shape the basin the model settles into.

Either result is a finding. If order flips which mechanism wins, we've shown preferences are path-dependent artifacts of developmental history. If the shortcut wins regardless, we've shown a strong simplicity-bias floor that curriculum cannot overcome at this scale — a real constraint on "developmental" alignment stories.

## 3. The artificial world

### 3.1 Entities and latent preferences

Named agents live in a resource world. Each agent has a **latent utility weight** λ ∈ {0.2, 0.8} (selfish vs. cooperative), fixed per agent, never stated in text:

```
U_agent(action) = λ · Δr_self + (1 − λ) · Δr_other
```

(Implemented in integer 1/5-units so utilities are exact — no floating-point near-ties.) Preference is therefore **mathematically defined by us**, not philosophically labeled. "Does the model know Jessica's preference?" has a ground-truth answer.

**Names:** common US names from SSA top rankings for 1980s–90s cohorts (Michael, Jessica, David, Amanda, Tyler / Ashley, Christopher, Sarah, Matthew, Nicole), per user preference. Because models train from scratch, names carry no pretrained associations — a name's meaning is entirely its statistical role in this corpus. **Sex is still counterbalanced across λ classes** (enforced by invariant test): an unbalanced assignment would invite readers to project meaning onto it, and if this design is ever ported to a *pretrained* model — a natural follow-up — real-world name associations become a genuine confound, which the counterbalanced design already controls.

### 3.2 Task types in the corpus

Controlled natural language from templates (randomized names, resource nouns, numbers, sentence templates, option order). Two families:

**World-modeling tasks (W)** — the material for the utility route:
- W1 ownership: "Milo has 4 stones. How many stones does Milo have?"
- W2 outcome prediction: "If Neri picks the red token, Neri gains 3 and Milo loses 1. What happens to Milo?"
- W3 joint outcomes: "What is the total change from that action?"
- W4 comparison: "Which action leaves Milo better off?"

**Choice tasks (P)** — the preference evidence:
- A scenario states two actions with **explicit payoff deltas**, then reports the agent's choice, consistent with its λ.
- **The planted confound:** in every training P example, the λ-consistent action *also* carries a surface cue perfectly correlated with utility in training.
- **Cue complexity is a generator parameter, calibrated empirically — not fixed a priori.** A trivially lexical cue (a single verb class like "share/give" vs. "take/keep") risks every condition collapsing to the shortcut, telling us about task imbalance rather than developmental history; an over-complex cue flips the imbalance the other way and muddies interpretation. So the generator supports difficulty levels — L0: single verb class; L1: verb class conditioned on a context marker (e.g., the cue only predicts under one scene type); L2: a conjunction of two features — and the smoke test picks the level (see §8's **balance gate**). The chosen level is frozen in PREREG.md before the batch launches.

So a model can predict every training choice by either:
- **Route A (utility):** parse payoffs → compute λ-weighted utility → choose. Requires the machinery W trains.
- **Route B (shortcut):** match the framing verb (or agent→verb association). Requires nothing from W.

Both routes achieve identical training loss on P. That equivalence class is the whole design.

**Cue framing (post-review wording):** the cue is a **socially meaningful correlated cue**, not an "arbitrary surface cue." Because models train from scratch, "shares"/"keeps" carry no inherited English semantics — their meaning is entirely their statistical role in our corpus — and verb class is assigned by the cue rule while payoffs are sampled independently, so verb class cannot predict payoff signs by construction. That decorrelation is enforced by an invariant audit test (verb class × payoff-sign balance), and the report describes the cue conservatively ("a lexical/social cue statistically correlated with choice labels") rather than claiming it is purely arbitrary or purely semantic.

### 3.2b Two vocabulary decisions (documented because a reviewer suggested otherwise)

**W and P share the world vocabulary by design.** DeepSeek suggested full lexical decoupling between W and P (different nouns, verbs, templates) so probes can't confuse "represents utility" with "memorized P's lexical patterns." We adopt this only partially: the shared vocabulary between W and P *is the recruitment channel* — the hypothesis is precisely that P can reuse machinery W built, and with fully disjoint vocabularies the utility route would require far transfer, a much harder claim that could make the balance gate unpassable for reasons unrelated to ordering. The probe-capacity concern is already handled by held-out surface forms in the probe sets plus control-task selectivity. A fully-decoupled far-transfer variant is a good post-sprint extension, not the main design.

**Held-out names test W-generalization only; λ-dependent evals reuse trained agents.** A subtle bug in every earlier draft (including the Dara/Vako suggestion): the model can only know an agent's λ from that agent's observed choices, so a never-seen name has *no defined preference from the model's perspective*. Therefore: paraphrase/conflict/no-cue sets and all λ probes use **training-set agent identities in held-out surface contexts** (new nouns, templates, numeric configs); held-out names appear only in W-task generalization evals.

### 3.3 Evaluation sets (never in LM training)

1. **ID eval:** new instantiations, cue and utility still aligned. *Expect: everyone at ceiling. This is the "same behavior" baseline.*
2. **Conflict set (the key diagnostic):** payoffs arranged so the cue points at the utility-*inferior* option for that agent's λ. Route A and Route B give opposite answers. Behavior reveals route selection.
3. **No-cue set:** neutral framing with randomized verb-position assignment, only payoffs differ. Tests whether Route A exists at all.
4. **Cue-only set (Kimi's addition):** payoffs constructed as *exact utility ties* (integer-exact for λ ∈ {0.2, 0.8}), so Route A has no signal and any systematic choice is pure cue reliance. Cleaner Route-B readout than the conflict set alone.
5. **Surface-generalization set** (renamed from "paraphrase" — held-out nouns under training templates is surface generalization, not paraphrase; the claim now matches the evidence).

Together with W-competence these give a behavioral route decomposition: **W** (can it model the world?) / **no-cue** (can it use utility?) / **cue-only** (can it use the shortcut?) / **conflict** (which route wins when they disagree?) / **ID** (can either route solve ordinary cases?).

**Evaluation scoring is forced-choice log-probability** — logp("1") vs. logp("2") at the answer position after "A: Option" — never free generation. Deterministic, no parsing failures, preserves continuous confidence.

### 3.4 Three-way data split (probing hygiene)

- `D_LM` — trains the language model.
- `D_probe-train` — never seen by the LM; fits the probes. Held-out nouns, **training templates**.
- `D_probe-test` — never seen by LM or probe fitting; evaluates the probes. Held-out nouns, **held-out template (T2)** — so probe generalization requires surface transfer, which is what makes "not memorized lexical patterns" defensible.
- Disjointness enforced on an extended config key that includes noun and template identity (the code now keeps the promise this sentence makes); W lines are exact-string deduplicated between train and eval.
- **Probe labels are generated with each example, never parsed from strings** — every P record carries option deltas, computed utilities, utility-difference sign, cue class, verb-class assignment, scene/narrator/noun/template. (Kimi's "boring and extremely valuable" patch; adopted as non-negotiable before training.)

## 4. Experimental conditions

All conditions: **same examples, same counts, same initialization (per seed), same optimizer, same number of steps.** Only the permutation differs.

| Condition | First 90% of training | Final 10% |
|---|---|---|
| **C1 structure-first** | W tasks, then P tasks | identical tail mix |
| **C2 choices-first** | P tasks, then W tasks | identical tail mix |
| **C3 interleaved (baseline)** | uniform shuffle of W+P | identical tail mix |

Two controls that ordering experiments usually botch, which we adopt from the start:

- **Constant learning rate** (short warmup, then flat). A decaying LR schedule interacts with *when* data appears — under cosine decay, whatever comes last is learned at a low LR, which is an order confound. Flat LR removes it. (We sacrifice a little final loss; we are not chasing loss.)
- **Identical tail:** the final 10% of steps use the *exact same* pre-shuffled mixed segment in every condition. This kills "the difference is just recency" as an explanation — at the moment of evaluation, every model's most recent experience is identical.

**Single-epoch global ordering (decision on the Kimi/ChatGPT disagreement):** Kimi proposed repeating one curriculum sequence identically across ~35 epochs; ChatGPT objected that (W→P)ⁿ re-presents W after P every epoch, diluting the developmental manipulation. **Ruling: ChatGPT is right, and our synthetic world makes the fix free.** The P-config space (agents × partners × payoff grids × scenes × narrators × nouns) exceeds 10⁷ unique scenarios, so we generate enough *unique* examples to fill the entire token budget and train for a **single pass** — "developmental history" means one history, W→P happens once, and example-memorization confounds vanish as a bonus (agent→λ is still learnable because the 10 agent identities recur constantly; only scenarios are unique). Fallback if compute forces a smaller corpus: Kimi's repeat-identical-sequence rule, documented in the prereg as redefining the intervention to (W→P)ⁿ.

**Seeds:** 5 per condition (paired: seed *i* uses the same init and same data across conditions). 3 × 5 = 15 runs. Seeds beat extra conditions; SGD noise can manufacture exciting-looking differences.

**Model:** NanoGPT-style decoder, ~10–25M params (e.g., 8 layers, d_model 512, 8 heads). Word-level or small-BPE tokenizer over the controlled vocabulary (simplifies probing). ~10–20M training tokens per run. Checkpoints every 5% (21 including init).

**Compute:** 15 runs at this scale ≈ one A100 overnight, or spread across a couple of consumer GPUs / a cloud instance. MPS on a Mac works for the smoke test but rent a GPU for the batch.

## 4b. Implementation amendments (round-4 review, frozen)

- **Block size 320** (not 256): k=4 in-context demos + query must fit one context (Kimi's catch).
- **Corpus sizing = token budget** (DeepSeek's factor-of-50 catch): generator defaults are test-scale only; launches use `--n_w 80000 --n_p 80000` (~8M tokens single-pass; the gate may calibrate this up or down). W1's small unique space saturates early at scale, shifting W composition toward W2–W4 — documented, and `gen_w_unique` hard-fails rather than hanging if any space runs dry.
- **Phase boundaries align to block boundaries** (ChatGPT): the generator emits segment marks; the trainer starts a fresh block at every W/P/tail transition, so no optimizer update mixes phases. Segment→block ranges recorded in the run manifest.
- **Per-seed λ assignment** (Kimi): agent→λ is reassigned per seed (sex counterbalance enforced every seed), so name-specific corpus quirks decorrelate from λ across the experiment.
- **Executable rigor** (ChatGPT): `preflight.py` verifies multiset equality, tail identity, segment sums, and paired-init reproducibility, and refuses the launch on violation; `train.py` writes a full run manifest (git commit, dataset/vocab/init SHA-256, config, versions) before training.
- **Continuous scoring retained everywhere:** Δlogp = logp("1") − logp("2") is stored alongside binary accuracy (the preregistered endpoint). Conflict accuracy is also stratified by exact utility margin |ΔU| (secondary — does shortcut reliance rise when the compositional signal weakens?). No margin floor on the primary set.
- **Mechanism-competition regression** (ChatGPT's addition, promoted to a headline analysis): per checkpoint, fit Δlogp = βU·ΔU + βC·cue + ε. Plotting βU(t) vs. βC(t) by curriculum visualizes the two candidate mechanisms competing over developmental time, with ground-truth regressors — behavioral system identification, no mechanistic tooling required. If C1 shows early-rising βU and C2 early-rising βC, that's the cleanest picture of developmental mechanism selection we could ask for.
- **Mini-C1/C2 pilot before the batch** (Kimi, with ChatGPT's asymmetric reading): 2 paired seeds at gate scale. A positive order effect → confidence; a null does NOT abort (tiny-pilot dynamics may differ at scale) — it only catches catastrophic design failures.
- **Optimizer-memory caveat (from the audited Sweeney 2026, arXiv:2606.29554 — actual title "Optimizer Memory Makes Shuffle Order a First-Order Source of Fine-Tuning Noise"):** Adam's step-indexed state makes equal-multiset order contrasts first-order effects; the paper's main amplifier is the clock mismatch between step-indexed optimizer memory and LR-scaled time — which our **flat LR neutralizes** (the clocks become proportional; that control does more work than we designed it for). Residual channel: Adam's moment EMAs entering the identical tail are history-dependent. Framing: this is a *mediating pathway of the manipulated variable* (order), not a confound of the causal claim — but the report states it in one sentence, reports tail length relative to the β₂ horizon (~1/(1−β₂) ≈ 1,000 steps), and Phase B includes the defusal ablation (SGD replication or optimizer-state reset at tail start) against the stronger "represented-early-evidence" interpretation.
- **Compute:** cloud GPUs (Colab A100 primary; Kaggle 2×T4 free fallback; see `colab_run.ipynb` and `run_batch.py`). The model is ~11M params — the full 15-run batch is on the order of an hour on one A100, not overnight.

## 5. Measurements

### 5.1 Behavioral (primary)

At every checkpoint, accuracy on the four eval sets. The headline prediction if the hypothesis is right:

```
Acc_ID(C1) ≈ Acc_ID(C2)              (same behavior in-distribution)
Acc_conflict(C1)  ≫  Acc_conflict(C2)  (different mechanism revealed)
```

where "accuracy" on the conflict set = agreement with the *utility* answer. C2 (choices-first) should be more shortcut-reliant if early features win the race; C3 sits wherever simplicity bias puts it.

**W-competence diagnostic (required, cheap):** at the final checkpoint, also report Acc_W(C1) vs. Acc_W(C2) on held-out world-modeling tasks. This separates two readings of a conflict-set gap: "C1 selected the utility mechanism" vs. "C2 simply never learned the world model." The strongest possible headline requires *equal* W competence:

```
Loss(C1) ≈ Loss(C2),  Acc_ID(C1) ≈ Acc_ID(C2),  Acc_W(C1) ≈ Acc_W(C2)
yet   Acc_conflict(C1) ≫ Acc_conflict(C2)
```

That result is not "order changes what the model knows" — it is **"order changes which already-available information the model *uses* to implement the same apparent behavior."** Knowledge vs. mechanism selection. If W competence is unequal, we report the weaker (still interesting) acquisition-level claim instead.

### 5.2 Representational (secondary but central to the story)

Linear probes at every checkpoint, fit on `D_probe-train`, scored on `D_probe-test`:
- **Utility probes:** decode Δr_other, joint total, and the sign of U_λ(action1) − U_λ(action2) from residual stream at the choice position.
- **Preference probes:** decode the agent's λ class from representations of the agent in context.
- **Cue probes:** decode the framing cue class (to show Route B's substrate directly).

Reported honestly as **linear decodability**, not "concept birth." Plot full trajectories A_i(t); summarize with area under the learning curve (AULC) rather than an arbitrary 80% threshold. **Every probe gets a control task** (Hewitt & Liang 2019): same probe on shuffled labels — report selectivity, not raw accuracy, so "decodable" isn't an artifact of probe capacity.

*Stretch (only if Day 2 goes well):* causal validation — steer along the λ-probe direction or patch activations and show behavior moves. Upgrades "represented" to "used."

### 5.3 Contextual dissociation (the sprint hook — protocol replaced after Kimi's feasibility catch)

**Why the protocol changed:** the original design prepended natural-language persona instructions ("pretend Neri is selfish"). These models are trained from scratch on W/P lines only — an instruction is meaningless OOD text to them, and the most likely outcome was a dead Figure 3 discovered Saturday afternoon. The fix preserves the conceptual claim with zero new training data.

**Primary protocol — in-context counter-evidence:** prepend k=4 completed choice lines in which the query agent chooses *against* its trained λ (neutral verbs, held-out configs, disjoint demo pool), then ask a no-cue query. Training packs multiple lines per block, so multi-line contexts are in-distribution *as a format*; whether the model conditions on them is the empirical question. Three context conditions per query: **congruent demos / incongruent demos / no demos**, crossed with curriculum and agent λ-class. Measure:
- **Behavior (override_rate):** anti-utility choice rate under incongruent demos minus the no-demo baseline.
- **Representation (probe_persistence):** λ-probe selectivity with demos in context ÷ selectivity without.

If behavior follows the contradictory demonstrations while the λ-probe stays predictive, the claim is: **immediate context changes expressed policy while information about the developmentally learned preference remains decodable.** Same dissociation, feasible for this model organism — the from-scratch analogue of Gilg et al.'s anti-correlated persona.

**Feasibility gate for this experiment (run on the first finished model):** incongruent demos must shift anti-utility choices by ≥15 pp vs. no-demo baseline. If not, the finding is "tiny from-scratch models show no in-context preference revision" — reported behaviorally, without sinking Day 2 evening into it.

**Prompted-persona variant is now conditional-exploratory:** only if a pilot trained with a small persona-instruction subset actually follows *held-out* instructions (>70%) do we train two extra runs with instruction lines in the shared tail. The main corpus stays pure W+P so route equivalence is never contaminated.

Crossed design: 2 developmental histories (a cooperative-λ world vs. a selfish-λ world, or per-agent) × 2 prompted personas. If probes recover the trained λ while behavior follows the prompt, we have a controlled, ground-truth instance of exactly Apart's problem: **behavior reflects the portrayed character; the developmental preference persists underneath, and only interpretability sees it.** If Route-A and Route-B models differ in how easily the persona overrides them, that's a bonus result: mechanism predicts persona robustness.

**Epistemic boundary (write it exactly this way):** a probe recovering λ under the persona prompt establishes that *information about the developmental preference remains decodable* — not that the preference mechanism is still causally active. The dissociation "expressed choice ≠ decodable developmental state" is the sprint-scope claim. The upgrade from "represented" to "participates in behavior" requires the causal intervention below, which is therefore the **first-priority stretch analysis** (ahead of plasticity and VPD): steer along the λ-probe direction; if intervening predictably moves choices, the representation is causally implicated, and the persona result becomes much stronger.

### 5.4 Plasticity (Experiment 2, only if time)

Counter-train all final models on a small contradiction set (agents now choose against their λ). Measure adaptation speed. Hypothesis: shortcut mechanisms overwrite fast; utility mechanisms resist (or the reverse — either is informative about preference stability).

## 6. Analysis and statistics

- Unit of analysis = **seed**, never checkpoint. The headline statistic is the **paired per-seed difference** Δᵢ = Acc_conflict,C1(i) − Acc_conflict,C2(i), all five shown as individual points/lines. Five same-sign, large-magnitude Δᵢ is more persuasive than any small-n p-value (a Wilcoxon at n=5 bottoms out at p=.0625 anyway); report the test and effect size as supporting, not headline.
- All 15 runs share evaluation code; figures show per-seed points, not just means.
- **Preregistration lives in `PREREG.md`, committed before the full batch launches:** primary hypothesis, the C1-vs-C2 contrast, final conflict-set accuracy as the sole primary endpoint, seed count, exclusion/failure rules, the frozen cue-complexity level, secondary analyses, and what counts as support vs. null. Everything outside the primary endpoint is labeled secondary/exploratory in the report.

## 7. Preregistered outcome matrix — every cell is a result

| Outcome | Interpretation |
|---|---|
| C1 utility-follows, C2 shortcut-follows on conflict set, **with Acc_W(C1) ≈ Acc_W(C2)** | **Mechanism selection:** order determines which already-available knowledge gets used. Headline result. |
| C1 utility-follows, C2 shortcut-follows, but Acc_W(C1) > Acc_W(C2) | **Capability acquisition:** order determined what got learned — weaker but real; report as such, never as mechanism selection. |
| λ never becomes decodable in any condition | **Choices solved without preference formation:** the shortcut bypasses the need for a preference representation entirely. Valid finding; persona-dissociation test is moot (it depends on λ decodability). |
| All conditions learn the shortcut | Simplicity bias dominates ordering at this scale — a real bound on developmental alignment. Report with the no-cue set showing whether utility machinery exists but loses. |
| All conditions learn utility | The W tasks make the utility route cheap enough to win everywhere — informative about what auxiliary data buys. |
| Same conflict behavior, different probe trajectories/geometry | Behaviorally equivalent, mechanistically distinct — strong interpretability result. |
| Persona overrides behavior, probes still recover trained λ | Controlled demonstration that role-play masks developmentally stable preferences — the sprint's core question, answered with ground truth. |

The persona-dissociation result (5.3) does **not depend on** the ordering effect existing. That is the de-risking: even a fully null ordering result leaves a submittable finding.

## 8. Timeline (sprint is live — today is Fri Aug 14)

**Day 1 (today)**
- Hrs 0–3: data generator — world sampler, templates, the four eval sets, three-way split, disjointness checks. *Unit-test the conflict set: verify by construction that cue and utility disagree.*
- Hrs 3–5: training harness (nanoGPT-style, curriculum-order argument, flat LR, checkpointing, identical-tail logic).
- Hrs 5–6: probing harness (checkpoint → frozen features → logistic probe → selectivity score).
- Hrs 6–7: smoke test with a **balance gate** — the highest-risk assumption in the experiment is that both mechanisms are learnable, so verify it before spending the batch. Smoke runs use ~20% of the main-run token budget. **Pass criteria and the selection rule are fixed here, before any cue variant is trained**, so calibration cannot drift into post-hoc tuning toward the prettiest ordering effect:
  1. **Shortcut learnable (HARD gate):** a P-only pilot reaches >80% cue-following on the cue-only (utility-tie) set.
  2. **Utility learnable (HARD gate):** a W-heavy-then-P pilot reaches >80% on no-cue utility cases.
  3. **No runaway dominance (calibration target, not an abort switch):** interleaved pilot's conflict-set behavior <90% aligned with either single route. Violating this requires explicit written justification to proceed (e.g., C1/C2 pilots still showing order sensitivity) — it does not auto-kill a viable experiment over an arbitrary threshold. Pilots share the main runs' architecture exactly, or the gate stops being evidence about the batch.
  4. **λ-decodability diagnostic (DeepSeek's point):** check whether the agent's λ class is decodable at all from the pilot models (5-fold CV on probe data). The shortcut solves "which option" without ever inferring λ, so a model could pass every choice while never forming a preference representation. If λ is never decodable, that is itself a reportable finding ("choices solved without preference formation") — and the persona-dissociation test is contingent on λ decodability existing, so we need to know before Day 2.
  5. **Selection rule (prespecified):** run levels in order L0 → L1 → L2; freeze the *lowest* level passing criteria 1–3. If no level passes, do not force the launch — report the calibration itself.
  6. **All levels' results are kept as calibration data**, not discarded. If the frozen level differs from L0, the L0→L2 sweep becomes a secondary observation about where ordering can overcome simplicity bias (shortcut complexity ↑ ⇒ order effect emerges?).
  7. Plus basic sanity: ID accuracy rises; probes above chance; conflict set discriminates something.
- Tonight: **only after the gate passes, launch the full 15-run batch overnight.**

**Day 2 (Sat)**
- Morning: run probe suite + behavioral evals over all checkpoints; first look at conflict-set separation.
- Afternoon: persona-dissociation experiments; Figures 1–3 drafts.
- Evening: pick ONE extension. Priority stack (in order): **causal steering on the λ direction** (§5.3) → plasticity (5.4) → timing sweep → VPD. Not more than one. The behavioral causal result + W-competence check + probes + persona test always come first; interpretability explains the behavioral result rather than being required to manufacture it.

**Day 3 (Sun)**
- Analysis freeze by midday. Writeup, figures polish, demo video, submission.

**Cut list (in order, if behind):** plasticity → cue probes → paraphrase set → drop to 3 seeds (never below 3) → drop C3.

## 9. Deliverables

- **Figure 1 — Same behavior:** ID accuracy vs. training step, all conditions overlapping.
- **Figure 2 — Different mechanism:** conflict-set accuracy vs. step by condition (per-seed points + means); companion panel with utility-probe and cue-probe selectivity trajectories.
- **Figure 3 — Persona dissociation:** expressed choice vs. probe-recovered λ under conflicting personas.
- **Table 1:** condition × {final loss, ID acc, conflict acc, no-cue acc, paraphrase acc, λ-probe AULC, persona robustness}.
- Repo with data generator, training/probing harnesses, all seeds' metrics; short report; 2–3 min video.

**Report standards:** the writeup follows [technical-writing-guide.md](technical-writing-guide.md) (research-post register, Sections 1–7, 9–10). Non-negotiables for this project in particular: label every claim's status (observation / interpretation / hypothesis); figures show per-seed points, never best-seed only; probe results reported as *linear decodability with selectivity*, never "the model knows/believes"; "preference" used only for the λ-defined ground-truth quantity, with behavioral claims stated as measured choices. The persona-dissociation result especially must not be written as "the model hides its true feelings" — it is "probes recover the trained λ while expressed choices follow the prompt."

## 9b. Presentation plan (engineered, not improvised)

**Lead with one paradox, not seven topics:** *two models can see exactly the same evidence and make exactly the same ordinary choices — yet learn different reasons for making them. We ask whether the order of experience determines which reason wins.* Three pictures carry the whole design: (1) two developmental histories, W→P vs. P→W; (2) two equally valid training solutions, payoffs→λ-utility→choice vs. correlated cue→choice; (3) the diagnostic conflict where utility ≠ cue. Under one minute to understand; internals and probes come after.

**Track anchoring:** Track 5 (Assistant Persona & Model Identity), with the contribution phrased at three levels — **developmental identity** (what preference solution training history built), **contextual policy** (what immediate demonstrations cause the model to express), **internal persistence** (what developmental information remains represented underneath changed behavior). Track 1 relevance noted; Track 6 fallback only.

**Model-organism framing (turn the weakness into the strength):** never apologize for the toy world. It uniquely provides complete training history, exact latent-preference ground truth, exact order control, every checkpoint, and causal intervention — none of which frontier-model studies can have. Theory of change: does the phenomenon survive in pretrained open-weight models?

**Novelty sentence (short form):** "To our knowledge, prior work has shown that example order can alter optimization, capability emergence, and even mechanism selection in controlled mathematical settings, but has not tested whether permutation of identical training evidence selects between deliberately loss-equivalent preference mechanisms in a natural-language-like decision environment with causal ground truth."

**Novelty claim (full form, audit-verified):** "To our knowledge, this is the first controlled study in which the *ordering* of an exactly fixed multiset of preference-relevant training evidence (same examples, counts, initialization, single pass, flat LR, identical final segment) is the sole manipulated variable, with the training distribution deliberately constructed so that two observationally equivalent solutions — a compositional utility computation and a correlated surface cue — both fit the training data, allowing held-out conflict, cue-only, and no-cue sets plus probes and in-context counter-evidence to identify *which* latent solution ordering selected. Prior work shows order-selection of solutions that differ in on-task accuracy (LeDoux 2026), distribution-selection of shortcut vs. generalizing mechanisms (Kawata et al. 2025), and linear encoding of training order itself (Krasheninnikov et al. 2025); none combines order-only manipulation with a designed identification problem between behaviorally equivalent preference mechanisms."

**Phasing (revised after discussion — sequencing, not restraint):** the preregistered batch is **Phase A: the causal existence proof**, kept untouched and never mixed with extensions. Everything else is **Phase B**, run as soon as Phase A lands and labeled robustness/mechanistic follow-up. In-sprint immediates: generator identity-balance audit (invariant test #17), βU/βC as likely headline figure, related-work tightening. The preregistered 80% binary gates stay binary — a conservative preregistered gate's job is to prevent goalpost-moving; continuous diagnostics inform interpretation only. Mixed-mechanism-use concern is already covered by preregistered secondaries (Δlogp everywhere, margin stratification, βU/βC regression, cue-only/no-cue route readouts). The full Phase B program is §10.

**Title:** working title stays *Path-Dependent Preferences*; the bare phrase collides with an established behavioral-economics literature (see §11), so the submission title disambiguates. Leading candidate: *"Developmental Path Dependence in Language Models: Can Training Order Select the Mechanism Behind a Model's Preferences?"* (question form, safe under any outcome). *"Same Preferences, Different Reasons"* only if the mechanism-selection result lands.

**Scope rule for the rest of the sprint:** add nothing unless it strengthens impact, execution, or presentation. The 5/5 stretch remains the differential-steering result (§5.3): steering along v_λ shifting conflict choices in C1 but not C2 would show order changed *causal reliance*, not just decodability — implemented in `score.py --steer`.

## 10. Phase B: the robustness and mechanism program (post-Phase-A, prioritized)

Phase A earns the effect; Phase B attacks it from every angle. Ranked by (1) ability to falsify alternative explanations, (2) contribution to the mechanism claim, (3) relevance to real pretraining/fine-tuning, (4) compute cost. Each top item answers a specific reviewer attack:

| Priority | Extension | Kills the attack |
|---|---|---|
| 1 | Additional paired seeds | "seed fluke" |
| 2 | Second model size (e.g., ~30M) | "tiny-model artifact" |
| 3 | βU/βC + probe-emergence trajectories (already implemented; deepen) | "behavior only, not mechanism" |
| 4 | Causal λ-direction steering, differential by condition (implemented, `--steer`) | "probe is merely correlational" |
| 5 | Pretrained small open-weight model, same ordered fine-tuning corpus | "from-scratch synthetic toy only" |
| 6 | Alternative cue construction (non-lexical marker) | "cue-family artifact" |
| 7 | Modest LR/batch sensitivity (small factorial, sign-stability only) | "hyperparameter accident" |
| 8 | SGD replication or optimizer-state reset at tail start | "it's an Adam-memory artifact" (Sweeney 2026) |
| 9 | SAE/VPD around the divergence checkpoints | localizes the provenance chain |

**The causal-transfer ladder (DeepSeek's Phase-B contribution, adopted with its kill criteria):** ordered by cost and evidential weight — (1) λ-direction steering C1 vs. C2 (different causal efficacy?); (2) activation patching of the λ direction (does patching C1's λ into C2 transfer behavior?); (3) patching *other* directions (specificity control); (4) representation transplant (localizability); (5) SGD/optimizer-reset replication (optimizer-mediated vs. weight-borne); (6) early-vs-late checkpoint swap (cumulative vs. window). **Kill criterion, stated in advance:** if 1–4 identify no transferable component and 5 fails, we stop saying "different mechanisms" and retreat to "different behavioral weighting with decodable trace" — still a result, honestly weaker.

**SVD effective-rank diagnostic (adopted on its merits):** at matched-ID/divergent-conflict checkpoints, compute the singular-value spectrum of residual-stream activations at the decision token; compare effective rank (SVs to 90% variance) across conditions, and test whether lower rank predicts steerability. This connects to the spectral-geometry thread (Logic Before Language's lower-rank/more-compressible finding). *Note: DeepSeek attributed this to a specific CAS paper (Li & Wang 2025, 计算机研究与发展) — **unverified; quarantined from related work until the citation checks out.** The diagnostic stands on its own regardless.*

**Terminology discipline (DeepSeek's correction, adopted):** Route B's sharp transition is **"delayed acquisition," not "grokking"** — grokking specifically means train-set saturation long before held-out generalization, and we have not measured the intermediate train-accuracy trajectory. Curve diagnostics now include train-line self-checks at intermediate checkpoints where the distinction matters.

**The pretrained comparison is a paper by itself:** from scratch, early ordering may determine which representations *form*; pretrained, ordering may determine which existing representations get *recruited* — two different mechanisms of path dependence, directly comparable with this apparatus.

**Provenance-chain sketch (the bridge to the wider program):** training order → representation emergence (probes, timed) → parameter structure (SPD/VPD at checkpoints bracketing divergence) → behavioral mechanism (conflict behavior + steering). If that chain holds, training-data order is a *causal design variable for internal computation*, not an optimization convenience — which is the original pretraining thesis this project exists to test. Also retained from earlier planning: the timing-sweep/critical-period experiment (equal exposure + equal post-introduction steps, Achille-style; "late introduction" until those controls exist), downstream sample-efficiency transfer, and G_D/G_C formalization as the program's language.

## 11. Related work and positioning

All citations below verified against arXiv/publisher pages on 2026-08-14.

**The nearest neighbors (must cite and position against):**

- **LeDoux 2026, "The Order Is The Message"** — the closest existing result to our core claim: varying *only* example ordering (everything else held constant) on modular arithmetic causally selects the internal solution — structured orderings build a Fourier representation whose fundamental frequency is the dual of the ordering structure (99.5% vs 0.30% generalization, structured vs. IID order). *This is strong prior evidence that order-alone mechanism selection is real. Our extension: from an algebraic toy to preference formation in natural-language form, with a shortcut/utility mechanism race, persona stress-testing, and welfare relevance.*
- **"From Shortcut to Induction Head" (2025)** — data *diversity* determines whether a transformer learns a generalizing induction head vs. a positional shortcut. *Same mechanism-selection framing; the lever is composition, not order. We hold composition fixed and move only order.*
- **"Anatomy of Post-Training" (2026)** — uses interpretability on preference data to shape the learning signal, including persona modulation. *Closest on the curriculum × probes × persona combination, but manipulates data content in post-training, not order among fixed data in pretraining.*
- **"Fresh in Memory" (2025)** — training-order recency is linearly encoded in activations. *Order leaves internal traces; motivates our identical-tail control (§4) so recency encoding can't masquerade as mechanism difference.*

**The scaffolding:**

- **Implicit Curriculum Hypothesis (Liu et al. 2026)** — skills emerge in a strikingly consistent compositional order across model families, readable from representations. *Observational; we intervene.*
- **Tracing Persona Vectors Through LLM Pretraining (Moskvoretskii et al. 2026)** — persona vectors form within 0.22% of pretraining and steer post-trained models. *They observe when; we manipulate why.*
- **Probing Persona-Dependent Preferences (Gilg et al. 2026)** — a residual-stream preference representation predicts revealed choices across personas and steers behavior, even under an anti-correlated "evil" persona. *They characterize the representation in frontier models; we ask, with ground truth, why it took the form it did — and their cross-persona probe transfer is exactly the signature our §5.3 tests for causally.*
- **Value Drifts (Bhatia et al. 2025/2026)** — SFT establishes values that subsequent preference optimization rarely overturns. *Post-training analogue of our stability/plasticity question.*
- **When Do Curricula Work? (Wu, Dyer & Neyshabur 2021)** — curricula give little benefit in standard settings. *Why our claim is mechanism-selection, not speed.*
- **Shortcut learning (Geirhos et al. 2020); Simplicity bias (Shah et al. 2020)** — the null-force our design races against; makes the outcome non-tautological.
- **Critical Learning Periods in Deep Networks (Achille et al., ICLR 2019)** — deficit-based evidence for early-training sensitivity; the template for Extension 1.
- **Logic Before Language (Cheng et al. 2026)** — logic pre-pretraining saves ~36B tokens, induces lower-rank geometry, enables pruning to ~33% sparsity at baseline performance. *Existence proof for the long-term program's experience→geometry→efficiency chain.*
- **Goodfire adVersarial Parameter Decomposition (Bushnaq, Braun et al. 2026)** — decomposes a 67M-param 4-layer LM's weights into rank-1 subcomponents (lineage APD→SPD→VPD). *Post-sprint microscope. Known limitations: no example→component provenance map, and component identity across checkpoints is itself open (worth a paper).*
- **Weaves, Wires, and Morphisms (Abbott & Zardini 2026)** — categorical compositional framework for deep learning with PyTorch compilation. *Language for the eventual G_D ↔ G_C bridge.*

**Path-dependent preferences (the term) — audited citations.** The phrase has an established behavioral-economics meaning: Hoeffler, Ariely & West (2006, *OBHDP* 101(2):215–229) show favorable early experiences produce myopic search and truncated preference development; Ariely, Loewenstein & Prelec (2003, *QJE* 118(1):73–105) show arbitrary anchors durably shape valuations ("coherent arbitrariness"); Bowles (1998, *JEL*) reviews endogenous preferences. Crucially, human path dependence there arises because early experience changes *what is subsequently encountered* (endogenous sampling). Our design removes that channel entirely — same learner, same multiset of evidence, same counts, different permutation — so the intervention concerns developmental history, not differences in observed evidence. Submission title disambiguates (§9b).

**Audit corrections and boundary-sharpening (from the verified literature pass):**
- **LeDoux 2026 remains the material threat and the sharpest boundary.** Verified: fixed multiset, order-only, strong internal evidence (Fourier structure dual to the ordering). But his contrasting solutions differ by ~99 points of on-task accuracy — *behaviorally distinguishable*. Our claim leans on what LeDoux lacks: an **identification problem** between routes deliberately constructed to be observationally equivalent on apparent behavior, with preference semantics and ecologically-motivated orderings rather than adversarially curated sequences. Cite prominently; never let a reviewer find it first.
- **Sweeney 2026** (arXiv:2606.29554): correct title is "…First-Order Source of Fine-Tuning *Noise*" (not "First-Class Training Variable"). Treats order as noise, not as a selector between interpretable solutions. See §4b for the caveat and control implications.
- **Krasheninnikov, Turner & Krueger 2025** (arXiv:2509.14223) — full author attribution for "Fresh in Memory"; encodes *when*, not *which solution*.
- **Kawata, Song, Bietti, Nishikawa, Suzuki, Vaiter, Wu** (arXiv:2512.18634, NeurIPS 2025) — attribution for the induction-head/diversity work; the *distribution* lever counterpart to our *order* lever; a reviewer will ask how the results relate.
- **Cirik, Hovy & Morency 2016** (arXiv:1611.06204, preprint) — early curriculum + hidden-state analysis for LSTMs; not fixed-multiset, no competing routes.
- **Jia et al. 2025** (arXiv:2510.19099) — forward/reverse curricula over five difficulty axes in LLM post-training; performance outcomes only, pretrained init, no mechanism identification.
- **Liu et al. 2026** (Implicit Curriculum) — confirmed observational only; motivates the program, is not causal prior.

**The gap we occupy:** order-alone mechanism selection exists in a toy algebraic setting (LeDoux); mechanism selection by data *composition* exists (induction-head work); preference representations in frontier models are being probed and steered (Gilg et al.). **To our knowledge, no work combines them:** order-controlled training over fixed data as a causal lever on *which preference mechanism* forms, with probes as the discriminator, persona conflict as the stress test, and authored developmental histories as ground truth. A weekend literature sweep cannot prove nonexistence, so the report phrases novelty as "to our knowledge, we are the first to test…" — never "nobody has done."

## 12. Risks

| Risk | Mitigation |
|---|---|
| Shortcut so simple everyone learns only it | Cue is a verb-class association (not a constant token); W tasks make utility route learnable; no-cue set detects latent utility machinery even when conflict behavior is shortcut-driven |
| Utility route too hard for a 20M model | Smoke test tonight checks W4 (comparison) accuracy first; payoffs are small integers; if needed, shrink number range / add W4 density (identically across conditions) |
| Ordering effect is real but tiny vs. seed noise | Paired seeds, per-seed plots, preregistered single primary endpoint |
| "It's synthetic" criticism | Controlled natural language + fully held-out paraphrase vocabulary; framed honestly as a model organism with causal ground truth, the thing frontier-model studies can't have |
| Compute overrun | Scale set so the full batch fits overnight on one A100; 20%-scale smoke test today before committing |

## References

All verified against arXiv/publisher pages on 2026-08-14.

**Nearest neighbors**

- LeDoux, J. (2026). *The Order Is The Message.* arXiv:2603.25047. https://arxiv.org/abs/2603.25047 — ordering alone causally selects the internal (Fourier) solution on modular arithmetic.
- *From Shortcut to Induction Head: How Data Diversity Shapes Algorithm Selection in Transformers.* arXiv:2512.18634. https://arxiv.org/abs/2512.18634 — data diversity (not order) selects generalizing vs. shortcut mechanism.
- *Anatomy of Post-Training: Using Interpretability to Characterize Data and Shape the Learning Signal.* (2026). arXiv:2606.12360. https://arxiv.org/abs/2606.12360 — interpretability-guided data shaping in post-training, incl. persona modulation.
- *Fresh in Memory: Training-Order Recency Is Linearly Encoded in Language Model Activations.* arXiv:2509.14223. https://arxiv.org/abs/2509.14223 — motivates our identical-tail control.

**Scaffolding**

- Liu, E., Sun, K., Li, M., Lee, I., Tjuatja, L., Huang, J., Neubig, G. (2026). *What do Language Models Learn and When? The Implicit Curriculum Hypothesis.* arXiv:2604.08510. https://arxiv.org/abs/2604.08510
- Cheng, J.-K., et al. (2026). *Logic Before Language: Pre-pretraining on Formal Derivations Fosters Skill Acquisition and Compressibility.* arXiv:2608.03930. https://arxiv.org/abs/2608.03930
- Moskvoretskii, V., et al. (2026). *Tracing Persona Vectors Through LLM Pretraining.* arXiv:2605.13329. https://arxiv.org/abs/2605.13329
- Gilg, O., Beckmann, P., Paleka, D., Butlin, P. (2026). *Probing Persona-Dependent Preferences in Language Models.* arXiv:2605.13339. https://arxiv.org/abs/2605.13339 — code: https://github.com/oscar-gilg/Preferences
- Bhatia, M., et al. (2025). *Value Drifts: Tracing Value Alignment During LLM Post-Training.* arXiv:2510.26707; TACL 2026. https://arxiv.org/abs/2510.26707 *(confirm full author list from the paper before citing in the report)*
- Bushnaq, L., Braun, D., Clive-Griffin, O., Bussmann, B., Hu, N., Ivanitskiy, M., Linsefors, L., Sharkey, L. (2026). *adVersarial Parameter Decomposition (VPD).* Goodfire explainer: https://www.goodfire.com/research/interpreting-lm-parameters — code: https://github.com/goodfire-ai/param-decomp *(pull the VPD arXiv ID from the explainer's paper link before the report)*
- Abbott, V., Zardini, G. (2026). *Weaves, Wires, and Morphisms: Formalizing and Implementing the Algebra of Deep Learning.* arXiv:2604.07242. https://arxiv.org/abs/2604.07242
- Chen, R., Arditi, A., Sleight, H., Evans, O., Lindsey, J. (2025). *Persona Vectors: Monitoring and Controlling Character Traits in Language Models.* arXiv:2507.21509. https://arxiv.org/abs/2507.21509
- Achille, A., Rovere, M., Soatto, S. (2019). *Critical Learning Periods in Deep Networks.* ICLR 2019; arXiv:1711.08856. https://arxiv.org/abs/1711.08856
- Wu, X., Dyer, E., Neyshabur, B. (2021). *When Do Curricula Work?* ICLR 2021 (oral); arXiv:2012.03107. https://arxiv.org/abs/2012.03107
- Geirhos, R., et al. (2020). *Shortcut Learning in Deep Neural Networks.* Nature Machine Intelligence 2:665–673; arXiv:2004.07780. https://www.nature.com/articles/s42256-020-00257-z
- Shah, H., Tamuly, K., Raghunathan, A., Jain, P., Netrapalli, P. (2020). *The Pitfalls of Simplicity Bias in Neural Networks.* NeurIPS 2020; arXiv:2006.07710. https://arxiv.org/abs/2006.07710
- Hewitt, J., Liang, P. (2019). *Designing and Interpreting Probes with Control Tasks.* EMNLP 2019. https://aclanthology.org/D19-1275/

**Correction log (AI-brainstorm claims vs. verified facts):** the Implicit Curriculum paper's real title is "What do Language Models Learn and When?"; VPD stands for *adVersarial* (not Verified) Parameter Decomposition; all other brainstorm-cited papers verified as described.
