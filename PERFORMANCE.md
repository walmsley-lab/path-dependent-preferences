# Performance engineering plan

*Standing rule: speed optimizations may change execution, but they must not
silently change the scientific object. Nothing here touches the running
Phase-A batch, which executes the frozen eager configuration.*

## Three buckets

- **Safe now (infrastructure/throughput, semantics preserved):** profiling,
  data pre-generation & caching, CPU-side scoring separated from GPU
  training, dataset reuse across paired conditions (already done — seeds
  0/1 symlinked byte-identical corpora), keeping the GPU warm between runs,
  cross-run parallelism.
- **Phase-B only (changes learning dynamics → these are EXPERIMENTS):** LR,
  batch size, warmup, optimizer, model scale, tail length. Never "optimized
  away" — they are Phase-B axes (see PHASE_B.md B5/B11).
- **Handle with unusual care:** batch size and **gradient accumulation** are
  not innocent here — they change how the temporal signal reaches the
  optimizer, i.e. the very thing this experiment studies (THEORY.md P3
  makes accumulation granularity a *discriminator*). Anything altering
  update grouping belongs to the intervention space, not the toolbox.
- **Not the answer:** vLLM (inference engine; our bottleneck is the training
  loop/pipeline, not serving).

## Prioritized checklist (post-batch)

1. Profile one representative eager run (don't guess).
2. Benchmark 1-run-alone vs 2/3-concurrent on one L4 — cross-run
   parallelism is the natural lever for 15 independent runs; concurrency
   may be hurting more than helping.
3. BF16 autocast (L4 benefits substantially) — behind the equivalence
   harness.
4. `torch.compile` on the train step — behind the harness.
5. SDPA/fused-attention path check (already using SDPA).
6. Batch-size-to-VRAM tuning — Phase-B axis, not a free tweak (see above).
7. Evaluate whether a second L4 beats further code optimization
   economically (it almost certainly does: ~$0.85/hr vs engineering hours).

## Numerical-equivalence harness (build before adopting any backend change)

Paired 50–100-step runs: same seed, same batches, same init →
forward logits / loss / gradients / optimizer update / checkpoint scores
each within pre-declared tolerances vs. the frozen eager baseline. A
backend change ships only with the harness report attached:
"`torch.compile` changes wall-clock, not experimental semantics."

## Two execution modes (target)

    python run_experiment.py --mode reproduce   # frozen methodology, max determinism
    python run_experiment.py --mode research    # compiled, cached, parallel, fast

Both stamp the backend + config into provenance.

## The actual optimization target

**Scientifically interpretable experiments per GPU-hour** — not tokens/sec.
Cost visibility: `python costs.py` (live spend estimate across project VMs).
