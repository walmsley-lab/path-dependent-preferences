"""The experiment API + guided workbench page (docs/workbench_architecture.md).

Stdlib only; run it wherever checkpoints live:

    python serve_api.py --port 8080     # open http://localhost:8080

The page leads with the experiment's framing, then hand-holds through a
guided walkthrough that carries ONE scenario through the whole argument:
meet an agent -> ordinary question -> force the routes apart -> remove the
shortcut -> explore freely. Playwright tests: tests/test_workbench.py.

Endpoints (the UI consumes ONLY these; later panels plug in the same way):
  GET  /api/runs                    run registry with provenance
  GET  /api/datasets                data dirs with manifests
  GET  /api/corpus?data=DIR         agents + lambda map + generation stats
  POST /api/query                   {run, ckpt, data, mode, agent?, cfg?}
"""

import argparse
import json
import random
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import generate_world as gw
from expedition_page import EXPEDITION, render_technique
from lab_page import LAB
from lab_spine import LAB_SPINE
from interact import Model
from train import pick_device

MODELS = {}
DEVICE = "cpu"


def get_model(run, ckpt):
    key = (run, ckpt)
    if key not in MODELS:
        MODELS[key] = Model(run, ckpt, DEVICE)
    return MODELS[key]


def api_runs():
    out = []
    for m in sorted(Path("runs").glob("*/run_manifest.json")):
        j = json.loads(m.read_text())
        cfg = j.get("config", {})
        out.append({"run": str(m.parent), "run_id": j.get("run_id"),
                    "commit": j.get("git_commit", "")[:8],
                    "dataset_dir": j.get("dataset_dir"),
                    "curriculum": j.get("curriculum"),
                    "n_params": j.get("n_params"),
                    "arch": f"{cfg.get('layers','?')}-layer decoder-only, "
                            f"d={cfg.get('d_model','?')}, "
                            f"{cfg.get('heads','?')} heads",
                    "ckpts": sorted(p.name for p in
                                    m.parent.glob("ckpt_*.pt"))})
    return out


def api_datasets():
    out = []
    for m in sorted(Path(".").glob("d*/**/manifest.json")):
        try:
            j = json.loads(m.read_text())
            if "agent_lambdas" not in j:
                continue     # pre-provenance or foreign manifest
            out.append({"data": str(m.parent), "level": j.get("level"),
                        "seed": j.get("seed")})
        except Exception:
            continue
    return out


def api_worldspec(data):
    man = json.loads((Path(data) / "manifest.json").read_text())
    return gw.build_world_spec(man["level"])


def api_curricula(data):
    man = json.loads((Path(data) / "manifest.json").read_text())
    return {"segments": man.get("segments", {})}


def api_series(run):
    series = []
    for f in sorted(Path(run).glob("score_ckpt_*.json")):
        r = json.loads(f.read_text())
        s = r.get("sets", {})
        row = {"pct": int(f.stem.split("_")[-1])}
        for k, key, m in [("conflict", "eval_conflict", "acc_utility"),
                          ("id", "eval_id", "acc_utility"),
                          ("nocue", "eval_nocue", "acc_utility"),
                          ("cueonly", "eval_cueonly", "acc_cue")]:
            if key in s and m in s[key]:
                row[k] = s[key][m]
        series.append(row)
    return {"run": run, "series": series}


def api_corpus(data):
    man = json.loads((Path(data) / "manifest.json").read_text())
    return {"level": man["level"], "seed": man["seed"],
            "agents": man["agent_lambdas"],
            "generation_stats": man.get("generation_stats", {}),
            # the world's building blocks, for the custom-scenario bench:
            # scenarios must be assembled from the closed vocabulary — the
            # organism can only read words that exist in its world
            "partners": gw.PARTNERS, "scenes": gw.SCENES,
            "nouns": gw.TRAIN_NOUNS, "deltas": gw.DELTAS,
            "coop_verbs": gw.COOP_VERBS, "self_verbs": gw.SELF_VERBS,
            "neut_verbs": gw.NEUT_VERBS, "narrators": gw.NARRATORS}


