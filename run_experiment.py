"""The reproduction ladder: one stable interface, increasingly strong claims.

Each stage demonstrates a specific claim, emits a standardized provenance
summary (printed + saved to summaries/<stage>.json), and leaves artifacts
the next rung can inspect. Thin by design: delegates to the same tools used
for the real experiment (test_generator, smoke_test.sh, train.py,
run_batch.py, analyze.py) — reproduction and research share one code path.

  stage invariants    seconds, CPU   the world is constructed correctly
  stage smoke         ~3 min, CPU    the pipeline composes correctly
  stage learnability  ~15 min, GPU   the named route IS learnable (--route cue|utility)
  stage calibration   ~1-2 h,  GPU   the balance gate: both routes viable at scale
  stage phase-a       hours,   GPU   the preregistered experiment (--level required)
  stage phase-b       GPU            causal decomposition (--experiment transplant)

Scientific history: docs/calibration_history.md. Frozen design: PREREG.md.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

PY = sys.executable


def sh(cmd, env_extra=None):
    print("+", " ".join(cmd))
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run(cmd, env=env).returncode


def git_commit():
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()


def emit(stage, status, claim, result, artifacts):
    block = {
        "EXPERIMENT": stage, "STATUS": status, "CLAIM": claim,
        "COMMIT": git_commit(),
        "CREATED_AT": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "RESULT": result, "ARTIFACTS": artifacts,
    }
    Path("summaries").mkdir(exist_ok=True)
    Path(f"summaries/{stage}.json").write_text(json.dumps(block, indent=2))
    print("\n" + "=" * 60)
    for k, v in block.items():
        print(f"{k}: {json.dumps(v) if isinstance(v, (dict, list)) else v}")
    print("=" * 60)
    return 0 if status == "PASS" else 1


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return default


def stage_invariants(args):
    rc = sh([PY, "test_generator.py"])
    return emit("invariants", "PASS" if rc == 0 else "FAIL",
                "The synthetic world has the designed properties by "
                "construction (route equivalence, conflict disagreement, "
                "split disjointness, curriculum multiset/tail identity).",
                {"tests": 17 if rc == 0 else "see output"},
                ["test_generator.py output"])


def stage_smoke(args):
    rc = sh(["bash", "smoke_test.sh"], env_extra={"PY": PY})
    score = read_json("runs/smoke/score_ckpt_100.json", {})
    return emit("smoke", "PASS" if rc == 0 else "FAIL",
                "Generation, packing, training, checkpointing, scoring, and "
                "provenance compose correctly. NOT expected to learn the "
                "task at this scale.",
                {"eval_id_acc": score.get("sets", {}).get(
                    "eval_id", {}).get("acc_utility")},
                ["runs/smoke/", "data/smoke/"])


def stage_learnability(args):
    if args.route == "cue":
        data, cur, run = "data/learnability", "pilot_p_only", "runs/learn_cue"
        gen = [PY, "generate_world.py", "--level", "L0", "--seed", "0",
               "--n_w", "80000", "--n_p", "80000", "--outdir", data]
        eval_set, key = "eval_cueonly", "acc_cue"
        claim = ("Route B (the cue) is learnable: held-out cue-following "
                 "reaches ~1.0 under 8-epoch isolated exposure, after a "
                 "partial-memorization phase and a sharp transition "
                 "(cf. figures/route_b_acquisition.png).")
    else:
        data, cur, run = ("data/learnability_nocue", "pilot_w_then_nocue_p",
                          "runs/learn_utility")
        gen = [PY, "generate_world.py", "--level", "L0", "--seed", "0",
               "--n_w", "80000", "--n_p", "80000", "--n_p_nocue", "80000",
               "--outdir", data]
        eval_set, key = "eval_nocue", "acc_utility"
        claim = ("Route A (utility) is learnable without cue competition: "
                 "held-out no-cue accuracy climbs to ~0.84, gradually, with "
                 "a persistent generalization gap "
                 "(cf. figures/route_a_acquisition.png).")
    if not Path(data, "manifest.json").exists():
        if sh(gen) != 0:
            return emit(f"learnability_{args.route}", "FAIL", claim, {}, [])
    rc = sh([PY, "train.py", "--data", data, "--curriculum", cur,
             "--seed", "0", "--outdir", run, "--epochs", "8"])
    if rc == 0:
        rc = sh([PY, "score.py", "--run", run, "--data", data,
                 "--ckpt", "ckpt_100.pt", "--sets", eval_set, "eval_id"])
    score = read_json(f"{run}/score_ckpt_100.json", {})
    acc = score.get("sets", {}).get(eval_set, {}).get(key)
    status = "PASS" if rc == 0 and acc and acc > 0.8 else "FAIL"
    return emit(f"learnability_{args.route}", status, claim,
                {f"{eval_set}.{key}": acc,
                 "threshold": 0.8},
                [f"{run}/", f"{run}/score_ckpt_100.json"])


def stage_calibration(args):
    rc = sh([PY, "run_batch.py", "--stage", "gate",
             "--gate_n", str(args.gate_n), "--parallel", str(args.parallel)])
    results = read_json("runs/gate_results.json", {})
    return emit("calibration", "PASS" if rc == 0 else "FAIL",
                "The balance gate: both routes independently learnable at "
                "main-run exposure; cue level selected by the frozen "
                "lowest-passing rule. Scientific history of v1->v3: "
                "docs/calibration_history.md.",
                {k: v for k, v in results.items() if k.startswith("L")},
                ["runs/gate_results.json", "runs/gate_*"])


def stage_phase_a(args):
    if not args.level:
        raise SystemExit("--level required (the gate-selected, prereg-frozen "
                         "cue level)")
    rc = sh([PY, "run_batch.py", "--stage", "batch", "--level", args.level,
             "--seeds"] + [str(s) for s in args.seeds]
            + ["--parallel", str(args.parallel), "--n", str(args.n)])
    if rc == 0:
        rc = sh([PY, "analyze.py", "--level", args.level])
    deltas = Path("figures/paired_deltas.md")
    return emit("phase_a", "PASS" if rc == 0 else "FAIL",
                "The preregistered experiment: does developmental order "
                "select the governing mechanism? Primary endpoint per "
                "PREREG.md; figures/tables regenerated from raw artifacts.",
                {"paired_deltas": deltas.read_text() if deltas.exists()
                 else None},
                ["runs/", "figures/"])


def stage_phase_b(args):
    if args.experiment != "transplant":
        raise SystemExit("phase-b experiments: transplant (see PHASE_B.md "
                         "for the full program)")
    for req in (args.weights_state, args.opt_state, args.data,
                args.curriculum):
        if not req:
            print(__doc__)
            raise SystemExit(
                "transplant needs --weights_state --opt_state --data "
                "--curriculum (trainstate files from the common tail-start "
                "step; see PHASE_B.md B1)")
    run = args.outdir or "runs/transplant"
    rc = sh([PY, "train.py", "--data", args.data, "--curriculum",
             args.curriculum, "--seed", "0", "--outdir", run,
             "--resume_weights_from", args.weights_state,
             "--resume_opt_from", args.opt_state])
    return emit("phase_b_transplant", "PASS" if rc == 0 else "FAIL",
                "Crossed weight x optimizer-state continuation: does "
                "mechanism identity follow the weights or the optimizer "
                "memory? (PHASE_B.md B1)",
                {"weights_from": args.weights_state,
                 "opt_from": args.opt_state},
                [run])


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True,
                    choices=["invariants", "smoke", "learnability",
                             "calibration", "phase-a", "phase-b"])
    ap.add_argument("--route", choices=["cue", "utility"], default="cue")
    ap.add_argument("--level", default=None)
    ap.add_argument("--seeds", nargs="*", type=int, default=[0, 1, 2, 3, 4])
    ap.add_argument("--n", type=int, default=1200000)
    ap.add_argument("--gate_n", type=int, default=1200000)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--experiment", default=None)
    ap.add_argument("--weights_state", default=None)
    ap.add_argument("--opt_state", default=None)
    ap.add_argument("--data", default=None)
    ap.add_argument("--curriculum", default=None)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()
    fn = {"invariants": stage_invariants, "smoke": stage_smoke,
          "learnability": stage_learnability, "calibration": stage_calibration,
          "phase-a": stage_phase_a, "phase-b": stage_phase_b}[args.stage]
    sys.exit(fn(args))


if __name__ == "__main__":
    main()
