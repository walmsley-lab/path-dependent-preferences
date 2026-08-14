"""Evaluation harness: forced-choice scoring, route metrics, probes, context test.

Everything scores by log-probability -- logp("1") vs logp("2") at the answer
position after "A: Option" -- never free generation. Continuous log-odds
(dlogp) are retained everywhere; binary accuracy is the preregistered endpoint.

Per checkpoint x eval set:
  acc_utility / acc_cue      agreement with each route's answer
  mean_dlogp                 logp("1") - logp("2")
  margin stratification      conflict accuracy by |u_diff| (fifth-units)
  beta_U, beta_C             OLS: dlogp ~ u_diff_toward_1 + cue_toward_1
                             (mechanism-competition coefficients over time)
Probes (residual stream, final prompt token, per layer):
  logistic probe for lambda_class / u_diff_sign / verb_class_1,
  selectivity = acc - shuffled-label acc (Hewitt-Liang control)
Context test (in-context counter-evidence):
  k demos (congruent/incongruent/none) prepended to no-cue or conflict queries,
  override_rate + probe persistence under context.

Usage:
  python score.py --run runs/C1_L0_s0 --data data/final_L0_seed0 \\
      --ckpt ckpt_100.pt --sets eval_id eval_conflict eval_nocue eval_cueonly
  ... --probes            # add probe suite
  ... --context eval_nocue --k 4   # add in-context test
"""

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch

from train import GPT, encode, pick_device

ANSWER_PREFIX = "A: Option"


def load_run(run_dir, ckpt, device):
    run_dir = Path(run_dir)
    stoi = json.loads((run_dir / "vocab.json").read_text())
    cfg = json.loads((run_dir / "run_manifest.json").read_text())["config"]
    model = GPT(len(stoi), cfg["d_model"], cfg["layers"], cfg["heads"],
                cfg["block"]).to(device)
    model.load_state_dict(torch.load(run_dir / ckpt, map_location=device))
    model.eval()
    return model, stoi, cfg


def load_set(data_dir, name):
    return [json.loads(l) for l in
            (Path(data_dir) / f"{name}.jsonl").read_text().splitlines()]


@torch.no_grad()
def forced_choice(model, stoi, prompts, device, block, batch=64,
                  return_hidden_layer=None):
    """Returns dlogp = logp('1') - logp('2') per prompt (+ optional hiddens)."""
    id1, id2 = stoi["1"], stoi["2"]
    out, hid = [], []
    for i in range(0, len(prompts), batch):
        chunk = [encode(f"{p} {ANSWER_PREFIX}", stoi)[-block:]
                 for p in prompts[i:i + batch]]
        lens = [len(c) for c in chunk]
        T = max(lens)
        x = torch.zeros(len(chunk), T, dtype=torch.long, device=device)
        for j, c in enumerate(chunk):
            x[j, :len(c)] = torch.tensor(c)
        if return_hidden_layer is not None:
            logits, hiddens = model(x, return_hidden=True)
            h = hiddens[return_hidden_layer]
            hid.extend(h[j, lens[j] - 1].float().cpu().numpy()
                       for j in range(len(chunk)))
        else:
            logits = model(x)
        lp = torch.log_softmax(logits, dim=-1)
        out.extend(float(lp[j, lens[j] - 1, id1] - lp[j, lens[j] - 1, id2])
                   for j in range(len(chunk)))
    return (np.array(out), np.array(hid)) if return_hidden_layer is not None \
        else np.array(out)


def score_set(model, stoi, records, device, block):
    dlogp = forced_choice(model, stoi, [r["prompt"] for r in records],
                          device, block)
    pred = np.where(dlogp > 0, 1, 2)
    res = {"n": len(records), "mean_dlogp": float(dlogp.mean())}
    ua = np.array([r["utility_answer"] or 0 for r in records])
    ca = np.array([r["cue_answer"] or 0 for r in records])
    if (ua > 0).all():
        res["acc_utility"] = float((pred == ua).mean())
    if (ca > 0).all():
        res["acc_cue"] = float((pred == ca).mean())
    # Mechanism-competition regression: dlogp ~ u_diff_toward_1 + cue_toward_1.
    u = np.array([r["u_diff"] for r in records], dtype=float)
    c = np.where(ca == 1, 1.0, np.where(ca == 2, -1.0, 0.0))
    X = np.stack([u, c, np.ones_like(u)], axis=1)
    beta, *_ = np.linalg.lstsq(X, dlogp, rcond=None)
    res["beta_U"], res["beta_C"] = float(beta[0]), float(beta[1])
    # Margin stratification (fifth-units; exact integers).
    margins = np.abs(u)
    strata = {}
    for m in sorted(set(margins.tolist())):
        idx = margins == m
        if idx.sum() >= 10 and (ua[idx] > 0).all():
            strata[str(int(m))] = float((pred[idx] == ua[idx]).mean())
    if strata:
        res["acc_utility_by_margin"] = strata
    return res


