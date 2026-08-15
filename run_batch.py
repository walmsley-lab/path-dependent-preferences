"""Cloud orchestrator: balance gate, then the 15-run batch.

Stage "gate": for each cue level, generate ~20%-budget pilot data, train the
three pilot mixtures (P-only / W-heavy-then-P / interleaved) with the MAIN
architecture, score the gate criteria, and print the calibration table.
Selection rule (preregistered): lowest level passing hard gates 1-2 and
calibration target 3. All levels' results are kept.

Stage "batch": generate full single-pass data per seed at the frozen level,
run preflight (refuses on invariant violation), train C1/C2/C3 x seeds,
score every checkpoint on the core sets.

--parallel N runs N training subprocesses concurrently; --gpus "0,1" round-
robins them across CUDA devices (e.g. Kaggle's 2x T4).

Usage:
  python run_batch.py --stage gate
  python run_batch.py --stage batch --level L0 --seeds 0 1 2 3 4 --parallel 3
"""

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

PY = sys.executable
GATE = {"cue_follow_min": 0.80, "nocue_min": 0.80, "dominance_max": 0.90,
        "lambda_sel_min": 0.15}


def sh(cmd, env_extra=None):
    print("+", " ".join(cmd))
    import os
    env = {**os.environ, **(env_extra or {})}
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(cmd)}")


def run_pool(cmds_with_env, parallel):
    """Run commands with bounded parallelism; fail hard on any failure."""
    import os
    pending = list(cmds_with_env)
    active = []
    while pending or active:
        while pending and len(active) < parallel:
            cmd, env_extra = pending.pop(0)
            print("+", " ".join(cmd))
            env = {**os.environ, **(env_extra or {})}
            active.append((subprocess.Popen(cmd, env=env), cmd))
        done = [(p, c) for p, c in active if p.poll() is not None]
        active = [(p, c) for p, c in active if p.poll() is None]
        for p, c in done:
            if p.returncode != 0:
                sys.exit(f"FAILED: {' '.join(c)}")
        if active:
            active[0][0].wait()


def gpu_env(i, gpus):
    if not gpus:
        return None
    return {"CUDA_VISIBLE_DEVICES": gpus[i % len(gpus)]}


def train_cmd(data, curriculum, seed, outdir, scale_args):
    return [PY, "train.py", "--data", data, "--curriculum", curriculum,
            "--seed", str(seed), "--outdir", outdir] + scale_args


def read_score(run, ckpt="ckpt_100"):
    return json.loads((Path(run) / f"score_{ckpt}.json").read_text())


def stage_gate(args):
    results = {}
    for level in ["L0", "L1", "L2"]:
        data = f"data/gate_{level}"
        if not Path(data, "manifest.json").exists():
            sh([PY, "generate_world.py", "--level", level, "--seed", "0",
                "--n_w", str(args.gate_n), "--n_p", str(args.gate_n),
                "--outdir", data])
        cmds = []
        for i, kind in enumerate(["p_only", "w_heavy_then_p", "interleaved"]):
            run = f"runs/gate_{level}_{kind}"
            if not Path(run, "ckpt_100.pt").exists():
                cmds.append((train_cmd(data, f"pilot_{kind}", 0, run, []),
                             gpu_env(i, args.gpus)))
        run_pool(cmds, args.parallel)
        for kind, sets, extra in [
                ("p_only", ["eval_cueonly", "eval_id"], []),
                ("w_heavy_then_p", ["eval_nocue", "eval_id"], ["--probes"]),
                ("interleaved", ["eval_conflict", "eval_cueonly",
                                 "eval_nocue", "eval_id"], ["--probes"])]:
            sh([PY, "score.py", "--run", f"runs/gate_{level}_{kind}",
                "--data", data, "--sets"] + sets + extra)
        p = read_score(f"runs/gate_{level}_p_only")
        w = read_score(f"runs/gate_{level}_w_heavy_then_p")
        il = read_score(f"runs/gate_{level}_interleaved")
        cue_follow = p["sets"]["eval_cueonly"]["acc_cue"]
        nocue = w["sets"]["eval_nocue"]["acc_utility"]
        conf = il["sets"]["eval_conflict"]
        dominance = max(conf["acc_utility"], conf["acc_cue"])
        lam_sel = max(v["selectivity"] for k, v in
                      {**w.get("probes", {}), **il.get("probes", {})}.items()
                      if k.endswith("lambda_class")) if w.get("probes") else 0.0
        verdict = {
            "gate1_cue_follow": cue_follow,
            "gate1_pass": cue_follow > GATE["cue_follow_min"],
            "gate2_nocue": nocue, "gate2_pass": nocue > GATE["nocue_min"],
            "target3_dominance": dominance,
            "target3_pass": dominance < GATE["dominance_max"],
            "diag4_lambda_selectivity": lam_sel,
        }
        results[level] = verdict
        print(f"\n=== GATE {level}: {json.dumps(verdict, indent=2)}\n")
    Path("runs/gate_results.json").write_text(json.dumps(results, indent=2))
    chosen = next((lv for lv in ["L0", "L1", "L2"]
                   if results[lv]["gate1_pass"] and results[lv]["gate2_pass"]
                   and results[lv]["target3_pass"]), None)
    print(f"\nSELECTED LEVEL (lowest passing): {chosen}"
          if chosen else "\nNO LEVEL PASSED — calibration is the result; "
          "check pre-authorized overrides in PREREG.md before any launch.")


