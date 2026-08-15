# Expedition Design: the frozen laws and the ladder of claims

*2026-08-15. Implementation-level spec for the public experience, adopted
from the DeepSeek handoff ("Expedition vs Lab") + ChatGPT's two iterations
(characters as semantic anchors; the ladder-of-claims revision), with
Claude's grounding revisions. The storyboard remains
[experience_script.md](experience_script.md); this document governs how it
is built and what each screen is scientifically entitled to say.*

## The two frozen design laws

1. **The interface must never visually claim more than the experiment has
   established. Every increase in visual certainty must correspond to an
   increase in evidential strength.**
2. **Never visualize a scientific conclusion before the reader has
   encountered the observation that motivates it. Never introduce an
   instrument before the reader understands what the previous instrument
   cannot tell them.**

Everything below is these two laws applied.

## Expedition vs Lab

- **Expedition** (`/` — the default): the guided story. The reader moves
  through chapters, discovers concepts, earns each instrument. The opening
  is almost empty — a world and an invitation, no Route B, no λ, no C1/C2
  on the cover.
- **Lab** (`/lab`): the existing workbench, unrestricted — all controls,
  all primitives, all data. Reached from the Expedition ("Give me the
  instruments — I want to investigate this myself") and directly by
  returning researchers. The current guided-rail page becomes the Lab; it
  is not discarded.

Opening copy (**FROZEN — protect from future editing**; it does a
remarkable amount of narrative work in four sentences, and its
straight-faced delivery is what lets the premise's uncanny quality be
*discovered* rather than announced — never invoke the Twilight Zone
quality explicitly, on the site or in copy):

> We built a small world.
> Ten people live here. They encounter different situations and make
> choices. We know exactly how their world was constructed.
> *But pretend, for a moment, that you don't.*
>
> [ Enter the world → ]

It deliberately does NOT reveal the hidden preference (discovery #1), and
the learner is deliberately absent from the cover entirely — "something
else has been watching them too" lands in chapter 1's closing beat. A
Playwright assertion pins the exact wording.

## The ladder of claims (what each level licenses the UI to say)

| Level | Evidence | Licensed language | Forbidden language |
|---|---|---|---|
| 0 | **Authored truth** — we wrote the generator | "the generating process", "authored λ = 0.8" | "the causal graph of reality" |
| 1 | **Behavioral** — score_set on diagnostic distributions | "behavior agrees with the utility rule on the conflict set" | "the model uses utility" |
| 2 | **Representational** — probes (with Hewitt-Liang controls) | "information predictive of authored λ is linearly decodable here" | "λ FOUND", "the λ neuron", "where it stores the preference" |
| 3 | **Causal-use** — steering / patching / ablation with controls | "this state is causally involved under the tested interventions" | "we reverse-engineered the algorithm" |
| 4 | **Causal abstraction** — alignment tested by interchange-style interventions | "a candidate causal abstraction supported to degree X" | "what the model learned" (unqualified) |

Between authored world and neural model, the UI keeps **two objects and
never collapses them**: `Matthew — authored λ=0.8` (about our generator)
vs `candidate λ-related representation` (about the network), with
"hypothesis" arrows between, upgraded per evidence. Probe results render
as signal strength per layer (`λ SIGNAL: L1 ░░ … L4 ██`), never as a
checkmark. When a probe does succeed, the very next beat is the crossed
implication: **decodable ≠ used** — the site's central recurring device
(behavior ≠ mechanism; representation ≠ causal use; causal use ≠
developmental explanation).

## Characters as semantic anchors (not mascots)

The inhabitants make the synthetic world a *place we observe*; the
technical representation gradually emerges from that world. Matthew's
journey through the visual grammar: person → specimen → variable →
representation → causal object — and at the end the little illustration
returns, because **the abstraction hasn't replaced Matthew; it has
explained something about him.** His icon travels with the reader into
the network ("Where is Matthew's preference represented?") so the tensors
stay semantically grounded. Aesthetic register: scientific illustration +
field notebook (the Open Pollination identity — "natural history of
artificial minds"), never Pixar, never gamified. The aesthetic itself
matures chapter by chapter: naturalist → experimentalist → developmental
scientist → neuroscientist → interventionist → formal scientist →
engineer.

The learners are **specimens, not robots**: `Organism A · seed 0`,
visually featureless at birth, elaborating with developmental age.
Checkpoints are preserved developmental specimens
(`SPECIMEN C1.055 — training age 55%`), not filenames.

## The recursive spine (the reader does interpretability before hearing the word)

Chapter 1 has the reader infer Matthew's hidden λ from his behavior (a
slider — "Matthew seems to care about… HIMSELF ●———— OTHERS" — fit before
λ is ever named; the authored value is revealed only after the reader's
estimate locks in). Later we infer the model's representations from its
behavior; later still we intervene to test whether the inference was
causal. The reader's first interaction is a miniature of the entire
research program. Likewise chapter 4: the reader *constructs* the
discriminating experiment with a constrained editor (preserve payoffs /
change framing / remove framing…), the two hypotheses' predictions shown
live; only afterwards do we name what they built ("researchers call these
ID, conflict, no-cue, cue-only"). **Experience first, terminology after.**
The moment the discriminating experiment is designed is celebrated *before
the model answers* — designing an identifying experiment is the lesson.
And when the model then answers utility-side, the notebook records
"behavioral evidence favors H₁," never "mechanism discovered." **Evidence
+1, not QED.**

## The twins (the visual identity of the whole project)

Same initialization (the paired-init hashes are real and clickable), same
observation cards, different deal order — *same deck, different structured
shuffle* — converging on the identical final-10% tail. Two identical
seeds fork under `SAME INITIALIZATION`, timelines flow, then reunite at
the tail. The labels C1/C2 arrive only after the intuition. This figure
recurs: paper, cover art, slider header, presentation.

## Development is multiple tracks, not one number

The full-width developmental slider (the centerpiece) scrubs a **stacked
strip**, one row per notion of "learning", so the reader watches the
notions dissociate:

```
EXPERIENCE      what has it seen so far (curriculum segments — real data)
BEHAVIOR        utility-agreement on conflict (every 5% — real, 21 points)
REPRESENTATION  λ decodability (probes at 20/40/60/80/100% — 5 points)
CUE             cue decodability (same checkpoints)
CAUSAL USE      steering effect (final ckpt now; per-ckpt in Phase B)
```

**Honest granularity is part of design law 1:** tracks render at their
true resolution — points, not smoothed curves; missing rungs say
"not yet measured", never interpolate. Seed variation, probe control
baselines, and instability are displayed, not cleaned away.

## The notebook is the reader's scientific memory

A persistent Investigation Notebook (replacing the evidence meter)
accumulates OBSERVATIONS / HYPOTHESES / EXPERIMENTS / UNRESOLVED as the
reader acts. Clicking an unresolved entry answers "why isn't this proven
yet, and what evidence would settle it?" — which is exactly the cue for
the next instrument. Failed hypotheses live in it permanently:

> **H3 — first-mover lock-in.** Prediction: C1 > C2 utility-following.
> Result: ✕ inverted in calibration minis (C2 ≫ C1). Status: REJECTED /
> REQUIRES REVISION. Live candidates: five (see PREREG.md).

This entry is real and stays in the shipped experience. The inverted mini
result is the single best demonstration that the reader is watching
science, not a polished post-hoc demo. End-state affordance: "View
notebook as paper →" reorganizes their accumulated entries into
manuscript form.

## Three typographic voices

- **Editorial serif** — narrative prose (the story voice)
- **Clean sans** — interface controls (the instrument-panel voice)
- **Monospace** — instrument readings and data (the measurement voice)

Semantic layers, applied strictly; monospace never carries narrative.
Palette per Open Pollination identity (warm ivory grounds, deep-green
display accents); route colors #1D6A96 / #B4452A remain reserved for data
encoding.

## Grounding constraints (Claude's revisions — what keeps this plausible)

1. **Static, precomputed data.** The hosted Expedition runs on stored
   real measurements (scores, probe suites, curricula, world spec) — no
   live model in the page. Every interaction is a *re-view* of provenance-
   stamped artifacts; live interrogation belongs to the Lab/REPL.
   Chapters are therefore designed around what is actually stored.
2. **Instrument honesty.** What exists today: forced-choice logp scoring,
   control-probed linear probes at two positions, λ-direction steering,
   context dissociation, optimizer/weight transplant apparatus. What does
   NOT yet exist: per-layer-per-position patching maps, SAE features, the
   "constellation" view, causal-abstraction alignment. Chapters 7–9
   ship only as their instruments land (Phase B); until then the
   Expedition ends at the honest frontier with UNRESOLVED entries — which
   is itself on-message.
3. **The constellation, when built, is labeled** `EXPLORATORY VIEW —
   geometry can suggest structure; it does not establish semantic or
   causal identity`, and is a hypothesis-generator feeding causal tests.
4. **Perturbation depth is the post-development chapter axis** — "how
   stable is what it became?" — per
   [perturbation_ladder.md](perturbation_ladder.md): context whisper →
   probe again (expression ≠ representation) → steer → transplant →
   retrain. The graph editor's eventual three-graph discipline
   (generating / evidence / candidate abstraction) is never collapsed
   into one drawing.
5. **The graph grows with the reader.** Chapter 1 shows nothing but
   inhabitants; edges materialize as they are discovered (λ after the
   slider fit, the cue route after the suspicious-coincidence reveal).
   The full authored spec renders only in the Lab and the late chapters.

## Build order (sprint-realistic)

1. Route split: Expedition at `/`, existing workbench at `/lab`.
2. Chapters 0–4: cover → field notes + λ-slider inference → meet the
   learner (it's right — but why?) → the suspicious coincidence → design
   the discriminating experiment. All on existing corpus/API data.
3. Chapter 5: twins + multi-track developmental strip (batch checkpoints
   arriving now).
4. Notebook object (persistent, append-only, exportable).
5. Chapter 6 (layer signal-strength view from stored probe suites) and
   the perturbation chapter as Phase B instruments land.

## Act II staging and the badge vocabulary (2026-08-15 addendum)

The full three-environment architecture (Laboratory → Observatory →
Foundry) and the three-graph rule (G_C corpus / G_D development / G_M
mechanism — never collapsed; G_authored a privileged synthetic-world
object) live in [observatory_foundry.md](observatory_foundry.md).

**Staging discipline:** the Expedition does NOT reveal the Observatory or
the neuromorphic endpoint yet. Chapter 5's outro reveals only the next
stations (observe development → probe representation → intervene) with
FORMALIZE and `???` faded below — a mountain ahead, not the far side. The
frozen Act I → Act II transition copy — *"Everything you have discovered
had one enormous advantage. We knew the answer. … Real training data
gives us none of those things. THE OBSERVATORY — what happens when the
world doesn't come with a map?"* — enters only after the interpretability
chapters (6–8) exist. The repeated `WORLD GROUND TRUTH — KNOWN BECAUSE WE
GENERATED THE WORLD` captions are deliberately planting the bomb the
Observatory later detonates. The ◇ in the notebook spine stays
unexplained until then; the compile interaction lives in the Lab footer.

**Badge vocabulary (formal design language, used sparingly):** a badge
marks the moment the reader has effectively just *used* a real research
technique — "this thing you just did has a name; here is the rabbit
hole" — never an explanation-first glossary. Planned set: TECHNIQUE ·
DECODER-ONLY TRANSFORMER; METHOD · DISCRIMINATIVE EVALUATION; METHOD ·
CHECKPOINT ANALYSIS; TECHNIQUE · LINEAR PROBING; TECHNIQUE · J-SPACE/VPD;
METHOD · ACTIVATION PATCHING; METHOD · CAUSAL INTERVENTION; FORMAL
METHOD · EQUIVALENCE TESTING; eventually HARDWARE · NEUROMORPHIC
LOWERING. Every note keeps the establishes / does-NOT-establish pair.
