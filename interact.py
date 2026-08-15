"""Meet the model organism: interrogate trained checkpoints interactively.

Load one run (or two, side by side — e.g. C1 vs C2, same seed), pick agents,
pose choice scenarios, and see: the model's choice with probabilities, what
the utility route says, what the cue route says, and (with --probes) what a
lambda-probe decodes at the agent and decision tokens. Render the SAME
scenario aligned / conflict / no-cue to watch the routes agree and disagree.

  python interact.py --run runs/C1_L1_s0 --data data/final_L1_seed0 \\
      --compare runs/C2_L1_s0 --probes

REPL commands:
  sample [id|conflict|nocue|cueonly]   random eval scenario of that kind
  again [id|conflict|nocue]            re-render the SAME scenario as a
                                       different mode (counterfactual triple)
  agent <Name>                         restrict sampling to one agent
  ckpt <ckpt_040.pt> [A|B]             switch checkpoint
  bio <Name>                           the agent's authored ground truth
  export <file.json>                   dump this session for the web explorer
  quit
"""

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch

import generate_world as gw
from score import load_run, forced_choice, load_set, extract_hidden, fit_probe
from train import pick_device


class Model:
    def __init__(self, run, ckpt, device):
        self.run, self.device = run, device
        self.load(ckpt)

    def load(self, ckpt):
        self.ckpt = ckpt
        self.model, self.stoi, self.cfg = load_run(self.run, ckpt, self.device)

    def ask(self, prompt):
        d = float(forced_choice(self.model, self.stoi, [prompt], self.device,
                                self.cfg["block"])[0])
        p1 = 1.0 / (1.0 + np.exp(-d))
        return {"choice": 1 if d > 0 else 2, "p1": round(p1, 3),
                "p2": round(1 - p1, 3), "dlogp": round(d, 3)}


def fit_lambda_probe(m, data_dir, layer=None):
    layer = layer if layer is not None else m.cfg["layers"] // 2
    tr = load_set(data_dir, "probe_train")
    H = extract_hidden(m.model, m.stoi, tr, m.device, m.cfg["block"], layer)
    y = np.array([1.0 if r["lambda_class"] == "COOP" else 0.0 for r in tr])
    probes = {}
    for pos in ("agent", "decision"):
        X = H[pos]
        mu, sd = X.mean(0), X.std(0) + 1e-6
        Xn = torch.tensor((X - mu) / sd, dtype=torch.float32)
        yv = torch.tensor(y, dtype=torch.float32)
        w = torch.zeros(Xn.shape[1], requires_grad=True)
        b = torch.zeros(1, requires_grad=True)
        opt = torch.optim.Adam([w, b], lr=0.05)
        for _ in range(300):
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                Xn @ w + b, yv) + 1e-3 * w.pow(2).sum()
            opt.zero_grad(); loss.backward(); opt.step()
        probes[pos] = (w.detach(), b.detach(), mu, sd, layer)
    return probes


def probe_read(m, probes, record):
    out = {}
    for pos, (w, b, mu, sd, layer) in probes.items():
        H = extract_hidden(m.model, m.stoi, [record], m.device,
                           m.cfg["block"], layer)[pos]
        x = torch.tensor((H[0] - mu) / sd, dtype=torch.float32)
        out[pos] = round(float(torch.sigmoid(x @ w + b)), 3)
    return out


def show(record, models, probes_by_name, lam_map):
    agent = record["agent"]
    print(f"\nAGENT {agent}   trained λ = {lam_map[agent]}   "
          f"mode = {record['mode']}")
    print(record["prompt"])
    ua, ca = record["utility_answer"], record["cue_answer"]
    print(f"  utility route says: {ua}    cue route says: {ca}")
    for name, m in models.items():
        a = m.ask(record["prompt"])
        line = (f"  [{name} @ {m.ckpt}]  choice {a['choice']}  "
                f"P(1)={a['p1']} P(2)={a['p2']}  Δlogp={a['dlogp']:+}")
        routes = []
        if ua:
            routes.append("UTILITY" if a["choice"] == ua else "")
        if ca:
            routes.append("CUE" if a["choice"] == ca else "")
        tag = "/".join(r for r in routes if r) or "neither?"
        line += f"  → follows {tag}"
        if name in probes_by_name:
            pr = probe_read(m, probes_by_name[name], record)
            line += (f"   λ-probe p(COOP): agent={pr['agent']} "
                     f"decision={pr['decision']}")
        print(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", default="ckpt_100.pt")
    ap.add_argument("--compare", default=None)
    ap.add_argument("--probes", action="store_true")
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    device = pick_device(args.device)

    models = {"A": Model(args.run, args.ckpt, device)}
    if args.compare:
        models["B"] = Model(args.compare, args.ckpt, device)
    manifest = json.loads((Path(args.data) / "manifest.json").read_text())
    lam_map = manifest["agent_lambdas"]
    level = manifest["level"]
    pools = {k: load_set(args.data, f"eval_{k}")
             for k in ("id", "conflict", "nocue", "cueonly")}
    probes_by_name = {}
    if args.probes:
        print("fitting λ-probes (once per model)…")
        for name, m in models.items():
            probes_by_name[name] = fit_lambda_probe(m, args.data)

    rng = random.Random()
    session, current_cfg, agent_filter = [], None, None
    print(f"loaded {len(models)} model(s), level {level}. "
          f"agents: {', '.join(sorted(lam_map))}. try: sample conflict")
    while True:
        try:
            cmd = input("organism> ").strip().split()
        except (EOFError, KeyboardInterrupt):
            break
        if not cmd:
            continue
        op = cmd[0]
        if op == "quit":
            break
        elif op == "agent":
            agent_filter = cmd[1] if len(cmd) > 1 else None
            print(f"agent filter: {agent_filter}")
        elif op == "bio":
            a = cmd[1]
            lam = lam_map.get(a)
            n = sum(1 for r in pools["id"] if r["agent"] == a)
            print(f"{a}: authored λ = {lam} "
                  f"({'cooperative' if lam and lam < 0.5 else 'selfish'}); "
                  f"assignment is per-seed (seed {manifest['seed']}); "
                  f"{n} held-out ID scenarios in this eval pool")
        elif op == "ckpt":
            which = cmd[2] if len(cmd) > 2 else "A"
            models[which].load(cmd[1])
            print(f"model {which} → {cmd[1]}")
        elif op == "sample":
            kind = cmd[1] if len(cmd) > 1 else "conflict"
            cands = [r for r in pools[kind]
                     if not agent_filter or r["agent"] == agent_filter]
            rec = rng.choice(cands)
            current_cfg = None  # eval records carry no cfg; 'again' needs one
            show(rec, models, probes_by_name, lam_map)
            session.append({"record": rec})
        elif op == "again":
            if current_cfg is None:
                # build a fresh cfg so the counterfactual triple shares one
                # scenario; agent-filtered
                amap = {k: v for k, v in lam_map.items()
                        if not agent_filter or k == agent_filter}
                current_cfg = gw.sample_p_config(
                    rng, amap, gw.TRAIN_NOUNS, "T1")
            mode = cmd[1] if len(cmd) > 1 else "conflict"
            _, rec = gw.render_p(current_cfg, level, mode)
            show(rec, models, probes_by_name, lam_map)
            session.append({"record": rec})
        elif op == "export":
            out = cmd[1] if len(cmd) > 1 else "session_export.json"
            Path(out).write_text(json.dumps(session, indent=1))
            print(f"wrote {out} ({len(session)} interactions) — feeds the "
                  "web explorer")
        else:
            print(__doc__)


if __name__ == "__main__":
    main()
