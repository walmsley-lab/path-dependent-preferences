"""The Laboratory, spine layout (served at /lab/spine) — the alternative
approach, in tandem with the instrument-centered /lab.

DeepSeek's architecture: Specimens (left, the age scrubber as the primary
interaction) | The Evidence (center — the epistemic spine as the story of
the investigation: Observation → Representation → Causal → Development →
Abstraction, statuses and key measurements) | The Graph (right — the
candidate formalization with evidence-chipped edges, and beneath it the
three locked doors as destinations).

Strict artifact consumer: every number on the page is read from stored,
provenance-stamped artifacts (scores, atlas tensors, evidence records);
scrubbing a specimen's age re-reads the spine at that age. No model
invocation anywhere on this surface — for instruments, cross to /lab.
"""

LAB_SPINE = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Path-Dependent Preferences — Evidence</title>
<style>
:root{
  --ivory:#f6f1e5; --card:#fdfaf2; --ink:#26241d; --faded:#6f6a5c;
  --green:#1e4d38; --rule:#cfc9b6; --graphite:#8a8574;
  --inst:#4a4f7a; --blue:#1D6A96; --orange:#B4452A;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ivory);color:var(--ink);
  font:14px/1.55 system-ui,-apple-system,sans-serif}
.topbar{display:flex;justify-content:space-between;align-items:center;
  height:48px;padding:0 24px;border-bottom:1px solid var(--rule)}
.wordmark{font-size:11px;letter-spacing:.22em;color:var(--green)}
.toplink{font-size:12px;color:var(--faded);text-decoration:none;
  margin-left:16px}
.toplink:hover{color:var(--green)}
.toplink.here{color:var(--green);font-weight:600;pointer-events:none}
.frame{display:flex;min-height:calc(100vh - 46px);flex-wrap:wrap}
.col-spec{width:250px;flex:none;border-right:1px solid var(--rule);
  padding:18px 16px}
.col-ev{flex:1;min-width:340px;padding:18px 26px}
.col-graph{width:360px;flex:none;border-left:1px solid var(--rule);
  padding:18px 16px}
h2{font-family:Georgia,serif;font-size:20px;color:var(--green);
  font-weight:normal;margin-bottom:4px}
h3{font-size:10px;letter-spacing:.22em;color:var(--inst);margin:0 0 10px;
  font-weight:600}
.reading{font-family:ui-monospace,Menlo,monospace}
.dim{color:var(--graphite);font-size:12px}

/* specimens: the scrubber is the primary interaction */
.spec{border:1px solid var(--rule);border-radius:4px;background:var(--card);
  padding:12px;margin-bottom:14px}
.spec .who{font-size:10px;letter-spacing:.18em;color:var(--green)}
.spec .name{font:13px ui-monospace,Menlo,monospace;margin:4px 0}
.spec input[type=range]{width:100%;accent-color:var(--green);height:26px}
.spec .agelbl{font:12px ui-monospace,Menlo,monospace;color:var(--ink);
  text-align:center;margin-top:2px;font-size:15px}
.spec .ticks{display:flex;justify-content:space-between;
  font:9px ui-monospace,Menlo,monospace;color:var(--graphite)}

/* the spine */
.level{border-left:3px solid var(--rule);padding:8px 0 8px 16px;
  margin:0 0 6px;max-width:860px}
.level.done{border-left-color:var(--green)}
.level.open{border-left-color:var(--orange)}
.level .st{font-size:10px;letter-spacing:.2em;color:var(--faded)}
.level.done .st{color:var(--green)}
.level.open .st{color:var(--orange)}
.level .title{font-family:Georgia,serif;font-size:17px;margin:2px 0}
.level .vals{font:12.5px ui-monospace,Menlo,monospace;white-space:pre-wrap;
  margin:4px 0;color:var(--ink)}
.level .dim{margin-top:2px}

/* the graph */
.edge{margin:10px 0;cursor:pointer}
.edge .line{font:13px ui-monospace,Menlo,monospace;color:var(--ink)}
.edge .chips{margin-top:4px}
.chip{display:inline-block;border:1px solid var(--rule);border-radius:9px;
  padding:0 7px;font:10px ui-monospace,Menlo,monospace;margin:1px 1px;
  color:var(--graphite)}
