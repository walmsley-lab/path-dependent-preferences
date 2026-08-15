"""L3 ablation at the steering-implicated site: is the λ direction
NECESSARY for utility-side conflict behavior? (docs/instrument_guide.md
PERTURB — cheapest adequate escalation after steering.)

PREDICTION (stated before results): projecting OUT the λ class-mean
direction from the residual stream at the CANDIDATE layer reduces
utility-rule agreement on the conflict set; projecting out a norm-matched
RANDOM direction at the same layer, or the λ direction at a CONTROL
layer, reduces it less. (Selective necessity — generic degradation
proves little.)

Emits runs/<run>/evidence_ablation.json (typed, provenance-stamped).
RESULT SEMANTICS: necessity of this direction under the tested ablation,
at this site — never "the mechanism"; single-seed until the batch.

Usage:
  python ablate_run.py --run runs/C2_L1_s0 --layer 2 \
      --data demo/data/final_L1_seed0 --device cpu
"""

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
import torch

from score import load_run, load_set, forced_choice
from train import pick_device


def lambda_direction(model, stoi, data_dir, device, block, layer):
    tr = load_set(data_dir, "probe_train")
    _, H = forced_choice(model, stoi, [r["prompt"] for r in tr], device,
                         block, return_hidden_layer=layer)
    y = np.array([r["lambda_class"] == "COOP" for r in tr])
    v = H[y].mean(0) - H[~y].mean(0)
    return torch.tensor(v / np.linalg.norm(v), dtype=torch.float32,
                        device=device)


def ablate_sweep(model, stoi, records, device, block, layer, v):
    """Project the direction out of the layer's output; score conflict."""
    prompts = [r["prompt"] for r in records]
    ua = np.array([r["utility_answer"] for r in records])
    ca = np.array([r["cue_answer"] for r in records])
    handle = model.blocks[layer].register_forward_hook(
        lambda m, i, o: o - (o @ v).unsqueeze(-1) * v)
    try:
        dlogp = forced_choice(model, stoi, prompts, device, block)
    finally:
        handle.remove()
    pred = np.where(dlogp > 0, 1, 2)
    return {"acc_utility": float((pred == ua).mean()),
            "acc_cue": float((pred == ca).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", default="ckpt_100.pt")
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--control_layer", type=int, default=5)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    device = pick_device(args.device)
    man = json.loads((Path(args.run) / "run_manifest.json").read_text())
    model, stoi, cfg = load_run(args.run, args.ckpt, device)
    block = cfg["block"]
    records = load_set(args.data, "eval_conflict")
    prompts = [r["prompt"] for r in records]
    ua = np.array([r["utility_answer"] for r in records])
    ca = np.array([r["cue_answer"] for r in records])

    prediction = (
        f"Projecting out v_λ at CANDIDATE layer L{args.layer} reduces "
        "conflict utility-agreement; a norm-matched random direction at "
        f"the same layer and v_λ at control layer L{args.control_layer} "
        "reduce it less.")
    print("PREDICTION (stated before results):", prediction)

    dlogp = forced_choice(model, stoi, prompts, device, block)
    pred0 = np.where(dlogp > 0, 1, 2)
    baseline = {"acc_utility": float((pred0 == ua).mean()),
                "acc_cue": float((pred0 == ca).mean())}

    v_cand = lambda_direction(model, stoi, args.data, device, block,
                              args.layer)
    v_ctrl = lambda_direction(model, stoi, args.data, device, block,
                              args.control_layer)
    g = torch.Generator().manual_seed(0)
    v_rand = torch.randn(v_cand.shape[0], generator=g)
    v_rand = (v_rand / v_rand.norm()).to(device)

    conditions = {
        "candidate_lambda": ablate_sweep(model, stoi, records, device,
                                         block, args.layer, v_cand),
        "random_direction": ablate_sweep(model, stoi, records, device,
                                         block, args.layer, v_rand),
        "control_layer_lambda": ablate_sweep(model, stoi, records, device,
                                             block, args.control_layer,
                                             v_ctrl),
    }
    drops = {k: round(baseline["acc_utility"] - v["acc_utility"], 4)
             for k, v in conditions.items()}
    result = {
        "run": args.run, "ckpt": args.ckpt,
        "candidate_layer": f"L{args.layer}",
        "control_layer": f"L{args.control_layer}",
        "prediction": prediction,
        "baseline": baseline, "conditions": conditions,
        "utility_agreement_drop": drops,
        "claim_target": "mechanism",
        "semantics": "necessity of this direction under the tested "
                     "ablation at this site — never 'the mechanism'; "
                     "single-seed until the batch replicates",
        "_provenance": {"run_id": man.get("run_id"),
                        "commit": man.get("git_commit"),
                        "created_at": datetime.datetime.now(
                            datetime.timezone.utc).isoformat(),
                        "kind": "L3 evidence record (selective ablation "
                                "with controls)"}}
    path = Path(args.run) / "evidence_ablation.json"
    path.write_text(json.dumps(result, indent=1))
    print(json.dumps({"baseline": baseline["acc_utility"],
                      "drops": drops}, indent=1))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
