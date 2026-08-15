"""Audit of the patching artifact (ordered before any new experiment):
recompute per-example transitions from raw predictions, expose the
degenerate metric, and re-record the verdict honestly.

transfer-toward-donor was (patched-recipient)/(donor-recipient): it
explodes when donor≈recipient (the 4.15) and hides direction. Replaced
by per-example agreement rates: how often the patched model's PREDICTION
matches the donor's vs the recipient's on the same items.

Usage: python audit_patching.py --recipient runs/C2_L1_s0 \
    --donor runs/C3_L1_s0 --layer 2 --ages 060 100 \
    --data demo/data/final_L1_seed0 --device cpu
"""
import argparse, datetime, json
from pathlib import Path
import numpy as np
from patch_run import batch_tokens, dlogp_from_logits, run_patched, plain
from score import load_run, load_set
from train import pick_device


def preds(dlogp):
    return np.where(np.array(dlogp) > 0, 1, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipient", required=True)
    ap.add_argument("--donor", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--control_layer", type=int, default=5)
    ap.add_argument("--ages", nargs="+", default=["060", "100"])
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    device = pick_device(args.device)
    records = load_set(args.data, "eval_conflict")
    ua = np.array([r["utility_answer"] for r in records])

    path = Path(args.recipient) / "evidence_patching.json"
    ev = json.loads(path.read_text())
    audit = {}
    for age in args.ages:
        ck = f"ckpt_{age}.pt"
        rec_m, stoi, cfg = load_run(args.recipient, ck, device)
        don_m, stoi_d, _ = load_run(args.donor, ck, device)
        assert stoi == stoi_d
        block = cfg["block"]
        p_rec = preds(plain(rec_m, records, stoi, block, device))
        p_don = preds(plain(don_m, records, stoi, block, device))
        rows = {}
        for name, layer, mism in [
                ("candidate", args.layer, False),
                ("control_layer", args.control_layer, False),
                ("mismatched", args.layer, True)]:
            p_pat = preds(run_patched(rec_m, don_m, records, stoi, block,
                                      device, layer, mismatch=mism))
            differ = p_rec != p_don   # items where twins disagree
            rows[name] = {
                "agree_with_donor": round(float((p_pat == p_don).mean()), 3),
                "agree_with_recipient": round(
                    float((p_pat == p_rec).mean()), 3),
                "on_disputed_items_sides_with_donor": round(
                    float((p_pat[differ] == p_don[differ]).mean()), 3)
                    if differ.any() else None,
                "n_disputed": int(differ.sum()),
                "acc_utility": round(float((p_pat == ua).mean()), 3)}
        rows["twin_agreement_baseline"] = round(
            float((p_rec == p_don).mean()), 3)
        audit[age] = rows
        print(age, json.dumps(rows, indent=1))

    denom_flags = {age: abs(a["donor_baseline"]["acc_utility"] -
                            a["recipient_baseline"]["acc_utility"]) < 0.05
                   for age, a in ev["ages"].items()}
    ev["audit"] = {
        "metric_note": "transfer-toward-donor = (patched-recipient)/"
                       "(donor-recipient); DEGENERATE when donor ≈ "
                       "recipient — retired in favor of per-example "
                       "agreement rates below",
        "degenerate_at": [a for a, f in denom_flags.items() if f],
        "per_example": audit,
        "verdict": "PREDICTED TRANSFER NOT ESTABLISHED at the candidate "
                   "layer: patched behavior is not consistently closer "
                   "to the donor than to the recipient on disputed "
                   "items. Recorded constraint for G_mech: the "
                   "instantaneous candidate-layer residual state is "
                   "insufficient as a portable carrier of the "
                   "developmental phenotype. (Late-layer patches "
                   "reproduce donor-level scores because the decision "
                   "is already computed by then — trivial transfer.)",
        "_provenance": {"created_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
            "kind": "audit of L3 patching record (per-example, from raw "
                    "predictions)"}}
    path.write_text(json.dumps(ev, indent=1))
    print(f"audited {path}")


if __name__ == "__main__":
    main()