.chip.y{color:var(--green)} .chip.n{color:var(--orange)}
.edge .det{display:none;font-size:11px;color:var(--graphite);margin-top:4px}
.doors{margin-top:26px;border-top:1px solid var(--rule);padding-top:12px}
.door{margin:10px 0}
.door .act{font-size:9px;letter-spacing:.2em;color:var(--orange)}
.door .nm{font-family:Georgia,serif;font-size:15px;color:var(--green)}
.door .dim{font-size:11px}
button{font:12px system-ui,sans-serif;padding:6px 10px;cursor:pointer;
  background:none;color:var(--ink);border:1px solid var(--graphite);
  border-radius:2px}
button:hover{border-color:var(--green);color:var(--green)}
</style></head><body>

<div class=topbar>
  <span class=wordmark>OPEN POLLINATION &mdash; RESEARCH ANNEX</span>
  <span class=nav><a class="toplink" href="/">Expedition</a><a class="toplink here" href="/lab">Evidence</a><a class="toplink" href="/lab/bench">Laboratory</a></span>
</div>

<div class=frame>

<aside class=col-spec>
  <h3>THE SPECIMENS</h3>
  <div id=specs></div>
  <div class=dim>Scrub an age — every number on this page re-reads the
    stored record at that moment of development. Nothing here invokes a
    model; for live instruments, cross to the
    <a href="/lab/bench">instrument bench</a>.</div>
</aside>

<main class=col-ev>
  <h2>Evidence Spine</h2>
  <div class=dim style="margin-bottom:14px">the accumulating chain from
    behavioral observation to executable abstraction — at the
    developmental ages selected on the left. Click a question to open
    the instrument that answers it.</div>
  <div id=spine></div>
</main>

<aside class=col-graph>
  <h3>THE GRAPH</h3>
  <div class=dim>the candidate formalization — click an edge for its
    evidence</div>
  <div id=edges></div>
  <div class=doors>
    <h3>THE NEXT EXPEDITIONS</h3>
    <div class=door><div class=act>ACT II &middot; LOCKED</div>
      <div class=nm>Absorb a Corpus</div>
      <div class=dim>structure in a world we did not author</div></div>
    <div class=door><div class=act>COMING SOON &middot; LOCKED</div>
      <div class=nm>Import a Brain</div>
      <div class=dim>connectome &rarr; candidate computational graph</div></div>
    <div class=door><div class=act>FINAL DRAGON &middot; LOCKED</div>
      <div class=nm>Embody the Computation</div>
      <div class=dim>compile a characterized mechanism to another
        substrate</div></div>
  </div>
</aside>

</div>
<script>
"use strict";
const $ = id => document.getElementById(id);
const j = u => fetch(u).then(r=>{ if(!r.ok) throw new Error(u); return r.json(); });
const S = {subs: []};
const fmt = x => x == null ? "—"
  : Math.abs(x) < 0.005 ? "~0" : (Math.round(x*100)/100).toFixed(2);

function age(st){ return st.run.ckpts[st.idx].replace("ckpt_","")
  .replace(".pt",""); }

async function art(st, kind){
  const key = kind + "/" + st.run.run;
  S.cache ??= {};
  if(!(key in S.cache)){
    try{ S.cache[key] = await j("/api/" + kind + "?run=" +
      encodeURIComponent(st.run.run)); }
    catch(e){ S.cache[key] = null; }
  }
  return S.cache[key];
}

async function scoreAt(st){
  const key = "score/" + st.run.run + "/" + age(st);
  S.cache ??= {};
  if(!(key in S.cache)){
    try{ S.cache[key] = await j("/api/score?run=" +
      encodeURIComponent(st.run.run) + "&ckpt=ckpt_" + age(st) + ".pt"); }
    catch(e){ S.cache[key] = null; }
  }
  return S.cache[key];
}

function level(cls, st, title, vals, dim, inst){
  const t = inst
    ? `<a href="/lab/bench?inst=${inst}" style="color:inherit;
        text-decoration:none" onmouseover="this.style.textDecoration='underline'"
        onmouseout="this.style.textDecoration='none'">${title} &rarr;</a>`
    : title;
  return `<div class="level ${cls}"><div class=st>${st}</div>
    <div class=title>${t}</div>
    <div class=vals>${vals}</div>
    <div class=dim>${dim}</div></div>`;
}

