"""Data generator for Path-Dependent Preferences (EXPERIMENT_PLAN.md sections 3-4).

World: named agents with a latent utility weight LAMBDA (weight on self-payoff).
P (choice) tasks admit two solutions that agree on all training data:
  Route A (utility):  U = lambda * d_self + (1 - lambda) * d_other, choose argmax.
  Route B (shortcut): pick the option whose framing-verb class matches the
                      agent's class, under the polarity rule of the cue level.
Cue levels:
  L0: chosen option's verb class always matches the agent's class.
  L1: match in "market" scenes, inverted in "river" scenes.
  L2: polarity = (scene == river) XOR (narrator == Rilo).
The cue is a socially meaningful correlated cue: trained from scratch, verb
semantics are defined entirely by their statistical role here, and verb class
is assigned by the cue rule while payoffs are sampled independently (audited
by test_verb_payoff_decorrelation).

Eval sets force the routes apart (conflict), remove the cue (no-cue), remove
the utility signal via exact ties (cue-only), or swap surface forms (surface).
Lambda-dependent sets reuse TRAINED agents in held-out surface contexts;
held-out names appear only in W-generalization evals (a never-seen agent has
no defined preference from the model's perspective). probe_test uses the
held-out template T2 so probe generalization requires surface transfer.
Every P record carries its probe labels; nothing is parsed from strings later.

Usage: python generate_world.py --level L0 --seed 0 --outdir data/L0
"""

import argparse
import json
import random
from pathlib import Path

# --- vocabulary -------------------------------------------------------------
# Common US names (SSA top rankings, 1980s-90s cohorts) per user preference.
# Models train from scratch, so names carry no pretrained associations here;
# sex is still counterbalanced across lambda classes so (a) readers can't
# project meaning onto the assignment and (b) the design ports unchanged to
# pretrained models, where name associations WOULD be a real confound.
# Agent lambda assignment is PER-SEED (sex-counterbalanced) so that any
# accidental corpus idiosyncrasy involving one name averages out across seeds
# instead of replicating: lambda must be independent of agent-identity quirks.
AGENT_NAMES = ["Michael", "Jessica", "David", "Amanda", "Tyler",
               "Ashley", "Christopher", "Sarah", "Matthew", "Nicole"]
NAME_SEX = {
    "Michael": "M", "David": "M", "Tyler": "M", "Christopher": "M", "Matthew": "M",
    "Jessica": "F", "Amanda": "F", "Ashley": "F", "Sarah": "F", "Nicole": "F",
}


def assign_lambdas(seed):
    """Deterministic per-seed name->lambda map; each class gets >=2 of each sex."""
    rng = random.Random(f"lambda-assign-{seed}")
    males = sorted(n for n in AGENT_NAMES if NAME_SEX[n] == "M")
    females = sorted(n for n in AGENT_NAMES if NAME_SEX[n] == "F")
    rng.shuffle(males)
    rng.shuffle(females)
    if seed % 2 == 0:
        coop = males[:2] + females[:3]
    else:
        coop = males[:3] + females[:2]
    return {n: (0.2 if n in coop else 0.8) for n in AGENT_NAMES}
PARTNERS = ["Kevin", "Rachel", "Brandon", "Megan",     # second agents, no lambda
            "Derek", "Amber", "Scott", "Crystal"]      # widened for v3 corpus scale
HELDOUT_NAMES = ["Joshua", "Brittany", "Eric", "Lauren"]  # W-generalization only
TRAIN_NOUNS = ["stones", "gems", "tokens", "shells"]
HELDOUT_NOUNS = ["lumens", "spools", "marbles"]        # probe + surface sets

COOP_VERBS = ["shares the pile", "offers a split", "divides the haul", "gives freely"]
SELF_VERBS = ["keeps the pile", "takes the lot", "grabs the haul", "hoards the stash"]
NEUT_VERBS = ["selects the red marker", "selects the blue marker",
              "follows plan A", "follows plan B"]
SCENES = ["market", "river"]
NARRATORS = ["Justin", "Heather"]
TEMPLATES = ["T1", "T2"]   # T2 is held out for probe_test only

