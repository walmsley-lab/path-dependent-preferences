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
.ages{display:flex;flex-wrap:wrap;gap:3px}
.ages button{padding:2px 7px;font:11px ui-monospace,Menlo,monospace}
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
.mtx{border-collapse:collapse;font:12.5px ui-monospace,Menlo,monospace;
  margin:8px 0}
.mtx th,.mtx td{border:1px solid var(--rule);padding:4px 10px;
  text-align:center}
.mtx th{font-weight:normal;color:var(--faded);font-size:11px}
.mtx td.name{text-align:left;cursor:pointer;color:var(--green)}
.mtx td.name:hover{text-decoration:underline}
.mtx td.hot{background:#e7efe4;font-weight:bold}
.scroller{overflow-x:auto}
.cform{display:grid;
  grid-template-columns:max-content minmax(110px,160px) max-content minmax(110px,160px);
  gap:10px 14px;align-items:center;margin:12px 0;max-width:560px}
.cform label{font-size:10px;letter-spacing:.15em;color:var(--faded);
  text-align:right}
.cform select,.mtx select{font:12px ui-monospace,Menlo,monospace;
  padding:4px 6px;border:1px solid var(--rule);border-radius:2px;
  background:#fff;width:100%}
.mtx select{width:90px}
textarea{width:100%;font:13px ui-monospace,Menlo,monospace;
  border:1px solid var(--rule);border-radius:3px;padding:8px;
  background:#fff;color:var(--ink)}

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
    <div class=age><div class=ages id=ageA></div>
      <div class=lbl id=ageAlbl></div></div>
  </div>
  <div class=specimen id=specB style="display:none">
    <div class=who>SUBJECT B</div>
    <select id=selB></select>
    <div class=idcard id=cardB></div>
    <div class=age><div class=ages id=ageB></div>
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
    <button data-inst=custom>&#9998; compose a scenario</button>
    <button data-inst=freeform>&#9000; freeform prompt</button>
    <div class=grp>CORPUS</div>
    <button data-inst=corpus>&#128214; read the corpus</button>
    <div class=grp>DEVELOPMENT</div>
    <button data-inst=trajectory>checkpoint trajectories</button>
    <div class=grp>REPRESENTATION</div>
    <button data-inst=probes>&lambda; / cue probes</button>
    <div class=grp>CAUSAL</div>
    <button data-inst=causal class=pending>steer &middot; patch &middot; ablate</button>
    <button data-inst=transplant class=pending>developmental transplant</button>
    <div class=grp>FORMALIZATION</div>
    <button data-inst=formal>derive candidate graph</button>
  </div>
</aside>

<main class=canvas id=canvas>
  <div id=canvas-empty>Choose a specimen and an instrument.</div>
</main>

<aside class=drawer>
  <h3 class=zone>MODELS OF THE WORLD</h3>
  <div class=note-dim style="font-size:10.5px;margin-bottom:4px">
    how the world was generated &rarr; what the corpus offers &rarr;
    what developed &rarr; what the network computes. Their disagreements
    are the point.</div>
  <div>
    <button class=tabbtn data-graph=generating>Generator</button>
    <button class=tabbtn data-graph=observational>Observational</button>
    <button class="tabbtn pending" data-graph=development>Development</button>
    <button class="tabbtn pending" data-graph=mechanism>Mechanism</button>
    <button class="tabbtn pending" data-graph=overlay>Overlay</button>
  </div>
  <hr class=g>
  <h3 class=zone>EVIDENCE</h3>
  <div class=note-dim style="font-size:10.5px;margin-bottom:4px">
    Experiments don&rsquo;t unlock chapters. Evidence unlocks claims.</div>
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
  {k:"mech", label:"Mechanism abstraction", st:"o",
   sup:"no candidate abstraction yet.",
   not:"— untested.",
   next:"derive candidate graph; test every edge causally."},
  {k:"repl", label:"Replicated mechanism", st:"o",
   sup:"requires the full seed battery.",
   not:"— untested.",
   next:"the 15-organism batch, scored and compared."},
  {k:"exec", label:"Executable formalization", st:"o",
   sup:"requires a causally supported abstraction first.",
   not:"— untested.",
   next:"executable surrogate + equivalence testing over the diagnostic domain."},
];

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
  return run.arch + "\n" + (run.n_params ? (run.n_params/1e6).toFixed(1) +
    "M parameters\n" : "") + "curriculum: " + (run.curriculum || "?") +
    "\ncommit: " + run.commit;
}

function bindSpecimen(which){
  const sel = $("sel"+which);
  const run = S.runs[+sel.value];
  const st = {run: run, ckptIdx: run.ckpts.length-1,
              data: datasetFor(run)};
  if(which === "A") S.A = st; else S.B = st;
  $("card"+which).textContent = idcard(run);
  renderAges(which);
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
  });
  $("age"+which+"lbl").textContent = "developmental age " +
    st.run.ckpts[st.ckptIdx].replace("ckpt_","").replace(".pt","") +
    "% · " + st.run.ckpts.length + " preserved snapshots on this bench " +
    "(a full organism preserves 21)";
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
    <div class=scene>${rA.record.prompt}</div><div class=duo>`;
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
    <div class=scroller><table class=mtx>
      <tr><th></th><th>AGENT&rsquo;S PAYOFF</th><th>PARTNER&rsquo;S PAYOFF</th></tr>
      <tr><td class=name style="cursor:default">option 1</td>
        <td><select id=c1s>${dsel(3)}</select></td>
        <td><select id=c1o>${dsel(-2)}</select></td></tr>
      <tr><td class=name style="cursor:default">option 2</td>
        <td><select id=c2s>${dsel(-2)}</select></td>
        <td><select id=c2o>${dsel(3)}</select></td></tr>
    </table></div>
    <div class=cform style="grid-template-columns:max-content 1fr;max-width:560px">
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
    <div class=note-dim>Off the diagnostic map — no authored answer exists
    for arbitrary text; this is exploration, not evidence. The world&rsquo;s
    vocabulary is closed: words the organism has never seen are refused,
    never silently mangled. Edit the template or write your own.</div>
    <textarea id=fftext rows=4>${tmpl}</textarea>
    <div style="margin:8px 0;font-size:12px">
      <label><input type=radio name=ffm value=continue checked>
        continue the text (greedy generation)</label>
      <label style="margin-left:12px"><input type=radio name=ffm value=choice>
        score as a choice (Option 1 vs 2)</label>
    </div>
    <button class=primary id=ffrun>Run against ${chip(S.A)} &rarr;</button>
    <div id=ffout style="margin-top:10px"></div></div>`);
  $("ffrun").onclick = runFreeform;
}

