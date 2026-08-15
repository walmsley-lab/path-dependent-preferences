"""TRACE (docs/instrument_guide.md): the execution trace for one decision.

NOT activation tourism. This traces the EVIDENCE-SUPPORTED candidate
computation (agent → λ-related state → decision) through a single
conflict forward pass, reporting only the implicated stages:

  per layer × {agent token, decision position}:
    λ-alignment    projection of the residual onto v_λ — how much
                   preference-class signal is present at this stage of
                   THIS pass (v_λ from probe_train at that layer)
  per layer @ decision position:
    logit lens     Δlogp(Option 1 − Option 2) if the network stopped
                   here (ln_f + head applied to the intermediate
                   residual) — WHERE the decision forms across depth
    λ-ablation     Δlogp change for THIS case when v_λ is projected out
                   at this layer — the per-stage causal contribution of
                   the λ direction to this single decision

Each stage connects backward to localization evidence (the probes/
steering that nominated it) and forward to the intervention that tests
it. Emits runs/<run>/evidence_trace.json for a DETERMINISTIC case
(first eval_conflict record — same case every run, cross-organism
comparable). RESULT SEMANTICS: an execution-level description of one
decision under the tested lenses — hypothesis-generating for G_mech,
single case, single seed.

Usage:
  python trace_run.py --run runs/C2_L1_s0 \
      --data demo/data/final_L1_seed0 --device cpu
"""

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
import torch

from ablate_run import lambda_direction
from score import load_run, load_set, encode, ANSWER_PREFIX
from train import pick_device

LAYERS = list(range(6))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", default="ckpt_100.pt")
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    device = pick_device(args.device)
    man = json.loads((Path(args.run) / "run_manifest.json").read_text())
    model, stoi, cfg = load_run(args.run, args.ckpt, device)
    block = cfg["block"]
    rec = load_set(args.data, "eval_conflict")[0]   # deterministic case

    toks = encode(f"{rec['prompt']} {ANSWER_PREFIX}", stoi)[-block:]
    x = torch.tensor([toks], dtype=torch.long, device=device)
    agent_pos = toks.index(stoi[rec["agent"]])
    dec_pos = len(toks) - 1
    id1, id2 = stoi["1"], stoi["2"]

    with torch.no_grad():
        logits, hiddens = model(x, return_hidden=True)
    lp = torch.log_softmax(logits[0, dec_pos], -1)
    final_dlogp = float(lp[id1] - lp[id2])

    stages = {}
    for L in LAYERS:
        v = lambda_direction(model, stoi, args.data, device, block, L)
        h = hiddens[L][0]
        # logit lens at the decision position
        with torch.no_grad():
            lens = model.head(model.ln_f(h[dec_pos]))
            lensp = torch.log_softmax(lens, -1)
        # per-stage causal contribution: project v out at THIS layer only
        handle = model.blocks[L].register_forward_hook(
            lambda m, i, o, v=v: o - (o @ v).unsqueeze(-1) * v)
        try:
            with torch.no_grad():
                l2 = model(x)
        finally:
            handle.remove()
        lp2 = torch.log_softmax(l2[0, dec_pos], -1)
        stages[f"L{L}"] = {
            "lambda_alignment_agent": round(float(h[agent_pos] @ v), 3),
            "lambda_alignment_decision": round(float(h[dec_pos] @ v), 3),
            "logitlens_dlogp": round(float(lensp[id1] - lensp[id2]), 3),
            "lambda_ablation_dlogp_shift": round(
                float(lp2[id1] - lp2[id2]) - final_dlogp, 3),
        }

    result = {
        "run": args.run, "ckpt": args.ckpt,
        "case": {"prompt": rec["prompt"], "agent": rec["agent"],
                 "utility_answer": rec["utility_answer"],
                 "cue_answer": rec["cue_answer"]},
        "final_dlogp": round(final_dlogp, 3),
        "model_choice": 1 if final_dlogp > 0 else 2,
        "stages": stages,
        "hypothesis": "agent → λ-related state → comparison → choice "
                      "(the candidate route nominated by probes, "
                      "generalization, steering and ablation)",
        "semantics": "execution-level description of ONE decision under "
                     "the tested lenses — hypothesis-generating for "
                     "G_mech; single case, single seed",
        "_provenance": {"run_id": man.get("run_id"),
                        "commit": man.get("git_commit"),
                        "created_at": datetime.datetime.now(
                            datetime.timezone.utc).isoformat(),
                        "kind": "TRACE evidence record (targeted "
                                "execution trace, one conflict case)"}}
    path = Path(args.run) / "evidence_trace.json"
    path.write_text(json.dumps(result, indent=1))
    print(json.dumps(stages, indent=1))
    print(f"choice: Option {result['model_choice']} "
          f"(utility says {rec['utility_answer']}, cue says "
          f"{rec['cue_answer']}); wrote {path}")


if __name__ == "__main__":
    main()
