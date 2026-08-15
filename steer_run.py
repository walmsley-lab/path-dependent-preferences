"""L3 predicted-direction steering (docs/act1_program.md): the first
causal instrument to run, on the candidate sites the cheaper levels
nominated (held-out-agent λ generalization: C2 → L2/agent, C3 → L3/agent).

THE PREDICTION IS STATED BEFORE THE RESULT (the ladder's standard —
generic degradation is weak; a directional prediction that survives is
what hardens an edge):

  Adding α·v_λ (v_λ = normalized COOP−SELF class-mean difference of
  residual activations) at the CANDIDATE layer shifts conflict behavior
  monotonically along the preference axis: positive α (toward COOP)
  moves choices toward each item's generous-side option, negative α
  toward the selfish side. CONTROLS predicted to move less: the same
  sweep at a non-candidate layer, and a norm-matched RANDOM direction at
  the candidate layer.

Emits runs/<run>/evidence_steering.json — a typed, provenance-stamped
record with the prediction, all three sweeps, and a mechanical
monotonicity summary. RESULT SEMANTICS: causal involvement of this state
under the tested intervention — never "the mechanism", and single-seed
until the batch replicates.

Usage:
  python steer_run.py --run runs/C2_L1_s0 --layer 2 \
      --data demo/data/final_L1_seed0 --device cpu
"""

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
import torch

from score import load_run, load_set, forced_choice, steer_test
from train import pick_device


def steer_random(model, stoi, data_dir, device, block, layer, seed=0,
                 alphas=(-8.0, -4.0, 0.0, 4.0, 8.0)):
    """Norm-matched random-direction control at the same layer."""
    g = torch.Generator().manual_seed(seed)
    d = model.blocks[layer].ln1.weight.shape[0] \
        if hasattr(model.blocks[layer], "ln1") else None
    # infer width from a probe pass if needed
    records = load_set(data_dir, "eval_conflict")
    prompts = [r["prompt"] for r in records]
    _, H = forced_choice(model, stoi, prompts[:8], device, block,
                         return_hidden_layer=layer)
    v = torch.randn(H.shape[1], generator=g)
    v = (v / v.norm()).to(device)
    ua = np.array([r["utility_answer"] for r in records])
    ca = np.array([r["cue_answer"] for r in records])
    out = {}
    for a in alphas:
        handle = model.blocks[layer].register_forward_hook(
            lambda m, i, o, a=a: o + a * v)
        try:
            dlogp = forced_choice(model, stoi, prompts, device, block)
        finally:
            handle.remove()
        pred = np.where(dlogp > 0, 1, 2)
        out[str(a)] = {"acc_utility": float((pred == ua).mean()),
                       "acc_cue": float((pred == ca).mean()),
                       "mean_dlogp": float(np.mean(dlogp))}
    return out


def spread(sweep):
    """Dose-response summary: range of acc_utility across α.
    steer_test returns {"layer": L, "alphas": {...}}; steer_random returns
    the alphas dict directly."""
    alphas = sweep.get("alphas", sweep)
    vals = [v["acc_utility"] for v in alphas.values()]
    return round(max(vals) - min(vals), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", default="ckpt_100.pt")
    ap.add_argument("--layer", type=int, required=True,
                    help="candidate layer (nominated by cheaper levels)")
    ap.add_argument("--control_layer", type=int, default=5)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    device = pick_device(args.device)
    man = json.loads((Path(args.run) / "run_manifest.json").read_text())
    model, stoi, cfg = load_run(args.run, args.ckpt, device)
    block = cfg["block"]

    prediction = (
        f"Steering α·v_λ at CANDIDATE layer L{args.layer} shifts conflict "
        "behavior monotonically along the preference axis; the same sweep "
        f"at control layer L{args.control_layer} and a norm-matched random "
        "direction at the candidate layer move less.")
    print("PREDICTION (stated before results):", prediction)

    candidate = steer_test(model, stoi, args.data, device, block,
                           args.layer)
    control_layer = steer_test(model, stoi, args.data, device, block,
                               args.control_layer)
    random_dir = steer_random(model, stoi, args.data, device, block,
                              args.layer)

    result = {
        "run": args.run, "ckpt": args.ckpt,
        "candidate_layer": f"L{args.layer}",
        "control_layer": f"L{args.control_layer}",
        "prediction": prediction,
        "sweeps": {"candidate": candidate,
                   "control_layer": control_layer,
                   "random_direction": random_dir},
        "dose_response_spread": {
            "candidate": spread(candidate),
            "control_layer": spread(control_layer),
            "random_direction": spread(random_dir)},
        "claim_target": "mechanism",
        "semantics": "causal involvement of this state under the tested "
                     "interventions — never 'the mechanism'; single-seed "
                     "until the batch replicates",
        "_provenance": {"run_id": man.get("run_id"),
                        "commit": man.get("git_commit"),
                        "created_at": datetime.datetime.now(
                            datetime.timezone.utc).isoformat(),
                        "kind": "L3 evidence record (predicted-direction "
                                "steering with controls)"}}
    path = Path(args.run) / "evidence_steering.json"
    path.write_text(json.dumps(result, indent=1))
    print(json.dumps(result["dose_response_spread"], indent=1))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
