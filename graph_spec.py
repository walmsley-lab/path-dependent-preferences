"""Graph specifications for the node editor (docs/graph_grammar.md).

Builds the four graph objects as typed node/edge specs with STABLE
positions, and populates each edge's evidence vector from the stored
artifacts. Positions are authored here and never recomputed, so that
changing the developmental age changes node and edge STATE only — the
reader can distinguish "the model changed" from "the layout moved."

Visual grammar (frozen):
  shape  -> node semantics   (rect / rect-dashed / circle / hex / diamond
                              / port / double)
  style  -> epistemic status (dotted candidate, dashed represented,
                              solid causal, double replicated)
  label  -> relationship semantics (predicts / causes / precedes /
                              facilitates / implements / assigns)
  color  -> graph family, never truth
  layout -> graph type (hierarchical / clustered / temporal)

Every evidence-bearing edge carries provenance. An edge's status is
DERIVED from its evidence vector by explicit rules (see `promote`), never
asserted by hand.
"""

import json
from pathlib import Path

import generate_world as gw

RUNS = Path("runs")
BATCH = Path("batch_results/runs")

# --- status derivation ------------------------------------------------

ORDER = ["candidate", "represented", "causal", "replicated", "executable"]


def promote(ev):
    """Status from the evidence vector — explicit rules, no hand-waving.

    candidate    : asserted or observed association only
    represented  : information recoverable above a matched control
    causal       : a predicted-direction intervention moved behavior more
                   than its controls
    replicated   : the causal result held across independent seeds
    """
    if ev.get("replication", {}).get("n_seeds", 0) >= 3 and ev.get("causal"):
        return "replicated"
    if ev.get("causal", {}).get("supported"):
        return "causal"
    if ev.get("representational", {}).get("supported"):
        return "represented"
    return "candidate"


def _load(path):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None


def _series(run):
    d = {}
    base = BATCH / run if (BATCH / run).exists() else RUNS / run
    for p in sorted(base.glob("score_ckpt_*.json")):
        s = json.loads(p.read_text())["sets"]
        d[int(p.stem.split("_")[-1])] = {
            "conflict_utility": s["eval_conflict"]["acc_utility"],
            "conflict_cue": s["eval_conflict"]["acc_cue"],
            "id": s["eval_id"]["acc_utility"]}
    return d


# --- G_generator: hierarchical, privileged ----------------------------

def g_generator(level="L1"):
    nodes = [
        {"id": "agent", "label": "agent", "shape": "rect", "x": 90, "y": 60},
        {"id": "lambda", "label": "λ", "shape": "rect-dashed",
         "x": 90, "y": 160, "note": "latent; never stated in the text"},
        {"id": "payoffs", "label": "d_self[o], d_other[o]", "shape": "rect",
         "x": 90, "y": 250},
        {"id": "utility", "label": "utility[o]", "shape": "hex",
         "x": 300, "y": 200},
        {"id": "argmax", "label": "argmax", "shape": "diamond",
         "x": 470, "y": 200},
        {"id": "choice", "label": "choice", "shape": "rect",
         "x": 620, "y": 200},
        {"id": "scene", "label": "scene", "shape": "rect",
         "x": 300, "y": 330},
        {"id": "framing", "label": "framing_class[o]", "shape": "rect",
         "x": 620, "y": 330},
        {"id": "rendered", "label": "rendered_framing[o]", "shape": "rect",
         "x": 620, "y": 410},
    ]
    E = lambda s, d, rel, mech: {
        "src": s, "dst": d, "relation": rel, "status": "authored",
        "evidence": {"authored": {"supported": True, "mechanism": mech}},
        "provenance": "generate_world.build_world_spec — privileged"}
    edges = [
        E("agent", "lambda", "assigns", "per-seed assignment, sex-balanced"),
        E("lambda", "utility", "computes", "U = λ·d_self + (1−λ)·d_other"),
        E("payoffs", "utility", "computes", "same"),
        E("utility", "argmax", "compares", "both options enter"),
        E("argmax", "choice", "determines", "choice = argmax_o U[o]"),
        E("choice", "framing", "assigns",
          "THE PLANTED CORRELATION: the generator assigns the class "
          "FROM the choice"),
        E("framing", "rendered", "realizes", "uniform draw among four "
          "surface phrases"),
    ]
    if level in ("L1", "L2"):
        edges.append(E("scene", "framing", "conditions",
                       "polarity inverts in river scenes"))
    return {"kind": "generator", "layout": "hierarchical",
            "status": "PRIVILEGED GROUND TRUTH — synthetic world only",
            "nodes": nodes, "edges": edges}