async function runFreeform(){
  const mode = document.querySelector("input[name=ffm]:checked").value;
  $("ffout").innerHTML = "<div class=note-dim>live inference — the model " +
    "is reading your words now…</div>";
  const r = await j("/api/freeform", {method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({run:S.A.run.run, ckpt:ckptOf(S.A),
      prompt: $("fftext").value, mode: mode})});
  if(r.oov){
    $("ffout").innerHTML = `<div class=note-dim style="color:var(--orange)">
      These words do not exist in this organism&rsquo;s world — it cannot
      read them:</div>
      <div class=reading style="color:var(--orange)">${r.oov.join("  ")}</div>
      <div class=note-dim>replace them with words from the world (the
      compose instrument lists the full vocabulary by category)</div>`;
    return;
  }
  if(mode === "choice"){
    const a = r.answer;
    $("ffout").innerHTML =
      "<div class=meter>" + meterLine("Option 1", a.p1) + "</div>" +
      "<div class=meter>" + meterLine("Option 2", a.p2) + "</div>" +
      `<div class=note-dim>forced-choice log-probability of the two answer
       tokens after your text — meaningful only if your text poses the
       world&rsquo;s kind of question</div>`;
  } else {
    $("ffout").innerHTML =
      `<div class=scene>&hellip;${r.continuation}</div>
       <div class=note-dim>${r.n_tokens} tokens · ${r.decoding} — this is
       what the organism expects the world to say next</div>`;
  }
}

/* ---- corpus reader ------------------------------------------------------ */

function segBars(segments){
  const colors = {W:"#1D6A96", P:"#B4452A", mixed:"#7A5FA8",
                  tail:"#8a8574"};
  let html = "";
  for(const [cur, segs] of Object.entries(segments || {})){
    const total = segs.reduce((a,s)=>a+s[1], 0);
    html += `<div style="display:flex;align-items:center;gap:8px;margin:3px 0">
      <span class=reading style="width:26px">${cur}</span>
      <div style="flex:1;display:flex;height:14px;border:1px solid var(--rule);border-radius:2px;overflow:hidden">` +
      segs.map(([name,count])=>`<div title="${name}: ${count.toLocaleString()} lines"
        style="width:${100*count/total}%;background:${colors[name]||"#ccc"}"></div>`).join("") +
      `</div></div>`;
  }
  return html + `<div class=note-dim style="font-size:11px">
    <span style="color:#1D6A96">■</span> W structure &nbsp;
    <span style="color:#B4452A">■</span> P choices &nbsp;
    <span style="color:#7A5FA8">■</span> interleaved &nbsp;
    <span style="color:#8a8574">■</span> shared tail — same deck,
    different deal</div>`;
}