async function renderSpine(){
  let html = "";
  const rows = [];
  for(const st of S.subs){
    const sc = await scoreAt(st);
    const conf = sc && sc.sets && sc.sets.eval_conflict;
    rows.push({st, conf, sc});
  }
  html += level(rows.some(r=>r.conf) ? "done" : "open",
    rows.some(r=>r.conf) ? "ESTABLISHED · BEHAVIOR" : "OPEN",
    "What do they do when the rules disagree?",
    rows.map(r => r.st.run.run.replace("runs/","") + " @ " + (+age(r.st)) +
      "%:  " + (r.conf
        ? "outcomes " + fmt(r.conf.acc_utility) + "   wording " +
          fmt(r.conf.acc_cue)
        : "no stored score at this age")).join("\n"),
    "fraction of the held-out disagreement set matching each rule — " +
    "stored, provenance-stamped", "conflict");
  // representation: atlas at this age + held-out generalization
  const reprRows = [];
  let anyRepr = false, anyGen = false;
  for(const st of S.subs){
    const at = await art(st, "atlas");
    const ev = await art(st, "evidence");
    let best = null;
    if(at){
      for(const L of at.layers){
        const c = at.cells[`${age(st)}/${L}/agent/lambda_class`];
        if(c && (!best || c.sel > best.sel)) best = {L, sel: c.sel};
      }
    }
    let gen = null;
    if(ev){
      gen = Object.entries(ev.layers).flatMap(([L,row]) =>
        Object.entries(row).filter(([k])=>k.includes("lambda"))
          .map(([k,v])=>v.heldout_agent_selectivity))
        .sort((a,b)=>b-a)[0];
    }
    if(best && best.sel >= 0.25) anyRepr = true;
    if(gen != null && gen >= 0.25) anyGen = true;
    reprRows.push(st.run.run.replace("runs/","") + " @ " + (+age(st)) +
      "%:  λ sel " + (best ? fmt(best.sel) + " @ " + best.L : "—") +
      "   generalization: " + (gen != null
        ? fmt(gen) + " across held-out agents (age 100)"
        : "UNTESTED"));
  }
  html += level(anyRepr ? "done" : "open",
    anyRepr ? "ESTABLISHED · REPRESENTATION" : "OPEN",
    "Is the hidden preference recoverable inside?",
    reprRows.join("\n"),
    (anyGen ? "generalizes across held-out agents — class information " +
      "beyond name recognition. " : "") +
    "recoverable by this probe ≠ used; read relative to the identity " +
    "floor at birth. What is established DIFFERS BY SPECIMEN — read each " +
    "line.", "probes");
  const causalRows = [];
  let anyCausal = false;
  for(const st of S.subs){
    const ev = await art(st, "steering");
    if(ev){
      anyCausal = true;
      const d = ev.dose_response_spread;
      causalRows.push(st.run.run.replace("runs/","") +
        ":  steering @ " + ev.candidate_layer + " spread " +
        fmt(d.candidate) + "  vs controls " + fmt(d.control_layer) +
        " (layer) / " + fmt(d.random_direction) + " (random)");
    } else {
      causalRows.push(st.run.run.replace("runs/","") +
        ":  no intervention records yet");
    }
  }
  html += level(anyCausal ? "done" : "open",
    anyCausal ? "EVIDENCE · CAUSAL (single-seed)" : "OPEN · CAUSAL",
    "Does that information cause the behavior?",
    causalRows.join("\n"),
    (anyCausal ? "predicted-direction steering at the nominated site " +
      "moved conflict behavior far more than the layer and random-" +
      "direction controls — causal involvement under the tested " +
      "intervention, single-seed until the batch replicates. " : "") +
    "patching and ablation next; the arrow hardens only with this " +
    "level", "causal");
  html += level("open", "OPEN · DEVELOPMENT",
    "What did childhood change, and what carries it?",
    "15-organism batch in training · crossed transplant apparatus ready",
    "paired-curriculum contrasts and the weights × optimizer-state " +
    "transplant matrix", "transplant");
  html += level("open", "OPEN · ABSTRACTION",
    "What minimal computation explains all of it?",
    "generate formal spec — pending the levels above",
    "the smallest executable abstraction that survives the evidence; " +
    "not another evidence graph", "formal");
  $("spine").innerHTML = html;
}

