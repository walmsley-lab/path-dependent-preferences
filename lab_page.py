"""The Laboratory (served at /lab): the instrument room.

Design (2026-08-15 handoff): the Expedition explains why each instrument
is needed; the Lab lets the researcher select a specimen, select an
instrument, inspect the trace, and promote it into evidence for or
against the formal graph. Three zones — specimen bench, instrument tray,
observation canvas — plus a graph drawer and an evidence ledger. Terse:
the story lives in the Expedition; readings are monospace; labels are
slate/indigo instrument voice. Same institution as the Expedition,
different room (the research annex, not the field station).

Interaction model: choose specimen -> choose instrument -> inspect
result. Instruments map onto the compute-escalation ladder
(docs/trace_ledger.md): cheap behavior first; representation reads from
stored probe records; causal and transplant instruments appear as
honestly-pending until Phase B produces their evidence records. The two
final dragons (COMPILE -> neuromorphic, IMPORT BRAIN -> connectome) live
inside the Formalization instrument, contextual rather than decorative.

The previous guided workbench remains at /lab/classic.
"""

LAB = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Path-Dependent Preferences — Laboratory</title>
<style>
:root{
  --ivory:#f6f1e5; --card:#fdfaf2; --ink:#26241d; --faded:#6f6a5c;
  --green:#1e4d38; --rule:#cfc9b6; --graphite:#8a8574;
  --inst:#4a4f7a; --blue:#1D6A96; --orange:#B4452A;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ivory);color:var(--ink);
  font:14px/1.55 system-ui,-apple-system,sans-serif}
a{color:var(--inst)}
.topbar{display:flex;justify-content:space-between;align-items:baseline;
  padding:12px 24px;border-bottom:1px solid var(--rule)}
.wordmark{font-size:11px;letter-spacing:.22em;color:var(--green)}
.toplink{font-size:12px;color:var(--faded);text-decoration:none}
.toplink:hover{color:var(--green)}
header.lab{padding:22px 24px 6px}
header.lab h1{font-family:Georgia,serif;font-size:24px;color:var(--green);
  font-weight:normal}
header.lab p{color:var(--faded);font-size:13px;max-width:60ch}
.frame{display:flex;gap:0;align-items:stretch;min-height:calc(100vh - 130px);
  flex-wrap:wrap}
.rail{width:264px;flex:none;border-right:1px solid var(--rule);
  padding:14px 16px}
.canvas{flex:1;padding:16px 22px;min-width:320px;overflow-x:auto}
.drawer{width:236px;flex:none;border-left:1px solid var(--rule);
  padding:14px 14px}
h3.zone{font-size:10px;letter-spacing:.22em;color:var(--inst);
  margin:14px 0 8px;font-weight:600}
h3.zone:first-child{margin-top:0}
hr.g{border:none;border-top:1px solid var(--rule);margin:14px 0}

/* specimen bench */
.specimen{border:1px solid var(--rule);border-radius:3px;padding:10px;
  margin-bottom:10px;background:var(--card)}
.specimen .who{font-size:10px;letter-spacing:.18em;color:var(--green)}
.specimen select{width:100%;margin:6px 0;font:12px ui-monospace,Menlo,monospace;
  padding:3px;border:1px solid var(--rule);background:#fff}
.idcard{font:11.5px ui-monospace,Menlo,monospace;color:var(--faded);
  white-space:pre-wrap}
.age{margin-top:8px}
.ages{display:flex;flex-wrap:nowrap;gap:2px}
.ages button{padding:2px 0;font:10px ui-monospace,Menlo,monospace;
  flex:1;text-align:center}
.ages button.on{background:var(--green);color:var(--ivory);
  border-color:var(--green)}
.age .lbl{font:10px ui-monospace,Menlo,monospace;color:var(--faded);
  margin-top:4px}
button{font:12px system-ui,sans-serif;padding:6px 10px;cursor:pointer;
  background:none;color:var(--ink);border:1px solid var(--graphite);
  border-radius:2px;text-align:left}
button:hover{border-color:var(--green);color:var(--green)}
button.primary{background:var(--green);color:var(--ivory);
  border-color:var(--green)}
button:disabled{opacity:.4;cursor:default}

/* instrument tray */
.tray button{display:block;width:100%;margin:3px 0}
.fam{margin:4px 0}
.fam summary{font-size:10px;letter-spacing:.2em;color:var(--graphite);
  cursor:pointer;padding:4px 0}
.fam[open] summary{color:var(--inst)}
.tray .grp{font-size:9px;letter-spacing:.2em;color:var(--graphite);
  margin:10px 0 3px}
.tray button.pending{color:var(--graphite)}

/* canvas */
#canvas-empty{color:var(--graphite);font-family:Georgia,serif;
  font-size:16px;margin-top:80px;text-align:center}
.trace{border:1px solid var(--rule);border-radius:3px;background:var(--card);
  padding:14px;margin-bottom:12px;max-width:940px}
.trace .cap{font-size:10px;letter-spacing:.2em;color:var(--inst);
  margin-bottom:8px}
.reading,.meter{font-family:ui-monospace,Menlo,monospace;font-size:13px;
  white-space:pre}
