"""The Model Organism Lab: a small compositional command language for
interrogating trained checkpoints. Not a chatbot — a laboratory.

Design contract (docs/workbench_architecture.md):
- A persistent CURRENT experimental object: sample once, then successively
  edit/flip/sweep/trace/compare THE SAME case — controlled experimentation,
  not unrelated queries.
- Every command compiles to the experiment's own generator/scorer/probe code
  (generate_world / score) so the lab cannot diverge from the measurements.
- Read-only throughout: source runs are never mutated. `save` writes a
  provenance-stamped session notebook (run, commit, checkpoint, every
  transformation and measurement) as a derived artifact.
- Unknown commands explain the grammar instead of crashing.

GRAMMAR
  sample <id|conflict|nocue|cueonly> [agent <Name>]   new current case
  mode <id|conflict|nocue|cueonly>     re-render current case as counterfactual
  flip cue | remove cue | restore cue  shorthands for mode conflict/nocue/id
  set agent <Name> | set scene <s> | set narrator <n> | set noun <n>
  set payoff <1|2> <self|other> <int>  edit the current scenario
  swap options
  sweep payoff <1|2> <self|other> [lo hi]   Δlogp curve; decision boundary
  trace                                current case across ALL checkpoints
  ask                                  re-ask current case
  probe                                λ-probe reads for current case (--probes)
  ckpt <ckpt_040.pt> [A|B]             move a model along development
  agents | bio <Name>                  the authored ground truth
  bookmark <name> | load <name> | bookmarks
  save [file.json]                     provenance-stamped session notebook
  help | quit

Usage:
  python interact.py --run runs/C1_L1_s0 --data data/final_L1_seed0 \\
      --compare runs/C2_L1_s0 --probes
"""

import argparse
import copy
import datetime
import json
import random
import subprocess
from pathlib import Path

import numpy as np
import torch

import generate_world as gw
from score import load_run, forced_choice, load_set, extract_hidden
from train import pick_device


class Model:
    def __init__(self, run, ckpt, device):
        self.run, self.device = run, device
        self.cache = {}
        self.load(ckpt)

    def load(self, ckpt):
        self.ckpt = ckpt
        if ckpt not in self.cache:
            self.cache[ckpt] = load_run(self.run, ckpt, self.device)
        self.model, self.stoi, self.cfg = self.cache[ckpt]

    def ask(self, prompt):
        d = float(forced_choice(self.model, self.stoi, [prompt], self.device,
                                self.cfg["block"])[0])
        p1 = 1.0 / (1.0 + np.exp(-d))
        return {"choice": 1 if d > 0 else 2, "p1": round(p1, 3),
                "p2": round(1 - p1, 3), "dlogp": round(d, 3)}

    def checkpoints(self):
        return sorted(p.name for p in Path(self.run).glob("ckpt_*.pt"))


def record_to_cfg(rec, rng):
    """Rebuild an editable cfg from an eval record. Framing verbs are
    re-sampled (the record stores classes, not strings) — scenario identity
    (agent, payoffs, scene, narrator, noun) is preserved exactly."""
    return {"agent": rec["agent"], "lam": rec["lambda"],
            "partner": rec["partner"],
            "options": [(rec["d_self_1"], rec["d_other_1"]),
                        (rec["d_self_2"], rec["d_other_2"])],
            "scene": rec["scene"], "narrator": rec["narrator"],
            "noun": rec["noun"], "template": rec["template"],
            "coop_verb": rng.choice(gw.COOP_VERBS),
            "self_verb": rng.choice(gw.SELF_VERBS),
            "neut_verbs": rng.sample(gw.NEUT_VERBS, 2),
            "cue_target_override": rng.choice([1, 2])}


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