# --- G_observational: what the corpus offers --------------------------

def g_observational(level="L1"):
    nodes = [
        {"id": "lambda_payoffs", "label": "λ + payoffs", "shape": "rect",
         "x": 90, "y": 90},
        {"id": "scene_wording", "label": "scene + wording", "shape": "rect",
         "x": 90, "y": 300},
        {"id": "u_pred", "label": "utility_prediction", "shape": "hex",
         "x": 330, "y": 90},
        {"id": "c_pred", "label": "cue_prediction", "shape": "hex",
         "x": 330, "y": 300},
        {"id": "choice", "label": "choice", "shape": "rect",
         "x": 570, "y": 195},
    ]
    prov = ("known from the generator and verified exhaustively on the "
            "corpus; in Act II this becomes INFERRED FROM CORPUS")
    edges = [
        {"src": "lambda_payoffs", "dst": "u_pred", "relation": "computes",
         "status": "authored", "evidence": {"authored": {"supported": True}},
         "provenance": prov},
        {"src": "scene_wording", "dst": "c_pred", "relation": "computes",
         "status": "authored", "evidence": {"authored": {"supported": True}},
         "provenance": prov},
        {"src": "u_pred", "dst": "choice", "relation": "predicts",
         "status": "candidate",
         "evidence": {"observational": {"supported": True,
                                        "note": "perfect on train"}},
         "provenance": prov},
        {"src": "c_pred", "dst": "choice", "relation": "predicts",
         "status": "candidate",
         "evidence": {"observational": {"supported": True,
                                        "note": "perfect on train"}},
         "provenance": prov},
    ]
    return {"kind": "observational", "layout": "clustered",
            "status": "OBSERVATIONAL STRUCTURE PRESENT IN CORPUS",
            "constraint": "utility_prediction(x) = cue_prediction(x) = "
                          "choice(x) for every training example",
            "nodes": nodes, "edges": edges}


# --- G_development: temporal ------------------------------------------

