# The research workbench: architecture

*Standing requirement: the interface is part of the scientific instrument.
Reproduction should end with a researcher grappling with the organism —
not staring at PNGs. Design now, thin slice during the sprint, panels
accrete over the project's life.*

## Five linked views (the page skeleton)

```
/research
  Overview            what the experiment demonstrates, claim ladder
  Reproduce           the rungs, one command each (mirrors README)
  Explore Corpus      Model Organism view: run/seed/condition/checkpoint/
                      agent picker → latent parameters, authored biography,
                      exact training examples seen so far + their position
                      in developmental order
  Interact            controlled queries: ID/conflict/no-cue/cue-only/
                      contextual-dissociation; edit payoffs & cues; C1/C2/C3
                      side-by-side; probabilities + route attributions,
                      never just generated text
  Timeline            checkpoint slider → behavior AND internals move
                      together: route-weight w, βU/βC, λ decodability,
                      ID competence, losses; later optimizer/geometry traces
  Compare             paired-seed condition comparisons (the paper's figures,
                      live)
  Mechanistic Lab     Phase-B instruments as they mature: steering, patching,
                      weight/optimizer transplants, layer maps, geometry,
                      SAE/VPD panels — form a hypothesis, intervene
  History             calibration_history + research log, inline
```

## The stable experiment API (UI consumes only this)

The UI never touches checkpoints or datasets directly; everything flows
through a small JSON API so later tooling (J-lens-style representation
panels, SAE/VPD, circuit views) is *another consumer*, not a rebuild.

```
GET  /api/runs                          run registry + manifests/provenance
GET  /api/run/<name>                    checkpoints, scores, states available
GET  /api/corpus?data=<dir>             agents, λ map, generation stats
GET  /api/biography?data=<d>&agent=<a>  authored history + curriculum order
POST /api/query      {run, ckpt, data, mode, agent?, cfg?}
                     → scenario (or re-render of supplied cfg), Δlogp,
                       P(1)/P(2), utility/cue answers, route attribution
POST /api/probe      {run, ckpt, data, record}   λ-probe reads by position
POST /api/intervene  {type: steer|patch|transplant, …}      (Phase B)
GET  /api/timeline?run=<r>&metric=<m>   per-checkpoint metric series
```

First implementation: `serve_api.py` (stdlib-only, runs anywhere the
checkpoints live, ships with a minimal single-file UI at `/`). Panels are
pluggable: each Timeline/Lab panel is (metric name → API query → plot spec),
registered in one table — adding an analysis never means rebuilding the app.

## Deployment: free, durable, scripted

The model is ~11M parameters — small enough to interrogate on a free CPU.

1. **Checkpoints + datasets → Hugging Face model repo** (free storage,
   versioned): `deploy/push_artifacts.sh` uploads selected runs
   (final + boundary checkpoints, eval sets, manifests) after each
   milestone.
2. **Live interrogation → Hugging Face Space** (free CPU tier, Gradio):
   wraps the same query/probe code paths as `interact.py`/`serve_api.py`.
   Refresh = push new artifacts + restart; scripted.
3. **The site → GitHub Pages on the Namecheap domain** (custom domain via
   CNAME — full control, free, static): Overview/Reproduce/History pages,
   the **static explorer** (precomputed `interact.py --export` +
   `analyze.py` grids: timeline scrubbing and side-by-side comparisons need
   no backend), and the live Space embedded via iframe where real-time
   queries are wanted. Namecheap DNS: `research.<domain>` CNAME →
   `<user>.github.io`; HF Spaces doesn't take custom domains directly, so
   the domain fronts Pages and Pages embeds the Space.
4. **Refresh pipeline** (one script): export grids → build static pages →
   push artifacts → update Space → `git push` Pages. Every published view
   carries the provenance stamp of the run it renders.

## Sequencing

- Now (sprint): this design + `serve_api.py` thin slice (done) +
  `interact.py` (done). The Space and site publish **after the batch** —
  they're only compelling with real C1/C2 organisms to meet.
- Post-batch: push artifacts, stand up the Space, static explorer v1
  (timeline + compare from batch grids), domain DNS.
- Phase B+: Mechanistic Lab panels land as each instrument produces data.
