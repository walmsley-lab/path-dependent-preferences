"""The identity-confound test: λ or just Matthew? (docs/act1_program.md L1)

λ is assigned per agent, so high λ decodability from the agent state may
be nothing more than agent-identity lookup — Michael always has the same
λ, and a linear classifier that recognizes "Michael" recovers his class
for free. The stronger claim (an abstract preference-class
representation) requires GENERALIZATION ACROSS HELD-OUT AGENTS: train
the probe on representations from a subset of agents, evaluate on
agents the probe never saw, with the sex-counterbalanced λ assignment
keeping both classes present in both splits.

Also runs the same split for the wording-cue target as a comparison, and
the standard within-agents probe for reference. Emits a typed,
provenance-stamped evidence record consumed by the Lab's formalization
instrument:

  runs/<run>/evidence_probe_generalization.json

RESULT SEMANTICS: 'recoverable across held-out agents' upgrades the
claim from identity-confounded to abstract-class-information; it still
establishes recoverability BY THIS PROBE only — never causal use.

Usage:
  python probe_generalization.py --runs runs/C2_L1_s0 runs/C3_L1_s0 \
      --data demo/data/final_L1_seed0 --ckpt ckpt_100.pt --device cpu
"""

import argparse
import datetime
import json
from pathlib import Path

import numpy as np

from score import (load_run, load_set, extract_hidden, fit_probe,
                   PROBE_TARGETS)
from train import pick_device

LAYERS = [0, 1, 2, 3, 4, 5]


def agent_split(records, seed=0):
    """Split by AGENT (not by record), keeping both λ classes on both
    sides via the per-class alternation of the sorted agent list."""
    by_class = {}
    for r in records:
        by_class.setdefault(r["lambda_class"], set()).add(r["agent"])
    train_agents, test_agents = set(), set()
    for cls in sorted(by_class):
        agents = sorted(by_class[cls])
        for i, a in enumerate(agents):
            (train_agents if i % 2 == 0 else test_agents).add(a)
    return train_agents, test_agents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", default="ckpt_100.pt")
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    device = pick_device(args.device)

    tr = load_set(args.data, "probe_train")
    te = load_set(args.data, "probe_test")
    records = tr + te
    train_agents, test_agents = agent_split(records)
    print(f"probe-train agents: {sorted(train_agents)}")
    print(f"held-out agents:    {sorted(test_agents)}")

    for run in args.runs:
        man = json.loads((Path(run) / "run_manifest.json").read_text())
        model, stoi, cfg = load_run(run, args.ckpt, device)
        out = {"run": run, "ckpt": args.ckpt,
               "question": "λ or just agent identity? probe trained on "
                           "half the agents, evaluated on agents it "
                           "never saw",
               "train_agents": sorted(train_agents),
               "heldout_agents": sorted(test_agents),
               "layers": {},
               "claim_target": "mechanism",
               "_provenance": {
                   "run_id": man.get("run_id"),
                   "commit": man.get("git_commit"),
                   "created_at": datetime.datetime.now(
                       datetime.timezone.utc).isoformat(),
                   "kind": "L1 evidence record "
                           "(agent-held-out probe generalization)"}}
        for L in LAYERS:
            H_all = extract_hidden(model, stoi, records, device,
                                   cfg["block"], L)
            row = {}
            for pos in ("agent", "decision"):
                H = H_all[pos]
                for target in ("lambda_class", "verb_class_1"):
                    y = np.array([PROBE_TARGETS[target](r)
                                  for r in records])
                    idx_tr = [i for i, r in enumerate(records)
                              if r["agent"] in train_agents]
                    idx_te = [i for i, r in enumerate(records)
                              if r["agent"] in test_agents]
                    acc, sel = fit_probe(H[idx_tr], y[idx_tr],
                                         H[idx_te], y[idx_te])
                    row[f"{pos}/{target}"] = {
                        "heldout_agent_acc": round(acc, 4),
                        "heldout_agent_selectivity": round(sel, 4)}
            out["layers"][f"L{L}"] = row
            print(f"{run} L{L}: " + "  ".join(
                f"{k}={v['heldout_agent_selectivity']}"
                for k, v in row.items() if "lambda" in k))
        path = Path(run) / "evidence_probe_generalization.json"
        path.write_text(json.dumps(out, indent=1))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
