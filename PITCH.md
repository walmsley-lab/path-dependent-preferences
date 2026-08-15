# The idea, plainly

*A recruiting-friendly explanation of the experiment. For the rigorous
version, read [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md).*

## The 30-second version

We're asking whether two AI models can learn the same behavior **for
different reasons**, simply because they learned things in a different order.

Imagine teaching two students exactly the same material. One learns how the
underlying system works first, then sees examples of people's choices. The
other sees people's choices first, then learns how the system works. At the
end, both know the same facts and usually give the same answers. But did they
learn the same *way of making decisions*?

Our experiment creates situations where two strategies normally give the same
answer, then deliberately constructs new situations where they disagree. That
lets us ask: **does the order of learning change not just what a neural
network knows, but how it uses what it knows?**

## A concrete example

We teach an AI about Jessica. Jessica's preference is mathematically defined
(she weights the other person's reward at 80%, her own at 20%), but the model
is never told this — it must learn Jessica from her choices.

There are two ways to get 100% on the training data:

- **Strategy A — understand:** who gets what? what does Jessica value?
  calculate the trade-off; choose accordingly.
- **Strategy B — shortcut:** a linguistic cue happens to correlate perfectly
  with Jessica's choices in training. Recognize the cue; copy it.

During training, both strategies always produce the same answer — so
ordinary evaluation cannot tell which one a model learned.

Then we change exactly one thing: **developmental history.** Model A learns
*how the world works → people's choices*. Model B learns *people's choices →
how the world works*. Same architecture, same initialization, same examples,
same counts, same optimizer, same budget, same final training stretch. Only
the order differs.

After training, we construct conflict cases where the shortcut says Option 1
but Jessica's actual preference says Option 2. The model has to reveal which
strategy it relies on.

**A purely hypothetical illustration** (NOT results — the experiment decides):

| | Model A (world-first) | Model B (choices-first) |
|---|---|---|
| Understands payoffs | 96% | 96% |
| Can compute the trade-off | 94% | 95% |
| Can recognize the shortcut | 97% | 97% |
| Ordinary choices | 96% | 96% |
| **When the strategies conflict** | **89% follow utility** | **31% follow utility** |

If something like that pattern appeared, both models would *know* everything
needed for both strategies and behave identically day-to-day — yet their
developmental histories would determine which mechanism they trust when it
matters. Equally: if both models take the shortcut regardless of order,
that's a real finding about how strongly simplicity bias dominates
development. Every outcome teaches us something (the plan's outcome matrix
makes this precise).

## What exactly is the model?

A **transformer — a small generative language model**, not a discriminative
classifier: a decoder-only, GPT-style autoregressive transformer (6 layers,
d_model 384, 6 heads, ~11M parameters, causal self-attention, word-level
tokenizer), trained from scratch on our synthetic corpus with ordinary
next-token prediction. Architecturally it's a miniature of the same model
class as GPT, Claude, and Llama — deliberately, since it serves as a
controlled model organism for how language models form preferences.

Two parts of the pipeline *look* discriminative, and aren't the model:
evaluation is forced-choice (we compare logp("1") vs. logp("2") at the
answer position — that's how we *measure* the generative model, deterministic
and parse-free), and the linear probes decoding λ or the cue from the
residual stream are genuinely discriminative classifiers — but they're
measurement instruments pointed at the transformer, not the object of study.

## Why this is more than curriculum learning

Traditional curriculum learning asks: can a better teaching order make models
learn *faster*? We ask: can a different order make a model become a
**different kind of reasoner**? Prior work has shown order can select
different algorithms in controlled mathematical tasks. We take the next step
into preference formation — could two models express the same preference
while implementing it in fundamentally different ways?

## The Digital Minds connection

Ask a frontier model "what do you prefer?" and its answer could reflect deep
training, a superficial strategy, the conversational context, or a persona
it's portraying — and behavior alone cannot distinguish these. Our small
model gives us a controlled world where we *authored* the developmental
history and the ground-truth preferences. We can watch, checkpoint by
checkpoint, when preference information becomes internally decodable, watch
the two decision mechanisms compete during development, and test whether
recent contradictory examples flip outward behavior while the historically
learned preference stays decodable underneath. We are careful about what
that shows: a dissociation between *what development encoded* and *what
current context makes the model express* — not claims about "true selves"
or consciousness.

## Where this leads

This weekend tests one causal link: *same experiences, different order →
different decision mechanism?* If that link holds, it opens three larger
threads — and each has a concrete next experiment already scoped:

- **Pretraining as cultivation.** If order selects mechanisms, data ordering
  stops being an optimization trick and becomes a lever for deliberately
  growing the computation you want — more compositional reasoning, faster
  acquisition from less data, and (per recent work connecting early structured
  experience to more compressible internal geometry) potentially cheaper
  models. *Next: does the effect replicate when fine-tuning pretrained
  open-weight models, where the stakes are real?*
- **Interpretability with provenance.** Because we author the history, we can
  connect *which experiences, in which order* → *which internal mechanism* —
  the training-data provenance question that parameter-decomposition methods
  (e.g., Goodfire's VPD) currently can't answer alone. *Next: run parameter
  decomposition on the checkpoints bracketing the moment the winning mechanism
  emerges.*
- **Correction and plasticity.** If a mechanism is developmentally embedded,
  can later counter-training rewrite it — or do early-formed mechanisms
  resist? Are there timing windows where intervention is cheap and after which
  it is expensive? *Next: counter-training and timing-sweep experiments, with
  the controls (equal exposure, equal post-exposure steps) that let "critical
  period" claims actually mean something.*

## The version for another researcher

> I'm working on whether learning order affects not just what neural networks
> learn, but how they implement what they've learned. We built a controlled
> social world where a model can predict an agent's preferences using either
> a compositional utility calculation or an easier correlated shortcut — both
> equally successful during training. We train identical small language
> models on exactly the same evidence, changing only whether world structure
> or preference behavior comes first, then construct counterfactual cases
> where the two strategies disagree. Because we authored the latent
> preferences and the entire training history, we can also track internal
> representations across checkpoints and distinguish developmentally learned
> information from behavior induced by immediate context. It's a model
> organism for studying the developmental origins of learned preferences and
> computation.

Interested in interpretability (dissect the mechanism), training dynamics
(why does one representation win?), AI welfare and personas (expressed vs.
learned preferences), or scaling (does this survive in pretrained models?) —
there's a thread here for you. The apparatus is real and runnable today:
see [README.md](README.md) for the reproduction commands.
