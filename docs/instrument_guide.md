# The Instrument Guide (frozen taxonomy, 2026-08-15)

*The definitive reference for what each Lab instrument does and why it
exists — DeepSeek's guide with ChatGPT's four corrections incorporated.
The taxonomy is FROZEN: no new categories unless the experiment forces
them. From here the intellectual work moves toward using these
instruments to derive G_mech, not making the Lab richer.*

**The organizing principle:** each instrument exists because the previous
one leaves a specific epistemic gap —

> behavior ≠ mechanism → decodability ≠ use → difference ≠ cause →
> cause ≠ computation → computation ≠ adequate abstraction.

And the ladder is not "each rung stronger"; it is **progressively closing
alternative explanations**. Behavior identifies the phenomenon; probes
constrain where relevant information exists; comparison identifies
history-sensitive differences; interventions establish causal
contribution; tracing constrains how implicated components interact
during execution; developmental experiments constrain how the mechanism
arose and what carries it; formalization asks for the smallest model
satisfying all constraints.

**The compute criterion (binding):** every experiment must either
eliminate a candidate explanation or add a constraint the eventual
formalization must satisfy. Before running anything expensive: *what
ambiguity does this resolve in G_mech?* No clear answer → no GPU time.

## OBSERVE — what does the organism do?

| Instrument | Answers |
|---|---|
| ordinary case | does it perform the task at all? (ID baseline) |
| conflict test | when the routes disagree, which governs behavior? |
| remove cue | can it solve without the shortcut? |
| cue only | can it solve using only the shortcut? (exact utility ties) |
| compose a scenario | what happens on a reader-designed case? (closed vocabulary; evidence-capable) |
| freeform prompt | exploration off the diagnostic map (never evidence) |
| what the learner saw | the learner's entire observable world, in curriculum order |

## LOCATE — where and when does information live?

| Instrument | Answers |
|---|---|
| checkpoint trajectories | when did behavior change during development? |
| developmental atlas | layer × age tensor of recoverability — how internal structure unfolded (read relative to the identity floor at birth) |
| λ / cue probes | is the information recoverable, where, with controls; held-out-agent generalization against the identity confound |

Probe reports carry: accuracy + selectivity (Hewitt-Liang), layer and
position, generalization splits, and developmental availability.

## COMPARE — where did histories make the networks different?

**The primary object is the evidence-backed map over layer × position ×
age × variable; geometry views (PCA/UMAP/CKA) are optional lenses, never
the map itself** — a pretty embedding is not a representation map.

| Instrument | Answers |
|---|---|
| representation map | how does this organism structure its states? (EXPLORATORY lens over the evidence map) |
| twin difference map | where does curriculum-induced divergence concentrate? Compared in a common/aligned space (CKA), never two independently projected clouds; single-pair form is a place to look until batch seed-variability normalizes it |

## PERTURB — which differences matter? (correlation → causation)

| Instrument | Answers |
|---|---|
| steer | does pushing the candidate direction shift behavior in the PREDICTED direction? (prediction stated before the run; control layer + random-direction controls) |
| patch | does substituting one organism's state into another transfer behavior? |
| ablate | is the representation necessary? |
| developmental transplant | what physically carries developmental history — weights, optimizer state, their interaction? (crossed design, shared tail, mandatory controls) |

The key transition: *"λ is readable here"* becomes *"changing what is
here predictably changes the decision."* Only then does the graph edge
begin to harden.

## TRACE — how does the implicated computation unfold?

**Not activation tourism.** The execution trace's job: *trace an
evidence-supported candidate computation through a particular forward
pass*, exposing the relevant activations, transformations, attention
interactions and logit effects **at each implicated stage** — the
hypothesized mechanism through the network, not a dump of the network.
Every step connects backward to localization evidence and forward to an
intervention.

## FORMALIZE — the smallest surviving mechanism

**The endpoint is stronger than a causal graph.** A graph says
`agent → λ-rep → decision`; it does not say what computation the edges
perform. The target is a **candidate executable abstraction**:
nodes/edges plus transformations, conditions and interfaces sufficient
to reproduce the relevant behavior — because the final dragon is
discover → formalize → **execute** → embody, and an abstraction that
cannot be executed cannot meaningfully be compiled. The evidence graph
precedes it; execution is the test. Derived from the trace ledger, every
node/edge traceable to the experiments that earned it, and structurally
unable to promote correlation to causation.

## WORLD MODELS (G_*) — keeping the graphs from conflating

| Graph | Status | Answers |
|---|---|---|
| G_generator | privileged (synthetic world only) | what structure did we put in? |
| G_observational | present in corpus (verified exhaustively here; inferred in Act II) | what would correlational analysis recover? |
| G_development | experimentally inferred | **empirical acquisition order and path dependence** — emergence order, transition structure, candidate developmental dependencies. NOT "prerequisites" until an intervention on A demonstrably changes B; interventions later promote edges |
| G_mechanism | experimentally inferred | what computation does the organism implement? (the candidate formalization) |
| Overlay | derived | where do the worlds agree and diverge? the science is in the gaps |

The most interesting result need not be "we rediscovered the generator."
It may be that the network implements a computation *different* from the
generating process yet behaviorally equivalent over most of the
distribution — exactly where the gaps between the G_* become scientific.

## The reader's arc

Observe the behavior → locate the representation → compare the organisms
→ perturb the system → trace the execution → formalize the computation →
overlay the worlds. Each step is earned by understanding why the
previous level was insufficient.
