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
.frame{display:flex;gap:0;align-items:stretch;min-height:calc(100vh - 130px)}
.rail{width:264px;flex:none;border-right:1px solid var(--rule);
  padding:14px 16px}
.canvas{flex:1;padding:16px 22px;min-width:0}
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
.age input{width:100%;accent-color:var(--green)}
.age .lbl{font:10px ui-monospace,Menlo,monospace;color:var(--faded)}
button{font:12px system-ui,sans-serif;padding:6px 10px;cursor:pointer;
  background:none;color:var(--ink);border:1px solid var(--graphite);
  border-radius:2px;text-align:left}
button:hover{border-color:var(--green);color:var(--green)}
button.primary{background:var(--green);color:var(--ivory);
  border-color:var(--green)}
button:disabled{opacity:.4;cursor:default}

/* instrument tray */
.tray button{display:block;width:100%;margin:3px 0}
.tray .grp{font-size:9px;letter-spacing:.2em;color:var(--graphite);
  margin:10px 0 3px}
.tray button.pending{color:var(--graphite);border-style:dashed}

/* canvas */
#canvas-empty{color:var(--graphite);font-family:Georgia,serif;
  font-size:16px;margin-top:80px;text-align:center}
.trace{border:1px solid var(--rule);border-radius:3px;background:var(--card);
  padding:14px;margin-bottom:12px}
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

/* drawer */
.drawer .tabbtn{display:inline-block;margin:2px 2px;padding:4px 8px;
  font-size:11px}
.evrow{border-top:1px solid var(--rule);padding:6px 2px;font-size:12px;
  cursor:pointer}
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
  <h3 class=zone>SPECIMEN BENCH</h3>
  <div class=specimen id=specA>
    <div class=who>SUBJECT A</div>
    <select id=selA></select>
    <div class=idcard id=cardA></div>
    <div class=age><input type=range id=ageA min=0 max=0 value=0>
      <div class=lbl id=ageAlbl></div></div>
  </div>
  <div class=specimen id=specB style="display:none">
    <div class=who>SUBJECT B</div>
    <select id=selB></select>
    <div class=idcard id=cardB></div>
    <div class=age><input type=range id=ageB min=0 max=0 value=0>
      <div class=lbl id=ageBlbl></div></div>
  </div>
  <button id=addB>+ add comparison specimen</button>

  <h3 class=zone style="margin-top:20px">INSTRUMENTS</h3>
  <div class=tray>
    <div class=grp>BEHAVIOR</div>
    <button data-inst=ordinary>ordinary case</button>
    <button data-inst=conflict>conflict test</button>
    <button data-inst=nocue>remove cue</button>
    <button data-inst=cueonly>cue only</button>
    <button id=newscen class=pending style="border-style:solid">new scenario &#8635;</button>
    <div class=grp>DEVELOPMENT</div>
    <button data-inst=trajectory>checkpoint trajectories</button>
    <div class=grp>REPRESENTATION</div>
    <button data-inst=probes>&lambda; / cue probes</button>
    <div class=grp>CAUSAL</div>
    <button data-inst=causal class=pending>steer &middot; patch &middot; ablate</button>
    <button data-inst=transplant class=pending>developmental transplant</button>
    <div class=grp>FORMALIZATION</div>
    <button data-inst=formal>evidence &amp; export</button>
  </div>
</aside>

<main class=canvas id=canvas>
  <div id=canvas-empty>Choose a specimen and an instrument.</div>
</main>

<aside class=drawer>
  <h3 class=zone>GRAPHS</h3>
  <div>
    <button class=tabbtn data-graph=generating>Generating</button>
    <button class="tabbtn pending" data-graph=development>Development</button>
    <button class="tabbtn pending" data-graph=mechanism>Mechanism</button>
    <button class="tabbtn pending" data-graph=overlay>Overlay</button>
  </div>
  <hr class=g>
  <h3 class=zone>EVIDENCE</h3>
  <div id=evidence></div>
</aside>

</div>
<script>
"use strict";
const $ = id => document.getElementById(id);
const j = (u,o) => fetch(u,o).then(r=>{ if(!r.ok) throw new Error(u+" "+r.status); return r.json(); });
const S = {runs:[], data:null, A:null, B:null, cfg:null, lastMode:null};
window.LABSTATE = S;