class Lab:
    def __init__(self, args):
        self.device = pick_device(args.device)
        self.models = {"A": Model(args.run, args.ckpt, self.device)}
        if args.compare:
            self.models["B"] = Model(args.compare, args.ckpt, self.device)
        self.data = args.data
        man = json.loads((Path(args.data) / "manifest.json").read_text())
        self.lam_map, self.level = man["agent_lambdas"], man["level"]
        self.seed = man["seed"]
        self.pools = {k: load_set(args.data, f"eval_{k}")
                      for k in ("id", "conflict", "nocue", "cueonly")}
        self.rng = random.Random()
        self.cur_cfg, self.cur_mode = None, "conflict"
        self.session, self.bookmarks = [], {}
        self.probes = {}
        if args.probes:
            print("fitting λ-probes…")
            for name, m in self.models.items():
                self.probes[name] = fit_lambda_probe(m, args.data)

    # -- rendering / display ------------------------------------------------
    def render(self):
        return gw.render_p(self.cur_cfg, self.level, self.cur_mode)[1]

    def show(self, note=""):
        rec = self.render()
        print(f"\n[{note or self.cur_mode}] AGENT {rec['agent']} "
              f"λ={rec['lambda']}")
        print(rec["prompt"])
        print(f"  utility says: {rec['utility_answer']}   "
              f"cue says: {rec['cue_answer']}")
        results = {}
        for name, m in self.models.items():
            a = m.ask(rec["prompt"])
            follows = []
            if rec["utility_answer"] == a["choice"]:
                follows.append("UTILITY")
            if rec["cue_answer"] == a["choice"]:
                follows.append("CUE")
            tag = "/".join(follows) or "neither"
            line = (f"  [{name} @ {m.ckpt}] choice {a['choice']} "
                    f"P(1)={a['p1']} Δlogp={a['dlogp']:+} → {tag}")
            if name in self.probes:
                pr = self.probe_read(name, rec)
                line += (f"  λ̂(COOP): agent={pr['agent']} "
                         f"decision={pr['decision']}")
                a["probe"] = pr
            print(line)
            results[name] = a
        self.session.append({"cmd": note or self.cur_mode, "record": rec,
                             "results": results})

    def probe_read(self, name, rec):
        out = {}
        m = self.models[name]
        for pos, (w, b, mu, sd, layer) in self.probes[name].items():
            H = extract_hidden(m.model, m.stoi, [rec], m.device,
                               m.cfg["block"], layer)[pos]
            x = torch.tensor((H[0] - mu) / sd, dtype=torch.float32)
            out[pos] = round(float(torch.sigmoid(x @ w + b)), 3)
        return out

    # -- commands -----------------------------------------------------------
    def cmd_sample(self, argv):
        kind = argv[0] if argv else "conflict"
        agent = argv[2] if len(argv) > 2 and argv[1] == "agent" else None
        cands = [r for r in self.pools[kind]
                 if not agent or r["agent"] == agent]
        rec = self.rng.choice(cands)
        self.cur_cfg = record_to_cfg(rec, self.rng)
        self.cur_mode = kind if kind != "id" else "id"
        self.show(f"sample {kind}")

    def cmd_set(self, argv):
        if argv[0] == "agent":
            self.cur_cfg["agent"] = argv[1]
            self.cur_cfg["lam"] = self.lam_map[argv[1]]
        elif argv[0] in ("scene", "narrator", "noun"):
            self.cur_cfg[argv[0]] = argv[1]
        elif argv[0] == "payoff":
            i, which, val = int(argv[1]) - 1, argv[2], int(argv[3])
            o = list(self.cur_cfg["options"][i])
            o[0 if which == "self" else 1] = val
            self.cur_cfg["options"][i] = tuple(o)
        self.show(f"set {' '.join(argv)}")

    def cmd_sweep(self, argv):
        # sweep payoff <1|2> <self|other> [lo hi]
        i, which = int(argv[1]) - 1, argv[2]
        lo, hi = (int(argv[3]), int(argv[4])) if len(argv) > 4 else (-5, 5)
        j = 0 if which == "self" else 1
        base = copy.deepcopy(self.cur_cfg)
        print(f"\nsweep option{i+1}.{which} ∈ [{lo},{hi}]  (mode {self.cur_mode})")
        rows = []
        for v in range(lo, hi + 1):
            if v == 0:
                continue
            cfg = copy.deepcopy(base)
            o = list(cfg["options"][i]); o[j] = v
            cfg["options"][i] = tuple(o)
            rec = gw.render_p(cfg, self.level, self.cur_mode)[1]
            cells = []
            for name, m in self.models.items():
                a = m.ask(rec["prompt"])
                cells.append(f"{name}:{a['choice']}({a['dlogp']:+.2f})")
            rows.append((v, rec["utility_answer"], " ".join(cells)))
        prev = None
        for v, ua, cells in rows:
            flip = " ← boundary" if prev and cells.split()[0][2] != \
                prev.split()[0][2] else ""
            print(f"  {v:+3d}  utility→{ua}  {cells}{flip}")
            prev = cells
        self.session.append({"cmd": f"sweep {' '.join(argv)}",
                             "rows": [(v, u, c) for v, u, c in rows]})

    def cmd_trace(self, argv):
        rec = self.render()
        print(f"\ndevelopmental trace (mode {self.cur_mode}): "
              f"utility says {rec['utility_answer']}, "
              f"cue says {rec['cue_answer']}")
        saved = {n: m.ckpt for n, m in self.models.items()}
        trace = {}
        for name, m in self.models.items():
            row = []
            for ck in m.checkpoints():
                m.load(ck)
                a = m.ask(rec["prompt"])
                row.append((ck.replace("ckpt_", "").replace(".pt", ""),
                            a["choice"], a["dlogp"]))
            m.load(saved[name])
            trace[name] = row
            print(f"  [{name}] " + " ".join(
                f"{p}%:{c}({d:+.1f})" for p, c, d in row))
        self.session.append({"cmd": "trace", "record": rec, "trace": trace})

    def cmd_bio(self, argv):
        a = argv[0]
        lam = self.lam_map.get(a)
        n = sum(1 for r in self.pools["id"] if r["agent"] == a)
        print(f"{a}: authored λ = {lam} "
              f"({'cooperative' if lam and lam < 0.5 else 'selfish'}), "
              f"assignment per-seed (seed {self.seed}); {n} held-out ID "
              f"scenarios; every training fact about {a} is enumerable from "
              f"the curriculum files (authored world)")

    def cmd_save(self, argv):
        out = argv[0] if argv else "notebook.json"
        commit = subprocess.run(["git", "rev-parse", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
        Path(out).write_text(json.dumps({
            "provenance": {
                "commit": commit,
                "created_at": datetime.datetime.now(
                    datetime.timezone.utc).isoformat(),
                "models": {n: {"run": m.run, "ckpt": m.ckpt}
                           for n, m in self.models.items()},
                "data": self.data, "level": self.level, "seed": self.seed},
            "steps": self.session}, indent=1, default=str))
        print(f"notebook saved: {out} ({len(self.session)} steps, "
              "provenance-stamped)")

    def dispatch(self, line):
        argv = line.split()
        op, rest = argv[0], argv[1:]
        if op == "sample":
            self.cmd_sample(rest)
        elif op == "mode":
            self.cur_mode = rest[0]; self.show(f"mode {rest[0]}")
        elif op == "flip" and rest == ["cue"]:
            self.cur_mode = "conflict"; self.show("flip cue")
        elif op == "remove" and rest == ["cue"]:
            self.cur_mode = "nocue"; self.show("remove cue")
        elif op == "restore" and rest == ["cue"]:
            self.cur_mode = "id"; self.show("restore cue")
        elif op == "set":
            self.cmd_set(rest)
        elif op == "swap" and rest == ["options"]:
            self.cur_cfg["options"] = self.cur_cfg["options"][::-1]
            self.show("swap options")
        elif op == "sweep":
            self.cmd_sweep(rest)
        elif op == "trace":
            self.cmd_trace(rest)
        elif op == "ask":
            self.show("ask")
        elif op == "probe":
            rec = self.render()
            for name in self.probes:
                print(f"  [{name}] λ̂(COOP) {self.probe_read(name, rec)}")
        elif op == "ckpt":
            which = rest[1] if len(rest) > 1 else "A"
            self.models[which].load(rest[0])
            print(f"model {which} → {rest[0]}")
        elif op == "agents":
            print("  " + "  ".join(f"{a}(λ={l})" for a, l in
                                   sorted(self.lam_map.items())))
        elif op == "bio":
            self.cmd_bio(rest)
        elif op == "bookmark":
            self.bookmarks[" ".join(rest)] = (copy.deepcopy(self.cur_cfg),
                                              self.cur_mode)
            print(f"bookmarked: {' '.join(rest)}")
        elif op == "bookmarks":
            print("  " + "\n  ".join(self.bookmarks) if self.bookmarks
                  else "  (none)")
        elif op == "load":
            self.cur_cfg, self.cur_mode = copy.deepcopy(
                self.bookmarks[" ".join(rest)])
            self.show(f"load {' '.join(rest)}")
        elif op == "save":
            self.cmd_save(rest)
        else:
            print(__doc__)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", default="ckpt_100.pt")
    ap.add_argument("--compare", default=None)
    ap.add_argument("--probes", action="store_true")
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    lab = Lab(args)
    print(f"Model Organism Lab — {len(lab.models)} model(s), level "
          f"{lab.level}, seed {lab.seed}. `help` for grammar; try: "
          "sample conflict")
    while True:
        try:
            line = input("lab> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line == "quit":
            break
        try:
            lab.dispatch(line)
        except Exception as e:
            print(f"error: {e} — `help` for grammar")


if __name__ == "__main__":
    main()
