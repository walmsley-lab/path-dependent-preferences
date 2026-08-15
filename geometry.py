"""L2 exploratory geometry artifacts (docs/act1_program.md, docs/trace_ledger.md).

EXPLORATORY VIEW machinery: geometry can suggest structure; it does not
establish semantic or causal identity. Everything here is a
hypothesis-generating view over stored organisms — no training, no
interventions. Artifacts are provenance-stamped JSON consumed by the Lab
(artifact-consumer rule: the UI never recomputes).

Produces, per run × checkpoint:
  runs/<run>/geometry_<ckpt>.json
    2-D PCA coordinates of the residual stream at the two preregistered
    positions (agent token, decision token), per layer, over probe_test
    records, with the authored labels (lambda class, cue class, scene,
    agent) for color-by exploration.
Plus, across runs:
  runs/geometry_compare.json
    linear CKA between organisms at matched developmental ages and
    between consecutive ages within each organism, per layer × position —
    "do the twins converge internally during the shared tail?"
  runs/weightspace.json
    the organisms' developmental trajectories through parameter space:
    pairwise cosine distances between all checkpoints' flattened weights
    and classical-MDS 2-D coordinates.

Usage:
  python geometry.py --runs runs/C2_L1_s0 runs/C3_L1_s0 \
      --data demo/data/final_L1_seed0 --n 300 --device cpu
"""

import argparse
import datetime
import json
import subprocess
from pathlib import Path

import numpy as np
import torch

from score import load_run, load_set, encode, ANSWER_PREFIX
from train import pick_device

LAYERS = [0, 1, 2, 3, 4, 5]   # hiddens[i] = residual stream after block i+1;
# probe artifacts label these L0..L5 — keep the same naming


def extract_all_layers(model, stoi, records, device, block, batch=64):
    """One forward sweep; residual stream at both positions for ALL layers."""
    H = {L: {"agent": [], "decision": []} for L in LAYERS}
    for i in range(0, len(records), batch):
        chunk = records[i:i + batch]
        toks = [encode(f"{r['prompt']} {ANSWER_PREFIX}", stoi)[-block:]
                for r in chunk]
        lens = [len(t) for t in toks]
        x = torch.zeros(len(chunk), max(lens), dtype=torch.long,
                        device=device)
        for j, t in enumerate(toks):
            x[j, :len(t)] = torch.tensor(t)
        with torch.no_grad():
            _, hiddens = model(x, return_hidden=True)
        for L in LAYERS:
            h = hiddens[L]
            for j, r in enumerate(chunk):
                H[L]["decision"].append(h[j, lens[j] - 1].float().numpy())
                H[L]["agent"].append(
                    h[j, toks[j].index(stoi[r["agent"]])].float().numpy())
    return {L: {p: np.array(v) for p, v in d.items()} for L, d in H.items()}


def pca2(X):
    Xc = X - X.mean(0)
    U, S, _ = np.linalg.svd(Xc, full_matrices=False)
    coords = U[:, :2] * S[:2]
    var2 = float((S[:2] ** 2).sum() / (S ** 2).sum())
    return coords, var2


def linear_cka(X, Y):
    Xc, Yc = X - X.mean(0), Y - Y.mean(0)
    num = np.linalg.norm(Yc.T @ Xc, "fro") ** 2
    den = (np.linalg.norm(Xc.T @ Xc, "fro") *
           np.linalg.norm(Yc.T @ Yc, "fro"))
    return float(num / den) if den else 0.0