LEVELS = ["L0", "L1", "L2"]
MIN_UTILITY_MARGIN = 2     # in 1/5-units; forbids near-ties (cue-only set aside)
DELTAS = [d for d in range(-5, 6) if d != 0]


def utility(lam, d_self, d_other):
    """Integer utility in 1/5-units: exact for lam in {0.2, 0.8}, no float ties."""
    w_self = round(lam * 5)
    return w_self * d_self + (5 - w_self) * d_other


def polarity(level, scene, narrator):
    """0 = chosen option's verb class matches agent class; 1 = inverted."""
    if level == "L0":
        return 0
    if level == "L1":
        return int(scene == "river")
    return int(scene == "river") ^ int(narrator == NARRATORS[1])


def cue_predict(level, lam, scene, narrator, verb_classes):
    """Route B's answer: 1-indexed option whose verb class the rule points at."""
    agent_class = "COOP" if lam < 0.5 else "SELF"
    if polarity(level, scene, narrator) == 1:
        agent_class = "SELF" if agent_class == "COOP" else "COOP"
    return verb_classes.index(agent_class) + 1


def utility_predict(lam, options):
    us = [utility(lam, ds, do) for ds, do in options]
    return 1 if us[0] > us[1] else 2


def tie_options(rng, lam):
    """Two options with EXACTLY equal utility (integer-exact for lam in {.2,.8}).

    lam=0.2: u1-u2 = 0.2*(s1-s2) + 0.8*(o1-o2) = 0 when opt2 = (s+4t, o-t).
    lam=0.8: symmetric with opt2 = (s+t, o-4t).
    """
    while True:
        s, o, t = rng.choice(DELTAS), rng.choice(DELTAS), rng.choice([-1, 1])
        opt2 = (s + 4 * t, o - t) if lam < 0.5 else (s + t, o - 4 * t)
        if all(v != 0 and abs(v) <= 5 for v in opt2):
            return [(s, o), opt2]


# --- P (choice) scenarios ---------------------------------------------------

def sample_p_config(rng, agent_map, noun_pool, template):
    """One choice scenario. Margin enforced (cue-only ties are built separately)."""
    agent = rng.choice(sorted(agent_map))
    lam = agent_map[agent]
    while True:
        options = [(rng.choice(DELTAS), rng.choice(DELTAS)) for _ in range(2)]
        us = [utility(lam, ds, do) for ds, do in options]
        if abs(us[0] - us[1]) >= MIN_UTILITY_MARGIN:
            break
    return {
        "agent": agent, "lam": lam, "partner": rng.choice(PARTNERS),
        "options": options,
        "scene": rng.choice(SCENES), "narrator": rng.choice(NARRATORS),
        "noun": rng.choice(noun_pool), "template": template,
        "coop_verb": rng.choice(COOP_VERBS), "self_verb": rng.choice(SELF_VERBS),
        "neut_verbs": rng.sample(NEUT_VERBS, 2),   # randomized position assignment
        "cue_target_override": rng.choice([1, 2]),  # used by cue-only mode
    }


def config_key(cfg):
    return (cfg["agent"], cfg["partner"], tuple(cfg["options"][0]),
            tuple(cfg["options"][1]), cfg["scene"], cfg["narrator"],
            cfg["noun"], cfg["template"])


def delta_str(d, noun):
    n = abs(d)
    unit = noun[:-1] if n == 1 else noun   # all nouns are regular plurals
    return f"gains {n} {unit}" if d > 0 else f"loses {n} {unit}"


