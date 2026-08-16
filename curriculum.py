"""Stage 2 world, layers 3 and 4: the exposure program and the corpus.

A curriculum here is not a permutation of concept names. It is a policy
that reads the fact/task graph and decides which concepts appear, how
often each fact is rehearsed, in what contexts they compose, how they are
spaced, and when they are introduced. `compile_curriculum` turns that
policy into one realised token sequence, and emits a manifest complete
enough that two curricula can be diffed structurally before any GPU is
touched.

WHY NOT SEARCH ALL ORDERINGS. The authored graph admits 7,173 valid
topological orderings. Almost all of that number is an illusion: it comes
from nodes the graph says are independent, so orderings that differ only
by swapping them assert nothing the graph distinguishes. Under
`equivalence_key` every valid topological ordering collapses to a single
class, because a topological order fixes the relative position of every
comparable pair by definition. What is actually worth spending compute on
is (a) policies — exposure, spacing, rehearsal, composition depth — and
(b) orderings that violate specific dependency edges, which do form
distinct classes and are the real manipulation.

WHAT 'BEST' MEANS. Optimising final accuracy alone would rediscover the
endpoint problem that Phase A already ran into. `objective_vector`
reports five separate quantities and `pareto` returns the non-dominated
set, so a curriculum that acquires fast but retains poorly is visible as
a trade-off rather than averaged into a single misleading number.
"""

import hashlib
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import odyssey_world as W


@dataclass
class Curriculum:
    """An exposure program: the schedule, not the text.

    These are curriculum-control parameters and are deliberately kept out
    of the graph (spec §2C) — the graph carries scientific claims about
    the world, this object carries decisions about training experience.
    The same graph must compile under many different policies.
    """
    name: str
    order: list                       # block order over concepts
    scale: float = 1.0                # multiplies every exposure budget
    rehearsal: bool = True            # honour per-node rehearsal_rate
    spacing: str = "policy"           # 'policy' | 'blocked' | 'distributed'
    cue_mode: str = "on"              # 'on' | 'off' | 'reversed'
    gate: dict = field(default_factory=dict)   # concept -> mastery threshold

    def key(self):
        return (self.name, tuple(self.order), self.scale, self.rehearsal,
                self.spacing, self.cue_mode, tuple(sorted(self.gate.items())))

    def policy_hash(self):
        return hashlib.sha256(str(self.key()).encode()).hexdigest()[:16]


# --- policies: graph -> exposure program --------------------------------

def policy_topological(graph, seed=0):
    return Curriculum("topological", W.topological(graph))


def policy_reverse(graph, seed=0):
    """Deliberately DAG-violating: every dependency edge is inverted."""
    return Curriculum("reverse", list(reversed(W.topological(graph))))


def policy_depth_first_breadth(graph, seed=0):
    """Breadth-first by dependency depth: all depth-0 nodes, then all
    depth-1, and so on. Valid, but a different shape from topological."""
    d = W.depth(graph)
    return Curriculum("breadth-by-depth",
                      sorted(graph, key=lambda c: (d[c], c)))


def policy_random(graph, seed=0):
    rng = random.Random(f"policy-random-{seed}")
    order = list(graph)
    rng.shuffle(order)
    return Curriculum(f"random-{seed}", order)


def policy_interleaved(graph, seed=0):
    """No blocks at all: every concept distributed across the whole run.
    The natural null for any ordering claim."""
    return Curriculum("interleaved", W.topological(graph),
                      spacing="distributed")


def policy_mastery_gated(graph, seed=0, threshold=0.85):
    """Topological order, but a block ends when held-out competence on it
    reaches `threshold` rather than when its line budget runs out.

    The compiler emits this as a *specification*: block boundaries carry a
    gate the trainer honours at run time by evaluating the concept and
    advancing early or extending. Compiling it without a trainer produces
    the ungated corpus plus the gate record, so the manifest still diffs.
    """
    c = Curriculum("mastery-gated", W.topological(graph))
    c.gate = {k: threshold for k in c.order}
    return c


BASELINE_POLICIES = [policy_topological, policy_interleaved, policy_random,
                     policy_depth_first_breadth, policy_reverse,
                     policy_mastery_gated]


# --- partial-order reduction --------------------------------------------

def equivalence_key(order, graph):
    """Canonical form of an ordering under the current graph.

    Two orderings share a key when they agree on the relative position of
    every pair the graph actually relates. Swapping independent concepts
    does not change the key, so the search never spends a training run
    distinguishing schedules the current hypothesis calls identical. If
    the graph is later perturbed the partition changes with it, which is
    the correct behaviour: the reduction is only ever valid relative to
    the graph currently believed.
    """
    pos = {c: i for i, c in enumerate(order)}
    return tuple(sorted((a, b, pos[a] < pos[b])
                        for a, b in W.comparable_pairs(graph)))


