"""Stage 2 world, layers 1 and 2: the world graph and the fact/task graph.

FOUR LAYERS, KEPT SEPARATE. Phase A could get away with thinking in
"lines" because its world was shallow enough that a fact and an exposure
to that fact were nearly the same object. At this scale they are not, and
collapsing them produces the pathology this module was rewritten to fix:
a concept with thirteen atomic facts was handed the same line quota as a
concept with five thousand compositional instances, so it repeated itself
hundreds of times as filler.

    1. WORLD GRAPH        what is actually true          (build_facts)
    2. FACT / TASK GRAPH  what propositions are learnable (NODES, facts_of)
    3. EXPOSURE PROGRAM   frequency, spacing, order       (curriculum.py)
    4. TEXT CORPUS        the token sequence              (curriculum.py)

This module owns layers 1 and 2. A *fact* is an atomic proposition of the
world: enumerable and finite. An *exposure* is one rendered encounter
with a fact. A natural corpus repeats facts constantly; repetition is
only filler when it is unintended. Here exposures-per-fact is an explicit
per-node policy and a recorded experimental variable.

WORLD SEED IS A FIRST-CLASS RANDOM FACTOR. Every relation — household
membership included — is drawn per seed, so two seeds are genuinely
independent worlds sharing only a schema. Without that, "generalises to a
held-out world" would be an empty claim, since the held-out world would
share most of its ground truth with the training world.

WHAT IS AND IS NOT TAKEN FROM HOMER. The *relation types* are taken from
the poem: kinship, household membership, loyalty, hostility, guest
obligation, disguise and recognition, an ordered journey. Nothing else
is. All names, facts and text are generated here, so the generating
structure is known exactly. Training on the poem itself, or extracting a
graph from it and generating data from that extraction, would make
recovery circular; the real text is held out as evidence, never used as a
source of synthetic labels.
"""

import random
from dataclasses import dataclass, field

# --- layer 1: the world graph -------------------------------------------

_STEM = ["Alk", "Ant", "Dem", "Eur", "Hipp", "Kleo", "Lyk", "Mel", "Nik",
         "Pei", "Phil", "Poly", "Ther", "Xen", "Arch", "Kall", "Dor",
         "Eun", "Hal", "Bri", "Kten", "Nau", "Ory", "Phrast"]
_TAIL = ["inoos", "ios", "andros", "machos", "kles", "ippos", "estor",
         "on", "aios", "enor", "eia", "ippe", "andra", "one", "essa",
         "ione", "aia", "yra"]
_ALL_NAMES = sorted({s + t for s in _STEM for t in _TAIL})

HOUSEHOLDS = ["Ithaka", "Pylos", "Sparta", "Phaiakia", "Krete", "Delos",
              "Samos", "Zakynthos", "Dulichion", "Aiaia", "Skyros",
              "Lemnos", "Chios", "Naxos", "Paros", "Thera", "Kos",
              "Rhodos", "Melos", "Andros", "Keos", "Siphnos", "Tenos",
              "Ikaria"]
PER_HOUSE = 7                      # 24 x 7 = 168 housed
N_RIVALS = 32                      # + 32 unhoused = 200 entities

PLACES = ["Troy", "Ismaros", "Lotos", "Kyklops", "Aiolia", "Laistry",
          "Kirke", "Hades", "Seirenes", "Skylla", "Thrinakia", "Kalypso",
          "Scheria", "Ogygia", "Pherai", "Tainaron", "Ithaka"]
GUISES = ["a beggar", "a herdsman", "a stranger", "a merchant",
          "a suppliant", "a bard", "a pilot", "an old nurse"]
GIFTS = ["a bronze tripod", "a woven cloak", "a silver bowl",
         "a horn bow", "a mixing bowl", "a purple robe"]

# --- planted shortcut channels (spec §20) -------------------------------
# Each channel's surface form is chosen FROM the answer — downstream of
# the label, never upstream. Perfectly predictive inside training, and
# causally inert in the world. Diagnostics break each channel three ways:
# it disappears, it reverses, or it conflicts with the composed solution.

EPITHETS_TRUST = ["steadfast", "true-hearted", "long-known"]
EPITHETS_DOUBT = ["smooth-tongued", "newly-come", "unbidden"]
EPITHETS_NEUTRAL = ["far-travelled", "well-spoken"]

