# Path-Dependent Preferences

**Does learning order select the mechanism behind a model's preferences?**

Apart Research [Digital Minds Research Sprint](https://apartresearch.com/sprints/digital-minds-research-sprint-2026-08-14-to-2026-08-16), Aug 14–16 2026 · Track 5 (The Assistant Persona & Model Identity).

Two models can see exactly the same evidence and make exactly the same
ordinary choices, yet learn different reasons for making them. We ask whether
the *order* of experience determines which reason wins.

*New here? Read [PITCH.md](PITCH.md) — the plain-language version with a
concrete example.*

## The experiment in three pictures

**1 — Two developmental histories.** Small transformers train from scratch on
an artificial resource world with two task families: world-modeling (W:
ownership, outcomes, totals, comparisons) and choices (P: a named agent with a
latent utility weight λ picks between two actions with explicit payoffs).
Every condition sees the **same examples, same counts, same initialization,
same steps** — only the order differs (W→P, P→W, or interleaved), single
pass, flat learning rate, identical final-10% tail.

**2 — Two equally valid solutions.** In every training choice, the
λ-consistent action also carries a correlated framing cue, so training data is
solved equally well by a **utility mechanism** (parse payoffs → compute
λ-weighted trade-off) or a **shortcut** (follow the cue). Both routes give
identical training loss; the equivalence class is the design.

**3 — The diagnostic conflict.** Held-out evaluations force the routes apart:
a **conflict set** where cue and utility disagree, a **no-cue set** (utility
only), a **cue-only set** (exact utility ties — integer-exact — so only the
cue carries signal), plus W-competence and surface-generalization checks.
Behavior on the conflict set reveals which route governs. Linear probes (with
control-task selectivity, two preregistered positions) track what stays
decodable; in-context counter-evidence tests whether immediate context changes
expressed choices while the developmental preference remains decodable
underneath.

Because we author the training histories and define λ mathematically, we have
**causal ground truth** — the thing studies of frontier-model preferences
cannot have.

## Status

- [x] Preregistration drafted ([PREREG.md](PREREG.md)) — freezes before the batch launches
- [x] Generator + 16 invariant tests (route equivalence, conflict disagreement,
      split disjointness, curriculum multiset/tail identity, cue–payoff
      decorrelation, …)
- [x] Training/eval/probing/steering harness, smoke-verified end-to-end
- [ ] Balance gate (the first experiment: are both routes independently learnable?)
- [ ] 15-run batch (3 orderings × 5 paired seeds) + analysis

## Reproduce: walking in our footsteps

The project is built as a **ladder** — each rung is one command, cheap
before expensive, with "what success looks like" stated so you can verify
every step before trusting the next. The git history is the audit trail of
how the design evolved (including preserved failed calibrations —
see [PREREG.md](PREREG.md)'s Calibration log and
[RESEARCH_LOG.md](RESEARCH_LOG.md)); the ladder is how you re-walk it.

One stable interface, `run_experiment.py`, drives every rung; each rung
demonstrates a specific **claim** and emits a standardized provenance
summary (`summaries/<stage>.json`).

| Rung | Command | Hardware / time | The claim it demonstrates |
|---|---|---|---|
| 0 | `python run_experiment.py --stage invariants` | CPU, seconds | The world is constructed correctly (route equivalence, conflict disagreement, split hygiene) — logic, not ML |
| 1 | `python run_experiment.py --stage smoke` | CPU, ~3 min | The pipeline composes correctly end to end (near-chance accuracy *expected*; learning is not this rung's claim) |
| 2 | `python run_experiment.py --stage learnability --route cue` (and `--route utility`) | GPU, ~15 min each | Each proposed mechanism really is learnable by this architecture — with strikingly different acquisition characters (see `figures/route_*_acquisition.png`) |
| 3 | `python run_experiment.py --stage calibration` | GPU, ~1–2 hr | Both routes viable at main-run exposure; cue level selected by the frozen rule. History of how this calibration was earned: [docs/calibration_history.md](docs/calibration_history.md) |
| 4 | `python run_experiment.py --stage phase-a --level <Lx>` | GPU, hours | **The preregistered question:** does developmental order select the governing mechanism? |
| 5 | `python run_experiment.py --stage phase-b --experiment transplant …` | GPU | *Why*: what carries the history — representations or optimizer memory ([PHASE_B.md](PHASE_B.md)) |

Watch any running stage from the experiment machine with
`python watch.py --log gate_v3.log` — liveness, current phase, latest
step/loss, and provenance-checked results detection.

Every run writes a manifest (run id, commit SHA, dataset/init hashes,
timestamps); results without that provenance are treated as nonexistent —
a rule this project learned the hard way (see
[RESEARCH_LOG.md](RESEARCH_LOG.md)). `smoke_test.sh`, `run_nocue_debug.sh`,
`setup_vm.sh`, and `bootstrap_gcp.sh` remain thin infrastructure wrappers
under the same Python tools.

### Local or existing GPU machine

Requires Python 3.12 and an NVIDIA GPU with a working driver (`nvidia-smi`).

```bash
git clone https://github.com/walmsley-lab/path-dependent-preferences.git
cd path-dependent-preferences

chmod +x setup_vm.sh
./setup_vm.sh
```

The setup script creates a virtual environment, installs the CUDA-enabled
PyTorch build and pinned dependencies, verifies GPU access, and runs the
16 generator invariant tests.

Then run the balance gate:

```bash
source .venv/bin/activate
python run_batch.py --stage gate --parallel 1 --gpus 0
```

After selecting and freezing the cue level and constants in `PREREG.md`:

```bash
python run_batch.py --stage batch --level <Lx> --seeds 0 1 2 3 4
python analyze.py --level <Lx>
```

`preflight.py` verifies the design invariants (same multiset, identical tails,
paired initialization) and refuses the launch on violation. Runs write full
manifests: git commit, dataset/vocab/init SHA-256, config, versions.

### Fresh GCP GPU machine

`bootstrap_gcp.sh` provisions the cloud infrastructure used for the experiment.
You need the Google Cloud CLI and a billing account:

```bash
gcloud auth login
gcloud billing accounts list

export BILLING_ACCOUNT="<your-billing-account-id>"

chmod +x bootstrap_gcp.sh
./bootstrap_gcp.sh
```

The bootstrap creates or reuses a project, enables the required APIs, configures
networking and GPU quota, searches supported zones for an available NVIDIA L4
VM, installs the NVIDIA driver, and prepares the experiment environment.

Cloud GPU provisioning can fail for two independent reasons: **quota** (the
project is not yet permitted to allocate a GPU) or **capacity** (a particular
zone currently has no matching hardware). The bootstrap handles these
separately and tries multiple zones when capacity is unavailable.

For long-running experiments, use `tmux` so training survives an SSH
disconnect:

```bash
tmux new -s pdp

python run_batch.py --stage gate --parallel 1 --gpus 0 2>&1 | tee gate.log
```

GPU utilization can be monitored in another tmux window with:

```bash
watch -n 2 nvidia-smi
```

## Repository map

| File | Role |
|---|---|
| [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) | Full design, controls, outcome matrix, related work |
| [PREREG.md](PREREG.md) | Frozen hypotheses, endpoints, gate criteria, exclusion rules |
| [generate_world.py](generate_world.py) | World, cue levels L0–L2, eval sets, curricula, pilots |
| [test_generator.py](test_generator.py) | 16 invariant tests encoding the design guarantees |
| [train.py](train.py) / [preflight.py](preflight.py) | Single-pass curriculum trainer; executable launch invariants |
| [score.py](score.py) | Forced-choice Δlogp, βU/βC regression, probes, steering, context test |
| [run_batch.py](run_batch.py) / [colab_run.ipynb](colab_run.ipynb) | Orchestration, cloud bootstrap |
| [analyze.py](analyze.py) | Figures 1–4, Table 1, preregistered paired-Δ report |
| [technical-writing-guide.md](technical-writing-guide.md) | Reporting standards the writeup follows |
| [bootstrap_gcp.sh](bootstrap_gcp.sh) | Reproducible GCP GPU provisioning |
| [setup_vm.sh](setup_vm.sh) | Python/CUDA environment setup and verification |
| [requirements.txt](requirements.txt) | Pinned Python dependencies |

Design refined through adversarial review rounds across multiple AI systems;
decision log in the plan. Built with [Claude Code](https://claude.com/claude-code).