def _render_body(cfg, level, verbs, noun):
    prefix = f"At the {cfg['scene']}, " if level in ("L1", "L2") else ""
    if level == "L2":
        prefix += f"{cfg['narrator']} reports: "
    a, b = cfg["agent"], cfg["partner"]
    o1, o2 = cfg["options"]
    if cfg["template"] == "T1":
        return " ".join([
            f"{prefix}{a} and {b} are dividing {noun}.",
            f"Option 1: {a} {verbs[0]}; {a} {delta_str(o1[0], noun)} and "
            f"{b} {delta_str(o1[1], noun)}.",
            f"Option 2: {a} {verbs[1]}; {a} {delta_str(o2[0], noun)} and "
            f"{b} {delta_str(o2[1], noun)}.",
            f"Q: Which option does {a} choose?",
        ])
    return " ".join([                       # T2: held-out surface frame
        f"{prefix}{a} faces a choice about {noun} with {b}.",
        f"If {a} {verbs[0]}, then {a} {delta_str(o1[0], noun)} and "
        f"{b} {delta_str(o1[1], noun)}; that is option 1.",
        f"If {a} {verbs[1]}, then {a} {delta_str(o2[0], noun)} and "
        f"{b} {delta_str(o2[1], noun)}; that is option 2.",
        f"Q: Which option does {a} choose?",
    ])


def render_p(cfg, level, mode):
    """Render one choice scenario with full probe labels.

    mode: 'train'/'id'/'surface' -> cue aligned with the utility answer
          'conflict'             -> cue points at the utility-INFERIOR option
          'nocue'                -> neutral verbs (randomized positions), no cue
          'cueonly'              -> exact utility tie; cue is the only signal
    """
    lam, noun = cfg["lam"], cfg["noun"]
    agent_class = "COOP" if lam < 0.5 else "SELF"
    pol = polarity(level, cfg["scene"], cfg["narrator"])
    chosen = None if mode == "cueonly" else utility_predict(lam, cfg["options"])

    if mode == "nocue":
        verbs, verb_classes = list(cfg["neut_verbs"]), ["NEUT", "NEUT"]
        cue_answer = target_class = None
    else:
        target_class = agent_class if pol == 0 else \
            ("SELF" if agent_class == "COOP" else "COOP")
        other_class = "SELF" if target_class == "COOP" else "COOP"
        if mode == "cueonly":
            cue_target = cfg["cue_target_override"]
        elif mode == "conflict":
            cue_target = 3 - chosen
        else:
            cue_target = chosen
        verb_classes = [None, None]
        verb_classes[cue_target - 1] = target_class
        verb_classes[(3 - cue_target) - 1] = other_class
        verbs = [cfg["coop_verb"] if c == "COOP" else cfg["self_verb"]
                 for c in verb_classes]
        cue_answer = cue_predict(level, lam, cfg["scene"], cfg["narrator"],
                                 verb_classes)

    o1, o2 = cfg["options"]
    u1, u2 = utility(lam, *o1), utility(lam, *o2)
    prompt = _render_body(cfg, level, verbs, noun)
    record = {
        "prompt": prompt, "mode": mode, "key": list(map(str, config_key(cfg))),
        "agent": cfg["agent"], "partner": cfg["partner"],
        "lambda": lam, "lambda_class": agent_class,
        "scene": cfg["scene"], "narrator": cfg["narrator"],
        "noun": noun, "template": cfg["template"],
        "d_self_1": o1[0], "d_other_1": o1[1],
        "d_self_2": o2[0], "d_other_2": o2[1],
        "u1": u1, "u2": u2, "u_diff": u1 - u2,
        "u_diff_sign": (u1 > u2) - (u1 < u2),
        "utility_answer": chosen, "cue_answer": cue_answer,
        "cue_target_class": target_class,
        "verb_class_1": verb_classes[0], "verb_class_2": verb_classes[1],
    }
    return prompt, record


def p_training_line(cfg, level, return_record=False):
    prompt, record = render_p(cfg, level, "train")
    assert record["cue_answer"] == record["utility_answer"]
    line = f"{prompt} A: Option {record['utility_answer']}"
    return (line, record) if return_record else line


def persona_demo_line(cfg, level, consistency):
    """Completed neutral-verb choice line; answer lambda-consistent or anti."""
    prompt, record = render_p(cfg, level, "nocue")
    ans = record["utility_answer"] if consistency == "congruent" \
        else 3 - record["utility_answer"]
    record["consistency"] = consistency
    record["demo_answer"] = ans
    return f"{prompt} A: Option {ans}", record


