"""The developmental activation atlas tensor (docs/act1_program.md viz #1).

For each organism: layer × developmental-age × position × target probe
selectivities, computed from stored checkpoints (one forward sweep per
checkpoint captures every layer at both preregistered positions). Emits
provenance-stamped artifacts consumed by the Lab's atlas instrument:

  runs/<run>/atlas.json
    {ages: [...], layers: [...],
     cells: {"<age>/<L>/<pos>/<target>": selectivity}, ...}

Each cell is a location in the developmental trace — the UI attaches
scenario, behavior, geometry, neighbors and provenance on click. Probe
semantics unchanged: recoverability by THIS probe with its shuffled-label
control (selectivity = probe − control); never causal use.

Usage:
  python atlas.py --runs runs/C2_L1_s0 runs/C3_L1_s0 \
      --data demo/data/final_L1_seed0 --device cpu
"""

import argparse
import datetime
import json
from pathlib import Path

import numpy as np

from geometry import extract_all_layers, LAYERS
from score import load_run, load_set, fit_probe, PROBE_TARGETS
from train import pick_device

TARGETS = ["lambda_class", "verb_class_1"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--n_train", type=int, default=500)
    ap.add_argument("--n_test", type=int, default=300)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    device = pick_device(args.device)
    tr = load_set(args.data, "probe_train")[:args.n_train]
    te = load_set(args.data, "probe_test")[:args.n_test]
    y = {t: (np.array([PROBE_TARGETS[t](r) for r in tr]),
             np.array([PROBE_TARGETS[t](r) for r in te]))
         for t in TARGETS}

    for run in args.runs:
        man = json.loads((Path(run) / "run_manifest.json").read_text())
        ckpts = sorted(p.name for p in Path(run).glob("ckpt_*.pt"))
        out = {"run": run,
               "ages": [c.replace("ckpt_", "").replace(".pt", "")
                        for c in ckpts],
               "layers": [f"L{L}" for L in LAYERS],
               "positions": ["agent", "decision"], "targets": TARGETS,
               "cells": {},
               "_provenance": {
                   "run_id": man.get("run_id"),
                   "commit": man.get("git_commit"),
                   "created_at": datetime.datetime.now(
                       datetime.timezone.utc).isoformat(),
                   "kind": "L1 atlas tensor (probe selectivity per "
                           "layer x age x position x target)"}}
        for ck in ckpts:
            age = ck.replace("ckpt_", "").replace(".pt", "")
            model, stoi, cfg = load_run(run, ck, device)
            H_tr = extract_all_layers(model, stoi, tr, device,
                                      cfg["block"])
            H_te = extract_all_layers(model, stoi, te, device,
                                      cfg["block"])
            for L in LAYERS:
                for pos in ("agent", "decision"):
                    for t in TARGETS:
                        acc, sel = fit_probe(H_tr[L][pos], y[t][0],
                                             H_te[L][pos], y[t][1])
                        out["cells"][f"{age}/L{L}/{pos}/{t}"] = {
                            "acc": round(acc, 3),
                            "sel": round(sel, 3)}
            print(f"{run} {ck} done")
        path = Path(run) / "atlas.json"
        path.write_text(json.dumps(out))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