def api_observe(data, agent=None, n=4):
    """Field notes for the Expedition: n ordinary (train-mode) scenarios for
    ONE agent, rendered by the authored generator — the WORLD's behavior,
    no model involved. Deterministic RNG so the notebook pages are stable
    across reloads (and so chapter 3 can re-read the same pages)."""
    man = json.loads((Path(data) / "manifest.json").read_text())
    amap = man["agent_lambdas"]
    if not agent:
        agent = "Matthew" if "Matthew" in amap else \
            sorted(amap, key=lambda a: (-amap[a], a))[0]
    lam = amap[agent]
    rng = random.Random(20260814)

    def pred(lam_hat, rec):
        u1 = lam_hat*rec["d_self_1"] + (1-lam_hat)*rec["d_other_1"]
        u2 = lam_hat*rec["d_self_2"] + (1-lam_hat)*rec["d_other_2"]
        return 1 if u1 >= u2 else 2

    # Field-note requirements (2026-08-15 UX incidents):
    # 1. every note INFORMATIVE — its prediction flips somewhere on the
    #    reader's slider (dominated options made the fit check vacuous);
    # 2. the WITHHELD pair must genuinely narrow the seen pair's band —
    #    otherwise any committable hypothesis auto-passes 4/4 and the
    #    revise loop (the failure->revision beat, the point of chapter 1)
    #    is unreachable.
    grid = [v / 100 for v in range(0, 101, 5)]

    def band(records):
        return {v for v in grid
                if all(pred(v, r) == r["utility_answer"] for r in records)}

    cands = []
    for _ in range(4000):
        if len(cands) >= 60:
            break
        cfg = gw.sample_p_config(rng, {agent: lam}, gw.TRAIN_NOUNS, "T1")
        _, rec = gw.render_p(cfg, man["level"], "train")
        if pred(0.001, rec) == pred(0.999, rec):
            continue
        cands.append((cfg, rec))

    chosen = None
    for i in range(len(cands)):
        for k in range(i + 1, len(cands)):
            seen = band([cands[i][1], cands[k][1]])
            if len(seen) < 8:
                continue          # seen pair must leave room to be wrong
            for m in range(len(cands)):
                for q in range(m + 1, len(cands)):
                    if m in (i, k) or q in (i, k):
                        continue
                    full = band([cands[j][1] for j in (i, k, m, q)])
                    if full and len(seen) - len(full) >= 4:
                        chosen = [cands[j] for j in (i, k, m, q)]
                        break
                if chosen:
                    break
            if chosen:
                break
        if chosen:
            break
    if not chosen:                # fallback: informative but unnarrowed
        chosen = cands[:n]

    obs = [{"record": rec,
            "cfg": {**cfg, "options": [list(o) for o in cfg["options"]]}}
           for cfg, rec in chosen[:n]]
    return {"agent": agent, "lam": lam, "level": man["level"],
            "observations": obs}


def api_corpus_lines(data, slice_name=None, n=60):
    """Real training lines, in curriculum order, from locally fetched
    slices (data/<dir>/slices/*.txt — head = the organism's first pages,
    tail = the shared final stretch, sample = evenly spaced mid-corpus).
    Returns the available slice names when none is requested."""
    sdir = Path(data) / "slices"
    slices = sorted(p.stem for p in sdir.glob("*.txt")) if sdir.exists() \
        else []
    if not slice_name:
        return {"slices": slices}
    if slice_name not in slices:
        return {"slices": slices, "error": "unknown slice"}
    lines = (sdir / f"{slice_name}.txt").read_text().splitlines()[:int(n)]
    out = [{"text": ln,
            "type": "P" if "Q: Which option does" in ln else "W"}
           for ln in lines if ln.strip()]
    return {"slice": slice_name, "lines": out, "slices": slices}


def api_render(body):
    """Render a scenario WITHOUT invoking any model — the live stimulus
    preview for the compose instrument. Same cfg semantics as api_query;
    returns the exact text the organism would receive."""
    man = json.loads((Path(body["data"]) / "manifest.json").read_text())
    cfg = body["cfg"]
    cfg["options"] = [tuple(o) for o in cfg["options"]]
    cfg["neut_verbs"] = list(cfg["neut_verbs"])
    prompt, rec = gw.render_p(cfg, man["level"], body.get("mode", "id"))
    return {"prompt": prompt, "record": rec}


def api_query(body):
    run, ckpt, data = body["run"], body.get("ckpt", "ckpt_100.pt"), body["data"]
    mode = body.get("mode", "conflict")
    man = json.loads((Path(data) / "manifest.json").read_text())
    rng = random.Random()
    if body.get("cfg"):
        cfg = body["cfg"]
        cfg["options"] = [tuple(o) for o in cfg["options"]]
        cfg["neut_verbs"] = list(cfg["neut_verbs"])
    else:
        amap = man["agent_lambdas"]
        if body.get("agent"):
            amap = {body["agent"]: amap[body["agent"]]}
        cfg = gw.sample_p_config(rng, amap, gw.TRAIN_NOUNS, "T1")
    _, rec = gw.render_p(cfg, man["level"], mode)
    ans = get_model(run, ckpt).ask(rec["prompt"])
    follows = []
    if rec["utility_answer"] and ans["choice"] == rec["utility_answer"]:
        follows.append("UTILITY")
    if rec["cue_answer"] and ans["choice"] == rec["cue_answer"]:
        follows.append("CUE")
    return {"record": rec, "answer": ans,
            "follows": "/".join(follows) or "NEITHER",
            "cfg": {**cfg, "options": [list(o) for o in cfg["options"]]}}