def g_development():
    """Relations among ACQUIRED STATES. Schedules are not nodes here.

    The earlier version of this graph had "early phase composition" and
    "shared tail" as nodes pointing at "acquisition", which was a
    category error: those are curriculum-control parameters, and an edge
    from a training phase to acquisition is close to tautological —
    of course the early phase precedes what is acquired later. Saying so
    tells us nothing about what depended on what.

    A developmental node is a state the model came to be in. A
    developmental edge is a claim that acquiring the source changes the
    acquisition of the target, and it is earned only by forking matched
    learners and measuring the difference. The exposure schedule belongs
    to `control_layer` below, which the UI renders as a synchronised
    timeline rather than as graph nodes.

    THREE THINGS THAT ARE NOT THE SAME, tracked per node:
      available_at  when the corpus first supplies evidence for it
      acquired_at   when behaviour or probes show it emerged
      depends_on    whether an intervention showed the dependency

    Phase A honestly supports the first two and almost none of the third.
    Its world has too few independent concepts to yield a dependency
    graph, which is the reason Milestone B exists. Leaving these edges
    unearned is the accurate report, not a gap to fill in.
    """
    spec = _load("graphs/g_development.json") or {"edges": []}

    nodes = [
        {"id": "utility", "label": "utility competence", "shape": "circle",
         "x": 110, "y": 90,
         "available_at": 0.0, "acquired_at": 0.45,
         "note": "utility-route accuracy reaches criterion in 15/15 runs"},
        {"id": "cue", "label": "cue competence", "shape": "circle",
         "x": 110, "y": 300,
         "available_at": 0.0, "acquired_at": 0.30,
         "note": "cue-route accuracy; the planted shortcut is available "
                 "from the first exposure"},
        {"id": "preference", "label": "route preference", "shape": "circle",
         "x": 380, "y": 195,
         "available_at": None, "acquired_at": 0.55,
         "note": "which route governs under conflict"},
        {"id": "stability", "label": "route stability", "shape": "circle",
         "x": 640, "y": 195,
         "available_at": None, "acquired_at": None,
         "note": "whether the preference holds once competence plateaus"},
    ]

    # Candidate edges only. Each names the fork that would earn it.
    edges = [
        {"src": "utility", "dst": "preference",
         "relation": "facilitates (candidate)", "status": "candidate",
         "evidence": {"observational": {
             "supported": True,
             "note": "utility competence reaches criterion before a stable "
                     "preference appears in 15/15 runs — temporal "
                     "precedence only; composition was never manipulated"}},
         "next_test": "checkpoint fork at 40%: continue matched copies "
                      "with and without further utility exposure, holding "
                      "total exposure constant, and compare exposures to "
                      "preference criterion",
         "provenance": "batch_results/runs/* · commit 8de3c010"},
        {"src": "cue", "dst": "preference",
         "relation": "competes with (candidate)", "status": "candidate",
         "evidence": {"observational": {
             "supported": True,
             "note": "cue competence emerges earlier than utility "
                     "competence; whether it delays or biases preference "
                     "is untested"}},
         "next_test": "checkpoint fork at 40% with cue_mode off in one "
                      "arm; if the cue was carrying preference, "
                      "competence collapses in that arm",
         "provenance": "batch_results/runs/* · commit 8de3c010"},
        {"src": "preference", "dst": "stability",
         "relation": "modulates (candidate)", "status": "candidate",
         "evidence": {"observational": {
             "supported": True,
             "note": "3/15 runs show a competence-preserving decline after "
                     "commitment (C1 2/5, C2 0/5, C3 1/5); explicitly "
                     "underpowered and never manipulated"},
             "replication": {"n_seeds": 0,
                             "note": "no interventional replication"}},
         "next_test": "checkpoint fork after commitment: vary spaced "
                      "retrieval of the utility route while holding total "
                      "exposure constant",
         "provenance": "batch_results/runs/* · commit 8de3c010"},
    ]
    for e in spec.get("edges", []):          # earned edges, when they exist
        if e.get("src") in {n["id"] for n in nodes}:
            edges.append(e)

    return {
        "kind": "development", "layout": "temporal",
        "status": "CANDIDATE STRUCTURE — no developmental dependency has "
                  "been established. Every edge here is temporal "
                  "precedence awaiting a fork experiment.",
        "nodes": nodes, "edges": edges,
        # The schedule. Rendered as a timeline band, never as nodes: it is
        # what we manipulate, not what the model acquired.
        "control_layer": {
            "label": "TRAINING EXPERIENCE (manipulated, not acquired)",
            "phases": [
                {"id": "structure", "label": "structure exposure",
                 "start": 0.0, "end": 0.35},
                {"id": "choice", "label": "choice exposure",
                 "start": 0.35, "end": 0.70},
                {"id": "cue", "label": "cue exposure",
                 "start": 0.0, "end": 0.70},
                {"id": "tail", "label": "shared tail",
                 "start": 0.70, "end": 1.0},
            ]},
    }


# --- G_mechanism: hierarchical, evidence-driven, age-aware ------------