def fit_probe(H_tr, y_tr, H_te, y_te, steps=300, lr=0.05, seed=0):
    """Logistic probe + shuffled-label control -> (acc, selectivity)."""
    g = torch.Generator().manual_seed(seed)
    def fit(y):
        X = torch.tensor((H_tr - H_tr.mean(0)) / (H_tr.std(0) + 1e-6),
                         dtype=torch.float32)
        Xt = torch.tensor((H_te - H_tr.mean(0)) / (H_tr.std(0) + 1e-6),
                          dtype=torch.float32)
        yv = torch.tensor(y, dtype=torch.float32)
        w = torch.zeros(X.shape[1], requires_grad=True)
        b = torch.zeros(1, requires_grad=True)
        opt = torch.optim.Adam([w, b], lr=lr)
        for _ in range(steps):
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                X @ w + b, yv) + 1e-3 * w.pow(2).sum()
            opt.zero_grad(); loss.backward(); opt.step()
        return float((((Xt @ w + b) > 0).float().numpy() == y_te).mean())
    acc = fit(y_tr)
    y_shuf = y_tr[torch.randperm(len(y_tr), generator=g).numpy()]
    acc_shuf = fit(y_shuf)
    return acc, acc - acc_shuf


PROBE_TARGETS = {
    "lambda_class": lambda r: 1.0 if r["lambda_class"] == "COOP" else 0.0,
    "u_diff_sign": lambda r: 1.0 if r["u_diff_sign"] > 0 else 0.0,
    "verb_class_1": lambda r: 1.0 if r["verb_class_1"] == "COOP" else 0.0,
}


def probe_suite(model, stoi, data_dir, device, block, layers):
    tr = load_set(data_dir, "probe_train")
    te = load_set(data_dir, "probe_test")
    out = {}
    for layer in layers:
        _, H_tr = forced_choice(model, stoi, [r["prompt"] for r in tr],
                                device, block, return_hidden_layer=layer)
        _, H_te = forced_choice(model, stoi, [r["prompt"] for r in te],
                                device, block, return_hidden_layer=layer)
        for name, fn in PROBE_TARGETS.items():
            y_tr = np.array([fn(r) for r in tr])
            y_te = np.array([fn(r) for r in te])
            acc, sel = fit_probe(H_tr, y_tr, H_te, y_te)
            out[f"L{layer}/{name}"] = {"acc": acc, "selectivity": sel}
    return out


def context_test(model, stoi, data_dir, device, block, query_set, k=4,
                 n_queries=200, seed=0):
    """In-context counter-evidence: congruent / incongruent / none demos."""
    rng = random.Random(seed)
    demos = load_set(data_dir, "persona_demos")
    by_agent = {}
    for d in demos:
        by_agent.setdefault((d["agent"], d["consistency"]), []).append(d)
    queries = [r for r in load_set(data_dir, query_set)
               if r["utility_answer"]]
    rng.shuffle(queries)
    queries = queries[:n_queries]
    results = {}
    for condition in ("none", "congruent", "incongruent"):
        prompts, keep = [], []
        for r in queries:
            if condition == "none":
                prompts.append(r["prompt"]); keep.append(r); continue
            pool = by_agent.get((r["agent"], condition), [])
            if len(pool) < k:
                continue
            ctx = " ".join(d["line"] for d in rng.sample(pool, k))
            prompts.append(f"{ctx} {r['prompt']}"); keep.append(r)
        dlogp = forced_choice(model, stoi, prompts, device, block)
        pred = np.where(dlogp > 0, 1, 2)
        ua = np.array([r["utility_answer"] for r in keep])
        results[condition] = {"n": len(keep),
                              "acc_utility": float((pred == ua).mean()),
                              "mean_dlogp": float(dlogp.mean())}
    if "incongruent" in results and "none" in results:
        results["override_rate"] = round(
            results["none"]["acc_utility"]
            - results["incongruent"]["acc_utility"], 4)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", default="ckpt_100.pt")
    ap.add_argument("--sets", nargs="*", default=["eval_id", "eval_conflict",
                                                  "eval_nocue", "eval_cueonly"])
    ap.add_argument("--probes", action="store_true")
    ap.add_argument("--probe_layers", nargs="*", type=int, default=None)
    ap.add_argument("--context", default=None,
                    help="query set for the in-context test, e.g. eval_nocue")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()

    device = pick_device(args.device)
    model, stoi, cfg = load_run(args.run, args.ckpt, device)
    block = cfg["block"]
    report = {"run": args.run, "ckpt": args.ckpt, "sets": {}}
    for name in args.sets:
        report["sets"][name] = score_set(
            model, stoi, load_set(args.data, name), device, block)
    if args.probes:
        layers = args.probe_layers or [cfg["layers"] // 2, cfg["layers"] - 1]
        report["probes"] = probe_suite(model, stoi, args.data, device, block,
                                       layers)
    if args.context:
        report["context"] = context_test(model, stoi, args.data, device,
                                         block, args.context, k=args.k)
    out = Path(args.run) / f"score_{args.ckpt.replace('.pt', '')}.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