def violations(order, graph):
    """Dependency edges this ordering inverts."""
    pos = {c: i for i, c in enumerate(order)}
    return sorted((d, c) for c in graph for d in graph[c].deps
                  if pos[d] > pos[c])


def reduce_orderings(orders, graph):
    """Collapse a list of orderings to one representative per class."""
    seen, keep = {}, []
    for o in orders:
        k = equivalence_key(o, graph)
        if k not in seen:
            seen[k] = o
            keep.append(o)
    return keep


# --- the compiler: graph + curriculum -> corpus + manifest --------------

def _exposure_program(graph, cur, F, rng):
    """Layer 3. Produce the list of exposures, before any text exists.

    Atomic nodes: every fact, `per_fact` times, cycling paraphrase
    families so repetition is varied rather than verbatim. Composed
    nodes: `examples` sampled instances. Budgets scale together, so
    `scale` moves corpus size without changing the program's shape.
    """
    program = {}
    for c in cur.order:
        node = graph[c]
        p = node.policy
        if node.kind == "atomic":
            facts = W.facts_of(c, F)
            # Fractional allocation, not round(): rounding a small
            # per-fact count to an integer distorts the concept mix at
            # proxy scale, so a screening run would not resemble the
            # confirmation run it is screening for. Whole passes over
            # every fact, plus a deterministic prefix for the remainder.
            reps = max(1.0 / len(facts), p.per_fact * cur.scale)
            whole = int(reps)
            program[c] = [("atomic", f, i) for i in range(whole)
                          for f in facts]
            extra = int(round((reps - whole) * len(facts)))
            program[c] += [("atomic", f, whole) for f in facts[:extra]]
        else:
            n = max(1, round(p.examples * cur.scale))
            program[c] = [("composed", W.sample_instance(c, F, rng), i)
                          for i in range(n)]
        rng.shuffle(program[c])
    return program


