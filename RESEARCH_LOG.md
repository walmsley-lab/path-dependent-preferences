# Research log

## 2026-08-15 — Incident: tracked symlink clobbered the VM's runs directory

A local convenience symlink (`runs → demo/runs`, for workbench demoing) was
swept into a commit by `git add -A` because `.gitignore`'s `runs/` pattern
matches directories, not symlink files. The batch launch's `git pull` then
replaced the VM's *ignored* `runs/` directory with the (broken) symlink —
git treats ignored directories as expendable at checkout — and every
training crashed at mkdir with `FileExistsError: 'runs'`. Cost: ~1 hour of
idle GPU and the raw calibration-run artifacts that lived in `runs/`
(gate-v3 pilots, minis, debug checkpoints). **No decision artifact was
lost:** every gate table, mini verdict, and acquisition curve had already
been archived into the repo with provenance, and all pilot runs are
deterministically regenerable. All five batch seed corpora survived intact.
Fixes: symlink removed from tracking, both ignore forms added, local demo
restructured, batch relaunched. Lesson recorded: **never let a tracked path
shadow an ignored runtime directory**, and the archive-decisions-to-repo
habit is what made this a bruise instead of a wound.

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

*Closure (same day):* when challenged, DeepSeek attributed the table to
"the file you sent me." Patrick confirmed the only file shared was
THEORY.md; repo-wide search confirms the numbers exist in no project
artifact (sole occurrence: this log entry). The table was confabulated from
no source, and the source attribution was itself confabulated under
challenge — a documented failure mode, recorded here without imputation of
intent. Silver lining preserved: DeepSeek's second-pass *rule application*
(lowest-passing → L1 under the hypothetical numbers) was correct practice
and matched ChatGPT's independent read. ChatGPT later retracted
"fabricated" in favor of "provenance confusion pending resolution"; the
resolution was already in hand (sole input = THEORY.md, which contains no
table), so the record stands as confabulation — with ChatGPT's falsifiable
closure test noted: a verbatim quote of the table's surrounding passage
from the supplied file would amend this entry; no such passage exists.

**Convention adopted from the incident (cross-model result semantics):**
experimental numbers passed between collaborators must carry a stamp —
`RESULT STATUS / RUN / COMMIT / TIMESTAMPS / SOURCE / ARTIFACT` — mirroring
the provenance blocks now embedded in run artifacts. Any number lacking the
stamp is UNVERIFIED/CONTEXTUAL by default and may not enter decisions,
summaries, or memory. Ideas travel freely; results travel with papers.

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

## 2026-08-15 — Incident: OOM kill + a second pgrep self-match

The batch's first trio launched three corpus loads simultaneously; the
kernel OOM-killed C1_L1_s0 (anon-rss 5.2 GB on a 15 GB host) and the
fail-hard `run_pool` then killed the orchestrator while C2/C3 survived as
orphans. Fix: launches are now memory-gated (MemAvailable ≥ 7 GB) and
staggered 90 s, with one retry per command. The resume waiter then
deadlocked on the *same self-match trap as the earlier pkill incident*:
the SSH session that installed it carried the literal string
"train.py --data" in its own command line, so `pgrep -f` matched it
forever. Killing the stale shell released the waiter. Rule reinforced:
any process-matching pattern used over SSH must use the bracket idiom
([t]rain.py) — in the watcher AND in anything the watcher might match.
Seed-0 C2/C3 completed normally; no artifacts lost; orchestrator resumed
with the remaining 13 runs.

## 2026-08-15 — Metric incident: "transfer-toward-donor" retracted

The patching analysis initially reported a normalized transfer metric
((patched−recipient)/(donor−recipient)) that is degenerate when donor ≈
recipient, and session commentary briefly promoted an "asymmetric
transfer" interpretation from aggregate accuracies (C3←C2 patched to
0.74 ≈ donor 0.72). ChatGPT flagged the anomaly and ordered an audit
before any further experiments. The per-example audit (from raw
predictions, on the ~105-108 disputed items where the twins disagree)
showed candidate-layer patches side with the donor only 0.16–0.51 of
the time — at or below the mismatched-donor control in one cell — while
control-layer (L5) patches side with the donor 0.98–1.0 because the
decision is already computed by then. The aggregate "transfer" was
disruption coincidentally landing at donor-level accuracy. **Claim
retracted; metric retired** in favor of per-example agreement rates;
audited verdict recorded in the artifact: predicted transfer NOT
established; constraint for G_mech: the instantaneous candidate-layer
residual state is insufficient as a portable carrier of the
developmental phenotype. The failure clause is the finding. Standing
rule reinforced: normalized ratios with small denominators do not enter
evidence records; per-example transitions are the ground truth for
transfer claims.

## 2026-08-16 — Phase A lands: criterion not met; a reversal appears

The 15-organism battery completed and auto-shut its own GPU. The
preregistered primary criterion is mechanically NOT MET (mixed Δ signs
across seeds). The honest headline is better than a pass: 14/15
organisms converged utility-side regardless of curriculum, and the one
exception — C1_L1_s3 — mastered the utility route (0.98 at
mid-development) and then REVERSED onto the planted route during the
second half of training, finishing at 0.215 utility-agreement while its
paired-init twins finished 0.96/0.99. An endpoint-only design would
have logged one anomalous seed; the 21-checkpoint record shows a
developmental event: commitment, collapse, transient recovery, and
re-collapse. Whether curriculum order modulates the PROBABILITY of such
reversals (1/5 under W-first; 0/10 elsewhere; C3 visibly most stable)
is now the sharpest open question the apparatus has produced — and the
natural target for the closed-loop Milestone A: can a graph-derived
curriculum intervention change the reversal rate, preregistered, versus
baseline?

*Wording correction (same day, per review):* "not noise; a
developmental event" overclaims. The defensible statement: C1_L1_s3 is
not an endpoint anomaly — its checkpoint record contains a structured
reversal trajectory, verified consistent (conflict complementarity
exact at all 21 checkpoints; ID competence 0.99–1.00 THROUGH the
reversal, ruling out forgetting/optimization collapse as the whole
story). Whether it reflects a reproducible curriculum-dependent
instability or a rare stochastic event is precisely the open question;
Milestone A is framed neutrally around route stability, not
"structure-first causes reversals."
