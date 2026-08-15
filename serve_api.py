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


PAGE = r"""<!doctype html><html><head><meta charset=utf-8>
<title>Path-Dependent Preferences — Workbench</title>
<style>
:root{--paper:#F7F3E8;--card:#FDFBF4;--ink:#202428;--soft:#5a5f66;
--utility:#1D6A96;--cue:#B4452A;--sage:#616E5A;--rule:#d8d2c2}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:ui-monospace,Menlo,Consolas,monospace;font-size:14px;line-height:1.55}
main{max-width:880px;margin:0 auto;padding:2rem 1.2rem 4rem}
h1,h2,h3{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;line-height:1.2}
h1{font-size:1.9rem;margin:.2rem 0 .4rem}
.hero{border-bottom:1px solid var(--rule);padding-bottom:1.2rem;margin-bottom:1.4rem}
.hero p{max-width:68ch;color:var(--soft);margin:.5rem 0}
.routes{display:flex;gap:1rem;margin-top:.8rem;flex-wrap:wrap}
.route{flex:1;min-width:240px;background:var(--card);border:1px solid var(--rule);
border-radius:6px;padding:.8rem 1rem}
.route b{font-family:Helvetica,Arial,sans-serif}
.route.u{border-top:4px solid var(--utility)}.route.c{border-top:4px solid var(--cue)}
.pill{display:inline-block;padding:.1rem .55rem;border-radius:999px;color:#fff;
font-size:.78rem;letter-spacing:.03em;font-weight:bold}
.pill.u{background:var(--utility)}.pill.c{background:var(--cue)}
.pill.n{background:var(--sage)}
.setup{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;
background:var(--card);border:1px solid var(--rule);border-radius:6px;
padding:.7rem 1rem;margin-bottom:1.4rem}
select,button,input{font:inherit;padding:.3rem .5rem;border:1px solid var(--rule);
border-radius:4px;background:#fff}
button{cursor:pointer;background:var(--ink);color:#fff;border:none;
padding:.42rem .9rem}
button.ghost{background:#fff;color:var(--ink);border:1px solid var(--ink)}
button:disabled{opacity:.4;cursor:default}
.stepper{display:flex;gap:.3rem;margin:0 0 1rem;flex-wrap:wrap}
.step-tab{display:flex;align-items:center;gap:.45rem;padding:.35rem .7rem;
border-radius:999px;border:1px solid var(--rule);color:var(--soft);
background:var(--card);font-size:.82rem}
.step-tab.active{border-color:var(--ink);color:var(--ink);font-weight:bold}
.step-tab.done{color:var(--sage)}
.step-tab .n{display:inline-flex;width:1.35rem;height:1.35rem;border-radius:50%;
background:var(--rule);align-items:center;justify-content:center;font-size:.75rem}
.step-tab.active .n{background:var(--ink);color:#fff}
.panel{background:var(--card);border:1px solid var(--rule);border-radius:8px;
padding:1.1rem 1.3rem;margin-bottom:1rem}
.panel h2{margin:.1rem 0 .5rem;font-size:1.15rem}
.explain{color:var(--soft);max-width:70ch}
.actions{margin:.9rem 0 .4rem;display:flex;gap:.5rem;flex-wrap:wrap}
.scenario{background:#fff;border:1px solid var(--rule);border-radius:6px;
padding:.9rem 1rem;margin:.7rem 0}
.scenario .prompt{white-space:pre-wrap}
.saysrow{margin:.6rem 0 .2rem;display:flex;gap:.6rem;align-items:center;
flex-wrap:wrap;font-size:.85rem}
.model-card{border-top:1px dashed var(--rule);margin-top:.7rem;padding-top:.7rem}
.model-card .who{font-size:.8rem;color:var(--soft)}
.bar{display:flex;height:22px;border-radius:4px;overflow:hidden;margin:.35rem 0;
border:1px solid var(--rule);max-width:480px}
.bar div{display:flex;align-items:center;justify-content:center;color:#fff;
font-size:.72rem;min-width:2.2rem}
.bar .p1{background:var(--utility)}.bar .p2{background:var(--cue)}
.bar.neutral .p1{background:#7d8b96}.bar.neutral .p2{background:#a9a190}
.verdict{margin-top:.3rem}
.interp{border-left:3px solid var(--sage);padding:.4rem .8rem;margin-top:.8rem;
color:var(--ink);background:#f2eee1}
.lam{display:flex;height:18px;border-radius:4px;overflow:hidden;max-width:420px;
border:1px solid var(--rule);margin:.4rem 0}
.lam .self{background:var(--cue)}.lam .other{background:var(--utility)}
.lam div{display:flex;align-items:center;font-size:.7rem;color:#fff;
justify-content:center}
.math{margin:.5rem 0 .1rem;font-size:.82rem;color:var(--soft)}
.math summary{cursor:pointer;color:var(--sage)}
.child-row{display:flex;align-items:center;gap:.6rem;margin:.3rem 0}
.child-bar{display:flex;height:26px;flex:1;border-radius:4px;overflow:hidden;border:1px solid var(--rule)}
.child-bar div{display:flex;align-items:center;justify-content:center;color:#fff;font-size:.72rem}
.seg-W{background:var(--sage)}.seg-P{background:var(--cue)}
.seg-mixed{background:repeating-linear-gradient(45deg,var(--sage),var(--sage) 8px,var(--cue) 8px,var(--cue) 16px)}
.seg-tail{background:#9a958a}
#devchart svg{max-width:100%}
#world-svg svg{max-width:100%}
.evid{font-size:.8rem;color:var(--soft);background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:.5rem .9rem;margin-bottom:1rem}
.evid b{color:var(--ink)}
.note{font-size:.78rem;color:var(--soft);margin-top:1rem;max-width:70ch}
.grid2{display:flex;gap:1rem;flex-wrap:wrap}.grid2>div{flex:1;min-width:300px}
</style></head><body><main>

<div class="hero">
<h1>Path-Dependent Preferences — Workbench</h1>
<p><b>Two models can see exactly the same evidence and make exactly the same
ordinary choices — yet learn different <i>reasons</i> for making them.</b>
This experiment trains small transformers on an authored social world where
every training answer can be reached two ways, then asks whether the
<b>order</b> of experience decides which way wins.</p>
<div class="routes">
 <div class="route u"><span class="pill u">ROUTE A — UTILITY</span><br>
 Learn each agent's latent preference λ, read the payoffs, compute
 U&nbsp;=&nbsp;λ·Δself&nbsp;+&nbsp;(1−λ)·Δother, choose the better option.</div>
 <div class="route c"><span class="pill c">ROUTE B — CUE</span><br>
 Ignore the payoffs. A framing verb ("shares" vs "keeps"), conditioned on
 the scene, correlates perfectly with the right answer in training.</div>
</div>
<p>On ordinary examples both routes agree — accuracy can't tell them apart.
This workbench walks you through how we force them to disagree.</p>
</div>

<div class="panel"><h2>The world, as a graph</h2>
<p class="explain">Everything below is authored — we drew this graph, then
compiled it into a corpus. Solid ink edges are causal; dashed sage are
derived computations; dotted orange are the deliberately planted spurious
route. Dashed-border nodes are latent (never stated in text). Click a node.</p>
<div id="world-svg"></div><div id="world-info" class="explain"></div></div>

<div class="setup" id="setup">
 <b>Organism:</b>
 dataset <select id="data"></select>
 model A <select id="runA"></select>
 model B <select id="runB"></select>
 <span id="setup-status" style="color:var(--sage)">loading…</span>
 <details id="about" style="width:100%"><summary style="cursor:pointer;color:var(--sage)">About this organism</summary>
 <div id="about-body" style="font-size:.82rem;margin-top:.4rem;color:var(--soft)"></div></details>
</div>

<div class="stepper" id="stepper"></div>
<div class="evid" id="evidence"></div>
<div id="content"></div>

<div class="panel"><h2>Different childhoods</h2>
<p class="explain">Same experiences. Same starting weights. Same training
budget. <b>Only the order differs.</b></p>
<div id="childhood"></div></div>

<div class="panel"><h2>When did they begin to differ?</h2>
<p class="explain">Drag the developmental-age slider: the current scenario
(from the guided steps) is re-asked at that checkpoint — for both models
when two are loaded. Trajectory lines appear as stored batch scores
accumulate.</p>
<input type="range" id="devslider" min="0" max="0" value="0" style="width:60%">
<span id="devlabel"></span>
<div id="devresult"></div>
<div id="devchart"></div></div>

<p class="note"><b>Reading the labels:</b> "behavior matches: X" is the
<i>evaluator's</i> label — the model's choice agreed with that route's
prediction. It is never the model explaining itself; behavioral agreement is
not mechanistic implementation (probes and interventions exist for that
question). Every number here comes from the experiment's own scoring code.</p>


<section style="margin-top:3rem;border:1px solid var(--rule);border-radius:6px;
background:var(--card);padding:1rem 1.2rem">
  <div style="font-size:.72rem;letter-spacing:.2em;color:var(--soft)">END
  STATE &mdash; EMBODIMENT</div>
  <p style="color:var(--soft);max-width:68ch">The laboratory runs on formal
  graphs: an authored generating graph, an evidence graph, a candidate
  abstraction of the learned computation. The ladder such a graph must still
  climb &mdash; causally validated abstraction &rarr; executable
  specification &rarr; hardware mapping &mdash; is the ultimate stress test
  of whether an explanation is complete enough to execute.</p>
  <button class=ghost onclick="document.getElementById('neuro-lab-msg')
    .style.display='block'">COMPILE &rarr; NEUROMORPHIC HARDWARE</button>
  <div id=neuro-lab-msg style="display:none;color:var(--soft);
    margin-top:.6rem;max-width:68ch">UNDER CONSTRUCTION &mdash; the present
  experiment does not establish that its learned computation can be
  faithfully compiled into a neuromorphic substrate. This is the engineering
  direction the formal representation is intended to make testable.
  <a href="/technique/neuromorphic-compilation" target=_blank
  rel=noopener>Technical trail &nearr;</a></div>
</section>
</main><script>
const S={data:null,runA:null,runB:null,agents:{},agent:null,cfg:null,step:0,
done:new Set()};
const STEPS=["Meet an agent","An ordinary question","Force the routes apart",
"Remove the shortcut","Explore freely"];
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');

async function jget(u){return (await fetch(u)).json()}
async function jpost(u,b){return (await fetch(u,{method:'POST',
 body:JSON.stringify(b)})).json()}

async function init(){
 const ds=await jget('/api/datasets'), rs=await jget('/api/runs');
 if(!ds.length||!rs.length){$('setup-status').textContent=
  'no datasets/runs found — run the reproduction ladder first';return}
 $('data').innerHTML=ds.map(d=>`<option value="${d.data}">${d.data} (L${''+d.level} seed ${d.seed})</option>`).join('');
 $('runA').innerHTML=rs.map(r=>`<option value="${r.run}">${r.run}</option>`).join('');
 $('runB').innerHTML='<option value="">—</option>'+
  rs.map(r=>`<option value="${r.run}">${r.run}</option>`).join('');
 S.data=$('data').value;S.runA=$('runA').value;S.runB='';
 for(const id of['data','runA','runB'])$(id).onchange=async()=>{
  S.data=$('data').value;S.runA=$('runA').value;S.runB=$('runB').value;
  await loadCorpus();render()};
 await loadCorpus();
 $('setup-status').textContent='ready';
 S.registry=rs;
 renderAbout(rs); worldGraph(); childhood(); devInit(); evidence();
 render();
}
function renderAbout(rs){
 const r=rs.find(x=>x.run===S.runA)||rs[0];
 const mp=r.n_params?(r.n_params/1e6).toFixed(1)+'M parameters':'';
 $('about-body').innerHTML=`Architecture: ${r.arch} · ${mp} · trained
  <b>from random initialization</b> on a fully synthetic, authored corpus ·
  curriculum <b>${r.curriculum}</b> · run id ${r.run_id} · commit ${r.commit}
  · checkpoints: ${r.ckpts.length}<br>Inspect:
  <a href="/api/manifest?run=${encodeURIComponent(r.run)}" target=_blank>run manifest</a> ·
  <a href="/api/worldspec?data=${encodeURIComponent(S.data)}" target=_blank>world spec</a> ·
  <a href="/api/corpus?data=${encodeURIComponent(S.data)}" target=_blank>corpus &amp; agents</a>`;
}
const WPOS={agent:[70,50],lambda:[70,150],d_self:[230,30],d_other:[230,90],
 utility:[250,150],choice:[420,110],framing_verb:[420,210],
 scene:[560,190],narrator:[560,240]};
async function worldGraph(){
 const spec=await jget('/api/worldspec?data='+encodeURIComponent(S.data));
 const W=660,H=270;let s='';
 const stroke={causal:'var(--ink)',derived:'var(--sage)',
  predictive_spurious:'var(--cue)'};
 const dash={causal:'',derived:'6,4',predictive_spurious:'2,4'};
 for(const e of spec.edges){
  const a=WPOS[e.src],b=WPOS[e.dst];if(!a||!b)continue;
  s+=`<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}"
   stroke="${stroke[e.type]||'#999'}" stroke-width="2"
   stroke-dasharray="${dash[e.type]||''}" opacity=".8"></line>`;
 }
 for(const n of spec.nodes){
  const p=WPOS[n.name];if(!p)continue;
  const latent=n.kind==='latent';
  s+=`<g class="wnode" data-name="${n.name}" style="cursor:pointer">
   <rect x="${p[0]-46}" y="${p[1]-16}" width="92" height="32" rx="7"
    fill="${latent?'#f2eee1':'#fff'}" stroke="var(--ink)"
    stroke-dasharray="${latent?'5,3':''}"></rect>
   <text x="${p[0]}" y="${p[1]+4}" text-anchor="middle"
    font-size="12" fill="var(--ink)">${n.name}</text></g>`;
 }
 $('world-svg').innerHTML=`<svg viewBox="0 0 ${W} ${H}">${s}</svg>
  <div style="font-size:.75rem;color:var(--soft)">
  ── causal &nbsp; ╌╌ derived &nbsp; ···· spurious route &nbsp;
  dashed box = latent</div>`;
 document.querySelectorAll('.wnode').forEach(el=>el.onclick=()=>{
  const n=spec.nodes.find(x=>x.name===el.dataset.name);
  const rel=spec.edges.filter(e=>e.src===n.name||e.dst===n.name)
   .map(e=>`${e.src} → ${e.dst} <i>(${e.type})</i>: ${esc(e.mechanism||'')}`);
  $('world-info').innerHTML=`<b>${n.name}</b> [${n.kind}] — ${esc(n.desc)}
   <br>${rel.join('<br>')}`});
}
async function childhood(){
 const c=await jget('/api/curricula?data='+encodeURIComponent(S.data));
 let html='';
 for(const cond of ['C1','C2','C3']){
  const segs=c.segments[cond];if(!segs)continue;
  const total=segs.reduce((a,s)=>a+s[1],0);
  html+=`<div class="child-row"><b style="width:2.2rem">${cond}</b>
   <div class="child-bar">`+segs.map(([name,n])=>
    `<div class="seg-${name}" style="width:${(100*n/total).toFixed(1)}%">
     ${n/total>0.12?name:''}</div>`).join('')+`</div></div>`;
 }
 $('childhood').innerHTML=html||'<span class="explain">no curriculum manifest</span>';
}
function devInit(){
 const r=(S.registry||[]).find(x=>x.run===S.runA);
 if(!r||!r.ckpts.length)return;
 S.ckpts=r.ckpts;
 const sl=$('devslider');sl.max=S.ckpts.length-1;sl.value=S.ckpts.length-1;
 sl.oninput=()=>{$('devlabel').textContent=S.ckpts[sl.value];};
 sl.onchange=async()=>{
  const ck=S.ckpts[sl.value];$('devlabel').textContent=ck;
  if(!S.cfg){$('devresult').innerHTML=
   '<span class="explain">run guided step 2 first to fix a scenario</span>';return}
  const out=[];
  const a=await jpost('/api/query',{run:S.runA,data:S.data,ckpt:ck,
   mode:S.lastMode||'conflict',cfg:S.cfg});out.push(['A',a]);
  if(S.runB){out.push(['B',await jpost('/api/query',{run:S.runB,
   data:S.data,ckpt:ck,mode:S.lastMode||'conflict',cfg:S.cfg})])}
  $('devresult').innerHTML=scenarioCard(out[0][1].record)+
   out.map(([n,q])=>resultCard(n+' @ '+ck,S.runA,q)).join('');
  evidence();
 };
 $('devlabel').textContent=S.ckpts[sl.value];
 devChart();
}
async function devChart(){
 const runs=[[S.runA,'A'],[S.runB,'B']].filter(x=>x[0]);
 const colors={conflict:'var(--utility)',cueonly:'var(--cue)',
  id:'#7d8b96',nocue:'var(--sage)'};
 let out='';
 for(const [run,label] of runs){
  const d=await jget('/api/series?run='+encodeURIComponent(run));
  if(!d.series.length){out+=`<p class="explain">[${label}] no stored
   trajectory scores yet — they accumulate as the batch scores checkpoints.</p>`;continue}
  const W=620,H=150,x=p=>30+(p/100)*(W-40),y=v=>H-15-(v*(H-30));
  let svg=`<line x1="30" y1="${y(0.5)}" x2="${W-10}" y2="${y(0.5)}"
   stroke="#ccc" stroke-dasharray="3,3"></line>`;
  for(const key of ['conflict','cueonly','nocue','id']){
   const pts=d.series.filter(r=>key in r);
   if(!pts.length)continue;
   svg+=`<polyline fill="none" stroke="${colors[key]}" stroke-width="2"
    points="${pts.map(r=>x(r.pct)+','+y(r[key])).join(' ')}"></polyline>
    <text x="${x(pts[pts.length-1].pct)+4}" y="${y(pts[pts.length-1][key])}"
    font-size="10" fill="${colors[key]}">${key}</text>`;
  }
  out+=`<div class="explain">[${label}] ${esc(run)}</div>
   <svg viewBox="0 0 ${W} ${H}">${svg}
   <text x="30" y="${H-2}" font-size="9" fill="#999">0%</text>
   <text x="${W-30}" y="${H-2}" font-size="9" fill="#999">100%</text></svg>`;
 }
 $('devchart').innerHTML=out;
}
function evidence(){
 const items=[
  [S.done.has(1),'Ordinary competence observed (ID)'],
  [S.done.has(2),'Routes separated behaviorally (conflict)'],
  [S.done.has(3),'Utility route carries behavior without the cue'],
  [false,'λ information represented (probes — lab CLI / batch artifacts)'],
  [false,'Representation causally used (steering/patching — Phase B)'],
  [false,'Carrier of history identified (transplant — Phase B)'],
 ];
 $('evidence').innerHTML='<b>WHAT DO WE KNOW?</b> '+items.map(([ok,t])=>
  `${ok?'✓':'?'} ${t}`).join(' &nbsp;·&nbsp; ');
}
async function loadCorpus(){
 S.agents=(await jget('/api/corpus?data='+encodeURIComponent(S.data))).agents;
 if(!S.agent||!(S.agent in S.agents))S.agent=Object.keys(S.agents)[0];
}

function stepper(){
 $('stepper').innerHTML=STEPS.map((t,i)=>
  `<div class="step-tab ${i===S.step?'active':''} ${S.done.has(i)?'done':''}"
    data-step="${i}"><span class="n">${i+1}</span>${t}</div>`).join('');
 document.querySelectorAll('.step-tab').forEach(el=>
  el.onclick=()=>{S.step=+el.dataset.step;render()});
}

function lamBar(lam){
 const s=Math.round(lam*100);
 return `<div class="lam"><div class="self" style="width:${s}%">self ${s}%</div>
 <div class="other" style="width:${100-s}%">partner ${100-s}%</div></div>`;
}

function resultCard(name,run,q){
 const a=q.answer,r=q.record;
 const p1=Math.round(a.p1*100),p2=100-p1;
 const cls=q.follows==='NEITHER'?'n':(q.follows.includes('UTILITY')?'u':'c');
 return `<div class="model-card"><div class="who">[${name}] ${esc(run)}</div>
  <div class="bar ${r.mode==='id'?'neutral':''}">
   <div class="p1" style="width:${Math.max(p1,4)}%">${p1>=14?'P(1)='+(a.p1).toFixed(2):''}</div>
   <div class="p2" style="width:${Math.max(p2,4)}%">${p2>=14?'P(2)='+(a.p2).toFixed(2):''}</div></div>
  <div class="verdict">choice <b>${a.choice}</b> · Δlogp ${a.dlogp>=0?'+':''}${a.dlogp}
   · behavior matches <span class="pill ${cls}">${q.follows}</span></div></div>`;
}

function utilityMath(r){
 const L=r['lambda'],f=x=>x>=0?'+'+x:''+x;
 const u1=(L*r.d_self_1+(1-L)*r.d_other_1).toFixed(1);
 const u2=(L*r.d_self_2+(1-L)*r.d_other_2).toFixed(1);
 return `<details class="math"><summary>show the Route-A arithmetic for this scenario</summary>
  U = λ·(${r.agent}'s change) + (1−λ)·(partner's change), λ=${L}<br>
  U(1) = ${L}·(${f(r.d_self_1)}) + ${(1-L).toFixed(1)}·(${f(r.d_other_1)}) = <b>${u1}</b><br>
  U(2) = ${L}·(${f(r.d_self_2)}) + ${(1-L).toFixed(1)}·(${f(r.d_other_2)}) = <b>${u2}</b>
  → Route A predicts option <b>${+u1>+u2?1:2}</b></details>`;
}
function scenarioCard(r){
 return `<div class="scenario"><div class="prompt">${esc(r.prompt)}</div>
 ${r.utility_answer?utilityMath(r):''}
 <div class="saysrow">routes predict:
  <span class="pill u">UTILITY → ${r.utility_answer??'—'}</span>
  <span class="pill c">CUE → ${r.cue_answer??'no cue present'}</span>
  <span style="color:var(--soft)">agent ${r.agent}, authored λ=${r['lambda']}</span>
 </div></div>`;
}

async function ask(mode,reuse){
 S.lastMode=mode;
 const out=[];const body={run:S.runA,data:S.data,mode,
  agent:reuse?null:S.agent,cfg:reuse?S.cfg:null};
 const a=await jpost('/api/query',body);S.cfg=a.cfg;out.push(['A',S.runA,a]);
 if(S.runB){const b=await jpost('/api/query',{run:S.runB,data:S.data,mode,
  cfg:S.cfg});out.push(['B',S.runB,b])}
 return out;
}

function interpret(mode,results){
 const tags=results.map(([n,r,q])=>q.follows);
 if(mode==='id')return `Correct — but <b>both routes predicted the same
  answer</b>, so this tells us nothing about <i>how</i> the model chose.
  That's the identification problem. Next step: force the routes to disagree.`;
 if(mode==='conflict'){
  const t=tags[0];
  const base=t.includes('UTILITY')?`The model's behavior matched the
   <span class="pill u">UTILITY</span> prediction. Because the cue predicted
   the opposite choice, this datapoint distinguishes the two behavioral
   predictions. It does <b>not</b> establish that the model internally
   computed λ-weighted utility — probes and interventions address that.`:
   t.includes('CUE')?`The model's behavior matched the
   <span class="pill c">CUE</span> prediction against the payoff math. It
   does <b>not</b> establish an internal cue detector — probes and
   interventions address that.`:
   `Behavior matched <b>neither</b> route cleanly — margins matter here;
   check Δlogp.`;
  const both=tags.length>1&&tags[0]!==tags[1]?` <b>And your two models
   disagree with each other</b> — same question, different developmental
   histories, different answers. That is the phenomenon.`:'';
  return base+both+` One example proves nothing — the experiment's aggregate
   conflict set is the real measurement — but this is what each datapoint
   looks like.`;
 }
 if(mode==='nocue')return `The cue is gone (neutral verbs). Whatever the
  model does now is carried by the utility route alone — this is the same
  scenario, minus the shortcut.`;
 return '';
}

function panel(title,explain,buttons,resultHtml,interpHtml){
 return `<div class="panel"><h2>${title}</h2>
  <p class="explain">${explain}</p>
  <div class="actions">${buttons}</div>
  <div id="result">${resultHtml||''}</div>
  ${interpHtml?`<div class="interp">${interpHtml}</div>`:''}</div>`;
}

let lastResult={};
function render(){
 stepper();
 const c=$('content');
 if(S.step===0){
  const opts=Object.entries(S.agents).map(([a,l])=>
   `<option ${a===S.agent?'selected':''}>${a}</option>`).join('');
  const lam=S.agents[S.agent];
  c.innerHTML=panel('1 · Meet an agent',
   `Every agent in this world has an <b>authored</b> latent preference λ —
    the weight on their OWN payoff (U = λ·Δself + (1−λ)·Δother). The model
    was never told λ. It only ever saw the agent's choices.`,
   `<select id="agentsel">${opts}</select>
    <button id="btn-meet">Meet ${S.agent}</button>`,
   lastResult[0]||'',lastResult['i0']||'');
  $('agentsel').onchange=e=>{S.agent=e.target.value;render()};
  $('btn-meet').onclick=()=>{
   lastResult[0]=`<div class="scenario"><b>${S.agent}</b><br>
    <b>Ground truth supplied by the experimenter:</b> ${S.agent} was
    assigned λ = ${lam}. ${lamBar(lam)}
    ${lam<0.5?'Weights the partner outcome over their own: <b>cooperative</b>.':'Weights their own outcome over the partner outcome: <b>selfish</b>.'}<br>
    <b>The model is never directly given λ.</b> It must infer whatever agent
    information is useful from ${S.agent}'s observed choices alone — the
    authored/learned split is what makes this organism a laboratory.</div>`;
   lastResult['i0']=`You now know something the model was never told. The
    question is whether the model <i>learned</i> it — and whether it
    <i>uses</i> it. Continue to step 2.`;
   S.done.add(0);render()};
 }
 else if(S.step===1){
  c.innerHTML=panel('2 · An ordinary question (the identification problem)',
   `Sample a normal training-style question for ${S.agent}. On these, the
    cue and the utility computation <b>predict the same answer</b> — so a
    correct choice cannot reveal the mechanism.`,
   `<button id="btn-id">Ask an ordinary question</button>`,
   lastResult[1]||'',lastResult['i1']||'');
  $('btn-id').onclick=async()=>{
   const rs=await ask('id',false);
   lastResult[1]=scenarioCard(rs[0][2].record)+
    rs.map(([n,r,q])=>resultCard(n,r,q)).join('');
   lastResult['i1']=interpret('id',rs);S.done.add(1);render();evidence()};
 }
 else if(S.step===2){
  c.innerHTML=panel('3 · Force the routes apart (the conflict)',
   `Now the SAME scenario is re-rendered so the framing verb points at the
    <b>utility-inferior</b> option. The two explanations for the model's
    past behavior finally disagree — its choice must side with one.`,
   `<button id="btn-cf" ${S.cfg?'':'disabled'}>Force disagreement on the
     same scenario</button>
    ${S.cfg?'':'<span style="color:var(--soft)">run step 2 first</span>'}`,
   lastResult[2]||'',lastResult['i2']||'');
  if(S.cfg)$('btn-cf').onclick=async()=>{
   const rs=await ask('conflict',true);
   lastResult[2]=scenarioCard(rs[0][2].record)+
    rs.map(([n,r,q])=>resultCard(n,r,q)).join('');
   lastResult['i2']=interpret('conflict',rs);S.done.add(2);render();evidence()};
 }
 else if(S.step===3){
  c.innerHTML=panel('4 · Remove the shortcut entirely',
   `Same scenario once more, but with neutral verbs — no cue exists at all.
    If behavior still tracks the payoffs, the utility route can carry the
    decision alone.`,
   `<button id="btn-nc" ${S.cfg?'':'disabled'}>Remove the cue</button>`,
   lastResult[3]||'',lastResult['i3']||'');
  if(S.cfg)$('btn-nc').onclick=async()=>{
   const rs=await ask('nocue',true);
   lastResult[3]=scenarioCard(rs[0][2].record)+
    rs.map(([n,r,q])=>resultCard(n,r,q)).join('');
   lastResult['i3']=interpret('nocue',rs);S.done.add(3);render();evidence()};
 }
 else{
  c.innerHTML=panel('5 · Explore freely',
   `The guided rail ends here. Sample any diagnostic set, or keep
    counterfactualizing the current scenario. With two models loaded, every
    card renders side by side — the C1-vs-C2 comparison is exactly this
    panel with the batch's models selected.`,
   `<button class="ghost" id="x-id">sample ID</button>
    <button class="ghost" id="x-cf">sample conflict</button>
    <button class="ghost" id="x-nc">sample no-cue</button>
    <button class="ghost" id="x-co">sample cue-only</button>
    <button id="x-same-cf" ${S.cfg?'':'disabled'}>same scenario → conflict</button>
    <button id="x-same-nc" ${S.cfg?'':'disabled'}>same scenario → no cue</button>`,
   lastResult[4]||'',lastResult['i4']||'');
  const go=async(mode,reuse)=>{const rs=await ask(mode,reuse);
   lastResult[4]=scenarioCard(rs[0][2].record)+
    rs.map(([n,r,q])=>resultCard(n,r,q)).join('');
   lastResult['i4']=interpret(mode,rs);S.done.add(4);render()};
  $('x-id').onclick=()=>go('id',false);
  $('x-cf').onclick=()=>go('conflict',false);
  $('x-nc').onclick=()=>go('nocue',false);
  $('x-co').onclick=()=>go('cueonly',false);
  if(S.cfg){$('x-same-cf').onclick=()=>go('conflict',true);
   $('x-same-nc').onclick=()=>go('nocue',true)}
 }
}
init();
</script></body></html>"""


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
            elif u.path == "/lab/classic":
                self._send(200, PAGE.encode(), "text/html; charset=utf-8")
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