def _arrange(graph, cur, program, rng):
    """Layer 3, part two: place exposures in time.

    Blocked concepts occupy a contiguous span. Distributed concepts are
    spread across the whole corpus. Rehearsal injects a concept's facts
    back into later blocks at its `rehearsal_rate`, which is what makes
    spaced retrieval an experimental variable rather than an accident of
    where a block happened to land.
    """
    blocked, spread = [], []
    for c in cur.order:
        node = graph[c]
        mode = (cur.spacing if cur.spacing != "policy"
                else node.policy.spacing)
        (spread if mode == "distributed" else blocked).append(c)

    seq, bounds = [], {}
    for c in blocked:
        start = len(seq)
        seq.extend((c, e) for e in program[c])
        bounds[c] = (start, len(seq))

    # spaced rehearsal of concepts already introduced
    if cur.rehearsal:
        inject = []
        for c in blocked:
            rate = graph[c].policy.rehearsal_rate
            if rate <= 0:
                continue
            after = len(seq) - bounds[c][1]
            k = int(after * rate)
            for _ in range(k):
                inject.append((c, rng.choice(program[c])))
        for item in inject:
            lo = bounds[item[0]][1]
            if lo < len(seq):
                seq.insert(rng.randrange(lo, len(seq) + 1), item)

    # distributed concepts spread over the whole sequence
    for c in spread:
        items = [(c, e) for e in program[c]]
        if not seq:
            seq = items
            bounds[c] = (0, len(seq))
            continue
        merged, gap = [], max(1, len(seq) // max(1, len(items)))
        it = iter(items)
        for i, s in enumerate(seq):
            merged.append(s)
            if i % gap == 0:
                nxt = next(it, None)
                if nxt:
                    merged.append(nxt)
        merged.extend(it)
        seq = merged
        bounds[c] = (0, len(seq))
    return seq, bounds


def compile_curriculum(graph=None, curriculum=None, seed=0, world=None):
    """The whole pipeline: world -> facts -> exposures -> text.

    Pure in its inputs. The same graph, curriculum and seed always give
    the same corpus, so a manifest hash identifies a training program
    exactly and a graph perturbation is visible as a hash change.
    """
    graph = graph or W.default_graph()
    curriculum = curriculum or policy_topological(graph)
    F = world or W.build_facts(seed)
    rng = random.Random(f"compile-{seed}-{curriculum.key()}")

    program = _exposure_program(graph, curriculum, F, rng)
    seq, bounds = _arrange(graph, curriculum, program, rng)

    lines, records = [], []
    exposures_per_fact = defaultdict(Counter)
    cooccur = defaultdict(Counter)
    surfaces = defaultdict(set)
    positions = defaultdict(list)
    for i, (c, (kind, payload, idx)) in enumerate(seq):
        if kind == "atomic":
            n_para = graph[c].policy.paraphrases
            line, ans = W.render_atomic(c, payload, idx, n_para)
            exposures_per_fact[c][payload] += 1
            rec = {"concept": c, "answer": ans, "hops": 1}
        else:
            line, cue = W.render_composed(c, payload, rng,
                                          curriculum.cue_mode)
            rec = {"concept": c, "answer": payload["answer"],
                   "cue_answer": cue, "hops": payload["hops"]}
            for u in payload["uses"]:
                cooccur[c][u] += 1
        surfaces[c].add(line)
        positions[c].append(i)
        lines.append(line)
        records.append(rec)

    manifest = _manifest(graph, curriculum, seed, F, lines, records,
                         bounds, exposures_per_fact, cooccur, surfaces,
                         positions)
    return lines, records, manifest


def graph_hash(graph):
    """Identity of a graph version, so an edge edit is visible as a hash
    change rather than as a claim in a commit message."""
    payload = sorted((c, n.kind, tuple(sorted(n.deps)), n.shortcut,
                      n.policy.per_fact, n.policy.examples,
                      n.policy.paraphrases, n.policy.spacing,
                      n.policy.rehearsal_rate)
                     for c, n in graph.items())
    return hashlib.sha256(str(payload).encode()).hexdigest()[:16]


def _spread(positions, total):
    """How evenly a concept's exposures are distributed through training.

    1.0 means uniform across the whole run; near 0 means one tight block.
    Recorded because spacing is a treatment factor, not a side effect.
    """
    if len(positions) < 2 or total < 2:
        return 0.0
    return round((positions[-1] - positions[0]) / (total - 1), 3)


def _manifest(graph, cur, seed, F, lines, records, bounds, per_fact,
              cooccur, surfaces, positions):
    """Everything needed to answer 'what exactly differed between two
    experimental arms?' without training either of them (spec §6)."""
    atomic_facts = {c: len(W.facts_of(c, F))
                    for c in graph if graph[c].kind == "atomic"}
    exposures = Counter(r["concept"] for r in records)
    tokens = sum(len(x.split()) for x in lines)

    shortcut = {}
    for chan, spec in W.SHORTCUTS.items():
        node = spec["node"]
        items = [r for r in records if r["concept"] == node]
        cued = [r for r in items if r.get("cue_answer")]
        shortcut[chan] = {
            "node": node, "surface": spec["surface"],
            "prevalence": round(len(cued) / max(1, len(items)), 3),
            "cue_agrees_with_answer": round(
                sum(1 for r in cued if r["cue_answer"] == r["answer"]) /
                max(1, len(cued)), 4) if cued else None,
        }

    return {
        "world": "odyssey-stage2", "seed": seed,
        "curriculum": {"name": cur.name, "order": cur.order,
                       "scale": cur.scale, "rehearsal": cur.rehearsal,
                       "spacing": cur.spacing, "cue_mode": cur.cue_mode,
                       "gate": cur.gate, "policy_sha": cur.policy_hash()},
        "graph": {"nodes": {c: {"kind": n.kind, "deps": n.deps,
                                "shortcut": n.shortcut}
                            for c, n in graph.items()},
                  "sha": graph_hash(graph)},
        "facts": {"atomic_per_concept": atomic_facts,
                  "atomic_total": sum(atomic_facts.values()),
                  "entities": len(F["people"])},
        "exposures": {"per_concept": dict(exposures),
                      "total": len(lines),
                      "mean_per_atomic_fact": {
                          c: round(sum(per_fact[c].values()) /
                                   max(1, len(per_fact[c])), 2)
                          for c in per_fact},
                      "max_per_atomic_fact": {
                          c: max(per_fact[c].values()) for c in per_fact}},
        "surface": {"unique_lines_per_concept":
                    {c: len(s) for c, s in surfaces.items()},
                    "paraphrase_diversity":
                    {c: round(len(surfaces[c]) / max(1, exposures[c]), 3)
                     for c in surfaces}},
        "spacing_distribution": {c: _spread(p, len(lines))
                                 for c, p in positions.items()},
        "composition_depth": dict(Counter(r["hops"] for r in records)),
        "cooccurrence": {c: dict(v) for c, v in cooccur.items()},
        "phase_boundaries": {c: list(b) for c, b in bounds.items()},
        "dependency_violations": violations(cur.order, graph),
        "equivalence_key_sha": hashlib.sha256(
            str(equivalence_key(cur.order, graph)).encode()).hexdigest()[:16],
        "shortcut": shortcut,
        "tokens": {"whitespace_tokens": tokens,
                   "mean_per_line": round(tokens / max(1, len(lines)), 1)},
        "hashes": {"corpus_sha256": hashlib.sha256(
            "\n".join(lines).encode()).hexdigest()},
    }


def diff_manifests(a, b):
    """Structural difference between two training programs.

    Run this before spending compute: if two arms differ only in fields
    that cannot affect learning, the comparison is not worth a GPU."""
    out = {}
    for field_ in ["exposures", "surface", "cooccurrence", "shortcut",
                   "dependency_violations", "tokens"]:
        if a.get(field_) != b.get(field_):
            out[field_] = {"a": a.get(field_), "b": b.get(field_)}
    out["same_equivalence_class"] = (a["equivalence_key_sha"] ==
                                     b["equivalence_key_sha"])
    out["same_corpus"] = (a["hashes"]["corpus_sha256"] ==
                          b["hashes"]["corpus_sha256"])
    return out


# --- what 'best' means --------------------------------------------------

# ONE primary objective for Milestone B (spec §19). Optimising a vague
# weighted score is what would let a curriculum look good by trading away
# something we care about, so the primary endpoint is single and named,
# and everything else is explicitly secondary.
PRIMARY_OBJECTIVE = (
    "sample_efficiency",
    f"exposures required to reach 0.80 held-out competence on "
    f"'{W.TARGET_NODE}' (fewer is better)", -1)

SECONDARY_OBJECTIVES = [
    ("final_competence", "target-task accuracy at the end of training", +1),
    ("compositional_generalization", "target accuracy on a held-out world",
     +1),
    ("retention", "accuracy on early concepts at the end of training", +1),
    ("strategy_stability", "1 - variance of the strategy index", +1),
    ("shortcut_reliance", "cue agreement on eval_conflict", -1),
]

OBJECTIVES = [PRIMARY_OBJECTIVE] + SECONDARY_OBJECTIVES


def objective_vector(result):
    """The primary endpoint plus its secondaries, never averaged.
    `pareto` is for later reporting; the Milestone B decision rests on
    the primary objective alone."""
    return {name: result.get(name) for name, _, _ in OBJECTIVES}


def pareto(rows):
    """Non-dominated set over whichever objectives every row reports.

    Objectives absent from the data are skipped rather than treated as
    ties or as missing-and-therefore-incomparable; a run that has not
    been scored on retention should not thereby become non-dominated.
    """
    signs = {n: s for n, _, s in OBJECTIVES}
    live = [n for n in signs
            if rows and all(r.get(n) is not None for r in rows)]
    if not live:
        raise ValueError("no objective is reported by every row")

    def dominates(x, y):
        if any(signs[n] * x[n] < signs[n] * y[n] for n in live):
            return False
        return any(signs[n] * x[n] > signs[n] * y[n] for n in live)

    return [r for r in rows
            if not any(dominates(o, r) for o in rows if o is not r)]


# --- artifact writing ---------------------------------------------------

def write_program(outdir, graph=None, curriculum=None, seed=0,
                  eval_world_seed=None):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    lines, records, manifest = compile_curriculum(graph, curriculum, seed)
    (out / "curriculum.txt").write_text("\n".join(lines) + "\n")
    for name, items in W.eval_sets(seed).items():
        (out / f"{name}.jsonl").write_text(
            "\n".join(json.dumps(r) for r in items) + "\n")
    if eval_world_seed is not None:
        held = W.eval_sets(eval_world_seed)
        (out / "eval_heldout_world.jsonl").write_text(
            "\n".join(json.dumps(r) for r in held["eval_id"]) + "\n")
        manifest["heldout_world_seed"] = eval_world_seed
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir")
    ap.add_argument("--policy", default="topological")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--survey", action="store_true",
                    help="compare the baseline policies without training")
    args = ap.parse_args()

    G = W.default_graph()
    by_name = {p(G).name.split("-")[0]: p for p in BASELINE_POLICIES}

    if args.survey:
        print(f"{'policy':<18}{'lines':>9}{'tokens':>11}"
              f"{'viol':>6}{'class':>10}")
        rows = []
        for pol in BASELINE_POLICIES:
            cur = pol(G, args.seed)
            cur.scale = args.scale
            _, _, m = compile_curriculum(G, cur, args.seed)
            rows.append(m)
            print(f"{m['curriculum']['name']:<18}"
                  f"{m['exposures']['total']:>9,}"
                  f"{m['tokens']['whitespace_tokens']:>11,}"
                  f"{len(m['dependency_violations']):>6}"
                  f"{m['equivalence_key_sha'][:8]:>10}")
        print("\nexposures per atomic fact (topological):")
        print(" ", json.dumps(rows[0]["exposures"]["mean_per_atomic_fact"]))
        print("atomic facts in the world:",
              rows[0]["facts"]["atomic_total"])
    else:
        pol = by_name.get(args.policy, policy_topological)
        cur = pol(G, args.seed)
        cur.scale = args.scale
        if args.outdir:
            m = write_program(args.outdir, G, cur, args.seed,
                              eval_world_seed=args.seed + 100)
        else:
            _, _, m = compile_curriculum(G, cur, args.seed)
        print(json.dumps(m, indent=1)[:1400])