def api_freeform(body):
    """Freeform text against a live organism. The world's vocabulary is
    CLOSED (word-level, built from its corpus): unknown words are
    reported back, never silently mangled. Two modes: 'continue' (greedy
    generation until <eol> or max_new) and 'choice' (forced-choice logp
    over Option 1/2). Freeform territory is off the diagnostic map — no
    authored answer exists for arbitrary text; the UI labels it
    exploration, not evidence."""
    import torch
    from train import EOL
    m = get_model(body["run"], body.get("ckpt", "ckpt_100.pt"))
    prompt = " ".join(body["prompt"].split())
    words = prompt.split()
    if not words:
        return {"error": "empty prompt"}
    oov = sorted({w for w in words if w not in m.stoi})
    if oov:
        return {"oov": oov}
    if body.get("mode") == "choice":
        return {"answer": m.ask(prompt)}
    itos = {i: w for w, i in m.stoi.items()}
    ids = [m.stoi[w] for w in words]
    block = m.cfg["block"]
    out = []
    with torch.no_grad():
        for _ in range(min(int(body.get("max_new", 40)), 80)):
            x = torch.tensor([ids[-block:]], dtype=torch.long,
                             device=DEVICE)
            logits = m.model(x)
            nxt = int(logits[0, -1].argmax())
            word = itos.get(nxt, "?")
            if word == EOL:
                break
            ids.append(nxt)
            out.append(word)
    return {"continuation": " ".join(out), "n_tokens": len(out),
            "decoding": "greedy (deterministic)"}


# (classic workbench page removed 2026-08-15 — superseded by the Expedition,
# the instrument bench, and the evidence spine; recoverable from git history)



class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/":
                self._send(200, EXPEDITION.encode(),
                           "text/html; charset=utf-8")
            elif u.path == "/lab":
                self._send(200, LAB_SPINE.encode(),
                           "text/html; charset=utf-8")
            elif u.path in ("/lab/bench", "/lab/spine"):
                page = LAB if u.path == "/lab/bench" else LAB_SPINE
                self._send(200, page.encode(), "text/html; charset=utf-8")
            elif u.path.startswith("/technique/"):
                html = render_technique(u.path.split("/technique/")[1])
                if html is None:
                    self._send(404, {"error": "unknown technique"})
                else:
                    self._send(200, html.encode(),
                               "text/html; charset=utf-8")
            elif u.path == "/api/observe":
                self._send(200, api_observe(
                    qs["data"][0], qs.get("agent", [None])[0],
                    int(qs.get("n", ["4"])[0])))
            elif u.path == "/api/runs":
                self._send(200, api_runs())
            elif u.path == "/api/datasets":
                self._send(200, api_datasets())
            elif u.path == "/api/worldspec":
                self._send(200, api_worldspec(qs["data"][0]))
            elif u.path == "/api/curricula":
                self._send(200, api_curricula(qs["data"][0]))
            elif u.path == "/api/series":
                self._send(200, api_series(qs["run"][0]))
            elif u.path == "/api/manifest":
                self._send(200, json.loads(
                    (Path(qs["run"][0]) / "run_manifest.json").read_text()))
            elif u.path == "/api/corpus":
                self._send(200, api_corpus(qs["data"][0]))
            elif u.path == "/api/corpus_lines":
                self._send(200, api_corpus_lines(
                    qs["data"][0], qs.get("slice", [None])[0],
                    int(qs.get("n", ["60"])[0])))
            elif u.path == "/api/geometry":
                p = (Path(qs["run"][0]) /
                     f"geometry_{qs['ckpt'][0].replace('.pt','')}.json")
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no geometry artifact"})
            elif u.path == "/api/geometry_compare":
                p = Path("runs/geometry_compare.json")
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no compare artifact"})
            elif u.path == "/api/weightspace":
                p = Path("runs/weightspace.json")
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no weightspace artifact"})
            elif u.path == "/api/atlas":
                p = Path(qs["run"][0]) / "atlas.json"
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no atlas artifact"})
            elif u.path == "/api/trace":
                p = Path(qs["run"][0]) / "evidence_trace.json"
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no trace record"})
            elif u.path == "/api/ablation":
                p = Path(qs["run"][0]) / "evidence_ablation.json"
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no ablation record"})
            elif u.path == "/api/patching":
                p = Path(qs["run"][0]) / "evidence_patching.json"
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no patching record"})
            elif u.path == "/api/steering":
                p = Path(qs["run"][0]) / "evidence_steering.json"
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no steering record"})
            elif u.path == "/api/evidence":
                p = (Path(qs["run"][0]) /
                     "evidence_probe_generalization.json")
                self._send(200, json.loads(p.read_text())) if p.exists() \
                    else self._send(404, {"error": "no evidence record"})
            elif u.path == "/api/score":
                self._send(200, json.loads(
                    (Path(qs["run"][0]) /
                     f"score_{qs['ckpt'][0].replace('.pt','')}.json"
                     ).read_text()))
            else:
                self._send(404, {"error": "unknown endpoint"})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(
                int(self.headers["Content-Length"])))
            if self.path == "/api/query":
                self._send(200, api_query(body))
            elif self.path == "/api/render":
                self._send(200, api_render(body))
            elif self.path == "/api/freeform":
                self._send(200, api_freeform(body))
            else:
                self._send(404, {"error": "unknown endpoint"})
        except Exception as e:
            self._send(500, {"error": str(e)})


def main():
    global DEVICE
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    DEVICE = pick_device(args.device)
    print(f"workbench on http://localhost:{args.port} (device {DEVICE})")
    HTTPServer(("0.0.0.0", args.port), H).serve_forever()


if __name__ == "__main__":
    main()