async function corpus(slice){
  const st = S.A;
  const [meta, lines] = await Promise.all([
    j("/api/corpus?data=" + encodeURIComponent(st.data)),
    j("/api/corpus_lines?data=" + encodeURIComponent(st.data) +
      (slice ? "&slice=" + encodeURIComponent(slice) : ""))]);
  const counts = meta.generation_stats || {};
  let html = `<div class=trace><div class=cap>THE SYNTHETIC CORPUS &middot;
    ${st.data} &middot; level ${meta.level} &middot; seed ${meta.seed}</div>
    <div class=note-dim>${Object.keys(meta.agents).length} agents with
    authored preferences · every line rendered by the generator from the
    world spec · three curricula are permutations of ONE line multiset</div>
    <div style="margin:10px 0">${segBars(S.segments)}</div>`;
  if(!lines.slices.length){
    html += `<div class=note-dim>no corpus slices fetched to this bench —
      the full corpus lives with the training runs; slices land under
      ${st.data}/slices/</div></div>`;
    canvas(html); return;
  }
  const label = s => s.replace("_head", " · first pages")
    .replace("_tail", " · shared tail").replace("_sample", " · mid-corpus");
  html += `<div style="margin:6px 0">` + lines.slices.map(s =>
    `<button style="padding:3px 9px;font-size:11px" class="${s===lines.slice?"primary":""}"
      onclick="corpus('${s}')">${label(s)}</button>`).join(" ") + `</div>`;
  if(lines.lines){
    html += `<div class=note-dim>actual training lines, in the exact order
      this curriculum presented them — a first-pages slice is literally
      the organism&rsquo;s earliest experience</div>
      <div style="margin-top:8px;max-height:420px;overflow-y:auto">` +
      lines.lines.map(l =>
        `<div style="display:flex;gap:8px;padding:3px 0;border-top:1px solid var(--rule)">
          <span class=reading style="color:${l.type==="P"?"#B4452A":"#1D6A96"};width:14px">${l.type}</span>
          <span style="font-size:13px;font-family:Georgia,serif">${l.text}</span></div>`).join("") +
      `</div>`;
  } else {
    html += `<div class=note-dim>choose a slice to read</div>`;
  }
  html += "</div>";
  canvas(html);
}
window.corpus = corpus;

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
    svg += `<text x=${W-190} y=${20+si*13} fill="${colors[si]}">${chip(subs[si])} · conflict</text>`;
  });
  svg += "</svg>";
  html += any ? svg : `<div class=note-dim>no stored checkpoint scores for
    this specimen yet — the main batch writes them as it trains</div>`;
  html += `<div class=note-dim>points, not smoothed curves — the honest
    resolution of the stored record</div></div>`;
  canvas(html);
}

/* ---- representation ----------------------------------------------------- */

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
    html += `</table></div>
    <div class=note-dim>selectivity = probe performance &minus; matched
      control (Hewitt-Liang). Click a representation for its developmental
      emergence.</div>
    <div class=note-dim style="margin-top:6px"><b>Established:</b>
      information above the matched control is decodable where the cells
      are large. <b>Not established:</b> that the organism <em>uses</em>
      it to choose — that is the locked causal instrument&rsquo;s
      question.</div>`;
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

