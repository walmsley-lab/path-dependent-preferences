"""The graph editor (served at /lab/graph).

The four graph objects rendered under the frozen visual grammar, with a
developmental slider that changes node and edge STATE while positions
stay fixed, an Edge Laboratory that opens any edge's evidence vector and
next discriminating test, and the experimental frontier ranked by
information value.

Implementation note: plain SVG and vanilla JS, served by the stdlib API
like every other surface here. A component framework was considered and
rejected — the layout is authored rather than computed, there is one
page of state, and adding a build step would put a compilation artifact
between the reader and artifacts that are meant to be inspectable.
"""

LAB_GRAPH = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Path-Dependent Preferences — Graphs</title>
<style>
:root{
  --ivory:#f6f1e5; --card:#fdfaf2; --ink:#26241d; --faded:#6f6a5c;
  --green:#1e4d38; --rule:#cfc9b6; --graphite:#8a8574;
  --inst:#4a4f7a; --blue:#1D6A96; --orange:#B4452A; --violet:#7A5FA8;
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
.frame{display:flex;min-height:calc(100vh - 48px);flex-wrap:wrap}
.main{flex:1;min-width:420px;padding:16px 22px}
.side{width:330px;flex:none;border-left:1px solid var(--rule);
  padding:16px 16px}
h2{font-family:Georgia,serif;font-size:20px;color:var(--green);
  font-weight:normal}
h3{font-size:10px;letter-spacing:.22em;color:var(--inst);margin:0 0 8px}
.dim{color:var(--graphite);font-size:12px}
.reading{font-family:ui-monospace,Menlo,monospace}
button{font:12px system-ui,sans-serif;padding:5px 10px;cursor:pointer;
  background:none;color:var(--ink);border:1px solid var(--graphite);
  border-radius:2px}
button:hover{border-color:var(--green);color:var(--green)}
button.on{background:var(--green);color:var(--ivory);
  border-color:var(--green)}
.tabs{margin:6px 0 10px}
.tabs button{margin-right:4px}
#canvas{border:1px solid var(--rule);border-radius:3px;background:#fff}
.gnode text{font:11px system-ui,sans-serif;fill:var(--ink)}
.gnode .sub{font:9px ui-monospace,Menlo,monospace;fill:var(--graphite)}
.gedge{cursor:pointer}
.gedge:hover .hit{stroke:rgba(30,77,56,.10)}
.elabel{font:9px ui-monospace,Menlo,monospace;fill:var(--faded)}
.legend{font:10px ui-monospace,Menlo,monospace;color:var(--faded);
  margin-top:6px;line-height:1.9}
.legend .k{display:inline-block;margin-right:14px}
.age{margin:10px 0;padding:10px;border:1px solid var(--rule);
  border-radius:3px;background:var(--card)}
.age input{width:100%;accent-color:var(--green);height:26px}
.age .lbl{font:13px ui-monospace,Menlo,monospace;text-align:center}
.ev{border-top:1px solid var(--rule);padding:7px 0;font-size:12px}
.ev .k{font:10px ui-monospace,Menlo,monospace;letter-spacing:.1em;
  color:var(--inst)}
.ev .y{color:var(--green)} .ev .n{color:var(--orange)}
.frontier div.row{border-top:1px solid var(--rule);padding:6px 0;
  font-size:12px;cursor:pointer}
.frontier div.row:hover{background:var(--card)}
.val{font:10px ui-monospace,Menlo,monospace;color:var(--inst)}
</style></head><body>

<div class=topbar>
  <span class=wordmark>OPEN POLLINATION &mdash; RESEARCH ANNEX</span>
  <span><a class=toplink href="/">Expedition</a>
    <a class=toplink href="/lab">Evidence</a>
    <a class=toplink href="/lab/bench">Laboratory</a>
    <a class="toplink here" href="/lab/graph">Graphs</a></span>
</div>

<div class=frame>
<main class=main>
  <h2>Models of the world</h2>
  <div class=dim>how the world was generated &rarr; what the corpus
    offers &rarr; what developed &rarr; what the network computes.
    Shapes carry node semantics; line style carries epistemic status;
    positions are fixed so that changing the age changes state, not
    layout.</div>
  <div class=tabs id=tabs></div>
  <div id=graphwrap></div>
  <div class=legend>
    <span class=k>▭ observed</span><span class=k>▭┄ latent</span>
    <span class=k>◯ learned state</span><span class=k>⬡ computation</span>
    <span class=k>◇ comparison</span><span class=k>▪ interface</span><br>
    <span class=k>⋯⋯ candidate</span><span class=k>┅┅ represented</span>
    <span class=k>━━ causal</span><span class=k>══ replicated</span>
    <span class=k>▬▬ authored (privileged)</span>
  </div>
  <div class=age id=agebox style="display:none">
    <div class=dim>DEVELOPMENTAL AGE — every value on this page is
      re-read from stored artifacts at the selected checkpoint</div>
    <input type=range id=age min=0 max=100 step=5 value=100>
    <div class=lbl id=agelbl>100%</div>
  </div>
</main>

<aside class=side>
  <h3>EDGE LABORATORY</h3>
  <div id=edgelab class=dim>Select an edge to open its evidence.</div>
  <hr style="border:none;border-top:1px solid var(--rule);margin:14px 0">
  <h3>EXPERIMENTAL FRONTIER</h3>
  <div class=dim style="font-size:11px">unresolved edges ranked by
    uncertainty × downstream impact ÷ cost — what to spend the next
    experiment on</div>
  <div class=frontier id=frontier></div>
</aside>
</div>

<script>
"use strict";
const $ = id => document.getElementById(id);
const j = u => fetch(u).then(r=>{ if(!r.ok) throw new Error(u); return r.json(); });
const S = {kind:"mechanism", age:100, graph:null, sel:null};
window.GRAPHSTATE = S;
const KINDS = [["generator","Generator"],["observational","Observational"],
               ["development","Development"],["mechanism","Mechanism"]];
const FAM = {generator:"#1e4d38", observational:"#1D6A96",
             development:"#7A5FA8", mechanism:"#B4452A"};
const DASH = {candidate:"2 4", represented:"7 4", causal:"",
              replicated:"", authored:""};
const W = {candidate:1.2, represented:1.5, causal:2.0, replicated:2.6,
           authored:1.6};

function shape(n, color){
  const w = Math.max(96, n.label.length*6.4), h = 30;
  const x = n.x, y = n.y;
  const t = `<text x=${x+w/2} y=${y+h/2+4} text-anchor=middle>${
    n.label.replace(/</g,"&lt;")}</text>`;
  if(n.shape === "circle")
    return `<ellipse cx=${x+w/2} cy=${y+h/2} rx=${w/2} ry=${h/2+4}
      fill=#fff stroke="${color}" stroke-width=1.3></ellipse>${t}`;
  if(n.shape === "hex"){
    const k=10;
    return `<polygon points="${x+k},${y} ${x+w-k},${y} ${x+w},${y+h/2}
      ${x+w-k},${y+h} ${x+k},${y+h} ${x},${y+h/2}" fill=#fff
      stroke="${color}" stroke-width=1.3></polygon>${t}`;
  }
  if(n.shape === "diamond")
    return `<polygon points="${x+w/2},${y-6} ${x+w},${y+h/2}
      ${x+w/2},${y+h+6} ${x},${y+h/2}" fill=#fff stroke="${color}"
      stroke-width=1.3></polygon>${t}`;
  if(n.shape === "port")
    return `<rect x=${x} y=${y} width=${w} height=${h} fill=#fff
      stroke="${color}" stroke-width=1.3></rect>
      <rect x=${x-4} y=${y+h/2-4} width=8 height=8 fill="${color}"></rect>${t}`;
  const dash = n.shape === "rect-dashed" ? ' stroke-dasharray="4 3"' : "";
  return `<rect x=${x} y=${y} width=${w} height=${h} rx=6 fill=#fff
    stroke="${color}" stroke-width=1.3${dash}></rect>${t}`;
}

function anchor(n){
  const w = Math.max(96, n.label.length*6.4);
  return {l:[n.x, n.y+15], r:[n.x+w, n.y+15], w:w};
}

function render(){
  const g = S.graph, color = FAM[g.kind];
  const nodes = Object.fromEntries(g.nodes.map(n=>[n.id,n]));
  let maxX = 0, maxY = 0;
  g.nodes.forEach(n=>{ const a=anchor(n);
    maxX=Math.max(maxX,n.x+a.w+30); maxY=Math.max(maxY,n.y+70); });
  let svg = `<svg id=canvas width="100%" viewBox="0 0 ${maxX} ${maxY}"
    style="max-width:${maxX}px"><defs>`;
  for(const st of Object.keys(DASH))
    svg += `<marker id=a-${st} viewBox="0 0 10 10" refX=9 refY=5
      markerWidth=6 markerHeight=6 orient=auto>
      <path d="M0 0 L10 5 L0 10 z" fill="${color}"></path></marker>`;
  svg += `</defs>`;
  g.edges.forEach((e,i)=>{
    const A = nodes[e.src], B = nodes[e.dst];
    if(!A || !B) return;
    const a = anchor(A), b = anchor(B);
    const from = (B.x >= A.x) ? a.r : a.l;
    const to   = (B.x >= A.x) ? b.l : b.r;
    const mx = (from[0]+to[0])/2;
    const d = `M${from[0]} ${from[1]} C${mx} ${from[1]} ${mx} ${to[1]} ${to[0]} ${to[1]}`;
    const sel = S.sel === i;
    svg += `<g class=gedge onclick="pickEdge(${i})">
      <path class=hit d="${d}" fill=none stroke="${sel?
        'rgba(30,77,56,.16)':'transparent'}" stroke-width=12></path>
      <path d="${d}" fill=none stroke="${color}"
        stroke-width=${W[e.status]||1.2}
        stroke-dasharray="${DASH[e.status]||""}"
        marker-end="url(#a-${e.status})"></path>`;
    if(e.status === "replicated")
      svg += `<path d="${d}" fill=none stroke="${color}" stroke-width=.8
        transform="translate(0,3)"></path>`;
    svg += `<text class=elabel x=${mx} y=${(from[1]+to[1])/2 - 5}
      text-anchor=middle>${e.relation}</text></g>`;
  });
  g.nodes.forEach(n=>{ svg += `<g class=gnode>${shape(n,color)}</g>`; });
  svg += `</svg>`;
  $("graphwrap").innerHTML = svg +
    `<div class=dim style="margin-top:6px">${g.status}` +
    (g.constraint ? ` &middot; <span class=reading style="font-size:11px">${
      g.constraint}</span>` : "") + `</div>`;
}

function evRow(k, v){
  if(!v) return "";
  const mark = v.supported === true ? "✓" : v.supported === false ? "○" : "·";
  const cls = v.supported === true ? "y" : "n";
  const val = (v.value !== undefined && v.value !== null)
    ? ` <span class=reading>${(+v.value).toFixed(2)}</span>` : "";
  return `<div class=ev><span class="k ${cls}">${mark} ${k.toUpperCase()}</span>${val}
    <div class=dim>${v.note || ""}</div></div>`;
}

window.pickEdge = i => {
  S.sel = i; render();
  const e = S.graph.edges[i];
  const ev = e.evidence || {};
  let html = `<div class=reading style="font-size:13px">${e.src} → ${e.dst}</div>
    <div class=dim>claim: <b>${e.relation}</b> · status:
      <b>${e.status}</b></div>`;
  for(const k of ["authored","observational","behavioral","representational",
                  "generalization","causal","necessity","portability",
                  "replication"])
    html += evRow(k, ev[k]);
  if(e.next_test)
    html += `<div class=ev><span class=k>NEXT DISCRIMINATING TEST</span>
      <div class=dim>${e.next_test}</div>
      <button style="margin-top:6px" onclick="designExperiment(${i})">
        Design experiment &rarr;</button></div>`;
  if(e.provenance)
    html += `<div class=dim style="margin-top:8px;font-size:11px">
      &#8627; ${e.provenance}</div>`;
  $("edgelab").innerHTML = html;
};

window.designExperiment = i => {
  const e = S.graph.edges[i];
  $("edgelab").innerHTML += `<div class=ev>
    <span class=k>EXPERIMENT SPECIFICATION (DRAFT)</span>
    <div class=reading style="font-size:11px;white-space:pre-wrap">claim    ${e.src} ${e.relation} ${e.dst}
status   ${e.status}
test     ${e.next_test}
arms     matched controls required (layer / direction / donor)
gate     in-distribution competence preserved
output   typed evidence record with provenance</div>
    <div class=dim>Compiling this into runnable configuration is Act II
    work; the specification is written here so the claim, its test, and
    its controls travel together. No experiment launches from this
    page.</div></div>`;
};

async function load(){
  S.graph = await j(`/api/graphspec?kind=${S.kind}&age=${S.age}`);
  S.sel = null;
  render();
  $("edgelab").innerHTML = "<div class=dim>Select an edge to open its " +
    "evidence.</div>";
  $("agebox").style.display = (S.kind === "mechanism") ? "block" : "none";
  const f = await j("/api/frontier");
  $("frontier").innerHTML = f.slice(0,6).map(r =>
    `<div class=row><span class=val>${r.value}</span> ${r.edge}
      <div class=dim>${r.graph} · ${r.status} · ${r.next_test}</div></div>`)
    .join("");
  document.body.dataset.ready = "1";
}

function tabs(){
  $("tabs").innerHTML = KINDS.map(([k,l]) =>
    `<button class="${k===S.kind?"on":""}" data-kind=${k}>${l}</button>`)
    .join("");
  document.querySelectorAll("[data-kind]").forEach(b =>
    b.onclick = () => { S.kind = b.dataset.kind; tabs(); load(); });
}

$("age").oninput = () => {
  S.age = +$("age").value; $("agelbl").textContent = S.age + "%";
};
$("age").onchange = () => { if(S.kind === "mechanism") load(); };
tabs(); load();
</script>
</body></html>
"""