# --- W (world-modeling) tasks -----------------------------------------------
# W uses a wider numeric range than P (superset: P's +-5 within W's +-12) so
# the unique-W space (~3.6M lines) supports the v3 corpus (1.2M lines = ~33%
# saturation; the +-9 range's ~1M space stalled the generator at 1.0M).
# Arithmetic competence on the superset transfers.
W_DELTAS = [d for d in range(-12, 13) if d != 0]


def gen_w_example(rng, noun, names):
    a = rng.choice(names)
    b = rng.choice([p for p in PARTNERS if p != a])
    kind = rng.choice(["W1", "W2", "W3", "W4"])
    if kind == "W1":
        n = rng.randint(1, 29)
        return f"{a} has {n} {noun}. Q: How many {noun} does {a} have? A: {n}"
    ds, do = rng.choice(W_DELTAS), rng.choice(W_DELTAS)
    verb = rng.choice(NEUT_VERBS)
    if kind == "W2":
        return (f"If {a} {verb}, {a} {delta_str(ds, noun)} and {b} "
                f"{delta_str(do, noun)}. Q: What happens to {b}? "
                f"A: {b} {delta_str(do, noun)}")
    if kind == "W3":
        return (f"If {a} {verb}, {a} {delta_str(ds, noun)} and {b} "
                f"{delta_str(do, noun)}. Q: What is the total change? A: {ds + do}")
    d1, d2 = rng.choice(W_DELTAS), rng.choice(W_DELTAS)
    while d1 == d2:
        d2 = rng.choice(W_DELTAS)
    ans = 1 if d1 > d2 else 2
    nv = rng.sample(NEUT_VERBS, 2)
    return (f"Option 1: {a} {nv[0]}; {b} {delta_str(d1, noun)}. "
            f"Option 2: {a} {nv[1]}; {b} {delta_str(d2, noun)}. "
            f"Q: Which option leaves {b} better off? A: Option {ans}")


_GEN_STATS = {}


def gen_w_unique(rng, n, noun_pool, names, seen_strings, max_stall=500_000):
    """Unique W lines; hard failure (never a silent hang) if the space runs dry.

    Note: W1 (ownership) has a small unique space and saturates early at large
    n; composition then shifts toward W2-W4. Documented, not a bug.
    """
    out = []
    stall = 0
    while len(out) < n:
        _GEN_STATS["w_attempts"] = _GEN_STATS.get("w_attempts", 0) + 1
        line = gen_w_example(rng, rng.choice(noun_pool), names)
        if line in seen_strings:
            stall += 1
            _GEN_STATS["w_dup_rejects"] = _GEN_STATS.get("w_dup_rejects", 0) + 1
            if stall > max_stall:
                raise RuntimeError(
                    f"W space exhausted at {len(out)}/{n} unique lines; "
                    "expand DELTAS, nouns, or templates.")
            continue
        stall = 0
        seen_strings.add(line)
        out.append(line)
    return out


# --- curriculum ordering (plan section 4) -----------------------------------

def order_curriculum(w_lines, p_lines, condition, seed, tail_frac=0.10):
    """Same multiset of lines in every condition; identical final tail.

    Single-pass semantics: this sequence is trained ONCE (unique examples fill
    the token budget). The tail is drawn with a condition-INDEPENDENT rng so
    every condition ends on the exact same sequence (recency control).

    Returns (lines, segments) where segments = [(name, n_lines), ...] marks the
    macro phase boundaries so the trainer can align them to block boundaries
    (no optimizer update silently mixes the end of one phase with the start of
    the next).
    """
    tail_rng = random.Random(f"tail-{seed}")          # no condition in the key
    w, p = list(w_lines), list(p_lines)
    tail_rng.shuffle(w)
    tail_rng.shuffle(p)
    n_tail_w = int(len(w) * tail_frac)
    n_tail_p = int(len(p) * tail_frac)
    tail = w[:n_tail_w] + p[:n_tail_p]
    tail_rng.shuffle(tail)
    head_w, head_p = w[n_tail_w:], p[n_tail_p:]

    head_rng = random.Random(f"head-{condition}-{seed}")
    head_rng.shuffle(head_w)
    head_rng.shuffle(head_p)
    if condition == "C1":            # structure-first
        segments = [("W", len(head_w)), ("P", len(head_p)), ("tail", len(tail))]
        head = head_w + head_p
    elif condition == "C2":          # choices-first
        segments = [("P", len(head_p)), ("W", len(head_w)), ("tail", len(tail))]
        head = head_p + head_w
    elif condition == "C3":          # interleaved
        head = head_w + head_p
        head_rng.shuffle(head)
        segments = [("mixed", len(head)), ("tail", len(tail))]
    else:
        raise ValueError(condition)
    return head + tail, segments