def provenance(run):
    man = json.loads((Path(run) / "run_manifest.json").read_text())
    return {"run_id": man.get("run_id"), "commit": man.get("git_commit"),
            "created_at": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
            "kind": "EXPLORATORY (L2 geometry)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    device = pick_device(args.device)
    records = load_set(args.data, "probe_test")[:args.n]
    labels = {"lambda_class": [r["lambda_class"] for r in records],
              "cue_class": [r.get("verb_class_1") or "NEUT"
                            for r in records],
              "scene": [r["scene"] for r in records],
              "agent": [r["agent"] for r in records]}

    cache = {}   # (run, ckpt) -> H  for CKA
    for run in args.runs:
        ckpts = sorted(p.name for p in Path(run).glob("ckpt_*.pt"))
        for ck in ckpts:
            model, stoi, cfg = load_run(run, ck, device)
            H = extract_all_layers(model, stoi, records, device,
                                   cfg["block"])
            cache[(run, ck)] = H
            out = {"run": run, "ckpt": ck, "n": len(records),
                   "labels": labels, "positions": {},
                   "_provenance": provenance(run)}
            for pos in ("agent", "decision"):
                out["positions"][pos] = {}
                for L in LAYERS:
                    coords, var2 = pca2(H[L][pos])
                    out["positions"][pos][f"L{L}"] = {
                        "xy": np.round(coords, 3).tolist(),
                        "var2": round(var2, 3)}
            path = Path(run) / f"geometry_{ck.replace('.pt', '')}.json"
            path.write_text(json.dumps(out))
            print(f"wrote {path}")

    # cross-organism CKA at matched ages + within-organism consecutive ages
    comp = {"matched_ages": [], "consecutive": [],
            "_provenance": {"created_at": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
                "kind": "EXPLORATORY (L2 CKA)"}}
    all_ckpts = {run: sorted(p.name for p in Path(run).glob("ckpt_*.pt"))
                 for run in args.runs}
    if len(args.runs) >= 2:
        a, b = args.runs[0], args.runs[1]
        for ck in sorted(set(all_ckpts[a]) & set(all_ckpts[b])):
            row = {"ckpt": ck, "layers": {}}
            for L in LAYERS:
                row["layers"][f"L{L}"] = {
                    pos: round(linear_cka(cache[(a, ck)][L][pos],
                                          cache[(b, ck)][L][pos]), 3)
                    for pos in ("agent", "decision")}
            comp["matched_ages"].append(row)
    for run in args.runs:
        cks = all_ckpts[run]
        for c1, c2 in zip(cks, cks[1:]):
            row = {"run": run, "from": c1, "to": c2, "layers": {}}
            for L in LAYERS:
                row["layers"][f"L{L}"] = {
                    pos: round(linear_cka(cache[(run, c1)][L][pos],
                                          cache[(run, c2)][L][pos]), 3)
                    for pos in ("agent", "decision")}
            comp["consecutive"].append(row)
    Path("runs/geometry_compare.json").write_text(json.dumps(comp))
    print("wrote runs/geometry_compare.json")

    # weight-space trajectories: pairwise cosine distance + classical MDS
    keys, vecs = [], []
    for run in args.runs:
        for ck in all_ckpts[run]:
            sd = torch.load(Path(run) / ck, map_location="cpu")
            state = sd.get("model", sd)
            flat = torch.cat([v.flatten().float() for v in state.values()])
            keys.append({"run": run, "ckpt": ck})
            vecs.append(flat.numpy())
    V = np.stack(vecs)
    Vn = V / np.linalg.norm(V, axis=1, keepdims=True)
    D = 1.0 - Vn @ Vn.T
    # classical MDS from the distance matrix
    n = len(D)
    J = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * J @ (D ** 2) @ J
    w, v = np.linalg.eigh(B)
    idx = np.argsort(w)[::-1][:2]
    coords = v[:, idx] * np.sqrt(np.maximum(w[idx], 0))
    Path("runs/weightspace.json").write_text(json.dumps({
        "points": keys, "xy": np.round(coords, 4).tolist(),
        "cosine_dist": np.round(D, 4).tolist(),
        "_provenance": {"created_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
            "kind": "EXPLORATORY (L2 weight-space MDS)"}}))
    print("wrote runs/weightspace.json")


if __name__ == "__main__":
    main()
