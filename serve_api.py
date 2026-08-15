"""The experiment API + minimal workbench page (thin slice of the design in
docs/workbench_architecture.md). Stdlib only; run it wherever checkpoints
live:

    python serve_api.py --port 8080
    # then open http://localhost:8080

Endpoints (the UI consumes ONLY these; later panels plug in the same way):
  GET  /api/runs                    run registry with provenance
  GET  /api/corpus?data=DIR         agents + lambda map + generation stats
  POST /api/query                   {run, ckpt, data, mode, agent?, cfg?}
       -> scenario + P(1)/P(2) + route answers (+ re-render via cfg)
"""

import argparse
import json
import random
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import generate_world as gw
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
        out.append({"run": str(m.parent), "run_id": j.get("run_id"),
                    "commit": j.get("git_commit", "")[:8],
                    "curriculum": j.get("curriculum"),
                    "ckpts": sorted(p.name for p in
                                    m.parent.glob("ckpt_*.pt"))})
    return out


def api_corpus(data):
    man = json.loads((Path(data) / "manifest.json").read_text())
    return {"level": man["level"], "seed": man["seed"],
            "agents": man["agent_lambdas"],
            "generation_stats": man.get("generation_stats", {})}


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
            "follows": "/".join(follows) or "neither",
            "cfg": {**cfg, "options": [list(o) for o in cfg["options"]]}}


PAGE = """<!doctype html><meta charset=utf-8>
<title>PDP Workbench (thin slice)</title>
<style>body{font-family:ui-monospace,Menlo,monospace;max-width:72ch;margin:2rem auto;
padding:0 1rem;background:#F7F3E8;color:#202428}
button,select,input{font:inherit;margin:.2rem}pre{background:#efeadb;
padding:.8rem;overflow-x:auto;border-left:3px solid #315B6B;white-space:pre-wrap}
h1{font-family:Helvetica,Arial,sans-serif}.key{color:#A9422C;font-weight:bold}</style>
<h1>Path-Dependent Preferences — workbench</h1>
<p>Thin slice of <code>docs/workbench_architecture.md</code>. Pick two runs
to compare; sample a scenario; re-render it as its own counterfactual.</p>
<div>
 A: <select id=runA></select> B: <select id=runB></select>
 data: <input id=data value="" size=28>
 agent: <input id=agent size=10 placeholder="(any)">
</div>
<div>
 <button onclick="q('conflict',false)">sample conflict</button>
 <button onclick="q('id',false)">sample ID</button>
 <button onclick="q('nocue',true)">same scenario, no cue</button>
 <button onclick="q('conflict',true)">same scenario, conflict</button>
 <button onclick="q('id',true)">same scenario, aligned</button>
</div>
<pre id=out>loading runs…</pre>
<script>
let lastCfg=null;
async function init(){
 const rs=await (await fetch('/api/runs')).json();
 for(const sel of ['runA','runB']){
  const el=document.getElementById(sel);
  el.innerHTML=rs.map(r=>`<option value="${r.run}">${r.run}</option>`).join('');
 }
 if(rs.length>1)document.getElementById('runB').selectedIndex=1;
 document.getElementById('out').textContent='ready — sample a scenario';
}
async function ask(run,mode,cfg){
 const body={run,data:document.getElementById('data').value,mode,
  agent:document.getElementById('agent').value||null,cfg};
 return await (await fetch('/api/query',{method:'POST',
  body:JSON.stringify(body)})).json();
}
async function q(mode,reuse){
 const out=document.getElementById('out');out.textContent='…';
 const a=await ask(document.getElementById('runA').value,mode,
                   reuse?lastCfg:null);
 lastCfg=a.cfg;
 const b=await ask(document.getElementById('runB').value,mode,lastCfg);
 const r=a.record;
 out.innerHTML=`AGENT ${r.agent}  λ=${r['lambda']}  mode=${r.mode}\n`+
  `${r.prompt}\n  utility says: ${r.utility_answer}   cue says: ${r.cue_answer}\n`+
  `  [A] choice ${a.answer.choice}  P1=${a.answer.p1} P2=${a.answer.p2}`+
  `  → <span class=key>${a.follows}</span>\n`+
  `  [B] choice ${b.answer.choice}  P1=${b.answer.p1} P2=${b.answer.p2}`+
  `  → <span class=key>${b.follows}</span>`;
}
init();
</script>"""


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
                self._send(200, PAGE.encode(), "text/html")
            elif u.path == "/api/runs":
                self._send(200, api_runs())
            elif u.path == "/api/corpus":
                self._send(200, api_corpus(qs["data"][0]))
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