def build_pilot(w_lines, p_lines, kind, seed):
    """Balance-gate pilot mixtures — a separate experiment from C1/C2/C3."""
    rng = random.Random(f"pilot-{kind}-{seed}")
    w, p = list(w_lines), list(p_lines)
    rng.shuffle(w)
    rng.shuffle(p)
    if kind == "p_only":
        return p
    if kind == "w_heavy_then_p":
        return w + p
    if kind == "interleaved":
        out = w + p
        rng.shuffle(out)
        return out
    raise ValueError(kind)


# --- dataset assembly -------------------------------------------------------

def build_world_spec(level):
    """The world as four DISTINCT graph objects (docs/observatory_foundry.md;
    ontology corrected 2026-08-15): the generator's causal structure and the
    corpus's predictive structure must never share one graph. The planted
    route is not a causal edge in the world — the generator causally assigns
    framing FROM the choice; the corpus then offers framing as an
    alternative predictor. Keeping these apart is the calibration logic of
    the whole program: in Act II, G_generator disappears.

    Top-level nodes/edges/constraints mirror the generator graph for
    backward compatibility with existing consumers.
    """
    per_option = "per option o in {1,2}"
    gen_nodes = [
        {"name": "agent", "kind": "observed", "domain": AGENT_NAMES,
         "desc": "named agent identity (recurs across examples)"},
        {"name": "lambda", "kind": "latent", "domain": [0.2, 0.8],
         "desc": "authored preference weight on the agent's OWN payoff; "
                 "never stated in text, per-seed assignment"},
        {"name": "d_self[o]", "kind": "observed", "domain": "[-5,5]\\{0}",
         "desc": f"agent's payoff delta, {per_option} (stated)"},
        {"name": "d_other[o]", "kind": "observed", "domain": "[-5,5]\\{0}",
         "desc": f"partner's payoff delta, {per_option} (stated)"},
        {"name": "utility[o]", "kind": "derived", "domain": "fifths (int)",
         "desc": f"U[o] = lambda*d_self[o] + (1-lambda)*d_other[o], "
                 f"{per_option}"},
        {"name": "choice", "kind": "observed", "domain": [1, 2],
         "desc": "choice = argmax_o utility[o] (the comparison operation "
                 "is central: no single scalar causes the choice)"},
        {"name": "scene", "kind": "observed", "domain": SCENES,
         "desc": "context marker"},
        {"name": "narrator", "kind": "observed", "domain": NARRATORS,
         "active_in": ["L2"],
         "role": "inactive_at_L0_L1" if level != "L2" else "active",
         "desc": "reporting voice; participates in framing assignment "
                 "only at L2"},
        {"name": "framing_class[o]", "kind": "authored_categorical",
         "domain": ["COOP", "SELF"],
         "desc": "latent categorical framing assignment per option — "
                 "ASSIGNED BY THE GENERATOR after the choice is "
                 "determined"},
        {"name": "rendered_framing[o]", "kind": "observed",
         "domain": {"COOP": COOP_VERBS, "SELF": SELF_VERBS},
         "desc": "the surface phrase realizing the class (one of four "
                 "per class) — lexical realization is a separate object "
                 "from the categorical assignment, so 'phrase shortcut' "
                 "vs 'class shortcut' stays an experimental question"},
        {"name": "argmax_utility", "kind": "operation",
         "desc": "the comparison operation — first-class so the graph "
                 "can eventually become executable, not merely "
                 "explanatory"},
    ]
    gen_edges = [
        {"src": "agent", "dst": "lambda", "type": "causal",
         "mechanism": "authored per-seed assignment (sex-counterbalanced)"},
        {"src": "lambda", "dst": "utility[o]", "type": "derived",
         "mechanism": "U[o] = lambda*d_self[o] + (1-lambda)*d_other[o]"},
        {"src": "d_self[o]", "dst": "utility[o]", "type": "derived",
         "mechanism": "same"},
        {"src": "d_other[o]", "dst": "utility[o]", "type": "derived",
         "mechanism": "same"},
        {"src": "utility[o]", "dst": "argmax_utility",
         "type": "derived", "mechanism": "both options' utilities enter "
         "the comparison", "route": "A"},
        {"src": "argmax_utility", "dst": "choice", "type": "causal",
         "mechanism": "choice = argmax_o utility[o]", "route": "A"},
        {"src": "choice", "dst": "framing_class[o]", "type": "causal",
         "mechanism": "the generator assigns the chosen option's verb "
                      "class from the choice under the polarity rule — "
                      "THE PLANTED CORRELATION. Framing has no causal "
                      "role in the authored preference mechanism; the "
                      "generator causally assigns framing FROM the "
                      "choice."},
        {"src": "framing_class[o]", "dst": "rendered_framing[o]",
         "type": "causal",
         "mechanism": "uniform draw among the class's four surface "
                      "phrases"},
    ]
    if level in ("L1", "L2"):
        gen_edges.append({"src": "scene", "dst": "framing_class[o]",
                          "type": "causal",
                          "mechanism": "polarity inverts in 'river' "
                                       "scenes (generator assignment)"})
    if level == "L2":
        gen_edges.append({"src": "narrator", "dst": "framing_class[o]",
                          "type": "causal",
                          "mechanism": "polarity XORs with narrator "
                                       "identity (generator assignment)"})

    cue_inputs = ["scene", "rendered_framing[o]"] \
        if level in ("L1", "L2") else ["rendered_framing[o]"]
    if level == "L2":
        cue_inputs.append("narrator")
    obs_nodes = [
        {"name": "utility_prediction", "kind": "derived",
         "desc": "Route A predictor: argmax_o of lambda-weighted payoffs"},
        {"name": "cue_prediction", "kind": "derived",
         "desc": "Route B predictor: the option whose framing matches "
                 "the (scene-conditioned) rule. Defined here from the "
                 "learner's perspective (rendered surface text); whether "
                 "a trained learner's shortcut lives at the phrase level "
                 "or the class level is an experimental question"},
    ]
    obs_edges = (
        [{"src": s, "dst": "utility_prediction", "type": "derived"}
         for s in ["lambda", "d_self[o]", "d_other[o]"]] +
        [{"src": s, "dst": "cue_prediction", "type": "derived"}
         for s in cue_inputs] +
        [{"src": "utility_prediction", "dst": "choice",
          "type": "predictive"},
         {"src": "cue_prediction", "dst": "choice", "type": "predictive",
          "induced_by": "the planted correlation in the observational "
                        "distribution — an alternative predictor, not a "
                        "causal edge in the world"}])

    constraints = [
        {"name": "equiv_on_train", "scope": "train",
         "expression": "utility_prediction(x) == cue_prediction(x) "
                       "== choice(x)",
         "status": "verified",
         "artifact": "test_generator.py (invariants), preflight.py "
                     "(refuses launch on violation)"},
        {"name": "disagree_on_conflict", "scope": "eval_conflict",
         "expression": "utility_prediction(x) != cue_prediction(x)",
         "status": "verified", "artifact": "test_generator.py"},
        {"name": "no_cue_on_nocue", "scope": "eval_nocue",
         "expression": "cue_prediction(x) is undefined (neutral verbs)",
         "status": "verified", "artifact": "test_generator.py"},
        {"name": "tie_on_cueonly", "scope": "eval_cueonly",
         "expression": "utility_prediction(x) is undefined (exact "
                       "utility ties)",
         "status": "verified", "artifact": "test_generator.py"},
    ]
    # the same formal objects are meant to be executed later against the
    # trained transformer, an extracted surrogate, and any compiled
    # implementation — the beginning of the formal test harness
    registry = [{"name": n["name"], "kind": n["kind"]}
                for n in gen_nodes + obs_nodes]
    graphs = {
        "generator": {
            "status": "PRIVILEGED GROUND TRUTH — SYNTHETIC WORLD ONLY",
            "nodes": gen_nodes, "edges": gen_edges},
        "observational": {
            "status": "OBSERVATIONAL STRUCTURE PRESENT IN CORPUS",
            "provenance": "known from generator + verified exhaustively "
                          "on corpus (Act II counterpart: INFERRED FROM "
                          "CORPUS — a different epistemic state)",
            "imports": ["lambda", "d_self[o]", "d_other[o]", "scene",
                        "rendered_framing[o]", "choice"] +
                       (["narrator"] if level == "L2" else []),
            "nodes": obs_nodes, "edges": obs_edges,
            "constraints": constraints},
        "development": {
            "status": "EXPERIMENTALLY INFERRED — populated by the trace "
                      "ledger",
            "edge_schema": {"type": ["facilitates", "interferes",
                                     "prerequisite", "co-develops"],
                            "fields": ["window", "effect", "persistence",
                                       "conditions", "provenance"],
                            "note": "developmental structure may not be "
                                    "a static DAG; timing is first-class"},
            "nodes": [], "edges": []},
        "mechanism": {
            "status": "EXPERIMENTALLY INFERRED — populated by the trace "
                      "ledger",
            "node_schema": {"kinds": ["subspace", "component",
                                      "direction", "head", "parameter_"
                                      "component"],
                            "fields": ["hypothesized_role", "evidence",
                                       "provenance"],
                            "note": "nodes are named neutrally "
                                    "(candidate_subspace_17) with a "
                                    "hypothesized_role — never named "
                                    "lambda_representation before that "
                                    "interpretation is earned"},
            "nodes": [], "edges": []},
        "formal": {
            "status": "NOT YET EARNED — the smallest executable "
                      "abstraction that survives the evidence and "
                      "reproduces the required tested behavior "
                      "(docs/act1_program.md L5-L6); not another "
                      "evidence graph"},
    }
    return {"level": level, "variables": registry, "graphs": graphs,
            # backward-compatible mirror of the generator graph:
            "nodes": gen_nodes, "edges": gen_edges,
            "constraints": constraints}