const EVIDENCE = [
  {k:"behavior", label:"Behavior: ID competence", st:"?",
   sup:"forced-choice accuracy on held-out ordinary cases (stored scores).",
   not:"which rule produced the behavior.",
   next:"conflict test (identification)."},
  {k:"ident", label:"Identification: conflict separates routes", st:"y",
   sup:"the diagnostic sets are constructed so the two rules disagree — by authorship, not measurement.",
   not:"which route this organism follows — run the conflict instrument.",
   next:"conflict test on each specimen."},
  {k:"repr", label:"Representation: λ decodable", st:"?",
   sup:"linear probes with Hewitt-Liang controls at 20/40/60/80/100% (stored where measured).",
   not:"that the model USES the information (decodable ≠ causal).",
   next:"steering / patching (Phase B)."},
  {k:"causal", label:"Causal use", st:"o",
   sup:"no intervention records yet.",
   not:"— untested.",
   next:"steer along the probe direction; patch across twins (Phase B)."},
  {k:"carrier", label:"Developmental carrier", st:"o",
   sup:"no transplant records yet.",
   not:"— untested.",
   next:"crossed weights × optimizer-state transplant at the common tail (B1)."},
];

function canvas(html){
  $("canvas").innerHTML = html;
}

function subj(which){ return which === "A" ? S.A : S.B; }

function idcard(run){
  return run.arch + "\n" + (run.n_params ? (run.n_params/1e6).toFixed(1) +
    "M parameters\n" : "") + "curriculum: " + (run.curriculum || "?") +
    "\ncommit: " + run.commit;
}

function bindSpecimen(which){
  const sel = $("sel"+which), age = $("age"+which);
  const run = S.runs[+sel.value];
  const st = {run: run, ckptIdx: run.ckpts.length-1};
  if(which === "A") S.A = st; else S.B = st;
  $("card"+which).textContent = idcard(run);
  age.max = run.ckpts.length-1;
  age.value = st.ckptIdx;
  ageLabel(which);
}

function ageLabel(which){
  const st = subj(which);
  const ck = st.run.ckpts[+$("age"+which).value];
  st.ckptIdx = +$("age"+which).value;
  $("age"+which+"lbl").textContent = "developmental age " +
    ck.replace("ckpt_","").replace(".pt","") + "%";
}

function ckptOf(st){ return st.run.ckpts[st.ckptIdx]; }

/* ---- behavior instruments ---------------------------------------------- */

function meterLine(label, p){
  const n = Math.round(p*20);
  return label.padEnd(9) + "█".repeat(n) + "░".repeat(20-n) +
    " " + (p*100).toFixed(1) + "%";
}

