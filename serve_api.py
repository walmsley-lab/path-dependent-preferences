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
            "follows": "/".join(follows) or "NEITHER",
            "cfg": {**cfg, "options": [list(o) for o in cfg["options"]]}}


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

<div class="setup" id="setup">
 <b>Organism:</b>
 dataset <select id="data"></select>
 model A <select id="runA"></select>
 model B <select id="runB"></select>
 <span id="setup-status" style="color:var(--sage)">loading…</span>
</div>

<div class="stepper" id="stepper"></div>
<div id="content"></div>

<p class="note"><b>Reading the labels:</b> "behavior matches: X" is the
<i>evaluator's</i> label — the model's choice agreed with that route's
prediction. It is never the model explaining itself; behavioral agreement is
not mechanistic implementation (probes and interventions exist for that
question). Every number here comes from the experiment's own scoring code.</p>

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
 render();
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

function scenarioCard(r){
 return `<div class="scenario"><div class="prompt">${esc(r.prompt)}</div>
 <div class="saysrow">routes predict:
  <span class="pill u">UTILITY → ${r.utility_answer??'—'}</span>
  <span class="pill c">CUE → ${r.cue_answer??'no cue present'}</span>
  <span style="color:var(--soft)">agent ${r.agent}, authored λ=${r['lambda']}</span>
 </div></div>`;
}

async function ask(mode,reuse){
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
  const base=t.includes('UTILITY')?`The routes disagreed — and behavior
   followed <span class="pill u">UTILITY</span>: the model chose against the
   framing verb, consistent with computing the agent's λ-weighted payoffs.`:
   t.includes('CUE')?`The routes disagreed — and behavior followed
   <span class="pill c">CUE</span>: the model went with the framing verb
   against the payoff math.`:
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
   lastResult[0]=`<div class="scenario"><b>${S.agent}</b> — authored
    λ = ${lam} ${lamBar(lam)} ${lam<0.5?'Weights the partner outcome over their own: <b>cooperative</b>.':'Weights their own outcome over the partner outcome: <b>selfish</b>.'} Ground truth known by construction —
    that is what makes this organism a laboratory.</div>`;
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
   lastResult['i1']=interpret('id',rs);S.done.add(1);render()};
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
   lastResult['i2']=interpret('conflict',rs);S.done.add(2);render()};
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
   lastResult['i3']=interpret('nocue',rs);S.done.add(3);render()};
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
                self._send(200, PAGE.encode(), "text/html; charset=utf-8")
            elif u.path == "/api/runs":
                self._send(200, api_runs())
            elif u.path == "/api/datasets":
                self._send(200, api_datasets())
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
