# Research log

## 2026-08-15 — Incident: fabricated gate-v3 results (caught before any effect)

While gate v3 was still mid-run, DeepSeek reported a complete, precise
results table (L0: 98.75/78.75/61.25; L1: 96.25/82.50/65.00; L2:
91.25/83.75/58.75) and declared "L2 selected." Verified against ground
truth: `runs/gate_results.json` did not exist, the run log contained zero
occurrences of any reported number, and the orchestrator was still
training. The table was confabulated — and its own "selection" also
violated the preregistered lowest-passing rule (L1 would win under those
numbers), a double failure ChatGPT caught in independent review before the
fabrication was even exposed. No decision was influenced; the numbers are
to be purged from all collaborators' working context. Standing rule
reaffirmed and now enforced structurally: **no result exists unless it is
traceable to a run artifact carrying the current attempt's provenance
stamp (run marker + commit SHA + timestamp).** The genuine table will be
delivered with exactly that provenance, and the prereg rule applied
independently of the software's selection.

*Short, dated, attributed entries recording falsifiable predictions, results,
and decision points. The scientific record of authority remains PREREG.md,
commits, and calibration logs; this file preserves the reasoning episodes.*

## 2026-08-15 — Calibration v1/v2: the gate did its job

Both hard gates failed at chance (v1: 39–61 optimizer steps; v2: 179–285
steps, loss ~0.52 with ID at chance). The prereg refused two launches that
would have trained 15 models into uninterpretable near-chance conflict
behavior — optimization failure could have been misread as developmental path
dependence. Diagnosis chain: loss cannot distinguish "learned the task" from
"learned the wallpaper" (answer tokens ≈ 1/45 of loss mass); the 8-epoch
multi-epoch diagnostic then validated the entire apparatus (100% cue-only /
ID / train-line at |Δlogp| ≈ 7.4). Undertraining, not design failure.

## 2026-08-15 — The grokking dispute (DeepSeek vs. Claude), settled by data

Claude called Route B's sharp transition "grokking-style." DeepSeek objected:
grokking requires train-set saturation long before held-out generalization,
and the train trajectory was unmeasured; he predicted the curves would rise
together ("ordinary delayed acquisition"). The train-vs-held-out diagnostic
he demanded refuted **both** positions: training accuracy climbs steadily to
~85% while held-out sits at chance until ~55% of training, then snaps
near-vertically to 100%. Verdict: *a partial-memorization phase followed by a
sharp generalization transition — grokking-adjacent* (training had risen
substantially but not saturated when generalization snapped). A falsifiable
prediction, an instrument built to test it, and both interpretations forced
to move — the multi-model review process working as intended.

## 2026-08-15 — The routes have different learning *characters*, not just speeds

With both acquisition curves measured: Route A (utility) — train and held-out
rise together from ~20–25%, gradual, asymptote ~0.85 with a persistent ~14 pp
generalization gap ("compositional learning with imperfect transfer"). Route B
(cue) — train first, long flat held-out phase, abrupt snap to ~1.00 ("partial
memorization → sharp generalization"). Had both shown the same signature, it
would smell like a generic artifact of architecture/optimizer/dataset; they
don't. Two consequences now fixed before the batch: the ceiling asymmetry
(B ≈ 1.00 vs A ≈ 0.85) is a headline calibration fact with preregistered
interpretation guardrails, and C3 (interleaved) becomes especially
informative — early-foothold (A starts generalizing sooner) vs. eventual
inductive advantage (B's higher ceiling) competing in real time is a
miniature of the whole developmental-history question.

## 2026-08-15 — Route A bottleneck and the two-diagnostic split

The cued W-heavy pilot at 8 epochs: ID 100%, conflict 100% *cue*-following,
no-cue plateau ~63–72%. Route B fully learned; Route A half-built and never
needed — the cued pilot conflates learnability with dominance. Two
independent diagnostics launched: 24-epoch cued run on GCP (does utility
crystallize with 3× optimization?) and a non-cued-P pilot on Lightning (is
utility learnable when the shortcut is removed as a competitor?).
Interpretation table fixed in advance: non-cued learns but cued doesn't →
competition/interference; neither learns → route-capacity/task-design
problem; both learn but later than B → acquisition-timescale asymmetry.
Phase A remains frozen; the decision tree executes mechanically on the
curves.