async function formal(){
  // derive candidate edges from STORED evidence only (artifact consumer:
  // no model invocation here) — every element says why it exists
  const st = S.A;
  let probeRow = null, conf = null;
  try{
    const sc = await j("/api/score?run=" + encodeURIComponent(st.run.run) +
                       "&ckpt=" + encodeURIComponent(ckptOf(st)));
    conf = (sc.sets || {}).eval_conflict || null;
    const pr = sc.probes || {};
    let best = null;
    for(const [k,v] of Object.entries(pr)){
      if(k.endsWith("lambda_class") &&
         (!best || v.selectivity > best.sel))
        best = {loc: k, sel: v.selectivity, acc: v.probe_acc};
    }
    probeRow = best;
  }catch(e){}
  // visual grammar (design law): association ⇢ dotted · represented
  // candidate ⇠dashed⇢ · causally supported → solid · replicated ⇒ ·
  // executable: categorically different. The arrow hardens as evidence
  // accumulates; nothing here has earned a solid arrow yet.
  const prov = "↳ " + (st.run.run_id || st.run.run) + " · " + ckptOf(st) +
    " · " + st.data + " · commit " + st.run.commit;
  const edge = (from,to,arrow,lines,status) => `<div class=half>
    <div class=who>${from} ${arrow} ${to}</div>
    <div class=reading style="white-space:pre-wrap;font-size:12px">${lines.join("\n")}</div>
    <div class=note-dim style="margin-top:6px">STATUS: ${status}</div>
    <details style="margin-top:4px"><summary style="font-size:11px;
      color:var(--inst);cursor:pointer">why do you believe this?</summary>
      <div class=note-dim style="font-size:11px">${prov}</div></details></div>`;
  let html = `<div class=trace><div class=cap>CANDIDATE FORMALIZATION &middot;
    DERIVED FROM STORED EVIDENCE &middot; ${chip(st)}</div>
    <div class=note-dim>Edges carry evidence vectors, never one confidence
    number. Statuses are promoted only by predicted-then-tested
    interventions.</div><div class=duo style="margin-top:10px">`;
  html += edge("hidden preference (λ)", "choice (candidate)", "⇢", [
    conf ? "behavioral   conflict agreement " + conf.acc_utility : "behavioral   no stored conflict scores",
    probeRow ? "represented  probe selectivity " + probeRow.sel + " @ " + probeRow.loc : "represented  no stored probe records",
    "causal       pending (steer / patch)",
    "development  pending (batch trajectories)",
  ], probeRow ? "REPRESENTED — not causally established" : "ASSOCIATED");
  html += edge("wording &amp; place", "choice (candidate)", "⇢", [
    conf ? "behavioral   conflict agreement " + conf.acc_cue : "behavioral   no stored conflict scores",
    "represented  cue probes stored where measured",
    "causal       pending",
    "development  pending",
  ], "ASSOCIATED — behaviorally dominated in this specimen");
  html += `</div>
    <div style="margin-top:12px">
      <button onclick="exportGraph()">export evidence graph (JSON)</button>
      <button disabled>generate candidate formal spec &middot; pending</button>
    </div></div>
    <div class=trace><div class=cap>THREE LOCKED DOORS</div>
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
    </div></div>`;
  canvas(html);
}

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

async function showGraph(kind){
  if(kind === "development" || kind === "mechanism" || kind === "overlay"){
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
  const ws = await j("/api/worldspec?data=" + encodeURIComponent(S.A.data));
  const g = kind === "observational" ? ws.graphs.observational
                                     : ws.graphs.generator;
  const cap = kind === "observational"
    ? "G_observational &middot; DERIVED FROM CORPUS"
    : "G_generator &middot; PRIVILEGED GROUND TRUTH — SYNTHETIC WORLD ONLY";
  let html = `<div class=trace><div class=cap>${cap}</div><div class=reading>`;
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
  custom:compose, freeform, corpus:()=>corpus(), trajectory,
  probes:()=>probes(), causal, transplant, formal};

async function init(){
  const [runs, ds] = await Promise.all([j("/api/runs"), j("/api/datasets")]);
  S.runs = runs; S.datasets = ds; S.data = ds[0].data;
  for(const which of ["A","B"]){
    const sel = $("sel"+which);
    sel.innerHTML = runs.map((r,i)=>
      `<option value=${i}>${r.run.replace("runs/","")} · ${r.curriculum||"?"}</option>`).join("");
    sel.onchange = ()=>bindSpecimen(which);
  }
  bindSpecimen("A");
  try{
    S.segments = (await j("/api/curricula?data=" +
      encodeURIComponent(S.A.data))).segments;
  }catch(e){ S.segments = {}; }
  $("addB").onclick = ()=>{
    $("specB").style.display = "block";
    $("addB").style.display = "none";
    bindSpecimen("B");
  };
  document.querySelectorAll("[data-inst]").forEach(b=>
    b.onclick = ()=>INSTRUMENTS[b.dataset.inst]());
  document.querySelectorAll("[data-graph]").forEach(b=>
    b.onclick = ()=>showGraph(b.dataset.graph));
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