function renderEdges(){
  const legend = `<div class=dim style="margin:8px 0;font:10px ui-monospace,Menlo,monospace">
    ⋯⋯ candidate &nbsp; ┄┄ represented &nbsp; ── causal &nbsp;
    ══ replicated</div>`;
  const edges = [
    {line:"agent ┄┄ λ ⋯⋯&gt; choice",
     chips:[["recoverable","y"],["generalizes","y"],["causal","-"],
            ["development","-"]],
     det:"λ-class recoverable and generalizes across held-out agents " +
         "(stored evidence records, age 100%). Causal use and " +
         "developmental localization pending — dotted until earned."},
    {line:"scene+wording ⋯⋯&gt; choice",
     chips:[["behavioral","n"],["recoverable","-"],["causal","-"]],
     det:"the planted route: present by construction, behaviorally " +
         "dominated in these specimens; representation-without-use is " +
         "the open causal question."}];
  $("edges").innerHTML = legend + edges.map((e,i)=>`<div class=edge
    onclick="const d=this.querySelector('.det');
      d.style.display=d.style.display==='block'?'none':'block'">
    <div class=line>${e.line}</div>
    <div class=chips>${e.chips.map(([c,s])=>
      `<span class="chip ${s==="y"?"y":s==="n"?"n":""}">${c}</span>`).join("")}</div>
    <div class=det>${e.det}</div></div>`).join("");
}

function renderSpecs(){
  $("specs").innerHTML = S.subs.map((st,si)=>{
    const ages = st.run.ckpts.map(c=>+c.replace("ckpt_","")
      .replace(".pt",""));
    const options = S.runs.map((r,ri)=>`<option value=${ri}
      ${r.run===st.run.run?"selected":""}>${r.run.replace("runs/","")} ·
      ${(r.curriculum||"?").replace("curriculum_","")}</option>`).join("");
    return `<div class=spec>
      <div class=who>SUBJECT ${si ? "B" : "A"}</div>
      <select data-sel=${si} style="width:100%;font:12px ui-monospace,Menlo,monospace;
        padding:3px;border:1px solid var(--rule);background:#fff;margin:4px 0">
        ${options}</select>
      <input type=range min=0 max=${st.run.ckpts.length-1}
        value=${st.idx} data-si=${si}>
      <div class=ticks>${ages.map(a=>`<span>${a}</span>`).join("")}</div>
      <div class=agelbl>developmental age ${+age(st)}%</div>
    </div>`;
  }).join("");
  document.querySelectorAll(".spec input").forEach(inp =>
    inp.oninput = () => {
      S.subs[+inp.dataset.si].idx = +inp.value;
      saveBench(); renderSpecs(); renderSpine();
    });
  document.querySelectorAll(".spec select").forEach(sel =>
    sel.onchange = () => {
      const run = S.runs[+sel.value];
      S.subs[+sel.dataset.sel] = {run, idx: run.ckpts.length-1};
      saveBench(); renderSpecs(); renderSpine();
    });
}

const BENCH_KEY = "pdp-bench-specimens";
function saveBench(){
  try{
    localStorage.setItem(BENCH_KEY, JSON.stringify({
      A: S.subs[0] ? {run:S.subs[0].run.run, idx:S.subs[0].idx} : null,
      B: S.subs[1] ? {run:S.subs[1].run.run, idx:S.subs[1].idx} : null}));
  }catch(e){}
}

async function init(){
  const runs = await j("/api/runs");
  S.runs = runs;
  const eligible = runs.filter(r =>
    (r.curriculum||"").startsWith("curriculum_"));
  const pick = eligible.length >= 2 ? eligible.slice(0,2)
              : runs.slice(0,2);
  S.subs = pick.map(r => ({run: r, idx: r.ckpts.length-1}));
  // shared bench selection: honor what the Laboratory has on the bench
  try{
    const saved = JSON.parse(localStorage.getItem(BENCH_KEY) || "null");
    if(saved){
      const bySaved = s => {
        if(!s) return null;
        const r = runs.find(x => x.run === s.run);
        return r ? {run: r, idx: Math.min(s.idx, r.ckpts.length-1)} : null;
      };
      const a = bySaved(saved.A), b = bySaved(saved.B);
      if(a) S.subs = b ? [a, b] : [a];
    }
  }catch(e){}
  renderSpecs(); renderEdges();
  await renderSpine();
  document.body.dataset.ready = "1";
}
init();
</script>
</body></html>
"""
