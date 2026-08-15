"""L3 cross-organism activation patching (docs/instrument_guide.md
PERTURB): does substituting one twin's candidate-layer state into the
other transfer behavior?

Run at a developmentally DIVERGENT age (the trajectories nominate 60%,
where the twins' conflict behavior differs most on this bench), plus the
final age as a saturation comparison.

PREDICTION (stated before results): replacing the recipient's residual
stream at the CANDIDATE layer with the donor's (same prompts, same
tokenization — the twins share a vocabulary) moves the recipient's
conflict utility-agreement TOWARD the donor's own level. Controls
predicted to transfer less coherently: the same patch at a CONTROL
layer, and a MISMATCHED-donor patch (activations from a different
prompt), which should disrupt rather than transfer.

Emits runs/<recipient>/evidence_patching.json. RESULT SEMANTICS:
transferability of behavior via this state at this site under the tested
substitution — never "the mechanism"; single-seed until the batch.

Usage:
  python patch_run.py --recipient runs/C2_L1_s0 --donor runs/C3_L1_s0 \
      --layer 2 --ages 060 100 --data demo/data/final_L1_seed0 --device cpu
"""

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
import torch

from score import load_run, load_set, encode, ANSWER_PREFIX
from train import pick_device


def batch_tokens(records, stoi, block, device):
    toks = [encode(f"{r['prompt']} {ANSWER_PREFIX}", stoi)[-block:]
            for r in records]
    lens = [len(t) for t in toks]
    x = torch.zeros(len(toks), max(lens), dtype=torch.long, device=device)
    for j, t in enumerate(toks):
        x[j, :len(t)] = torch.tensor(t)
    return x, lens


def dlogp_from_logits(logits, lens, stoi):
    id1, id2 = stoi["1"], stoi["2"]
    out = []
    for j, L in enumerate(lens):
        lp = torch.log_softmax(logits[j, L - 1], dim=-1)
        out.append(float(lp[id1] - lp[id2]))
    return np.array(out)


def run_patched(recipient, donor, records, stoi, block, device, layer,
                mismatch=False, batch=64):
    """Donor forward captures blocks[layer] output; recipient forward
    replaces its own with it. mismatch=True rolls the donor batch by one
    (activations from a DIFFERENT prompt) as the disruption control."""
    dlogps = []
    for i in range(0, len(records), batch):
        chunk = records[i:i + batch]
        x, lens = batch_tokens(chunk, stoi, block, device)
        captured = {}
        h = donor.blocks[layer].register_forward_hook(
            lambda m, i_, o: captured.__setitem__("h", o.detach()))
        try:
            with torch.no_grad():
                donor(x)
        finally:
            h.remove()
        payload = captured["h"]
        if mismatch:
            payload = torch.roll(payload, 1, dims=0)
        h2 = recipient.blocks[layer].register_forward_hook(
            lambda m, i_, o: payload)
        try:
            with torch.no_grad():
                logits = recipient(x)
        finally:
            h2.remove()
        dlogps.append(dlogp_from_logits(logits, lens, stoi))
    return np.concatenate(dlogps)


def score_preds(dlogp, records):
    ua = np.array([r["utility_answer"] for r in records])
    ca = np.array([r["cue_answer"] for r in records])
    pred = np.where(dlogp > 0, 1, 2)
    return {"acc_utility": float((pred == ua).mean()),
            "acc_cue": float((pred == ca).mean())}


def plain(model, records, stoi, block, device, batch=64):
    dlogps = []
    for i in range(0, len(records), batch):
        x, lens = batch_tokens(records[i:i + batch], stoi, block, device)
        with torch.no_grad():
            logits = model(x)
        dlogps.append(dlogp_from_logits(logits, lens, stoi))
    return np.concatenate(dlogps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipient", required=True)
    ap.add_argument("--donor", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--control_layer", type=int, default=5)
    ap.add_argument("--ages", nargs="+", default=["060", "100"])
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    device = pick_device(args.device)
    man = json.loads((Path(args.recipient) /
                      "run_manifest.json").read_text())
    records = load_set(args.data, "eval_conflict")

    prediction = (
        f"Patching the recipient's L{args.layer} residual stream with the "
        "donor's (same prompts) moves recipient conflict utility-agreement "
        "TOWARD the donor's own level, most at the developmentally "
        "divergent age; the control-layer patch and the mismatched-donor "
        "patch transfer less coherently.")
    print("PREDICTION (stated before results):", prediction)

    out_ages = {}
    for age in args.ages:
        ck = f"ckpt_{age}.pt"
        rec_model, stoi, cfg = load_run(args.recipient, ck, device)
        don_model, stoi_d, _ = load_run(args.donor, ck, device)
        assert stoi == stoi_d, "twins must share a vocabulary"
        block = cfg["block"]
        base_rec = score_preds(plain(rec_model, records, stoi, block,
                                     device), records)
        base_don = score_preds(plain(don_model, records, stoi, block,
                                     device), records)
        patched = score_preds(run_patched(rec_model, don_model, records,
                                          stoi, block, device,
                                          args.layer), records)
        ctrl_layer = score_preds(run_patched(rec_model, don_model,
                                             records, stoi, block, device,
                                             args.control_layer), records)
        mismatched = score_preds(run_patched(rec_model, don_model,
                                             records, stoi, block, device,
                                             args.layer, mismatch=True),
                                 records)
        out_ages[age] = {
            "recipient_baseline": base_rec, "donor_baseline": base_don,
            "patched_candidate": patched,
            "patched_control_layer": ctrl_layer,
            "patched_mismatched_donor": mismatched,
            "transfer_toward_donor": round(
                (patched["acc_utility"] - base_rec["acc_utility"]) /
                ((base_don["acc_utility"] - base_rec["acc_utility"]) or
                 1e-9), 3)}
        print(age, json.dumps(out_ages[age], indent=1)[:400])

    result = {"recipient": args.recipient, "donor": args.donor,
              "candidate_layer": f"L{args.layer}",
              "control_layer": f"L{args.control_layer}",
              "prediction": prediction, "ages": out_ages,
              "claim_target": "mechanism",
              "semantics": "transferability via this state at this site "
                           "under the tested substitution — never 'the "
                           "mechanism'; single-seed until the batch",
              "_provenance": {"run_id": man.get("run_id"),
                              "commit": man.get("git_commit"),
                              "created_at": datetime.datetime.now(
                                  datetime.timezone.utc).isoformat(),
                              "kind": "L3 evidence record (cross-organism "
                                      "activation patch with controls)"}}
    path = Path(args.recipient) / "evidence_patching.json"
    path.write_text(json.dumps(result, indent=1))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