async function askSubject(st, mode, cfg){
  const body = {run: st.run.run, ckpt: ckptOf(st), data: S.data, mode: mode};
  if(cfg) body.cfg = cfg;
  return j("/api/query", {method:"POST",
    headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
}

function answerBlock(st, r){
  const rec = r.record, a = r.answer;
  return `<div class=half><div class=who>SUBJECT ${st===S.A?"A":"B"} &middot; age ${ckptOf(st).replace("ckpt_","").replace(".pt","")}%</div>
    <div class=meter>${meterLine("Option 1", a.p1)}</div>
    <div class=meter>${meterLine("Option 2", a.p2)}</div>
    <div class=reading>matches: ${r.follows}</div></div>`;
}

async function behave(mode){
  S.lastMode = mode;
  const rA = await askSubject(S.A, mode, S.cfg);
  S.cfg = rA.cfg;               // same scenario across modes and subjects
  let html = `<div class=trace><div class=cap>BEHAVIOR &middot; ${mode.toUpperCase()} &middot; forced-choice log-probability</div>
    <div class=scene>${rA.record.prompt}</div><div class=duo>`;
  html += answerBlock(S.A, rA);
  if(S.B){
    const rB = await askSubject(S.B, mode, S.cfg);
    html += answerBlock(S.B, rB);
  }
  html += `</div><div class=note-dim style="margin-top:8px">utility answer:
    Option ${rA.record.utility_answer ?? "—"} &middot; cue answer: Option
    ${rA.record.cue_answer ?? "—"} &middot; same scenario is reused across
    instruments until &#8635; new scenario</div></div>`;
  canvas(html);
}

/* ---- development -------------------------------------------------------- */

async function trajectory(){
  const subs = S.B ? [S.A, S.B] : [S.A];
  const series = await Promise.all(subs.map(st =>
    j("/api/series?run=" + encodeURIComponent(st.run.run))));
  let html = `<div class=trace><div class=cap>DEVELOPMENT &middot; STORED
    CHECKPOINT SCORES (conflict = utility-agreement)</div>`;
  const W=520, H=180, colors=["#1e4d38","#B4452A"];
  let svg = `<svg width=${W} height=${H} viewBox="0 0 ${W} ${H}">`;
  svg += `<line x1=30 y1=10 x2=30 y2=${H-25} stroke="#cfc9b6"></line>`;
  svg += `<line x1=30 y1=${H-25} x2=${W-10} y2=${H-25} stroke="#cfc9b6"></line>`;
  svg += `<text x=2 y=14>1.0</text><text x=2 y=${H-22}>0.0</text>`;
  let any = false;
  series.forEach((s, si) => {
    const pts = s.series.filter(r => "conflict" in r);
    if(!pts.length) return;
    any = true;
    const path = pts.map((r,i) =>
      (i?"L":"M") + (30 + (W-45)*r.pct/100) + " " +
      (10 + (H-35)*(1-r.conflict))).join(" ");
    svg += `<path d="${path}" fill=none stroke="${colors[si]}" stroke-width=1.6></path>`;
    pts.forEach(r => {
      svg += `<circle cx=${30 + (W-45)*r.pct/100} cy=${10 + (H-35)*(1-r.conflict)} r=2.5 fill="${colors[si]}"></circle>`;
    });
    svg += `<text x=${W-120} y=${20+si*13} fill="${colors[si]}">SUBJECT ${si?"B":"A"} conflict</text>`;
  });
  svg += "</svg>";
  html += any ? svg : `<div class=note-dim>no stored checkpoint scores for
    this specimen yet — the main batch writes them as it trains</div>`;
  html += `<div class=note-dim>points, not smoothed curves — the honest
    resolution of the stored record</div></div>`;
  canvas(html);
}

/* ---- representation ----------------------------------------------------- */

async function probes(){
  const st = S.A;
  let html = `<div class=trace><div class=cap>REPRESENTATION &middot;
    LINEAR PROBES (with control tasks) &middot; ${ckptOf(st)}</div>`;
  try{
    const sc = await j("/api/score?run=" + encodeURIComponent(st.run.run) +
                       "&ckpt=" + encodeURIComponent(ckptOf(st)));
    const pr = sc.probes;
    if(pr && Object.keys(pr).length){
      html += `<div class=reading>`;
      for(const [k,v] of Object.entries(pr)){
        html += k.padEnd(28) + " probe " + (v.probe_acc??"—") +
          "  control " + (v.control_acc??"—") +
          "  selectivity " + (v.selectivity??"—") + "\n";
      }
      html += `</div><div class=note-dim>decodable &ne; used — causal
        instruments decide that</div>`;
    } else {
      html += `<div class=note-dim>no probe records stored at this
        checkpoint. Probes run at ages 20/40/60/80/100% in the main batch;
        selectivity = probe − control (Hewitt-Liang).</div>`;
    }
  }catch(e){
    html += `<div class=note-dim>no stored score record at this
      checkpoint (${e.message})</div>`;
  }
  html += "</div>";
  canvas(html);
}

/* ---- pending instruments ------------------------------------------------ */

function causal(){
  canvas(`<div class=trace><div class=cap>CAUSAL &middot; PENDING</div>
    <div class=note-dim>Steering along probe directions exists in the REPL
    harness; patching and ablation arrive with Phase B. Per the trace
    ledger, causal instruments run only on candidate mechanisms that
    survive the cheaper levels — and every run writes an evidence record,
    with the predicted direction stated before the intervention.</div></div>`);
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

function formal(){
  canvas(`<div class=trace><div class=cap>FORMALIZATION &middot; EVIDENCE &amp; EXPORT</div>
    <div class=note-dim>Edges carry evidence vectors (behavioral,
    representational, developmental, causal, replication) — never one
    confidence number. Statuses are promoted by predicted-then-tested
    interventions only.</div>
    <div style="margin-top:12px">
      <button onclick="exportGraph()">export evidence graph (JSON)</button>
      <button disabled>generate candidate formal spec &middot; pending</button>
    </div></div>
    <div class=trace><div class=cap>THE TWO DIRECTIONS OF TRAVEL</div>
    <div class=duo>
      <div class=half><div class=who>IMPORT A BRAIN</div>
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
      <div class=half><div class=who>EMBODY THE GRAPH</div>
        <div class=note-dim>Given a computation we understand, can we build
        a physical substrate that executes it?</div>
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

window.dragon = k => { const el = $("dragon-"+k);
  el.style.display = el.style.display === "none" ? "block" : "none"; };

window.exportGraph = async () => {
  const ws = await j("/api/worldspec?data=" + encodeURIComponent(S.data));
  canvas(`<div class=trace><div class=cap>EVIDENCE GRAPH EXPORT &middot;
    G_authored (privileged: synthetic world)</div>
    <div class=reading style="white-space:pre-wrap;font-size:11.5px">${
    JSON.stringify(ws, null, 1).replace(/</g,"&lt;")}</div>
    <div class=note-dim>G_development and G_mechanism export here as their
    evidence records accumulate.</div></div>`);
};

/* ---- graphs drawer ------------------------------------------------------ */

async function showGraph(kind){
  if(kind !== "generating"){
    canvas(`<div class=trace><div class=cap>${kind.toUpperCase()} GRAPH &middot;
      PENDING</div><div class=note-dim>This graph populates as evidence
      records accumulate (${kind === "development"
        ? "paired-curriculum contrasts from the main batch"
        : kind === "mechanism"
        ? "probe, decomposition and intervention records"
        : "requires at least two graphs"}). It will not be drawn before
      the evidence exists.</div></div>`);
    return;
  }
  const ws = await j("/api/worldspec?data=" + encodeURIComponent(S.data));
  let html = `<div class=trace><div class=cap>GENERATING GRAPH &middot;
    G_authored &middot; KNOWN BECAUSE WE WROTE IT</div><div class=reading>`;
  for(const e of ws.edges || []){
    html += String(e.src).padEnd(16) + " → " +
      String(e.dst).padEnd(16) + "  [" + (e.type||"") + "]\n";
  }
  html += `</div><div class=note-dim>a privileged object that exists only
    because this world is synthetic — the calibration target for every
    inferred graph</div></div>`;
  canvas(html);
}

/* ---- evidence ledger ----------------------------------------------------- */

function renderEvidence(){
  $("evidence").innerHTML = EVIDENCE.map((e,i)=>{
    const mark = e.st === "y" ? "✓" : e.st === "o" ? "○" : "?";
    const cls = e.st === "y" ? "y" : "o";
    return `<div class=evrow data-ev=${i}><span class="st ${cls}">${mark}</span>
      ${e.label}<div class=evdetail id=evd${i} style="display:none">
      <b>supports:</b> ${e.sup}<br><b>does not establish:</b> ${e.not}<br>
      <b>next:</b> ${e.next}</div></div>`;
  }).join("");
  document.querySelectorAll(".evrow").forEach(r=>r.onclick=()=>{
    const d = $("evd"+r.dataset.ev);
    d.style.display = d.style.display === "none" ? "block" : "none";
  });
}

/* ---- boot ---------------------------------------------------------------- */

const INSTRUMENTS = {ordinary:()=>behave("id"), conflict:()=>behave("conflict"),
  nocue:()=>behave("nocue"), cueonly:()=>behave("cueonly"),
  trajectory, probes, causal, transplant, formal};

async function init(){
  const [runs, ds] = await Promise.all([j("/api/runs"), j("/api/datasets")]);
  S.runs = runs; S.data = ds[0].data;
  for(const which of ["A","B"]){
    const sel = $("sel"+which);
    sel.innerHTML = runs.map((r,i)=>
      `<option value=${i}>${r.run.replace("runs/","")} · ${r.curriculum||"?"}</option>`).join("");
    sel.onchange = ()=>bindSpecimen(which);
    $("age"+which).oninput = ()=>ageLabel(which);
  }
  bindSpecimen("A");
  $("addB").onclick = ()=>{
    $("specB").style.display = "block";
    $("addB").style.display = "none";
    bindSpecimen("B");
  };
  document.querySelectorAll("[data-inst]").forEach(b=>
    b.onclick = ()=>INSTRUMENTS[b.dataset.inst]());
  document.querySelectorAll("[data-graph]").forEach(b=>
    b.onclick = ()=>showGraph(b.dataset.graph));
  $("newscen").onclick = ()=>{ S.cfg = null;
    if(S.lastMode) behave(S.lastMode); };
  renderEvidence();
  arrival();
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
  $("arr-conflict").onclick = ()=>behave("conflict");
  $("arr-probes").onclick = probes;
}
init();
</script>
</body></html>
"""