def g_mechanism(run="C2_L1_s0", age=100):
    """Edges carry real evidence vectors; the representational term is
    read at the requested developmental age from the atlas tensor."""
    atlas = _load(RUNS / run / "atlas.json")
    gen = _load(RUNS / run / "evidence_probe_generalization.json")
    steer = _load(RUNS / run / "evidence_steering.json")
    abl = _load(RUNS / run / "evidence_ablation.json")
    patch = _load(RUNS / run / "evidence_patching.json")
    series = _series(run)
    age_key = f"{int(age):03d}"

    def best_probe(target):
        if not atlas:
            return None
        best = None
        for L in atlas["layers"]:
            c = atlas["cells"].get(f"{age_key}/{L}/agent/{target}")
            if c and (best is None or c["sel"] > best["sel"]):
                best = {"layer": L, **c}
        return best

    lam = best_probe("lambda_class")
    cue = best_probe("verb_class_1")
    beh = series.get(int(age), {})

    nodes = [
        {"id": "agent_tok", "label": "agent token", "shape": "port",
         "x": 80, "y": 80},
        {"id": "text", "label": "scene + wording tokens", "shape": "port",
         "x": 80, "y": 320},
        {"id": "lam_state", "label": "λ-associated state",
         "shape": "circle", "x": 320, "y": 80,
         "note": "named neutrally: a direction whose recoverability "
                 "tracks the authored class"},
        {"id": "cue_state", "label": "cue-associated state",
         "shape": "circle", "x": 320, "y": 320},
        {"id": "comparison", "label": "candidate comparison",
         "shape": "hex", "x": 560, "y": 200,
         "note": "hypothesized; not yet traced"},
        {"id": "choice", "label": "choice", "shape": "rect",
         "x": 780, "y": 200},
    ]

    def sel_ev(p, label):
        if not p:
            return {"supported": False,
                    "note": f"no {label} probe record at this age"}
        return {"supported": p["sel"] >= 0.25,
                "value": p["sel"], "where": f"{p['layer']} / agent state",
                "note": f"selectivity {p['sel']:.2f} at {p['layer']} "
                        f"(probe {p['acc']:.2f}); read at age {int(age)}%. "
                        "Recoverability by this probe, not use."}

    gen_best = None
    if gen:
        gen_best = max((v["heldout_agent_selectivity"]
                        for row in gen["layers"].values()
                        for k, v in row.items() if "lambda" in k),
                       default=None)

    steer_ok = abl_ok = None
    if steer:
        d = steer["dose_response_spread"]
        steer_ok = d["candidate"] > 2 * max(d["control_layer"],
                                            d["random_direction"])
    if abl:
        d = abl["utility_agreement_drop"]
        abl_ok = d["candidate_lambda"] > 2 * max(d["random_direction"], 0.02)
        abl_selective = d["candidate_lambda"] > 2 * max(
            d["random_direction"], d["control_layer_lambda"])

    edges = [
        {"src": "agent_tok", "dst": "lam_state", "relation": "represented in",
         "evidence": {
             "representational": sel_ev(lam, "λ"),
             "generalization": ({"supported": gen_best is not None
                                 and gen_best >= 0.25,
                                 "value": gen_best,
                                 "note": "held-out-agent probe: the class "
                                         "is recoverable from agents the "
                                         "probe never saw"}
                                if gen_best is not None else
                                {"supported": False,
                                 "note": "identity confound untested"})},
         "provenance": f"{run} · atlas age {int(age)}% · "
                       f"evidence_probe_generalization.json",
         "next_test": "vary the split; measure partition variance"},
        {"src": "lam_state", "dst": "comparison", "relation": "feeds",
         "evidence": {"observational": {
             "supported": False,
             "note": "hypothesized route; the execution trace has not "
                     "isolated a comparison stage"}},
         "provenance": f"{run} · evidence_trace.json",
         "next_test": "targeted attribution at the implicated window"},
        {"src": "comparison", "dst": "choice", "relation": "determines",
         "evidence": {"observational": {
             "supported": False, "note": "hypothesized"}},
         "provenance": "—",
         "next_test": "trace, then intervene on the traced stage"},
        {"src": "lam_state", "dst": "choice", "relation": "influences",
         "evidence": {
             "behavioral": ({"supported": True,
                             "value": beh.get("conflict_utility"),
                             "note": f"conflict agreement with the utility "
                                     f"rule {beh.get('conflict_utility')} "
                                     f"at age {int(age)}%"}
                            if beh else {"supported": False,
                                         "note": "no stored score"}),
             "causal": ({"supported": bool(steer_ok),
                         "value": steer["dose_response_spread"]["candidate"],
                         "note": "predicted-direction steering exceeded "
                                 "both controls" if steer_ok else
                                 "steering did not exceed controls"}
                        if steer else {"supported": False,
                                       "note": "no intervention record"}),
             "necessity": ({"supported": bool(abl_ok),
                            "value": abl["utility_agreement_drop"]["candidate_lambda"],
                            "note": ("partial dependence; NOT uniquely "
                                     "localized (control layer ablates as "
                                     "strongly)" if not abl_selective else
                                     "selective at the candidate layer")}
                           if abl else {"supported": False,
                                        "note": "no ablation record"}),
             "portability": ({"supported": False,
                              "note": "cross-run patching did not transfer "
                                      "behavior toward the donor on "
                                      "disputed items (audited)"}
                             if patch else {"supported": False,
                                            "note": "untested"}),
             "replication": {"n_seeds": 1,
                             "note": "single seed; batch replication pending"}},
         "provenance": f"{run} · evidence_steering.json · "
                       f"evidence_ablation.json · evidence_patching.json",
         "next_test": "replicate steering across the batch seeds"},
        {"src": "text", "dst": "cue_state", "relation": "represented in",
         "evidence": {"representational": sel_ev(cue, "cue")},
         "provenance": f"{run} · atlas age {int(age)}%",
         "next_test": "held-out-scene probe"},
        {"src": "cue_state", "dst": "choice", "relation": "influences",
         "evidence": {
             "behavioral": ({"supported": beh.get("conflict_cue", 0) > 0.5,
                             "value": beh.get("conflict_cue"),
                             "note": f"conflict agreement with the wording "
                                     f"rule {beh.get('conflict_cue')} at "
                                     f"age {int(age)}%"}
                            if beh else {"supported": False,
                                         "note": "no stored score"}),
             "causal": {"supported": False,
                        "note": "no intervention on the cue direction yet"}},
         "provenance": f"{run} · score_ckpt_{age_key}.json",
         "next_test": "steer the cue direction with matched controls"},
    ]
    for e in edges:
        e["status"] = promote(e["evidence"])
    return {"kind": "mechanism", "layout": "hierarchical",
            "status": f"EXPERIMENTALLY INFERRED — {run} at age {int(age)}%",
            "run": run, "age": int(age), "nodes": nodes, "edges": edges}