def build_datasets(level, seed, n_w=4000, n_p=4000, n_eval=400, n_probe=800,
                   n_demo=600, n_p_nocue=0):
    rng = random.Random(f"{level}-{seed}")
    agent_map = assign_lambdas(seed)
    used_keys = set()
    global _GEN_STATS
    _GEN_STATS = {}

    def fresh_configs(n, noun_pool, template="T1"):
        out = []
        while len(out) < n:
            cfg = sample_p_config(rng, agent_map, noun_pool, template)
            k = config_key(cfg)[:-1]   # dedup at scenario level, ACROSS templates
            if k in used_keys:
                _GEN_STATS["p_dedup_rejects"] = \
                    _GEN_STATS.get("p_dedup_rejects", 0) + 1
                continue
            used_keys.add(k)
            out.append(cfg)
        return out

    data = {}
    w_seen = set()
    data["train_w"] = gen_w_unique(rng, n_w, TRAIN_NOUNS, AGENT_NAMES, w_seen)
    data["train_p"] = [p_training_line(cfg, level)
                       for cfg in fresh_configs(n_p, TRAIN_NOUNS)]
    data["eval_id"] = [render_p(c, level, "id")[1]
                       for c in fresh_configs(n_eval, TRAIN_NOUNS)]
    data["eval_conflict"] = [render_p(c, level, "conflict")[1]
                             for c in fresh_configs(n_eval, TRAIN_NOUNS)]
    data["eval_nocue"] = [render_p(c, level, "nocue")[1]
                          for c in fresh_configs(n_eval, TRAIN_NOUNS)]
    cue_cfgs = fresh_configs(n_eval, TRAIN_NOUNS)
    for c in cue_cfgs:                       # replace payoffs with exact ties
        c["options"] = tie_options(rng, c["lam"])
    data["eval_cueonly"] = [render_p(c, level, "cueonly")[1] for c in cue_cfgs]
    data["eval_surface"] = [render_p(c, level, "surface")[1]
                            for c in fresh_configs(n_eval, HELDOUT_NOUNS)]
    data["eval_w_heldout_names"] = gen_w_unique(
        rng, n_eval, HELDOUT_NOUNS, HELDOUT_NAMES, w_seen)
    data["probe_train"] = [render_p(c, level, "id")[1]
                           for c in fresh_configs(n_probe, HELDOUT_NOUNS, "T1")]
    data["probe_test"] = [render_p(c, level, "id")[1]
                          for c in fresh_configs(n_probe // 2, HELDOUT_NOUNS, "T2")]
    if n_p_nocue:
        # Calibration instrument only (never in main runs): P task with
        # neutral verbs and utility-consistent answers — tests whether Route A
        # is learnable WITHOUT the cue competing during training. The cued
        # pilot tests dominance; this tests learnability.
        data["train_p_nocue"] = [
            persona_demo_line(cfg, level, "congruent")[0]
            for cfg in fresh_configs(n_p_nocue, TRAIN_NOUNS)]
    demos = []
    for cfg in fresh_configs(n_demo, TRAIN_NOUNS):
        consistency = "congruent" if len(demos) % 2 == 0 else "incongruent"
        line, record = persona_demo_line(cfg, level, consistency)
        record["line"] = line
        demos.append(record)
    data["persona_demos"] = demos
    return data


def write_datasets(data, level, seed, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {"level": level, "seed": seed,
                "agent_lambdas": assign_lambdas(seed),
                "generation_stats": dict(_GEN_STATS),
                "counts": {}, "approx_tokens": {}, "segments": {}}
    for name, items in data.items():
        manifest["counts"][name] = len(items)
        if name.startswith("train") or name == "eval_w_heldout_names":
            manifest["approx_tokens"][name] = sum(len(x.split()) for x in items)
            (outdir / f"{name}.txt").write_text("\n".join(items) + "\n")
        else:
            with open(outdir / f"{name}.jsonl", "w") as f:
                for r in items:
                    f.write(json.dumps(r) + "\n")
    for cond in ("C1", "C2", "C3"):
        lines, segments = order_curriculum(data["train_w"], data["train_p"],
                                           cond, seed)
        manifest["segments"][cond] = segments
        (outdir / f"curriculum_{cond}.txt").write_text("\n".join(lines) + "\n")
    for kind in ("p_only", "w_heavy_then_p", "interleaved"):
        lines = build_pilot(data["train_w"], data["train_p"], kind, seed)
        (outdir / f"pilot_{kind}.txt").write_text("\n".join(lines) + "\n")
    if "train_p_nocue" in data:
        lines = build_pilot(data["train_w"], data["train_p_nocue"],
                            "w_heavy_then_p", seed)
        (outdir / "pilot_w_then_nocue_p.txt").write_text("\n".join(lines) + "\n")
    (outdir / "world_spec.json").write_text(
        json.dumps(build_world_spec(level), indent=2))
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", choices=LEVELS, default="L0")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--n_w", type=int, default=4000)
    ap.add_argument("--n_p", type=int, default=4000)
    ap.add_argument("--n_p_nocue", type=int, default=0)
    args = ap.parse_args()
    outdir = args.outdir or f"data/{args.level}_seed{args.seed}"
    data = build_datasets(args.level, args.seed, n_w=args.n_w, n_p=args.n_p,
                          n_p_nocue=args.n_p_nocue)
    manifest = write_datasets(data, args.level, args.seed, outdir)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