.meter{margin:3px 0}
.scene{font-family:Georgia,serif;font-size:15px;margin:4px 0 10px}
.duo{display:flex;gap:12px;flex-wrap:wrap}
.duo .half{flex:1;min-width:230px;border:1px solid var(--rule);
  border-radius:3px;padding:10px;background:#fff}
.duo .half .who{font-size:10px;letter-spacing:.16em;color:var(--green);
  margin-bottom:6px}
svg text{font:10px ui-monospace,Menlo,monospace;fill:var(--faded)}
.note-dim{color:var(--graphite);font-size:12px}
.mtx{border-collapse:collapse;font:12.5px ui-monospace,Menlo,monospace;
  margin:8px 0}
.mtx th,.mtx td{border:none;padding:4px 10px;text-align:center}
.mtx th{font-weight:normal;color:var(--faded);font-size:11px;
  border-bottom:1px solid var(--rule)}
.mtx td.name{text-align:left;cursor:pointer;color:var(--green)}
.mtx td.name:hover{text-decoration:underline}
.mtx td.hot{background:#e7efe4;font-weight:bold}
.scroller{overflow-x:auto}
.cform{display:grid;
  grid-template-columns:max-content 1fr max-content 1fr;
  gap:10px 14px;align-items:center;margin:12px 0}
.cform label{font-size:10px;letter-spacing:.15em;color:var(--faded);
  text-align:right}
.cform select,.mtx select{font:12px ui-monospace,Menlo,monospace;
  padding:4px 6px;border:1px solid var(--rule);border-radius:2px;
  background:#fff;width:100%}
.mtx select{width:100%}
.mtx.fill{width:100%}
textarea{width:100%;font:13px ui-monospace,Menlo,monospace;
  border:1px solid var(--rule);border-radius:3px;padding:8px;
  background:#fff;color:var(--ink)}

/* drawer */
.drawer .tabbtn{display:inline-block;margin:2px 2px;padding:4px 8px;
  font-size:11px}
.evrow{padding:3px 2px;font-size:11px;cursor:pointer;line-height:1.4}
.evrow:hover{background:var(--card)}
.evrow .st{font-family:ui-monospace,Menlo,monospace}
.evrow .st.y{color:var(--green)} .evrow .st.o{color:var(--orange)}
.evdetail{font-size:11.5px;color:var(--faded);padding:6px 2px;
  border-top:1px dashed var(--rule)}
</style></head><body>

<div class=topbar>
  <span class=wordmark>OPEN POLLINATION &mdash; RESEARCH ANNEX</span>
  <span>
    <a class=toplink href="/">&larr; the Expedition</a>&nbsp;&nbsp;
    <a class=toplink href="/lab">evidence view</a>&nbsp;&nbsp;
    <a class=toplink href="/lab/classic">classic workbench</a>
  </span>
</div>

<header class=lab>
  <h1>Laboratory</h1>
  <p>Inspect trained organisms, compare developmental histories, and test
  hypotheses about what they learned.
  <details style="display:inline"><summary style="display:inline;
    cursor:pointer;color:var(--inst)">experiment context</summary>
  <span class=reading style="display:block;margin-top:6px;font-size:12px">C1  W &rarr; P &rarr; tail
C2  P &rarr; W &rarr; tail
C3  interleaved &rarr; tail
paired init &#10003;   same multiset &#10003;   same token budget &#10003;</span>
  </details></p>
</header>

<div class=frame>

<aside class=rail>
  <h3 class=zone>SPECIMEN</h3>
  <div class=specimen id=specA>
    <div class=who>SUBJECT A</div>
    <select id=selA></select>
    <div class=age><div class=lbl style="margin:0 0 3px">Developmental
      age</div><div class=ages id=ageA></div></div>
    <details><summary style="font-size:11px;color:var(--inst);
      cursor:pointer">metadata</summary>
      <div class=idcard id=cardA></div></details>
  </div>
  <div class=specimen id=specB style="display:none">
    <div class=who>SUBJECT B<span id=removeB title="remove specimen"
      style="float:right;cursor:pointer;font-size:14px;line-height:.8;
      color:var(--graphite)">&minus;</span></div>
    <select id=selB></select>
    <div class=age><div class=lbl style="margin:0 0 3px">Developmental
      age</div><div class=ages id=ageB></div></div>
    <details><summary style="font-size:11px;color:var(--inst);
      cursor:pointer">metadata</summary>
      <div class=idcard id=cardB></div></details>
  </div>
  <button id=addB style="width:100%">+ Add comparison specimen</button>

  <h3 class=zone style="margin-top:18px">INSTRUMENTS</h3>
  <div class=tray>
    <details class=fam open><summary title="what does the organism do?">OBSERVE</summary>
      <button data-inst=ordinary>Ordinary case</button>
      <button data-inst=conflict>Conflict test</button>
      <button data-inst=nocue>Remove cue</button>
      <button data-inst=cueonly>Cue only</button>
      <button data-inst=custom>Compose a scenario</button>
      <button data-inst=freeform>Freeform prompt</button>
      <button data-inst=corpus>What the learner saw</button>
    </details>
    <details class=fam><summary title="where and when does information live?">LOCATE</summary>
      <button data-inst=trajectory>Checkpoint trajectories</button>
      <button data-inst=atlas>Developmental atlas</button>
      <button data-inst=probes>&lambda; / cue probes</button>
    </details>
    <details class=fam><summary title="where did developmental histories make the networks different?">COMPARE</summary>
      <button data-inst=constellation>Representation map</button>
      <button data-inst=diffmap>Twin difference map</button>
    </details>
    <details class=fam><summary title="which differences matter? correlation becomes causation here">PERTURB</summary>
      <button data-inst=causal>Steer, patch, ablate</button>
      <button data-inst=transplant class=pending>Developmental transplant</button>
    </details>
    <details class=fam><summary title="what sequence of transformations produced this decision?">TRACE</summary>
      <button data-inst=exectrace>Execution trace</button>
    </details>
    <details class=fam><summary title="the smallest mechanism that explains what survived">FORMALIZE</summary>
      <button data-inst=formal>Derive candidate graph</button>
      <button data-inst=worldmodels>World models (G_*)</button>
    </details>
  </div>
  <button id=beyond class=quiet style="margin-top:22px;width:100%">
    Beyond this experiment &rarr;</button>
</aside>

<main class=canvas id=canvas>
  <div id=canvas-empty>Choose a specimen and an instrument.</div>
</main>

<aside class=drawer>
  <h3 class=zone>EVIDENCE</h3>
  <div class=note-dim style="font-size:10px;margin-bottom:4px">
    Experiments produce evidence. Evidence constrains claims.
    The graph is the consequence.</div>
  <div id=evidence></div>
</aside>

</div>
<script>
"use strict";
const $ = id => document.getElementById(id);
const j = (u,o) => fetch(u,o).then(r=>{ if(!r.ok) throw new Error(u+" "+r.status); return r.json(); });
const S = {runs:[], datasets:[], data:null, A:null, B:null, cfg:null,
           lastMode:null};

function datasetFor(run){
  // match the run's recorded dataset by basename; fall back to the first
  const base = (run.dataset_dir || "").split("/").pop();
  const hit = S.datasets.find(d => d.data.split("/").pop() === base);
  return (hit || S.datasets[0]).data;
}
window.LABSTATE = S;

async function claimArtifacts(st){
  const out = {};
  try{ out.score = await j("/api/score?run=" +
    encodeURIComponent(st.run.run) + "&ckpt=ckpt_100.pt"); }catch(e){}
  try{ out.gen = await j("/api/evidence?run=" +
    encodeURIComponent(st.run.run)); }catch(e){}
  try{ out.steer = await j("/api/steering?run=" +
    encodeURIComponent(st.run.run)); }catch(e){}
  try{ out.abl = await j("/api/ablation?run=" +
    encodeURIComponent(st.run.run)); }catch(e){}
  try{ out.patch = await j("/api/patching?run=" +
    encodeURIComponent(st.run.run)); }catch(e){}
  return out;
}

function bestLambda(gen){
  if(!gen) return null;
  return Object.entries(gen.layers).flatMap(([L,row]) =>
    Object.entries(row).filter(([k])=>k.includes("lambda"))
      .map(([k,v])=>({loc:L+"/"+k.split("/")[0],
                      sel:v.heldout_agent_selectivity})))
    .sort((a,b)=>b.sel-a.sel)[0];
}

async function renderEvidence(){
  const st = S.A;
  if(!st){ return; }
  const A = await claimArtifacts(st);
  const conf = A.score && A.score.sets && A.score.sets.eval_conflict;
  let probe = null;
  if(A.score && A.score.probes){
    for(const [k,v] of Object.entries(A.score.probes))
      if(k.endsWith("lambda_class") && (!probe || v.selectivity > probe.sel))
        probe = {loc:k, sel:v.selectivity};
  }
  const gen = bestLambda(A.gen);
  const steerOk = A.steer && A.steer.dose_response_spread.candidate >
    2 * Math.max(A.steer.dose_response_spread.control_layer,
                 A.steer.dose_response_spread.random_direction);
  const ablNec = A.abl && A.abl.utility_agreement_drop.candidate_lambda >
    2 * Math.max(A.abl.utility_agreement_drop.random_direction, 0.02);
  const ablSel = A.abl && A.abl.utility_agreement_drop.candidate_lambda >
    2 * Math.max(A.abl.utility_agreement_drop.random_direction,
                 A.abl.utility_agreement_drop.control_layer_lambda);
  const patchFail = A.patch && A.patch.audit;

  // claim = {mark, label, why, limit, next}
  const established = [{mark:"✓",
    label:"The diagnostic distinguishes the candidate rules",
    why:"by construction: utility and cue disagree on every conflict "+
        "item (constraint verified — test_generator.py, preflight.py)",
    limit:"says nothing about which rule any organism uses",
    next:"—"}];
  const supported = [], constrained = [], open = [];

  if(conf){
    supported.push({mark:"◐",
      label:"Preferentially follows the utility route",
      why:"conflict behavior " + fmt(conf.acc_utility) + " utility / " +
          fmt(conf.acc_cue) + " cue (stored scores, " + chip(st) + ")",
      limit:"single organism; behavior only — not mechanism",
      next:"replication across the 15-organism batch"});
  } else {
    open.push({mark:"?", label:"Utility-route behavior",
      why:"no stored conflict scores for this specimen",
      limit:"—", next:"score the diagnostic sets"});
  }
  if(probe){
    const c = {mark:"◐", label:"Latent preference internally recoverable",
      why:"best controlled probe selectivity " + fmt(probe.sel) + " @ " +
          probe.loc,
      limit:"recoverable by this probe ≠ used; identity floor applies",
      next: gen ? "—" : "held-out-agent generalization "+
        "(probe_generalization.py)"};
    if(gen && gen.sel >= 0.25){
      c.label = "Latent preference recoverable AND generalizes";
      c.why += "; held-out-agent selectivity " + fmt(gen.sel) + " @ " +
        gen.loc + " — beyond name recognition";
    }
    supported.push(c);
  } else {
    open.push({mark:"?", label:"λ recoverable",
      why:"no probe records at this age", limit:"—",
      next:"probes at stored checkpoints"});
  }
  if(A.steer){
    supported.push({mark:"◐",
      label:"λ-associated direction causally involved",
      why:"predicted-direction steering: spread " +
          fmt(A.steer.dose_response_spread.candidate) + " @ " +
          A.steer.candidate_layer + " vs controls " +
          fmt(A.steer.dose_response_spread.control_layer) + " / " +
          fmt(A.steer.dose_response_spread.random_direction),
      limit:"causal involvement under the tested intervention — not "+
            "sufficiency, not 'the mechanism'; single seed",
      next:"replication; then targeted trace at the implicated window"});
  } else {
    open.push({mark:"○", label:"Causal involvement",
      why:"no intervention records", limit:"—",
      next:"predicted-direction steering (steer_run.py)"});
  }
  if(A.abl && ablNec && !ablSel){
    constrained.push({mark:"△",
      label:"Selective localization contradicted",
      why:"ablating v_λ matters (drop " +
          fmt(A.abl.utility_agreement_drop.candidate_lambda) +
          ", random ~0) but the control layer drops " +
          fmt(A.abl.utility_agreement_drop.control_layer_lambda) +
          " — necessity is not unique to the candidate layer",
      limit:"'distributed representation' is a hypothesis, not a result",
      next:"execution trace: where do the two layers' λ-directions "+
           "enter the computation?"});
  } else if(A.abl && ablSel){
    supported.push({mark:"◐", label:"λ direction selectively necessary",
      why:"candidate drop " +
          fmt(A.abl.utility_agreement_drop.candidate_lambda) +
          " exceeds both controls",
      limit:"necessity under this ablation only; single seed",
      next:"replication"});
  }
  if(patchFail){
    constrained.push({mark:"△",
      label:"Portable-state hypothesis constrained",
      why:"audited per-example: patched behavior does not side with the "+
          "donor on disputed items (candidate ≤ mismatched control in "+
          "one cell); late-layer patches transfer trivially",
      limit:"the instantaneous candidate-layer residual state is "+
            "insufficient as a portable carrier of the phenotype",
      next:"what DOES carry it? → developmental transplant (batch-gated)"});
  }
  open.push({mark:"○", label:"Developmental carrier",
    why:"no transplant records", limit:"—",
    next:"crossed weights × optimizer-state transplant (B1, batch-gated)"});
  open.push({mark:"○", label:"Minimal mechanism abstraction",
    why:"constraints accumulating (see CONSTRAINED)", limit:"—",
    next:"derive candidate graph from the ledger; test its predictions"});
  open.push({mark:"○", label:"Replication across seeds",
    why:"batch in training", limit:"—", next:"the 15-organism battery"});
  open.push({mark:"○", label:"Executable formalization",
    why:"requires a causally supported abstraction", limit:"—",
    next:"executable surrogate + equivalence testing"});

  const row = (c, i) =>
    `<div class=evrow data-ev=${i}><span class="st ${
      c.mark==="✓"?"y":c.mark==="△"?"o":""}">${c.mark}</span>
      ${c.label}<div class=evdetail id=evd${i} style="display:none">
      <b>Why we believe this:</b> ${c.why}<br>
      <b>Limit:</b> ${c.limit}<br>
      <b>Next discriminating test:</b> ${c.next}</div></div>`;
  const section = (name, arr, off) =>
    `<div class=note-dim style="font-size:9px;letter-spacing:.18em;
      margin-top:8px">${name}</div>` +
    (arr.length ? arr.map((c,i)=>row(c, off+i)).join("")
                : `<div class=note-dim>none yet</div>`);
  let i0 = 0;
  let html = section("ESTABLISHED", established, i0);
  i0 += established.length;
  html += section("SUPPORTED", supported, i0); i0 += supported.length;
  html += section("CONSTRAINED", constrained, i0);
  i0 += constrained.length;
  html += section("OPEN", open, i0);
  $("evidence").innerHTML = html;
  document.querySelectorAll(".evrow").forEach(r=>r.onclick=()=>{
    const d = $("evd"+r.dataset.ev);
    d.style.display = d.style.display === "none" ? "block" : "none";
  });
}

function canvas(html){
  $("canvas").innerHTML = html;
}

function subj(which){ return which === "A" ? S.A : S.B; }

function chip(st){
  const who = st === S.A ? "A" : "B";
  const cur = (st.run.curriculum || "?").replace("curriculum_","");
  const age = ckptOf(st).replace("ckpt_","").replace(".pt","");
  return who + " · " + cur + " · age " + age + "%";
}

function idcard(run){
  // one attribute per line: "6-layer decoder-only, d=384, 6 heads"
  // becomes an aligned key-value card
  const m = (run.arch || "").match(/(\d+)-layer ([^,]+), d=(\d+), (\d+) heads/);
  const rows = m
    ? [["architecture", m[1] + "-layer " + m[2]],
       ["width", "d=" + m[3] + " · " + m[4] + " heads"]]
    : [["architecture", run.arch || "?"]];
  if(run.n_params)
    rows.push(["parameters", (run.n_params/1e6).toFixed(1) + "M"]);
  rows.push(["curriculum",
             (run.curriculum || "?").replace("curriculum_", "")]);
  rows.push(["commit", run.commit]);
  return rows.map(([k, v]) => k.padEnd(13) + v).join("\n");
}

function refreshActive(){
  if(S.activeInst && INSTRUMENTS[S.activeInst])
    INSTRUMENTS[S.activeInst]();
  renderEvidence();
}

function bindSpecimen(which, silent){
  const sel = $("sel"+which);
  const run = S.runs[+sel.value];
  const st = {run: run, ckptIdx: run.ckpts.length-1,
              data: datasetFor(run)};
  const prevData = which === "A" && S.A ? S.A.data : null;
  if(which === "A") S.A = st; else S.B = st;
  if(which === "A" && prevData && prevData !== st.data)
    S.cfg = null;   // the reused scenario belongs to the old world
  $("card"+which).textContent = idcard(run);
  renderAges(which);
  if(!silent) refreshActive();
}

function renderAges(which){
  const st = subj(which);
  const box = $("age"+which);
  box.innerHTML = st.run.ckpts.map((ck,i)=>
    `<button data-i=${i} class="${i===st.ckptIdx?"on":""}">${
      ck.replace("ckpt_","").replace(".pt","").replace(/^0+(?=\d)/,"")}%</button>`).join("");
  box.querySelectorAll("button").forEach(b=>b.onclick=()=>{
    st.ckptIdx = +b.dataset.i;
    renderAges(which);
    refreshActive();
  });
}

function ckptOf(st){ return st.run.ckpts[st.ckptIdx]; }

/* ---- behavior instruments ---------------------------------------------- */

function meterLine(label, p){
  const n = Math.round(p*20);
  return label.padEnd(9) + "█".repeat(n) + "░".repeat(20-n) +
    " " + (p*100).toFixed(1) + "%";
}

async function askSubject(st, mode, cfg){
  const body = {run: st.run.run, ckpt: ckptOf(st), data: st.data, mode: mode};
  if(cfg) body.cfg = cfg;
  return j("/api/query", {method:"POST",
    headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
}

function answerBlock(st, r){
  const rec = r.record, a = r.answer;
  return `<div class=half><div class=who>${chip(st)}</div>
    <div class=meter>${meterLine("Option 1", a.p1)}</div>
    <div class=meter>${meterLine("Option 2", a.p2)}</div>
    <div class=reading>matches: ${r.follows}</div></div>`;
}

function liveBadge(){
  return `<span style="font-size:9px;letter-spacing:.15em;
    color:var(--orange);border:1px solid var(--orange);border-radius:2px;
    padding:1px 6px;margin-left:8px">LIVE MODEL INFERENCE</span>`;
}

async function behave(mode, customCfg){
  S.lastMode = mode;
  canvas(`<div class=trace><div class=cap>BEHAVIOR &middot;
    ${mode.toUpperCase()} ${liveBadge()}</div>
    <div class=note-dim>asking ${chip(S.A)} — forced-choice
    log-probability over the two options, computed by the model now,
    not retrieved&hellip;</div></div>`);
  if(customCfg !== undefined) S.cfg = customCfg;
  const rA = await askSubject(S.A, mode, S.cfg);
  S.cfg = rA.cfg;               // same scenario across modes and subjects
  let html = `<div class=trace><div class=cap>BEHAVIOR &middot;
    ${mode.toUpperCase()} ${liveBadge()}</div>
    <div style="display:flex;gap:14px;align-items:stretch">
    <div style="flex:1;min-width:0">
    <div class=reading style="font-size:10px;letter-spacing:.2em;
      color:var(--inst)">PROMPT</div>
    <div class=scene>${rA.record.prompt}</div>
    <div class=reading style="font-size:10px;letter-spacing:.2em;
      color:var(--inst);margin-bottom:4px">RESPONSE</div>
    <div class=duo>`;
  html += answerBlock(S.A, rA);
  let crossWorld = false;
  if(S.B){
    const shared = S.B.data === S.A.data;
    crossWorld = !shared;
    const rB = await askSubject(S.B, mode, shared ? S.cfg : null);
    html += answerBlock(S.B, rB);
    if(crossWorld){
      html += `</div><div class=scene style="font-size:13px;color:var(--graphite)">
        SUBJECT B lives in a different world (its own agents and λ
        assignments) — its scenario is sampled from its own corpus:
        ${rB.record.prompt}</div><div class=duo style="display:none">`;
    }
  }
  html += `</div><div class=note-dim style="margin-top:8px">utility answer:
    Option ${rA.record.utility_answer ?? "—"} &middot; cue answer: Option
    ${rA.record.cue_answer ?? "—"} &middot; ${crossWorld ?
    "cross-world comparison: same instrument, per-world scenarios" :
    "same scenario is reused across instruments until you refresh"}</div>
    </div>
    <div style="display:flex;flex-direction:column;justify-content:center;
      flex:none">
      <button id=tile-refresh title="new scenario"
        style="font-size:24px;line-height:1;padding:12px 14px">&#8635;</button>
    </div>
    </div></div>`;
  canvas(html);
  $("tile-refresh").onclick = ()=>{ S.cfg = null; behave(S.lastMode); };
}

/* ---- compose: a user-authored scenario, run against the model ---------- */

async function compose(){
  const world = await j("/api/corpus?data=" + encodeURIComponent(S.A.data));
  const opts = (arr, sel) => arr.map(v =>
    `<option ${v===sel?"selected":""}>${v}</option>`).join("");
  const dsel = d => opts(world.deltas, d);
  canvas(`<div class=trace><div class=cap>COMPOSE A SCENARIO</div>
    <div class=note-dim>assembled from this world&rsquo;s closed
    vocabulary — the organism can only read words that exist in its
    world</div>
    <div class=cform>
      <label>AGENT</label><select id=cA>${opts(Object.keys(world.agents))}</select>
      <label>PARTNER</label><select id=cP>${opts(world.partners)}</select>
      <label>PLACE</label><select id=cS>${opts(world.scenes)}</select>
      <label>RESOURCE</label><select id=cN>${opts(world.nouns)}</select>
    </div>
    <div class=scroller><table class="mtx fill">
      <tr><th></th><th>AGENT&rsquo;S PAYOFF</th><th>PARTNER&rsquo;S PAYOFF</th></tr>
      <tr><td class=name style="cursor:default">option 1</td>
        <td><select id=c1s>${dsel(3)}</select></td>
        <td><select id=c1o>${dsel(-2)}</select></td></tr>
      <tr><td class=name style="cursor:default">option 2</td>
        <td><select id=c2s>${dsel(-2)}</select></td>
        <td><select id=c2o>${dsel(3)}</select></td></tr>
    </table></div>
    <div class=cform style="grid-template-columns:max-content 1fr">
      <label>PRESENTATION</label><select id=cM>
        <option value=id>ordinary (wording agrees with outcomes)</option>
        <option value=conflict>conflict (wording opposes outcomes)</option>
        <option value=nocue>no cue (neutral wording)</option>
      </select>
    </div>
    <button class=primary id=crun>Run against the model &rarr;</button>
    <div class=note-dim style="margin-top:8px">the authored world computes
    its own answer from the agent&rsquo;s λ; the model answers by live
    forced-choice inference — then they are compared</div></div>`);
  $("crun").onclick = ()=>{
    const cfg = {
      agent: $("cA").value, lam: world.agents[$("cA").value],
      partner: $("cP").value,
      options: [[+$("c1s").value, +$("c1o").value],
                [+$("c2s").value, +$("c2o").value]],
      scene: $("cS").value, narrator: world.narrators[0],
      noun: $("cN").value, template: "T1",
      coop_verb: world.coop_verbs[0], self_verb: world.self_verbs[0],
      neut_verbs: world.neut_verbs.slice(0,2), cue_target_override: 1,
    };
    behave($("cM").value, cfg);
  };
}

/* ---- freeform: talk to the organism ------------------------------------ */

async function freeform(){
  let tmpl = "At the river, Matthew and Kevin are dividing stones.";
  try{
    const o = await j("/api/observe?n=1&data=" +
                      encodeURIComponent(S.A.data));
    tmpl = o.observations[0].record.prompt.split("Q:")[0].trim();
  }catch(e){}
  canvas(`<div class=trace><div class=cap>FREEFORM PROMPT ${liveBadge()}</div>
    <div class=note-dim>EXPLORE FREELY — off the diagnostic map: no
    authored answer exists for arbitrary text, so nothing here enters the
    evidence ledger (compose-within-the-world is the evidence-capable
    counterpart). The vocabulary is closed by design: unknown words are
    refused, never silently mangled. Edit the template or write your
    own.</div>
    <textarea id=fftext rows=4>${tmpl}</textarea>
    <div style="margin:8px 0;font-size:12px">
      <label><input type=radio name=ffm value=continue checked>
        continue the text (greedy generation)</label>
      <label style="margin-left:12px"><input type=radio name=ffm value=choice>
        score as a choice (Option 1 vs 2)</label>
    </div>
    <button class=primary id=ffrun>Run against ${chip(S.A)} &rarr;</button>
    <div id=ffout style="margin-top:10px;min-height:170px"></div></div>`);
  $("ffrun").onclick = runFreeform;
}

function ffBlock(label, inner){
  return `<div style="margin-top:8px">
    <div class=reading style="font-size:10px;letter-spacing:.2em;
      color:var(--inst)">${label}</div>${inner}</div>`;
}

async function runFreeform(){
  const mode = document.querySelector("input[name=ffm]:checked").value;
  const promptText = $("fftext").value;
  const promptEcho = ffBlock("PROMPT",
    `<div class=scene style="margin:2px 0">${promptText
      .replace(/</g,"&lt;")}</div>`);
  $("ffout").innerHTML = promptEcho + ffBlock("RESPONSE",
    "<div class=note-dim>live inference — the model is reading your " +
    "words now…</div>");
  const r = await j("/api/freeform", {method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({run:S.A.run.run, ckpt:ckptOf(S.A),
      prompt: promptText, mode: mode})});
  if(r.oov){
    $("ffout").innerHTML = promptEcho + `<div class=reading style="color:var(--orange);
      font-size:11px;letter-spacing:.15em">OUTSIDE THIS ORGANISM&rsquo;S
      EXPERIENCE</div>
      <div class=note-dim>This learner was raised in a deliberately
      closed linguistic world. These words never occurred in its training
      vocabulary — there is no representation of them to interrogate —
      so interpreting a response would not be a valid test:</div>
      <div class=reading style="color:var(--orange)">${r.oov.join("  ")}</div>
      <div class=note-dim style="margin-top:6px">Stay inside the world:
      replace them with known vocabulary (the compose instrument lists it
      by category). &nbsp;<a class=toplink
      href="/technique/closed-world" target=_blank rel=noopener>Why is
      the world closed? &nearr;</a></div>`;
    return;
  }
  if(mode === "choice"){
    const a = r.answer;
    $("ffout").innerHTML = promptEcho + ffBlock("RESPONSE",
      "<div class=meter>" + meterLine("Option 1", a.p1) + "</div>" +
      "<div class=meter>" + meterLine("Option 2", a.p2) + "</div>" +
      `<div class=note-dim>forced-choice log-probability of the two answer
       tokens after your text — meaningful only if your text poses the
       world&rsquo;s kind of question</div>`);
  } else {
    $("ffout").innerHTML = promptEcho + ffBlock("RESPONSE",
      `<div class=scene style="margin:2px 0">&hellip;${r.continuation}</div>
       <div class=note-dim>${r.n_tokens} tokens · ${r.decoding} — this is
       what the organism expects the world to say next</div>`);
  }
}

/* ---- corpus reader ------------------------------------------------------ */

function segBars(segments){
  const colors = {W:"#1D6A96", P:"#B4452A", mixed:"#7A5FA8",
                  tail:"#8a8574"};
  const label = {W:"structure-rich", P:"choice-rich", mixed:"interleaved",
                 tail:"shared tail"};
  let html = "";
  for(const [cur, segs] of Object.entries(segments || {})){
    const total = segs.reduce((a,s)=>a+s[1], 0);
    html += `<div style="display:flex;align-items:center;gap:8px;margin:3px 0">
      <span class=reading style="width:26px">${cur}</span>
      <div style="flex:1;display:flex;height:16px;border:1px solid var(--rule);border-radius:2px;overflow:hidden">` +
      segs.map(([name,count])=>`<div title="${label[name]||name}: ${count.toLocaleString()} lines"
        style="width:${100*count/total}%;background:${colors[name]||"#ccc"}"></div>`).join("") +
      `</div></div>`;
  }
  return html + `<div class=note-dim style="font-size:11px">
    <span style="color:#1D6A96">■</span> structure-rich &nbsp;
    <span style="color:#B4452A">■</span> choice-rich &nbsp;
    <span style="color:#7A5FA8">■</span> interleaved &nbsp;
    <span style="color:#8a8574">■</span> shared tail</div>`;
}

function annotate(line, world){
  const verbs = world.coop_verbs.concat(world.self_verbs);
  let html = line.replace(/</g,"&lt;");
  for(const v of verbs)
    html = html.split(v).join(`<span style="color:#B4452A;border-bottom:1.5px solid #B4452A" title="wording — the planted route lives here">${v}</span>`);
  for(const s of world.scenes)
    html = html.replace(new RegExp("\\b"+s+"\\b"),
      `<span style="border-bottom:1.5px dotted #B4452A" title="scene — conditions the wording rule">${s}</span>`);
  html = html.replace(/(gains|loses) (\d+) (\w+)/g,
    `<span style="color:#1D6A96" title="outcomes — the authored route lives here">$1 $2 $3</span>`);
  html = html.replace(/A: (Option \d)/,
    `A: <span style="border:1px solid var(--green);padding:0 4px;border-radius:2px" title="the observed answer — the only supervision">$1</span>`);
  return html;
}

async function corpus(slice, showN){
  const st = S.A;
  const [world, lines] = await Promise.all([
    j("/api/corpus?data=" + encodeURIComponent(st.data)),
    j("/api/corpus_lines?data=" + encodeURIComponent(st.data) +
      (slice ? "&slice=" + encodeURIComponent(slice) + "&n=" +
       (showN || 5) : ""))]);
  // one real choice line for the annotated exhibit
  let exhibit = null;
  try{
    const h = await j("/api/corpus_lines?data=" +
      encodeURIComponent(st.data) + "&slice=" +
      (lines.slices.includes("C2_head") ? "C2_head" : lines.slices[0]) +
      "&n=10");
    exhibit = (h.lines.find(l => l.type === "P") || h.lines[0]);
  }catch(e){}

  let html = `<div class=trace><div class=cap>WHAT THE LEARNER SAW</div>
    <div class=scene style="font-size:17px">This is the learner&rsquo;s
      entire world.</div>
    <div class=note-dim>It was never shown our graph, any agent&rsquo;s
      hidden preference, the utility rule, or an explanation of the task.
      It received only text like this — hover the annotations:</div>`;
  if(exhibit){
    html += `<div class=scene style="border:1px solid var(--rule);
      border-radius:3px;padding:10px;margin:10px 0;font-size:14px">${
      annotate(exhibit.text, world)}</div>
    <div class=note-dim>
      <span style="color:#1D6A96">■ outcomes</span> — the authored route
      lives here &nbsp;·&nbsp;
      <span style="color:#B4452A">■ wording &amp; place</span> — the
      planted route lives here &nbsp;·&nbsp; the boxed answer is the only
      supervision. There is more than one way to become good at
      predicting it.</div>`;
  }
  html += `</div>

  <div class=trace><div class=cap>SAME EXPERIENCES &middot; DIFFERENT
    CHILDHOODS</div>
    <div style="margin:8px 0">${segBars(S.segments)}</div>
    <div class=note-dim>Every learner receives the same multiset of
      training lines and the identical final stretch. Nothing added,
      nothing removed — only the order changed.</div>
    <details style="margin-top:8px"><summary style="font-size:12px;
      color:var(--inst);cursor:pointer">what exactly is a
      &ldquo;structure-rich&rdquo; line? (from the generator, not a
      paraphrase)</summary>
      <div class=note-dim style="margin-top:6px">Four kinds, all with
      NEUTRAL verbs, none involving anyone&rsquo;s preference:<br>
      &nbsp;&nbsp;W1 counting — &ldquo;A has 12 stones. Q: How many
      stones does A have?&rdquo;<br>
      &nbsp;&nbsp;W2 consequences — &ldquo;If A selects the red marker,
      A gains 3 and B loses 2. Q: What happens to B?&rdquo;<br>
      &nbsp;&nbsp;W3 arithmetic — &ldquo;Q: What is the total
      change?&rdquo;<br>
      &nbsp;&nbsp;W4 objective comparison — &ldquo;Q: Which option
      leaves B better off?&rdquo; (argmax practice with no preference
      involved)<br>
      A <b>choice-rich</b> line is the only kind where anyone
      <em>chooses</em>: agent, partner, two framed options with payoffs,
      and &ldquo;Q: Which option does A choose?&rdquo; — preference
      evidence and the planted wording exist ONLY here.</div></details>
  </div>

  <div class=trace><div class=cap>INSPECT THE ACTUAL CORPUS</div>`;
  if(!lines.slices.length){
    html += `<div class=note-dim>no corpus slices fetched to this bench —
      the full corpus lives with the training runs</div></div>`;
  } else {
    const label = s => s.replace("_head", " · beginning")
      .replace("_tail", " · shared tail").replace("_sample", " · middle");
    html += `<div style="margin:6px 0">` + lines.slices.map(s =>
      `<button style="padding:3px 9px;font-size:11px" class="${s===lines.slice?"primary":""}"
        onclick="corpus('${s}')">${label(s)}</button>`).join(" ") + `</div>`;
    if(lines.lines){
      html += `<div class=note-dim>actual training lines, in the exact
        order this curriculum presented them</div>
        <div style="margin-top:8px">` +
        lines.lines.map(l =>
          `<div style="display:flex;gap:8px;padding:3px 0;border-top:1px solid var(--rule)">
            <span class=reading title="${l.type==="P"?"choice-rich":"structure-rich"}"
              style="color:${l.type==="P"?"#B4452A":"#1D6A96"};width:14px">${l.type}</span>
            <span style="font-size:13px;font-family:Georgia,serif">${l.text}</span></div>`).join("") +
        `</div>
        <button class=quiet style="margin-top:6px"
          onclick="corpus('${lines.slice}', ${(showN||5)+20})">show more
          training lines</button>`;
    } else {
      html += `<div class=note-dim>choose a slice — 5 lines shown by
        default</div>`;
    }
  }
  html += `</div>
  <div class=trace><div class=scene style="font-size:16px">You know more
    than the learner does.</div>
    <div class=note-dim>You know the graph that generated these lines.
    You know λ exists. You know which correlations were planted. The
    learner receives only the corpus above — and in Act II, when the
    corpus is real, so will we.</div></div>`;
  canvas(html);
}
window.corpus = corpus;

/* ---- development/* ---- development -------------------------------------------------------- */

async function trajectory(){
  const subs = S.B ? [S.A, S.B] : [S.A];
  const series = await Promise.all(subs.map(st =>
    j("/api/series?run=" + encodeURIComponent(st.run.run))));
  let html = `<div class=trace><div class=cap>DEVELOPMENT &middot; when
    does behavior change as this organism grows?</div>
    <div class=note-dim>Each dot is a STORED measurement: at a preserved
    developmental age, the fraction of the held-out disagreement set
    (hundreds of cases where the two rules point at different options)
    on which behavior matched the <b>outcome rule</b>. 1.0 = always
    outcomes · 0.0 = always wording · the dashed line is chance.</div>`;
  const W=520, H=210, padL=38, padR=14, padT=12, padB=30,
        colors=["#1e4d38","#B4452A"];
  let svg = `<line x1=${padL} y1=${padT} x2=${padL} y2=${H-padB}
      stroke="#cfc9b6"></line>
    <line x1=${padL} y1=${H-padB} x2=${W-padR} y2=${H-padB}
      stroke="#cfc9b6"></line>
    <line x1=${padL} y1=${padT+(H-padT-padB)/2} x2=${W-padR}
      y2=${padT+(H-padT-padB)/2} stroke="#cfc9b6"
      stroke-dasharray="4 4"></line>
    <text x=4 y=${padT+6}>1.0</text>
    <text x=4 y=${padT+(H-padT-padB)/2+4}>0.5</text>
    <text x=4 y=${H-padB+4}>0.0</text>
    <text x=${W/2-60} y=${H-6}>developmental age %</text>
    <text x=${padL+4} y=${padT+(H-padT-padB)/2-4}
      style="font-style:italic">chance</text>`;
  let any = false;
  const sx = pct => padL + (W-padL-padR)*pct/100;
  const sy = v => padT + (H-padT-padB)*(1-v);
  series.forEach((s, si) => {
    const pts = s.series.filter(r => "conflict" in r);
    if(!pts.length) return;
    any = true;
    svg += `<path d="${pts.map((r,i)=>(i?"L":"M")+sx(r.pct).toFixed(1)+
      " "+sy(r.conflict).toFixed(1)).join(" ")}" fill=none
      stroke="${colors[si]}" stroke-width=1.6></path>`;
    pts.forEach(r => {
      svg += `<circle cx=${sx(r.pct).toFixed(1)} cy=${sy(r.conflict)
        .toFixed(1)} r=3.2 fill="${colors[si]}"><title>age ${r.pct}%:
        ${(r.conflict*100).toFixed(1)}% outcomes</title></circle>
        <text x=${sx(r.pct)-8} y=${H-padB+14}>${r.pct}</text>`;
    });
    svg += `<text x=${W-160} y=${padT+12+si*13}
      fill="${colors[si]}">${chip(subs[si])}</text>`;
  });
  html += any
    ? `<div class=scroller><svg viewBox="0 0 ${W} ${H}"
        style="width:100%;max-width:${W}px;height:auto;border:1px solid
        var(--rule);border-radius:3px;background:#fff;margin-top:8px">
        ${svg}</svg></div>
      <div class=note-dim style="margin-top:6px">points, not smoothed
        curves — the honest resolution of this bench (${
        series[0].series.filter(r=>"conflict" in r).length} preserved
        ages; the full record holds 21). <b>Established:</b> when
        behavior moved. <b>Not established:</b> what changed inside
        (probes) or whether it is causal (locked). An interesting window
        here is exactly where to point the representation
        instruments.</div>`
    : `<div class=note-dim>no stored checkpoint scores for this
        specimen yet — the main batch writes them as it trains</div>`;
  html += "</div>";
  canvas(html);
}

/* ---- representation/* ---- representation ----------------------------------------------------- */

const HUMAN = {lambda_class: "Hidden preference λ",
  u_diff_sign: "Utility difference", verb_class_1: "Wording cue"};
const fmt = x => x == null ? "—"
  : Math.abs(x) < 0.005 ? "~0" : (Math.round(x*100)/100).toFixed(2);

function parseProbes(pr){
  // "L3/agent/lambda_class" -> byPos[pos][target][layer] = selectivity
  const byPos = {};
  for(const [k, v] of Object.entries(pr || {})){
    const m = k.match(/^L(\d+)\/(\w+)\/(\w+)$/);
    if(!m) continue;
    ((byPos[m[2]] ??= {})[m[3]] ??= {})[+m[1]] =
      {sel: v.selectivity, probe: v.probe_acc, control: v.control_acc};
  }
  return byPos;
}

async function scoreFor(st, ck){
  S.scoreCache ??= {};
  const key = st.run.run + "/" + ck;
  if(!(key in S.scoreCache)){
    try{
      S.scoreCache[key] = await j("/api/score?run=" +
        encodeURIComponent(st.run.run) + "&ckpt=" + encodeURIComponent(ck));
    }catch(e){ S.scoreCache[key] = null; }
  }
  return S.scoreCache[key];
}

async function probes(pos){
  pos = (typeof pos === "string") ? pos : (S.probePos || "agent");
  S.probePos = pos;
  const st = S.A;
  const sc = await scoreFor(st, ckptOf(st));
  const byPos = parseProbes(sc && sc.probes);
  const table = byPos[pos] || {};
  const targets = Object.keys(HUMAN).filter(t => t in table)
    .concat(Object.keys(table).filter(t => !(t in HUMAN)));
  const layers = [...new Set(Object.values(table)
    .flatMap(o => Object.keys(o).map(Number)))].sort((a,b)=>a-b);
  let html = `<div class=trace><div class=cap>REPRESENTATION &middot;
    what information can be read from ${chip(st)}, and where</div>
    <div style="margin:6px 0;font-size:12px">read from:
      <button class="${pos==="agent"?"primary":""}" style="padding:3px 10px"
        onclick="probes('agent')">agent state</button>
      <button class="${pos==="decision"?"primary":""}" style="padding:3px 10px"
        onclick="probes('decision')">decision state</button></div>`;
  if(!targets.length){
    html += `<div class=note-dim>No probe records stored at this age for
      this specimen. Open a representation&rsquo;s developmental view from
      an age that has records (the pilot carries probes at 20/60/100%;
      batch organisms at 100%) — or wait for the batch&rsquo;s full probe
      schedule.</div>`;
  } else {
    html += `<div class=scroller><table class=mtx><tr><th></th>` +
      layers.map(l=>`<th>Layer ${l}</th>`).join("") + "</tr>";
    for(const t of targets){
      const best = Math.max(...layers.map(l => table[t][l]?.sel ?? -1));
      html += `<tr><td class=name data-t="${t}">${HUMAN[t] || t}</td>` +
        layers.map(l => {
          const c = table[t][l];
          const hot = c && c.sel === best && c.sel >= 0.25;
          return `<td class="${hot?"hot":""}">${fmt(c && c.sel)}</td>`;
        }).join("") + "</tr>";
    }
    let confound = "";
    try{
      const ev = await j("/api/evidence?run=" +
        encodeURIComponent(st.run.run));
      const best = Object.entries(ev.layers).flatMap(([L,row]) =>
        Object.entries(row).filter(([k])=>k.includes("lambda"))
          .map(([k,v])=>({loc:L+"/"+k, sel:v.heldout_agent_selectivity})))
        .sort((a,b)=>b.sel-a.sel)[0];
      confound = best && best.sel >= 0.25
        ? `<b>Identity confound tested:</b> the λ probe still recovers
           the class from AGENTS IT NEVER SAW (held-out-agent
           selectivity ${fmt(best.sel)} @ ${best.loc}) — evidence for
           class information beyond name recognition.`
        : `<b>Identity confound tested:</b> λ recovery collapses on
           held-out agents — what this probe reads may be agent
           identity, not an abstract preference class.`;
    }catch(e){
      confound = `<b>Identity confound UNRESOLVED:</b> λ is fixed per
        agent, so recovery from the agent state may be name recognition
        rather than an abstract preference class. The held-out-agent
        probe (probe_generalization.py) decides.`;
    }
    html += `</table></div>
    <div class=note-dim>selectivity = probe performance &minus; matched
      control (Hewitt-Liang). Click a representation for its developmental
      emergence.</div>
    <div class=note-dim style="margin-top:6px"><b>Evidence:</b> THIS
      linear probe can recover the labeled information above its matched
      control from these states — recoverability by this probe under
      this evaluation, not &ldquo;the representation&rdquo; in general.
      <b>Small cells:</b> not recovered by this probe here — which is
      not evidence of absence. <b>Never established here:</b> causal
      use.</div>
    <div class=note-dim style="margin-top:6px">${confound}</div>
    <div class=note-dim style="margin-top:6px">the ladder this instrument
      climbs: recoverable &rarr; generalizes &rarr; developmentally
      localized &rarr; causally used &rarr; replicated &rarr; abstracted
      &rarr; executable</div>`;
  }
  html += `<details style="margin-top:6px"><summary style="font-size:11px;
    color:var(--inst);cursor:pointer">inspect measurement (raw values,
    provenance)</summary><div class=reading style="font-size:11px;
    white-space:pre-wrap">${JSON.stringify((sc && sc.probes) || {}, null, 1)
    .replace(/</g,"&lt;")}
&#8627; ${st.run.run_id || st.run.run} · ${ckptOf(st)} · ${st.data} · commit ${st.run.commit}</div></details></div>
  <div id=devemergence></div>`;
  canvas(html);
  document.querySelectorAll(".mtx td.name").forEach(td =>
    td.onclick = () => emergence(td.dataset.t, pos));
}

function cellGlyph(sel){
  if(sel == null) return "—";
  const a = Math.abs(sel);
  return a >= 0.5 ? "█" : a >= 0.25 ? "▒" : a >= 0.1 ? "░" : "·";
}

async function emergence(target, pos){
  const subs = S.B ? [S.A, S.B] : [S.A];
  let html = `<div class=trace><div class=cap>DEVELOPMENTAL EMERGENCE
    &middot; ${HUMAN[target] || target} &middot; ${pos} state</div>`;
  let site = null;
  for(const st of subs){
    const ages = st.run.ckpts;
    const rows = {};
    for(const ck of ages){
      const sc = await scoreFor(st, ck);
      const t = parseProbes(sc && sc.probes)[pos] || {};
      for(const [l, c] of Object.entries(t[target] || {})){
        (rows[l] ??= {})[ck] = c.sel;
        if(!site || c.sel > site.sel)
          site = {sel: c.sel, layer: l, ck: ck, st: st};
      }
    }
    const layers = Object.keys(rows).map(Number).sort((a,b)=>a-b);
    html += `<div class=reading style="margin-top:8px">${chip(st)}</div>`;
    if(!layers.length){
      html += `<div class=note-dim>no probe records for this specimen
        yet</div>`;
      continue;
    }
    html += `<div class=scroller><table class=mtx><tr><th></th>` +
      ages.map(ck=>`<th>${ck.replace("ckpt_","").replace(".pt","")}%</th>`)
      .join("") + "</tr>";
    for(const l of layers){
      html += `<tr><td class=name style="cursor:default">Layer ${l}</td>` +
        ages.map(ck => `<td title="${fmt(rows[l][ck])}">${
          cellGlyph(rows[l][ck])}</td>`).join("") + "</tr>";
    }
    html += "</table></div>";
  }
  html += `<div class=note-dim>█ &ge;.50 &nbsp; ▒ &ge;.25 &nbsp; ░ &ge;.10
    &nbsp; · measured, weak &nbsp; — not measured. Hover a cell for the
    value. When did this representation appear — and does curriculum
    change the when or the where?</div>`;
  // behavior on the same time axis: does information become recoverable
  // before, during, or after the behavioral transition?
  for(const st of subs){
    try{
      const s = await j("/api/series?run=" + encodeURIComponent(st.run.run));
      const pts = s.series.filter(r => "conflict" in r);
      if(!pts.length) continue;
      html += `<div class=reading style="margin-top:8px;font-size:11px">
        ${chip(st)} · behavior on the same ages (fraction matching the
        outcome rule on the disagreement set)</div>
        <div class=meter>` + pts.map(r =>
          String(r.pct).padStart(3) + "%:" +
          "█".repeat(Math.round(r.conflict*10)).padEnd(10,"░") + " " +
          (r.conflict*100).toFixed(0) + "%").join("   ") + `</div>`;
    }catch(e){}
  }
  html += `<div class=note-dim style="margin-top:6px">before / during /
    after — the timing relation between recoverability and behavior is
    the developmental question, and it is read from stored artifacts
    only.</div>`;
  if(site && site.sel >= 0.25){
    html += `<div class=reading style="margin-top:8px;color:var(--orange)">
      CANDIDATE SITE: Layer ${site.layer} &middot; ${pos} state &middot;
      ${HUMAN[target] || target} (selectivity ${fmt(site.sel)} @ age ${
      site.ck.replace("ckpt_","").replace(".pt","")}%, ${chip(site.st)})
      &mdash; the causal instrument tests whether it matters (locked)</div>`;
  }
  html += "</div>";
  $("devemergence").innerHTML = html;
}
window.probes = probes;

/* ---- constellation: L2 exploratory geometry (stored artifacts) --------- */

const GEO_COLORS = {
  lambda_class: {SELF:"#B4452A", COOP:"#1D6A96"},
  cue_class: {SELF:"#B4452A", COOP:"#1D6A96", NEUT:"#8a8574"},
  scene: {market:"#7A5FA8", river:"#1e4d38"},
};

function scatterSVG(geo, layer, pos, colorBy, title){
  const cell = geo.positions[pos][layer];
  if(!cell) return "<div class=note-dim>no artifact for this view</div>";
  const xs = cell.xy.map(p=>p[0]), ys = cell.xy.map(p=>p[1]);
  const xmin=Math.min(...xs), xmax=Math.max(...xs),
        ymin=Math.min(...ys), ymax=Math.max(...ys);
  const W=300, H=240, pad=14;
  const sx = x => pad + (W-2*pad)*(x-xmin)/((xmax-xmin)||1);
  const sy = y => H-pad - (H-2*pad)*(y-ymin)/((ymax-ymin)||1);
  const labels = geo.labels[colorBy];
  let pts = "";
  cell.xy.forEach((p,i)=>{
    const c = (GEO_COLORS[colorBy]||{})[labels[i]] || "#26241d";
    pts += `<circle cx=${sx(p[0]).toFixed(1)} cy=${sy(p[1]).toFixed(1)}
      r=2.4 fill="${c}" fill-opacity=.65><title>${labels[i]}</title></circle>`;
  });
  return `<div><div class=reading style="font-size:11px">${title} ·
    2-D PCA (${Math.round(cell.var2*100)}% var)</div>
    <svg width=${W} height=${H} viewBox="0 0 ${W} ${H}"
      style="border:1px solid var(--rule);border-radius:3px;background:#fff">
      ${pts}</svg></div>`;
}

async function constellation(opts){
  opts = opts || S.geoOpts ||
    {layer:"L3", pos:"agent", colorBy:"lambda_class"};
  S.geoOpts = opts;
  const subs = S.B ? [S.A, S.B] : [S.A];
  const geos = [];
  for(const st of subs){
    try{
      geos.push(await j("/api/geometry?run=" +
        encodeURIComponent(st.run.run) + "&ckpt=" +
        encodeURIComponent(ckptOf(st))));
    }catch(e){ geos.push(null); }
  }
  const btn = (key, val, label) => `<button style="padding:3px 9px;
    font-size:11px" class="${opts[key]===val?"primary":""}"
    onclick='constellation(Object.assign({},window.LABSTATE.geoOpts,
      {${key}:"${val}"}))'>${label||val}</button>`;
  const animBtn = `<button style="padding:3px 9px;font-size:11px"
    onclick='animateConstellation()'>&#9654; animate development</button>`;
  let html = `<div class=trace><div class=cap>REPRESENTATION MAP &middot;
    EXPLORATORY VIEW — geometry can suggest structure; it does not
    establish semantic or causal identity</div>
    <div style="margin:6px 0;font-size:11px">
      layer ${["L0","L1","L2","L3","L4","L5"].map(l=>btn("layer",l)).join("")}
      &nbsp; read from ${btn("pos","agent")} ${btn("pos","decision")}
      &nbsp; color by ${btn("colorBy","lambda_class","hidden preference")}
      ${btn("colorBy","cue_class","wording class")}
      ${btn("colorBy","scene","place")} &nbsp; ${animBtn}</div>
    <div class=note-dim>each point is one held-out scenario&rsquo;s
      residual-stream state; a pattern here is a HYPOTHESIS — the probe
      and (locked) causal instruments decide what it means</div>
    <div class=duo style="margin-top:8px">`;
  subs.forEach((st,i)=>{
    html += `<div class=half>` + (geos[i]
      ? scatterSVG(geos[i], opts.layer, opts.pos, opts.colorBy, chip(st))
      : `<div class=who>${chip(st)}</div><div class=note-dim>no geometry
        artifact at this age — run geometry.py for this specimen</div>`) +
      `</div>`;
  });
  html += `</div></div>`;

  // twin convergence (CKA) + weight-space trajectories, from artifacts
  try{
    const comp = await j("/api/geometry_compare");
    html += `<div class=trace><div class=cap>TWIN SIMILARITY THROUGH
      DEVELOPMENT &middot; linear CKA, ${opts.layer} &middot; 1.0 =
      identical geometry</div><div class=scroller><table class=mtx>
      <tr><th></th>` + comp.matched_ages.map(r=>`<th>${
        r.ckpt.replace("ckpt_","").replace(".pt","")}%</th>`).join("") +
      `</tr><tr><td class=name style="cursor:default">agent state</td>` +
      comp.matched_ages.map(r=>`<td>${r.layers[opts.layer].agent
        .toFixed(2)}</td>`).join("") + `</tr>
      <tr><td class=name style="cursor:default">decision state</td>` +
      comp.matched_ages.map(r=>`<td>${r.layers[opts.layer].decision
        .toFixed(2)}</td>`).join("") + `</tr></table></div>
      <div class=note-dim>same-age geometry similarity between the
      differently-raised twins — where it dips, their internal worlds
      differ most</div></div>`;
  }catch(e){}
  try{
    const ws = await j("/api/weightspace");
    const runsIn = [...new Set(ws.points.map(p=>p.run))];
    const colors = ["#1e4d38","#B4452A"];
    const xs = ws.xy.map(p=>p[0]), ys = ws.xy.map(p=>p[1]);
    const xmin=Math.min(...xs), xmax=Math.max(...xs),
          ymin=Math.min(...ys), ymax=Math.max(...ys);
    const W=460, H=200, pad=18;
    const sx = x => pad + (W-2*pad)*(x-xmin)/((xmax-xmin)||1);
    const sy = y => H-pad - (H-2*pad)*(y-ymin)/((ymax-ymin)||1);
    let svg = "";
    runsIn.forEach((r,ri)=>{
      const idx = ws.points.map((p,i)=>p.run===r?i:-1).filter(i=>i>=0);
      svg += `<path fill=none stroke="${colors[ri]}" stroke-width=1.3
        d="${idx.map((i,k)=>(k?"L":"M")+sx(ws.xy[i][0]).toFixed(1)+" "+
        sy(ws.xy[i][1]).toFixed(1)).join(" ")}"></path>`;
      idx.forEach(i=>{
        const age = ws.points[i].ckpt.replace("ckpt_","").replace(".pt","");
        svg += `<circle cx=${sx(ws.xy[i][0]).toFixed(1)}
          cy=${sy(ws.xy[i][1]).toFixed(1)} r=3 fill="${colors[ri]}">
          <title>${r} · age ${age}%</title></circle>`;
      });
      svg += `<text x=${W-150} y=${16+ri*13}
        fill="${colors[ri]}">${r.replace("runs/","")}</text>`;
    });
    html += `<div class=trace><div class=cap>DEVELOPMENTAL TRAJECTORIES
      IN WEIGHT SPACE &middot; classical MDS of pairwise cosine
      distances</div>
      <svg width=${W} height=${H} viewBox="0 0 ${W} ${H}"
        style="border:1px solid var(--rule);border-radius:3px;
        background:#fff">${svg}</svg>
      <div class=note-dim>each dot is a preserved checkpoint; hover for
      identity. Both organisms depart from the SAME initialization —
      whether their paths converge during the shared tail is the
      developmental question, stated in parameter space</div></div>`;
  }catch(e){}
  canvas(html);
}
window.constellation = constellation;

async function animateConstellation(){
  // step every bench age for Subject A (and B): birth cloud -> structure
  const ages = S.A.run.ckpts.map((_,i)=>i);
  for(const i of ages){
    S.A.ckptIdx = i;
    if(S.B && i < S.B.run.ckpts.length) S.B.ckptIdx = i;
    renderAges("A"); if(S.B) renderAges("B");
    await constellation(S.geoOpts);
    await new Promise(r=>setTimeout(r, 1100));
  }
}
window.animateConstellation = animateConstellation;

/* ---- developmental atlas (viz #1) --------------------------------------- */

function atlasGlyph(lam, cue){
  const m = Math.max(lam||0, cue||0);
  if(m < 0.1) return {g:"·", c:"var(--graphite)", t:"weak"};
  const which = (lam||0) >= (cue||0) ? "λ" : "cue";
  const col = which === "λ" ? "#1D6A96" : "#B4452A";
  if(m >= 0.5) return {g:"●"+which, c:col, t:"strong"};
  if(m >= 0.25) return {g:"○"+which, c:col, t:"moderate"};
  return {g:"◦", c:col, t:"emerging"};
}

async function atlas(sel){
  const subs = S.B ? [S.A, S.B] : [S.A];
  const arts = [];
  for(const st of subs){
    try{ arts.push(await j("/api/atlas?run=" +
      encodeURIComponent(st.run.run))); }
    catch(e){ arts.push(null); }
  }
  const pos = (sel && sel.pos) || S.atlasPos || "agent";
  S.atlasPos = pos;
  let html = `<div class=trace><div class=cap>DEVELOPMENTAL ACTIVATION
    ATLAS &middot; each cell is a location in the developmental trace</div>
    <div style="margin:6px 0;font-size:11px">read from
      <button class="${pos==="agent"?"primary":""}" style="padding:3px 10px"
        onclick='atlas({pos:"agent"})'>agent state</button>
      <button class="${pos==="decision"?"primary":""}" style="padding:3px 10px"
        onclick='atlas({pos:"decision"})'>decision state</button></div>`;
  subs.forEach((st, si) => {
    const a = arts[si];
    html += `<div class=reading style="margin-top:10px">${chip(st)}</div>`;
    if(!a){
      html += `<div class=note-dim>atlas tensor not yet computed for
        this specimen (atlas.py is the producer; it consumes stored
        checkpoints only)</div>`;
      return;
    }
    html += `<div class=scroller><table class=mtx><tr><th></th>` +
      a.ages.map(g=>`<th>${+g}%</th>`).join("") + "</tr>";
    for(const L of a.layers){
      html += `<tr><td class=name style="cursor:default">Layer ${L.slice(1)}</td>` +
        a.ages.map(g => {
          const lam = (a.cells[`${g}/${L}/${pos}/lambda_class`]||{}).sel;
          const cue = (a.cells[`${g}/${L}/${pos}/verb_class_1`]||{}).sel;
          const gl = atlasGlyph(lam, cue);
          return `<td style="cursor:pointer;color:${gl.c}"
            onclick='atlasCell(${si},"${g}","${L}")'
            title="λ ${fmt(lam)} · cue ${fmt(cue)} · click to inspect">${gl.g}</td>`;
        }).join("") + "</tr>";
    }
    html += `</table></div>`;
  });
  html += `<div class=note-dim>●λ strong (&ge;.50) &nbsp; ○λ moderate
    (&ge;.25) &nbsp; ◦ emerging (&ge;.10) &nbsp; · weak. Blue = hidden
    preference, orange = wording cue — whichever this probe recovers more
    strongly. Click any cell to inspect that location. Recoverability by
    this probe only; never causal use.</div>
    <div class=note-dim style="margin-top:6px"><b>Read relative to the
    birth column.</b> λ is fixed per agent and this probe&rsquo;s
    train/test split shares agents, so agent-identity information alone
    buys nonzero λ recovery even from the newborn&rsquo;s random
    weights — the age-0 column IS the identity floor. Development is
    what rises above it; the held-out-agent instrument (λ / cue probes)
    controls the confound properly.</div>
    <div id=atlascell></div></div>`;
  canvas(html);
}
window.atlas = atlas;

async function atlasCell(si, age, L){
  const st = (S.B ? [S.A, S.B] : [S.A])[si];
  const a = await j("/api/atlas?run=" + encodeURIComponent(st.run.run));
  const pos = S.atlasPos || "agent";
  const ck = "ckpt_" + age + ".pt";
  const lam = a.cells[`${age}/${L}/${pos}/lambda_class`] || {};
  const cue = a.cells[`${age}/${L}/${pos}/verb_class_1`] || {};
  const ages = a.ages;
  const i = ages.indexOf(age);
  const neigh = t => ages.map(g =>
    `${+g}%:${fmt((a.cells[`${g}/${L}/${pos}/${t}`]||{}).sel)}`)
    .join("  ");
  let behav = "no stored behavior at this age";
  try{
    const s = await j("/api/series?run=" + encodeURIComponent(st.run.run));
    const row = s.series.find(r => r.pct === +age);
    if(row && "conflict" in row)
      behav = (row.conflict*100).toFixed(0) +
        "% of the disagreement set matched the outcome rule";
  }catch(e){}
  let geoThumb = "";
  try{
    const geo = await j("/api/geometry?run=" +
      encodeURIComponent(st.run.run) + "&ckpt=" + encodeURIComponent(ck));
    geoThumb = scatterSVG(geo, L, pos, "lambda_class",
      "geometry at this location (exploratory)");
  }catch(e){}
  $("atlascell").innerHTML = `<div style="border-top:1px solid var(--rule);
    margin-top:10px;padding-top:8px">
    <div class=reading style="font-size:11px">${chip(st)} · Layer ${L.slice(1)}
      · ${pos} state · age ${+age}%</div>
    <div class=reading style="margin-top:4px">λ    probe ${fmt(lam.acc)}
      selectivity ${fmt(lam.sel)}\ncue  probe ${fmt(cue.acc)}
      selectivity ${fmt(cue.sel)}</div>
    <div class=note-dim>behavior at this age: ${behav}</div>
    <div class=note-dim>λ across ages @ this layer:   ${neigh("lambda_class")}</div>
    <div class=note-dim>cue across ages @ this layer: ${neigh("verb_class_1")}</div>
    <div style="margin-top:6px">${geoThumb}</div>
    <div class=note-dim>&#8627; ${a._provenance.run_id} · ${ck} ·
      commit ${(a._provenance.commit||"").slice(0,8)}</div></div>`;
}
window.atlasCell = atlasCell;

/* ---- twin difference map (viz #4, single-pair EXPLORATORY form) --------- */

async function diffmap(sel){
  const pos = (sel && sel.pos) || S.diffPos || "agent";
  S.diffPos = pos;
  let comp;
  try{ comp = await j("/api/geometry_compare"); }
  catch(e){
    canvas(`<div class=trace><div class=cap>TWIN DIFFERENCE MAP</div>
      <div class=note-dim>no comparison artifact — geometry.py produces
      it from two specimens&rsquo; stored checkpoints</div></div>`);
    return;
  }
  const layers = Object.keys(comp.matched_ages[0].layers);
  const cell = (row, L) => {
    const d = 1 - row.layers[L][pos];
    const bg = d >= 0.15 ? "#B4452A" : d >= 0.08 ? "#d99a86" :
               d >= 0.03 ? "#efd9c9" : "#f6f1e5";
    return `<td style="background:${bg};cursor:pointer"
      title="1−CKA = ${d.toFixed(2)} · click for the geometry"
      onclick='constellation({layer:"${L}",pos:"${pos}",colorBy:"lambda_class"})'>${
      d.toFixed(2)}</td>`;
  };
  let html = `<div class=trace><div class=cap>TWIN DIFFERENCE MAP &middot;
    where did childhood leave a detectable difference? &middot;
    EXPLORATORY</div>
    <div class=note-dim>1 &minus; linear CKA between the two bench
    specimens&rsquo; geometry at matched ages — darker = their internal
    representations differ more. <b>Single-pair form:</b> normalization
    against within-condition seed variability arrives with the batch;
    until then a hot cell is a place to LOOK, not a finding.</div>
    <div style="margin:6px 0;font-size:11px">
      <button class="${pos==="agent"?"primary":""}" style="padding:3px 10px"
        onclick='diffmap({pos:"agent"})'>agent state</button>
      <button class="${pos==="decision"?"primary":""}" style="padding:3px 10px"
        onclick='diffmap({pos:"decision"})'>decision state</button></div>
    <div class=scroller><table class=mtx><tr><th></th>` +
    comp.matched_ages.map(r=>`<th>${+r.ckpt.replace("ckpt_","")
      .replace(".pt","")}%</th>`).join("") + "</tr>";
  for(const L of layers){
    html += `<tr><td class=name style="cursor:default">Layer ${L.slice(1)}</td>` +
      comp.matched_ages.map(r=>cell(r, L)).join("") + "</tr>";
  }
  html += `</table></div>
    <div class=note-dim>click a hot cell to open the geometry at that
    layer — then probes, then (locked) causal tests: look &rarr; probe
    &rarr; trace &rarr; intervene</div></div>`;
  canvas(html);
}
window.diffmap = diffmap;

async function exectrace(){
  const subs = S.B ? [S.A, S.B] : [S.A];
  let html = "";
  let shownCase = false;
  for(const st of subs){
    let tr = null;
    try{ tr = await j("/api/trace?run=" +
      encodeURIComponent(st.run.run)); }catch(e){}
    if(!tr){
      html += `<div class=trace><div class=cap>EXECUTION TRACE &middot;
        ${chip(st)}</div><div class=note-dim>no trace record yet
        (trace_run.py — it will not draw a graph before the traces
        exist)</div></div>`;
      continue;
    }
    if(!shownCase){
      shownCase = true;
      html += `<div class=trace><div class=cap>EXECUTION TRACE &middot;
        ONE DECISION, THE IMPLICATED STAGES ONLY — never a dump of the
        network</div>
        <div class=scene>${tr.case.prompt}</div>
        <div class=reading style="font-size:12px">utility says Option
        ${tr.case.utility_answer} · wording says Option
        ${tr.case.cue_answer}</div>
        <div class=note-dim>hypothesis under trace: ${tr.hypothesis}</div>
        </div>`;
    }
    const Ls = Object.keys(tr.stages);
    html += `<div class=trace><div class=cap>${chip(st)} &middot; chose
      Option ${tr.model_choice} (Δlogp ${fmt(tr.final_dlogp)})</div>
      <div class=scroller><table class=mtx><tr><th></th>` +
      Ls.map(l=>`<th>${l}</th>`).join("") + `</tr>
      <tr><td class=name style="cursor:default" title="projection of the residual onto v_λ at the agent token">λ signal @ agent</td>` +
      Ls.map(l=>`<td>${fmt(tr.stages[l].lambda_alignment_agent)}</td>`).join("") + `</tr>
      <tr><td class=name style="cursor:default" title="projection at the decision position">λ signal @ decision</td>` +
      Ls.map(l=>`<td>${fmt(tr.stages[l].lambda_alignment_decision)}</td>`).join("") + `</tr>
      <tr><td class=name style="cursor:default" title="Δlogp(1−2) if the network stopped at this layer">decision forming (lens)</td>` +
      Ls.map(l=>`<td>${fmt(tr.stages[l].logitlens_dlogp)}</td>`).join("") + `</tr>
      <tr><td class=name style="cursor:default" title="how this case's Δlogp moves when v_λ is projected out at this layer">λ-ablation shift</td>` +
      Ls.map(l=>`<td>${fmt(tr.stages[l].lambda_ablation_dlogp_shift)}</td>`).join("") + `</tr>
      </table></div>
      <div class=note-dim>${tr.semantics}. Each row connects backward to
      the localization evidence that nominated it and forward to the
      intervention that tests it.</div>
      <div class=note-dim>&#8627; ${tr._provenance.run_id} · ${tr.ckpt} ·
      commit ${(tr._provenance.commit||"").slice(0,8)}</div></div>`;
  }
  canvas(html);
}

/* ---- pending instruments ------------------------------------------------ */

async function causal(){
  const subs = S.B ? [S.A, S.B] : [S.A];
  let any = false;
  let html = `<div class=trace><div class=cap>PERTURB &middot; STEERING
    &middot; predicted-direction intervention with controls</div>`;
  for(const st of subs){
    let ev = null;
    try{ ev = await j("/api/steering?run=" +
      encodeURIComponent(st.run.run)); }catch(e){}
    html += `<div class=reading style="margin-top:10px">${chip(st)}</div>`;
    if(!ev){
      html += `<div class=note-dim>no steering record for this specimen
        yet (steer_run.py is the producer; it states its prediction
        before running)</div>`;
      continue;
    }
    any = true;
    html += `<div class=note-dim><b>Prediction (stated before the
      result):</b> ${ev.prediction}</div>`;
    const sweepTable = (name, sweepIn) => {
      const sweep = sweepIn.alphas || sweepIn;
      const alphas = Object.keys(sweep);
      return `<div class=reading style="font-size:11px;margin-top:6px">${name}</div>
        <div class=scroller><table class=mtx><tr><th>α</th>` +
        alphas.map(a=>`<th>${a}</th>`).join("") + `</tr>
        <tr><td class=name style="cursor:default">matches outcomes</td>` +
        alphas.map(a=>`<td>${fmt(sweep[a].acc_utility)}</td>`).join("") +
        `</tr></table></div>`;
    };
    const spark = (sweepIn, color) => {
      const sweep = sweepIn.alphas || sweepIn;
      const ks = Object.keys(sweep).sort((a,b)=>+a-+b);
      const W=140, H=36;
      const pts = ks.map((k,i)=>
        (i?"L":"M") + (6+(W-12)*i/(ks.length-1)).toFixed(1) + " " +
        (H-4-(H-8)*sweep[k].acc_utility).toFixed(1)).join(" ");
      return `<svg width=${W} height=${H} viewBox="0 0 ${W} ${H}"
        style="vertical-align:middle"><path d="${pts}" fill=none
        stroke="${color}" stroke-width=1.6></path></svg>`;
    };
    html += `<div style="margin:6px 0">
      ${spark(ev.sweeps.candidate, "#1e4d38")} candidate
      ${spark(ev.sweeps.control_layer, "#8a8574")} layer ctrl
      ${spark(ev.sweeps.random_direction, "#B4452A")} random ctrl
      <span class=note-dim style="font-size:10px">(acc-utility vs α —
      the candidate should be the only sloped line)</span></div>`;
    html += sweepTable("CANDIDATE " + ev.candidate_layer + " · λ direction",
                       ev.sweeps.candidate);
    html += sweepTable("control · " + ev.control_layer + " · λ direction",
                       ev.sweeps.control_layer);
    html += sweepTable("control · " + ev.candidate_layer +
                       " · random direction", ev.sweeps.random_direction);
    const d = ev.dose_response_spread;
    const verdict = d.candidate > Math.max(d.control_layer,
                                           d.random_direction)
      ? "dose-response at the candidate site EXCEEDS both controls — " +
        "consistent with the prediction"
      : "dose-response at the candidate site does NOT exceed the " +
        "controls — the prediction is not supported here";
    html += `<div class=reading style="margin-top:6px">spread:
      candidate ${fmt(d.candidate)} · control layer ${fmt(d.control_layer)}
      · random ${fmt(d.random_direction)}</div>
    <div class=note-dim><b>${verdict}.</b> Semantics: ${ev.semantics}.</div>
    <div class=note-dim>&#8627; ${ev._provenance.run_id} · ${ev.ckpt} ·
      commit ${(ev._provenance.commit||"").slice(0,8)}</div>`;
  }
  html += `</div>`;

  // ---- ablation: necessity with controls -------------------------------
  html += `<div class=trace><div class=cap>PERTURB &middot; ABLATE &middot;
    is the λ direction NECESSARY?</div>`;
  for(const st of subs){
    let ab = null;
    try{ ab = await j("/api/ablation?run=" +
      encodeURIComponent(st.run.run)); }catch(e){}
    html += `<div class=reading style="margin-top:8px">${chip(st)}</div>`;
    if(!ab){ html += `<div class=note-dim>no ablation record yet
      (ablate_run.py)</div>`; continue; }
    const d = ab.utility_agreement_drop;
    html += `<div class=note-dim><b>Prediction (stated before the
      result):</b> ${ab.prediction}</div>
      <div class=reading style="font-size:12px">baseline utility-agreement
      ${fmt(ab.baseline.acc_utility)}
drop when ablating:  v_λ @ ${ab.candidate_layer} ${fmt(d.candidate_lambda)}
                     random @ ${ab.candidate_layer} ${fmt(d.random_direction)}
                     v_λ @ ${ab.control_layer} ${fmt(d.control_layer_lambda)}</div>`;
    const bar = (label, val, color) => {
      const w = Math.min(Math.abs(val)*600, 160);
      return `<div style="font:11px ui-monospace,Menlo,monospace">${label.padEnd(14)}
        <span style="display:inline-block;height:9px;width:${w}px;
        background:${color};vertical-align:middle"></span> ${fmt(val)}</div>`;
    };
    html += `<div style="margin:6px 0">
      ${bar("v_λ @ cand", d.candidate_lambda, "#1e4d38")}
      ${bar("random @ cand", d.random_direction, "#B4452A")}
      ${bar("v_λ @ ctrl", d.control_layer_lambda, "#8a8574")}</div>`;
    const selective = d.candidate_lambda >
      2 * Math.max(d.random_direction, d.control_layer_lambda);
    const necessary = d.candidate_lambda >
      2 * Math.max(d.random_direction, 0.02);
    html += `<div class=note-dim><b>${selective
      ? "Necessary AND selectively localized — prediction fully supported"
      : necessary
      ? "The λ direction is necessary (random control ~0), but NOT " +
        "selectively localized to the candidate layer — the failed " +
        "clause is itself a constraint on G_mech"
      : "Prediction not supported at this site"}.</b></div>
    <div class=note-dim>&#8627; ${ab._provenance.run_id} · ${ab.ckpt} ·
      commit ${(ab._provenance.commit||"").slice(0,8)}</div>`;
  }
  html += `</div>`;

  // ---- patching: transfer with controls --------------------------------
  html += `<div class=trace><div class=cap>PERTURB &middot; PATCH &middot;
    does the twin&rsquo;s state TRANSFER behavior?</div>`;
  for(const st of subs){
    let pa = null;
    try{ pa = await j("/api/patching?run=" +
      encodeURIComponent(st.run.run)); }catch(e){}
    html += `<div class=reading style="margin-top:8px">${chip(st)} as
      recipient</div>`;
    if(!pa){ html += `<div class=note-dim>no patching record yet
      (patch_run.py)</div>`; continue; }
    html += `<div class=note-dim><b>Prediction (stated before the
      result):</b> ${pa.prediction}</div>`;
    for(const [age, row] of Object.entries(pa.ages)){
      const r = row.recipient_baseline.acc_utility,
            dn = row.donor_baseline.acc_utility,
            p = row.patched_candidate.acc_utility;
      const lo = Math.min(r, dn, p) - 0.05, hi = Math.max(r, dn, p) + 0.05;
      const X = v => 8 + 224 * (v - lo) / (hi - lo);
      html += `<div class=reading style="font-size:12px;margin-top:6px">age ${+age}%</div>
      <svg width=280 height=34 viewBox="0 0 280 34">
        <line x1=8 y1=17 x2=232 y2=17 stroke="#cfc9b6"></line>
        <circle cx=${X(r).toFixed(1)} cy=17 r=4 fill="#1e4d38"><title>recipient ${fmt(r)}</title></circle>
        <circle cx=${X(dn).toFixed(1)} cy=17 r=4 fill="#1D6A96"><title>donor ${fmt(dn)}</title></circle>
        <circle cx=${X(p).toFixed(1)} cy=17 r=5 fill="none" stroke="#B4452A"
          stroke-width=2><title>patched ${fmt(p)}</title></circle>
        <text x=${X(r).toFixed(1)} y=31 text-anchor=middle
          style="font:8px ui-monospace">rec</text>
        <text x=${X(dn).toFixed(1)} y=8 text-anchor=middle
          style="font:8px ui-monospace">donor</text>
        <text x=${X(p).toFixed(1)} y=31 text-anchor=middle
          style="font:8px ui-monospace;fill:#B4452A">patched</text></svg>`;
      const au = pa.audit && pa.audit.per_example &&
                 pa.audit.per_example[age];
      if(au){
        html += `<div class=reading style="font-size:11.5px">on the ${au.candidate.n_disputed} items where the twins DISAGREE,
  the patched model sides with the donor ${fmt(au.candidate
    .on_disputed_items_sides_with_donor)} of the time
  (control layer ${fmt(au.control_layer
    .on_disputed_items_sides_with_donor)} · mismatched ${fmt(au
    .mismatched.on_disputed_items_sides_with_donor)})</div>`;
      }
    }
    if(pa.audit){
      html += `<div class=note-dim style="margin-top:6px"><b>AUDITED
        VERDICT:</b> ${pa.audit.verdict}</div>
        <div class=note-dim style="font-size:10.5px">${pa.audit
        .metric_note}</div>`;
    }
    html += `<div class=note-dim>&#8627; ${pa._provenance.run_id} ·
      commit ${(pa._provenance.commit||"").slice(0,8)}</div>`;
  }
  html += `</div>`;
  canvas(html);
}

function transplant(){
  canvas(`<div class=trace><div class=cap>DEVELOPMENTAL TRANSPLANT &middot;
    PENDING (B1)</div>
    <div class=reading>              optimizer C1   optimizer C2   fresh
weights C1         &middot;              &middot;            &middot;
weights C2         &middot;              &middot;            &middot;</div>
    <div class=note-dim style="margin-top:8px">We raised two twins
    differently. Now swap parts of their developmental state and continue
    on the identical common tail. Distinguishes: weights carry history /
    optimizer state carries it / their interaction / the tail erases it.
    The trainstates (&theta;, m, v, RNG) are already preserved at every
    curriculum boundary; this instrument activates when the batch
    finishes.</div></div>`);
}

/* ---- formalization ------------------------------------------------------ */

async function formal(){
  const st = S.A;
  let probeRow = null, conf = null;
  try{
    const sc = await j("/api/score?run=" + encodeURIComponent(st.run.run) +
                       "&ckpt=" + encodeURIComponent(ckptOf(st)));
    conf = (sc.sets || {}).eval_conflict || null;
    const pr = sc.probes || {};
    let best = null;
    for(const [k,v] of Object.entries(pr)){
      if(k.endsWith("lambda_class") && (!best || v.selectivity > best.sel))
        best = {loc: k, sel: v.selectivity};
    }
    probeRow = best;
  }catch(e){}
  let gen = null;
  try{
    const ev = await j("/api/evidence?run=" +
      encodeURIComponent(st.run.run));
    gen = Object.entries(ev.layers).flatMap(([L,row]) =>
      Object.entries(row).filter(([k])=>k.includes("lambda"))
        .map(([k,v])=>({loc:L+"/"+k, sel:v.heldout_agent_selectivity})))
      .sort((a,b)=>b.sel-a.sel)[0] || null;
  }catch(e){}
  const prov = "↳ " + (st.run.run_id || st.run.run) + " · " + ckptOf(st) +
    " · " + st.data + " · commit " + st.run.commit;
  const chipRow = (items) => items.map(([label, val, ok]) =>
    `<span style="border:1px solid var(--rule);border-radius:10px;
      padding:1px 9px;font:11px ui-monospace,Menlo,monospace;
      color:${ok===true?"var(--green)":ok===false?"var(--orange)":"var(--graphite)"}">${label} ${val}</span>`)
    .join(" ");
  const edgeCard = (line, chips, detail, id) => `
    <div style="margin:14px 0">
      <div class=reading style="font-size:15px;cursor:pointer"
        onclick="const d=document.getElementById('${id}');
          d.style.display=d.style.display==='none'?'block':'none'">${line}</div>
      <div style="margin:6px 0">${chips}</div>
      <div id=${id} style="display:none" class=note-dim>${detail}
        <div style="margin-top:4px">${prov}</div></div>
    </div>`;
  let html = `<div class=trace><div class=cap>CANDIDATE FORMALIZATION
    &middot; ${chip(st)} &middot; click an edge for its evidence</div>`;
  let steer = null;
  try{ steer = await j("/api/steering?run=" +
    encodeURIComponent(st.run.run)); }catch(e){}
  const steerOk = steer && steer.dose_response_spread.candidate >
    2 * Math.max(steer.dose_response_spread.control_layer,
                 steer.dose_response_spread.random_direction);
  html += edgeCard(
    steerOk ? "agent identity ─── λ ──── choice   (hardening)"
            : "agent identity ─── λ ──⇢ choice   (candidate)",
    chipRow([
      ["behavioral", conf ? fmt(conf.acc_utility) : "—", !!conf],
      ["recoverable", probeRow ? fmt(probeRow.sel) : "—", !!probeRow],
      ["generalizes", gen ? fmt(gen.sel) : "untested",
       gen ? gen.sel >= 0.25 : null],
      ["causal", steer ? "steer " + fmt(steer.dose_response_spread
        .candidate) : "○", steerOk || null],
      ["portable", "not supported", false],
      ["development", "○", null]]),
    (probeRow ? "λ-class recoverable @ " + probeRow.loc + " (this probe, " +
      "this evaluation). " : "") +
    (gen ? "Held-out-agent selectivity " + fmt(gen.sel) + " @ " + gen.loc +
      " — class information beyond name recognition. " :
      "Identity confound untested. ") +
    "Causal use and developmental localization pending — the arrow stays " +
    "dotted until intervention hardens it.",
    "edge-lam");
  html += edgeCard(
    "scene + wording ──⇢ choice   (candidate, behaviorally dominated)",
    chipRow([
      ["behavioral", conf ? fmt(conf.acc_cue) : "—", conf ? false : null],
      ["recoverable", "stored where measured", null],
      ["causal", "○", null]]),
    "The planted route: present in the corpus by construction; this " +
    "specimen's conflict behavior sides against it. Whether its " +
    "representation exists but is unused is exactly the causal " +
    "instrument's question.",
    "edge-cue");
  html += `<div style="margin-top:14px">
      <button onclick="exportGraph()">export evidence graph (JSON)</button>
      <button disabled>generate candidate formal spec &middot; pending</button>
    </div>
    <div class=note-dim style="margin-top:8px">evidence vectors, never one
    confidence number; solid arrows are earned by intervention only</div>
    </div>`;
  canvas(html);
}

function doors(){
  canvas(`<div class=trace><div class=cap>BEYOND THIS EXPERIMENT</div>
    <div class=duo>
      <div class=half><div class=who>ABSORB A CORPUS</div>
        <div class=reading style="font-size:10px;color:var(--orange)">ACT II &middot; LOCKED</div>
        <div class=note-dim>Can these instruments discover structure in a
        world we did not author?</div>
        <button style="margin-top:8px" onclick="dragon('corpus')">ABSORB
        &rarr; UNMAPPED CORPUS</button>
        <div id=dragon-corpus class=note-dim style="display:none;margin-top:8px">
        LOCKED — the instruments must first be validated here, in a world
        whose answers we know. When they are, a corpus arrives without a
        map.</div></div>
      <div class=half><div class=who>IMPORT A BRAIN</div>
        <div class=reading style="font-size:10px;color:var(--orange)">COMING SOON &middot; LOCKED</div>
        <div class=note-dim>Given a physical biological substrate, can we
        recover enough structure and dynamics to produce an executable
        formal abstraction?</div>
        <button style="margin-top:8px" onclick="dragon('brain')">IMPORT
        &rarr; BIOLOGICAL CONNECTOME</button>
        <div id=dragon-brain class=note-dim style="display:none;margin-top:8px">
        COMING SOON — connectome &rarr; candidate computational graph. A
        wiring diagram is not yet a brain: this instrument asks what
        additional evidence (cell types, synaptic properties, dynamics,
        plasticity, neuromodulation, functional recordings) is required to
        turn biological structure into a testable computational
        specification. Structure is a hypothesis; evidence promotes it.
        </div></div>
      <div class=half><div class=who>EMBODY THE COMPUTATION</div>
        <div class=reading style="font-size:10px;color:var(--orange)">FINAL DRAGON &middot; LOCKED</div>
        <div class=note-dim>Can a sufficiently characterized mechanism be
        compiled into another substrate?</div>
        <button style="margin-top:8px" onclick="dragon('neuro')">COMPILE
        &rarr; NEUROMORPHIC HARDWARE</button>
        <div id=dragon-neuro class=note-dim style="display:none;margin-top:8px">
        UNDER CONSTRUCTION — the present experiment does not establish that
        its learned computation can be faithfully compiled into a
        neuromorphic substrate. This is the engineering direction the
        formal representation is intended to make testable.
        <a href="/technique/neuromorphic-compilation" target=_blank
        rel=noopener>technical trail &nearr;</a></div></div>
    </div></div>`);
}
window.doors = doors;

window.dragon = k => { const el = $("dragon-"+k);
  el.style.display = el.style.display === "none" ? "block" : "none"; };

window.exportGraph = async () => {
  const ws = await j("/api/worldspec?data=" + encodeURIComponent(S.A.data));
  canvas(`<div class=trace><div class=cap>WORLD SPEC EXPORT &middot; four
    graphs, epistemic statuses distinct</div>
    <div class=reading style="white-space:pre-wrap;font-size:11.5px">${
    JSON.stringify(ws.graphs, null, 1).replace(/</g,"&lt;")}</div>
    <div class=note-dim>G_generator is privileged to the synthetic world;
    G_observational is derived from the corpus; G_development and
    G_mechanism populate from the trace ledger as evidence accumulates.
    </div></div>`);
};

/* ---- graphs drawer ------------------------------------------------------ */

function worldmodels(){ showGraph("generating"); }

function graphSwitcher(active){
  const kinds = [["generating","Generator"],["observational","Observational"],
    ["development","Development"],["mechanism","Mechanism"],
    ["overlay","Overlay"]];
  return `<div style="margin-bottom:8px"><span class=note-dim
    style="font-size:10px;letter-spacing:.15em">MODELS OF THE WORLD —
    how it was generated &rarr; what the corpus offers &rarr; what
    developed &rarr; what the network computes. Their disagreements are
    the point.&nbsp;&nbsp;</span>` +
    kinds.map(([k,l])=>`<button style="padding:3px 9px;font-size:11px"
      class="${k===active?"primary":""}"
      onclick="showGraph('${k}')">${l}</button>`).join(" ") + "</div>";
}

async function showGraph(kind){
  if(kind === "development" || kind === "mechanism" || kind === "overlay"){
    canvas(graphSwitcher(kind) +
      `<div class=trace><div class=cap>${kind.toUpperCase()} GRAPH &middot;
      PENDING</div><div class=note-dim>This graph populates as evidence
      records accumulate (${kind === "development"
        ? "paired-curriculum contrasts from the main batch"
        : kind === "mechanism"
        ? "probe, decomposition and intervention records"
        : "requires at least two graphs"}). It will not be drawn before
      the evidence exists.</div></div>`);
    return;
  }
  const ws = await j("/api/worldspec?data=" + encodeURIComponent(S.A.data));
  const g = kind === "observational" ? ws.graphs.observational
                                     : ws.graphs.generator;
  const cap = kind === "observational"
    ? "G_observational &middot; DERIVED FROM CORPUS"
    : "G_generator &middot; PRIVILEGED GROUND TRUTH — SYNTHETIC WORLD ONLY";
  let html = graphSwitcher(kind) +
    `<div class=trace><div class=cap>${cap}</div><div class=reading>`;
  for(const e of g.edges || []){
    const arrow = e.type === "predictive" ? "⇢" : "→";
    html += String(e.src).padEnd(20) + " " + arrow + " " +
      String(e.dst).padEnd(20) + "  [" + (e.type||"") + "]\n";
  }
  html += "</div>";
  if(kind === "observational"){
    html += `<div class=note-dim style="margin-top:6px">⇢ = predictive:
      an alternative predictor induced by the observational distribution,
      NOT a causal edge in the world. Training constraint:
      utility_prediction == cue_prediction == choice on every training
      example — the identification problem, stated formally.</div>`;
  } else {
    html += `<div class=note-dim style="margin-top:6px">Note the direction
      of the planted route: the generator causally assigns framing FROM
      the choice. Framing has no causal role in the authored preference
      mechanism. In Act II this graph is the one that disappears.</div>`;
  }
  html += "</div>";
  canvas(html);
}

/* ---- evidence ledger ----------------------------------------------------- */

// (renderEvidence defined above — live claim ladder)

/* ---- boot ---------------------------------------------------------------- */

const INSTRUMENTS = {ordinary:()=>behave("id"), conflict:()=>behave("conflict"),
  nocue:()=>behave("nocue"), cueonly:()=>behave("cueonly"),
  custom:compose, freeform, corpus:()=>corpus(), trajectory,
  probes:()=>probes(), constellation:()=>constellation(),
  atlas:()=>atlas(), diffmap:()=>diffmap(), exectrace, causal,
  transplant, formal, worldmodels};

async function init(){
  const [runs, ds] = await Promise.all([j("/api/runs"), j("/api/datasets")]);
  S.runs = runs; S.datasets = ds; S.data = ds[0].data;
  for(const which of ["A","B"]){
    const sel = $("sel"+which);
    sel.innerHTML = runs.map((r,i)=>
      `<option value=${i}>${r.run.replace("runs/","")} · ${r.curriculum||"?"}</option>`).join("");
    sel.onchange = ()=>bindSpecimen(which);   // re-fires active instrument
  }
  bindSpecimen("A", true);
  try{
    S.segments = (await j("/api/curricula?data=" +
      encodeURIComponent(S.A.data))).segments;
  }catch(e){ S.segments = {}; }
  $("addB").onclick = ()=>{
    $("specB").style.display = "block";
    $("addB").style.display = "none";
    bindSpecimen("B");   // re-fires the active instrument with B added
  };
  $("removeB").onclick = ()=>{
    S.B = null;
    $("specB").style.display = "none";
    $("addB").style.display = "block";
    refreshActive();
  };
  document.querySelectorAll("[data-inst]").forEach(b=>
    b.onclick = ()=>{ S.activeInst = b.dataset.inst;
                      INSTRUMENTS[b.dataset.inst](); });
  $("beyond").onclick = doors;
  renderEvidence();
  arrival();
  const want = new URLSearchParams(location.search).get("inst");
  if(want && INSTRUMENTS[want]){
    const btn = document.querySelector(`[data-inst='${want}']`);
    if(btn){ btn.closest("details").open = true; }
    S.activeInst = want;
    INSTRUMENTS[want]();
  }
  document.body.dataset.ready = "1";
}

/* the crossing: arriving from the expedition is a handoff, not a dump */
function arrival(){
  let fromExp = false, stage = 0;
  try{
    fromExp = localStorage.getItem("pdp-crossing") === "1";
    if(fromExp) localStorage.removeItem("pdp-crossing");
    const p = JSON.parse(localStorage.getItem("pdp-expedition-v1") || "{}");
    stage = p.stage || 0;
  }catch(e){}
  if(!fromExp) return;
  const qs = [];
  if(stage >= 13) qs.push("its behavior sides with the outcome rule when " +
    "the rules disagree — but HOW does the network compute that?");
  if(stage >= 5) qs.push("does it represent the hidden preference you " +
    "inferred in chapter 1, anywhere inside?");
  qs.push("what did developmental order change — and where does the " +
    "history live?");
  canvas(`<div class=trace><div class=cap>YOU HAVE CROSSED FROM THE FIELD
      STATION</div>
    <div class=scene>The learner you have been questioning is already on
      the bench — SUBJECT A, at full developmental age. Your open
      questions came with you:</div>
    <div class=reading style="white-space:pre-wrap">${qs.map(q=>"?  "+q).join("\n")}</div>
    <div style="margin-top:12px">
      <button class=primary id=arr-conflict>Run the instrument you already
        know — the conflict test &rarr;</button>
      <button id=arr-probes>Lower the first new instrument — the probes &rarr;</button>
    </div>
    <div class=note-dim style="margin-top:8px">or choose any specimen and
      instrument from the bench — this room does not mind what order you
      work in</div></div>`);
  $("arr-conflict").onclick = ()=>{ S.activeInst = "conflict";
    behave("conflict"); };
  $("arr-probes").onclick = ()=>{ S.activeInst = "probes"; probes(); };
}
init();
</script>
</body></html>
"""