# --- experimental frontier --------------------------------------------

def frontier(graphs):
    """Rank unresolved edges by information value.

    value ∝ uncertainty × downstream impact ÷ estimated cost.
    Uncertainty is highest for edges with some support but no causal
    test; impact counts downstream dependents; cost is a coarse tier.
    """
    items = []
    for g in graphs:
        deps = {}
        for e in g["edges"]:
            deps[e["src"]] = deps.get(e["src"], 0) + 1
        for e in g["edges"]:
            if e["status"] in ("authored", "replicated"):
                continue
            ev = e["evidence"]
            has_repr = ev.get("representational", {}).get("supported")
            has_causal = ev.get("causal", {}).get("supported")
            uncertainty = 0.9 if (has_repr and not has_causal) else (
                0.6 if not has_repr and not has_causal else 0.3)
            impact = 1 + deps.get(e["dst"], 0)
            cost = 3.0 if "replicate" in (e.get("next_test") or "") else 1.0
            items.append({
                "graph": g["kind"], "edge": f"{e['src']} → {e['dst']}",
                "status": e["status"],
                "next_test": e.get("next_test") or "—",
                "value": round(uncertainty * impact / cost, 3)})
    return sorted(items, key=lambda d: -d["value"])


def build(kind, run="C2_L1_s0", age=100, level="L1"):
    if kind == "generator":
        return g_generator(level)
    if kind == "observational":
        return g_observational(level)
    if kind == "development":
        return g_development()
    if kind == "mechanism":
        return g_mechanism(run, age)
    raise ValueError(kind)