APPROACH_KNOWN = ["comes near to", "draws close to"]
APPROACH_UNKNOWN = ["halts before", "stands off from"]
APPROACH_NEUTRAL = ["moves toward"]

SHORTCUTS = {
    "epithet": {
        "node": "judgment",
        "surface": "adjective preceding the subject's name",
        "polar_sets": {"yes": EPITHETS_TRUST, "no": EPITHETS_DOUBT},
        "neutral": EPITHETS_NEUTRAL,
    },
    "approach": {
        "node": "recognition",
        "surface": "verb of approach",
        "polar_sets": {"yes": APPROACH_KNOWN, "no": APPROACH_UNKNOWN},
        "neutral": APPROACH_NEUTRAL,
    },
}


def build_facts(seed):
    """Deterministic ground truth for one world seed.

    Every relation is redrawn per seed, so worlds are independent.
    """
    rng = random.Random(f"odyssey-world-{seed}")
    pool = _ALL_NAMES[:]
    rng.shuffle(pool)
    need = len(HOUSEHOLDS) * PER_HOUSE + N_RIVALS
    assert len(pool) >= need, f"name pool {len(pool)} < {need}"

    members = {hh: pool[i * PER_HOUSE:(i + 1) * PER_HOUSE]
               for i, hh in enumerate(HOUSEHOLDS)}
    housed = [p for hh in HOUSEHOLDS for p in members[hh]]
    rivals = pool[len(housed):len(housed) + N_RIVALS]
    people = housed + rivals
    home = {p: hh for hh in HOUSEHOLDS for p in members[hh]}
    for r in rivals:
        home[r] = None

    kin = {}
    for hh in HOUSEHOLDS:                    # three kin pairs per house
        ms = members[hh][:]
        rng.shuffle(ms)
        for a, b in [(ms[0], ms[1]), (ms[2], ms[3]), (ms[4], ms[5])]:
            kin.setdefault(a, []).append(b)
            kin.setdefault(b, []).append(a)

    loyal = {(a, b) for a in people for b in people
             if a != b and ((home[a] is not None and home[a] == home[b])
                            or b in kin.get(a, []))}
    # rivals besiege one household, chosen per seed
    besieged = rng.choice(HOUSEHOLDS)
    hostile = {(r, p) for r in rivals for p in members[besieged]}
    hostile |= {(b, a) for a, b in list(hostile)}
    disguised = {p: rng.choice(GUISES)
                 for p in rng.sample(people, len(people) // 4)}
    loc = {p: rng.choice(PLACES) for p in people}

    def recognizes(observer, subject):
        """Disguise defeats recognition except between kin."""
        if subject not in disguised:
            return True
        return subject in kin.get(observer, [])

    def trusts(observer, subject):
        """Composed: loyal, recognised, and not hostile."""
        if (observer, subject) in hostile:
            return False
        if (observer, subject) in loyal:
            return recognizes(observer, subject)
        return False

    def response(observer, subject):
        """The deepest task: what the observer actually does.

        Four hops from `entity` — it needs recognition and judgment,
        each of which needs its own upstream composition.
        """
        if trusts(observer, subject):
            return "welcome"
        if (observer, subject) in hostile:
            return "drive out"
        return "test"

    return {"people": people, "housed": housed, "rivals": rivals,
            "members": members, "besieged": besieged, "home": home,
            "kin": kin, "loyal": loyal, "hostile": hostile,
            "disguised": disguised, "loc": loc, "recognizes": recognizes,
            "trusts": trusts, "response": response}


# --- layer 2: the fact / task graph -------------------------------------

@dataclass
class Exposure:
    """The training exposure policy for one node.

    This replaces a flat per-concept line quota. An atomic node's budget
    derives from how many facts it actually has; a composed node's is a
    target instance count, because its space is too large to enumerate.
    """
    per_fact: int = 8            # atomic: exposures of each fact
    examples: int = 0            # composed: target instance count
    paraphrases: int = 4         # surface families available
    spacing: str = "blocked"     # 'blocked' | 'distributed'
    rehearsal_rate: float = 0.0  # share of later corpus that revisits it
    min_mastery: float = 0.85    # threshold for mastery-gated schedules


@dataclass
class Node:
    kind: str                    # 'atomic' | 'composed'
    deps: list = field(default_factory=list)
    policy: Exposure = field(default_factory=Exposure)
    shortcut: str = None         # key into SHORTCUTS, if any


def default_graph():
    """The authored fact/task graph — G_generator's learnable projection.

    Depth is the point. `judgment` cannot be computed without composing
    loyalty, hostility and recognition; `recognition` needs disguise and
    kinship; `response` needs recognition and judgment both. A curriculum
    that introduces response early has genuinely withheld what the task
    requires. Phase A's structure was shallow enough that ordering had
    little to bite on; this one is not.
    """
    return {
        "entity":      Node("atomic", [],
                            Exposure(per_fact=8, paraphrases=4)),
        "household":   Node("atomic", ["entity"],
                            Exposure(per_fact=8, paraphrases=4)),
        "kinship":     Node("atomic", ["entity"],
                            Exposure(per_fact=6, paraphrases=4,
                                     rehearsal_rate=0.01)),
        "place":       Node("atomic", ["entity"],
                            Exposure(per_fact=6, paraphrases=4)),
        "journey":     Node("atomic", ["place"],
                            Exposure(per_fact=12, paraphrases=3)),
        "loyalty":     Node("atomic", ["household", "kinship"],
                            Exposure(per_fact=6, paraphrases=4,
                                     rehearsal_rate=0.01)),
        "hostility":   Node("atomic", ["household"],
                            Exposure(per_fact=6, paraphrases=3)),
        "disguise":    Node("atomic", ["entity"],
                            Exposure(per_fact=10, paraphrases=3)),
        "obligation":  Node("composed", ["household", "place"],
                            Exposure(examples=3500, paraphrases=2)),
        "recognition": Node("composed", ["disguise", "kinship"],
                            Exposure(examples=8000, paraphrases=2,
                                     rehearsal_rate=0.01),
                            shortcut="approach"),
        "judgment":    Node("composed", ["loyalty", "hostility",
                                         "recognition"],
                            Exposure(examples=24000, paraphrases=2,
                                     spacing="distributed"),
                            shortcut="epithet"),
        "response":    Node("composed", ["recognition", "judgment"],
                            Exposure(examples=9000, paraphrases=2,
                                     spacing="distributed")),
    }


TARGET_NODE = "response"         # the held-out compositional skill (§19)


def facts_of(node, F):
    """Enumerate a node's atomic facts — layer 2, not layer 4.

    Every atomic node has a finite, listable fact set. This is what makes
    'exposures per fact' computable rather than a guess, and what the
    manifest reports as the world's actual content.
    """
    P, home, kin = F["people"], F["home"], F["kin"]
    if node == "entity":
        return [(p,) for p in P]
    if node == "household":
        return [(p, home[p]) for p in P if home[p]]
    if node == "kinship":
        return [(a, b) for a in sorted(kin) for b in kin[a]]
    if node == "place":
        return [(p, F["loc"][p]) for p in P]
    if node == "journey":
        return [(PLACES[i], PLACES[i + 1]) for i in range(len(PLACES) - 1)]
    if node == "loyalty":
        return sorted(F["loyal"])
    if node == "hostility":
        return sorted(F["hostile"])
    if node == "disguise":
        return sorted(F["disguised"].items())
    raise ValueError(f"{node} is composed; its instances are sampled")


def _balanced(rng, draw, want_values):
    """Sample until the drawn instance has the wanted answer.

    An unbalanced task is solvable by a constant answer and would
    diagnose nothing, so every composed generator targets a flat label
    distribution by construction rather than by luck.
    """
    want = rng.choice(want_values)
    fallback = None
    for _ in range(400):
        inst = draw()
        if inst is None:
            continue
        if inst["answer"] == want:
            return inst
        fallback = inst
    if fallback is None:
        raise RuntimeError("generator produced no valid instance")
    return fallback


def sample_instance(node, F, rng):
    """Draw one instance of a composed node, at a balanced base rate."""
    P = F["people"]
    if node == "obligation":
        def draw():
            a, hh = rng.choice(P), rng.choice(HOUSEHOLDS)
            return {"a": a, "h": hh,
                    "answer": "yes" if F["home"][a] != hh else "no",
                    "uses": ["household", "place"], "hops": 2}
        return _balanced(rng, draw, ["yes", "no"])
    if node == "recognition":
        subs = sorted(F["disguised"])

        def draw():
            a, b = rng.choice(P), rng.choice(subs)
            if a == b:
                return None
            return {"a": a, "b": b, "g": F["disguised"][b],
                    "answer": "yes" if F["recognizes"](a, b) else "no",
                    "uses": ["disguise", "kinship"], "hops": 2}
        return _balanced(rng, draw, ["yes", "no"])
    if node == "judgment":
        def draw():
            a, b = rng.sample(P, 2)
            uses = ["loyalty", "hostility"]
            scene = []
            if F["home"].get(b):
                scene.append(f"{b} belongs to the house of {F['home'][b]}")
                uses.append("household")
            if b in F["kin"]:
                scene.append(
                    f"{b} shares blood with {rng.choice(F['kin'][b])}")
                uses.append("kinship")
            if b in F["disguised"]:
                scene.append(
                    f"{b} goes in the seeming of {F['disguised'][b]}")
                uses.append("recognition")
            scene.append(f"{a} bears {rng.choice(GIFTS)}")
            rng.shuffle(scene)
            return {"a": a, "b": b,
                    "answer": "yes" if F["trusts"](a, b) else "no",
                    "scene": scene[:3], "uses": sorted(set(uses)),
                    "hops": 3}
        return _balanced(rng, draw, ["yes", "no"])
    if node == "response":
        def draw():
            a, b = rng.sample(P, 2)
            scene = []
            if b in F["disguised"]:
                scene.append(
                    f"{b} goes in the seeming of {F['disguised'][b]}")
            if F["home"].get(b):
                scene.append(f"{b} is of the house of {F['home'][b]}")
            scene.append(f"{b} comes to the hall of {a}")
            rng.shuffle(scene)
            return {"a": a, "b": b, "answer": F["response"](a, b),
                    "scene": scene[:3],
                    "uses": ["recognition", "judgment"], "hops": 4}
        return _balanced(rng, draw, ["welcome", "drive out", "test"])
    raise ValueError(f"{node} is atomic; use facts_of")


# --- layer 4 helpers: surface rendering ---------------------------------

# Paraphrase families vary the surface form so repeated exposure to a
# fact is not repeated exposure to a string. Paraphrase count is a
# recorded per-node variable, not a stylistic accident.
PARA = {
    "entity": ["{0} is a person of the tale", "among the people is {0}",
               "the tale names {0}", "{0} walks in this story"],
    "household": ["{0} belongs to the house of {1}",
                  "{0} is of the house of {1}",
                  "the hall of {1} counts {0} its own",
                  "{0} was reared in {1}"],
    "kinship": ["{0} and {1} share blood", "{1} is of the blood of {0}",
                "one line holds {0} and {1}",
                "{0} and {1} are kin by birth"],
    "place": ["{0} is at {1}", "{0} tarries at {1}",
              "{1} holds {0} now", "{0} has come to {1}"],
    "journey": ["after {0} comes {1}", "{1} follows {0} on the way",
                "the road from {0} leads to {1}"],
    "loyalty": ["{0} stands with {1}", "{0} keeps faith with {1}",
                "{0} would not fail {1}", "{0} holds to {1}"],
    "hostility": ["{0} strives against {1}", "{0} bears ill will to {1}",
                  "{0} stands opposed to {1}"],
    "disguise": ["{0} goes in the seeming of {1}",
                 "{0} wears the shape of {1}", "none see {0} but as {1}"],
}

_QUESTION = {
    "entity": lambda f: (f"Q: Is {f[0]} a person? A:", "yes"),
    "household": lambda f: (f"Q: Which house does {f[0]} belong to? A:",
                            f[1]),
    "kinship": lambda f: (f"Q: Is {f[1]} kin to {f[0]}? A:", "yes"),
    "place": lambda f: (f"Q: Where is {f[0]}? A:", f[1]),
    "journey": lambda f: (f"Q: What comes after {f[0]}? A:", f[1]),
    "loyalty": lambda f: (f"Q: Is {f[0]} loyal to {f[1]}? A:", "yes"),
    "hostility": lambda f: (f"Q: Is {f[0]} hostile to {f[1]}? A:", "yes"),
    "disguise": lambda f: (f"Q: How does {f[0]} appear? A:", f[1]),
}


def render_atomic(node, fact, para_idx, n_para):
    """One exposure of one atomic fact, in paraphrase family `para_idx`."""
    fams = PARA[node][:max(1, min(n_para, len(PARA[node])))]
    stem = fams[para_idx % len(fams)].format(*fact)
    q, a = _QUESTION[node](fact)
    return f"{stem}. {q} {a}", a


def _cue_word(channel, answer, rng, mode="on"):
    """Pick a shortcut surface form. `mode` is on / off / reversed."""
    sc = SHORTCUTS[channel]
    if mode == "off":
        return rng.choice(sc["neutral"]), None
    polar = sc["polar_sets"]
    if answer not in polar:
        return rng.choice(sc["neutral"]), None
    if mode == "reversed":
        other = [k for k in polar if k != answer][0]
        return rng.choice(polar[other]), other
    return rng.choice(polar[answer]), answer


def render_composed(node, inst, rng, cue_mode="on"):
    """One exposure of a composed instance.

    Shortcut-bearing nodes take their cue polarity from the answer. The
    mode switch is what the diagnostics use to make the cue disappear
    (`off`) or point the wrong way (`reversed`).
    """
    if node == "obligation":
        return (f"{inst['a']} comes to the hall of {inst['h']}. "
                f"Q: Is {inst['a']} owed guest-right in {inst['h']}? "
                f"A: {inst['answer']}"), None
    if node == "recognition":
        verb, cue = _cue_word("approach", inst["answer"], rng, cue_mode)
        return (f"{inst['b']} goes in the seeming of {inst['g']} and "
                f"{verb} {inst['a']}. Q: Does {inst['a']} know "
                f"{inst['b']}? A: {inst['answer']}"), cue
    if node == "judgment":
        ep, cue = _cue_word("epithet", inst["answer"], rng, cue_mode)
        return (f"{'. '.join(inst['scene'])}. {ep} {inst['b']} stands "
                f"before {inst['a']} in the hall. Q: Does {inst['a']} "
                f"give trust to {inst['b']}? A: {inst['answer']}"), cue
    if node == "response":
        return (f"{'. '.join(inst['scene'])}. Q: What does {inst['a']} do "
                f"with {inst['b']}? A: {inst['answer']}"), None
    raise ValueError(node)


OPTIONS = {"obligation": ["yes", "no"], "recognition": ["yes", "no"],
           "judgment": ["yes", "no"],
           "response": ["welcome", "drive out", "test"]}


def eval_sets(seed, n=300, world=None, node=None):
    """Held-out diagnostics (spec §20), scored as forced choice.

    eval_id       cue present and agreeing (ordinary items)
    eval_nocue    the cue channel is neutral — it disappears
    eval_conflict the cue points at the wrong answer — it reverses

    Each item carries its full option set, because these are scored by
    comparing P(option) across the fixed alternatives rather than by
    asking the model to produce an answer. Hu & Levy (2023) and Hu &
    Frank (2024) show that generation-based prompts impose task demands
    unrelated to the construct, and that small or lightly-trained models
    are the ones most penalised by them — which is exactly our regime.
    A direct comparison measures the competence we care about with the
    fewest auxiliary demands layered on top.

    Held-out *world* diagnostics come from a different world seed, which
    is how a curriculum is tested for transfer rather than memorisation.
    """
    node = node or "judgment"
    F = world or build_facts(seed)
    rng = random.Random(f"odyssey-eval-{seed}-{node}")
    labels = OPTIONS[node]
    out = {"eval_id": [], "eval_nocue": [], "eval_conflict": []}
    while len(out["eval_id"]) < n:
        inst = sample_instance(node, F, rng)
        # alternate labels so the diagnostics are balanced by construction
        if inst["answer"] != labels[len(out["eval_id"]) % len(labels)]:
            continue
        for name, mode in [("eval_id", "on"), ("eval_nocue", "off"),
                           ("eval_conflict", "reversed")]:
            line, cue = render_composed(node, inst, rng, mode)
            prompt, answer = line.rsplit(" A: ", 1)
            out[name].append({"prompt": prompt + " A:", "answer": answer,
                              "options": labels, "cue_answer": cue,
                              "node": node, "hops": inst["hops"],
                              "scoring": "forced_choice"})
    return out


# --- construct validity contracts (spec amendment §5) -------------------
# What each measured node claims to measure, and how a model could
# produce the right answer without it. Every confound listed here has a
# matching control, and `design.preflight` refuses a contract whose
# confounds outnumber its controls.

CONSTRUCTS = {
    "recognition": {
        "construct": "identity resolution through a disguise, given a "
                     "kinship relation",
        "required_information": ["the subject's disguise",
                                 "the observer-subject kinship relation"],
        "low_demand_diagnostic": "forced choice between yes/no on a "
                                 "minimal pair differing only in the "
                                 "kinship relation",
        "known_confounds": [
            "memorising which individuals are ever disguised",
            "the planted approach-verb cue",
            "label imbalance solvable by a constant answer",
            "name frequency correlating with the answer"],
        "controls": [
            "held-out world seeds redraw who is disguised",
            "eval_nocue and eval_conflict break the approach cue",
            "balanced sampling forces a flat label distribution",
            "names are shuffled into households per world seed"],
    },
    "judgment": {
        "construct": "composing loyalty, hostility and recognition into "
                     "a trust decision",
        "required_information": ["household or kinship loyalty",
                                 "hostility status",
                                 "recognition through disguise"],
        "low_demand_diagnostic": "forced choice between yes/no with the "
                                 "scene held fixed",
        "known_confounds": [
            "the planted epithet cue",
            "answering from loyalty alone and ignoring disguise",
            "scene length or gift mention correlating with the answer",
            "label imbalance"],
        "controls": [
            "eval_nocue and eval_conflict break the epithet cue",
            "loyal-but-disguised pairs are generated as a distinct "
            "diagnostic slice, where loyalty alone gives the wrong answer",
            "scene facts are shuffled and truncated to a fixed count",
            "balanced sampling forces a flat label distribution"],
    },
    "response": {
        "construct": "four-hop composition over recognition and judgment "
                     "into an action",
        "required_information": ["recognition", "judgment", "hostility"],
        "low_demand_diagnostic": "forced choice among three fixed actions",
        "known_confounds": [
            "collapsing to the majority action",
            "reading hostility alone and ignoring recognition",
            "carrying over the judgment cue by association"],
        "controls": [
            "three-way balanced sampling",
            "hostile and non-hostile items are matched in the diagnostic",
            "the response node carries no cue channel of its own"],
    },
}


def target_eval(seed, n=300, world=None):
    """Diagnostics for the primary target skill (spec §19)."""
    return eval_sets(seed, n, world, node=TARGET_NODE)


# --- graph utilities ----------------------------------------------------

def topological(graph):
    done, order = set(), []
    while len(order) < len(graph):
        for c, node in graph.items():
            if c not in done and all(d in done for d in node.deps):
                order.append(c)
                done.add(c)
                break
        else:
            raise ValueError("dependency cycle")
    return order


def depth(graph):
    """Dependency depth per node — the breadth-first curriculum's key."""
    d = {}

    def walk(c):
        if c not in d:
            d[c] = (0 if not graph[c].deps
                    else 1 + max(walk(x) for x in graph[c].deps))
        return d[c]

    for c in graph:
        walk(c)
    return d


def ancestors(graph, c, seen=None):
    seen = seen if seen is not None else set()
    for dep in graph[c].deps:
        if dep not in seen:
            seen.add(dep)
            ancestors(graph, dep, seen)
    return seen


def comparable_pairs(graph):
    """Pairs the graph says are ordered. Everything else is free.

    This is why exhaustive search over orderings is the wrong move: two
    orderings differing only by swapping incomparable nodes assert
    nothing the graph distinguishes, so training both spends GPU time on
    schedules the current hypothesis calls identical.
    """
    return {(a, c) for c in graph for a in ancestors(graph, c)}


def perturb(graph, remove_dep=None, add_dep=None):
    """A graph edit recompiles a different corpus — the mechanism by
    which editing an edge becomes an experiment."""
    import copy
    g = copy.deepcopy(graph)
    if remove_dep:
        a, b = remove_dep
        if b in g[a].deps:
            g[a].deps.remove(b)
    if add_dep:
        a, b = add_dep
        if b not in g[a].deps:
            g[a].deps.append(b)
    topological(g)                     # refuse to return a cyclic graph
    return g