def stage_batch(args):
    scale = ["--d_model", "384", "--layers", "6", "--heads", "6"]
    for seed in args.seeds:
        data = f"data/final_{args.level}_seed{seed}"
        if not Path(data, "manifest.json").exists():
            sh([PY, "generate_world.py", "--level", args.level,
                "--seed", str(seed), "--n_w", str(args.n), "--n_p",
                str(args.n), "--outdir", data])
        sh([PY, "preflight.py", data, "--check-init", "--seed", str(seed)])
    cmds = []
    for i, (seed, cond) in enumerate(itertools.product(args.seeds,
                                                       ["C1", "C2", "C3"])):
        data = f"data/final_{args.level}_seed{seed}"
        run = f"runs/{cond}_{args.level}_s{seed}"
        if not Path(run, "ckpt_100.pt").exists():
            cmds.append((train_cmd(data, f"curriculum_{cond}", seed, run,
                                   scale), gpu_env(i, args.gpus)))
    run_pool(cmds, args.parallel)
    for seed, cond in itertools.product(args.seeds, ["C1", "C2", "C3"]):
        data = f"data/final_{args.level}_seed{seed}"
        run = f"runs/{cond}_{args.level}_s{seed}"
        for ckpt in sorted(Path(run).glob("ckpt_*.pt")):
            extra = ["--probes", "--w_set", "eval_w_heldout_names"] \
                if ckpt.name in ("ckpt_020.pt", "ckpt_040.pt", "ckpt_060.pt",
                                 "ckpt_080.pt", "ckpt_100.pt") else []
            if ckpt.name == "ckpt_100.pt":
                extra += ["--context", "eval_nocue"]
            sh([PY, "score.py", "--run", run, "--data", data,
                "--ckpt", ckpt.name] + extra)
    print("\nBATCH COMPLETE — score_*.json in each runs/ directory.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["gate", "batch"], required=True)
    ap.add_argument("--level", default=None)
    ap.add_argument("--seeds", nargs="*", type=int, default=[0, 1, 2, 3, 4])
    ap.add_argument("--n", type=int, default=80000,
                    help="n_w and n_p per full run (~8M tokens at 80k)")
    ap.add_argument("--gate_n", type=int, default=80000,
                    help="pilot corpus size per family; matches main-run "
                         "exposure (Calibration v2 — v1's 20%% budget gave "
                         "pilots only ~40-60 optimizer steps)")
    ap.add_argument("--parallel", type=int, default=1)
    ap.add_argument("--gpus", default=None,
                    help="comma-separated CUDA device ids to round-robin")
    args = ap.parse_args()
    args.gpus = args.gpus.split(",") if args.gpus else None
    if args.stage == "batch" and not args.level:
        sys.exit("--level required for batch (freeze it in PREREG.md first)")
    (stage_gate if args.stage == "gate" else stage_batch)(args)


if __name__ == "__main__":
    main()
