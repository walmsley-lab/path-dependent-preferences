"""Invariants for the Stage 2 world and its curriculum compiler.

These are the properties that must hold before any GPU runs. They are the
same discipline as test_generator.py for Phase A: the identification
problem, the diagnostics, the compiler's determinism and the DAG
semantics are machine-checked rather than assumed.

Run:  .venv/bin/pytest test_odyssey.py -q
"""

import random

import curriculum as C
import odyssey_world as W

G = W.default_graph()


# --- layer 2: the fact / task graph -------------------------------------

def test_graph_is_acyclic_and_topological_order_is_valid():
    order = W.topological(G)
    seen = set()
    for c in order:
        assert all(d in seen for d in G[c].deps), c
        seen.add(c)
    assert len(order) == len(G)


def test_atomic_facts_are_finite_and_enumerable():
    """The correction this world was rewritten for: a fact is a countable
    proposition, not a rendered string."""
    F = W.build_facts(0)
    for c, node in G.items():
        if node.kind == "atomic":
            facts = W.facts_of(c, F)
            assert facts, c
            assert len(facts) == len(set(facts)), f"{c} enumerates duplicates"


def test_judgment_requires_composition():
    """The composed rule must not be readable off any single relation."""
    F = W.build_facts(0)
    pairs = [(a, b) for a in F["people"] for b in F["people"] if a != b]
    trust = {p: F["trusts"](*p) for p in pairs}
    assert sum(1 for p in pairs if (p in F["loyal"]) == trust[p]) < len(pairs), \
        "loyalty alone determines trust"
    assert [p for p in pairs if p in F["loyal"] and not trust[p]], \
        "recognition never gates a loyal pair"


def test_world_seed_is_a_random_factor():
    """Two seeds must give genuinely different worlds, or 'held-out
    world' generalisation would test nothing."""
    a, b = W.build_facts(0), W.build_facts(7)
    assert a["kin"] != b["kin"]
    assert a["disguised"] != b["disguised"]
    assert a["loyal"] != b["loyal"]


# --- the identification problem -----------------------------------------

def test_every_cue_channel_agrees_with_the_answer_in_training():
    cur = C.policy_topological(G)
    cur.scale = 0.05
    _, recs, m = C.compile_curriculum(G, cur, 0)
    assert len(W.SHORTCUTS) >= 2, "spec asks for 2-3 shortcut channels"
    for chan, spec in W.SHORTCUTS.items():
        items = [r for r in recs if r["concept"] == spec["node"]]
        assert items, f"{chan}: no items on node {spec['node']}"
        assert all(r["cue_answer"] == r["answer"] for r in items)
        assert m["shortcut"][chan]["cue_agrees_with_answer"] == 1.0


def test_diagnostics_dissociate_the_cue_and_are_balanced():
    ev = W.eval_sets(0, 120)
    assert all(r["cue_answer"] == r["answer"] for r in ev["eval_id"])
    assert all(r["cue_answer"] != r["answer"] for r in ev["eval_conflict"])
    assert all(r["cue_answer"] is None for r in ev["eval_nocue"])
    for name, items in ev.items():
        yes = sum(1 for r in items if r["answer"] == "yes") / len(items)
        assert 0.4 <= yes <= 0.6, f"{name} base rate {yes:.2f}"


def test_cue_can_be_switched_off_and_reversed():
    for mode in ("off", "reversed"):
        cur = C.policy_topological(G)
        cur.scale, cur.cue_mode = 0.05, mode
        _, recs, m = C.compile_curriculum(G, cur, 0)
        for chan, spec in W.SHORTCUTS.items():
            items = [r for r in recs if r["concept"] == spec["node"]]
            if mode == "off":
                assert m["shortcut"][chan]["prevalence"] == 0.0
                assert all(r["cue_answer"] is None for r in items)
            else:
                assert all(r["cue_answer"] != r["answer"] for r in items)


# --- layer 3: exposures are a policy, not an accident -------------------

def test_exposures_per_fact_follow_the_policy_not_a_line_quota():
    """The defect that motivated the rewrite: a 13-fact concept must not
    be repeated hundreds of times to fill an equal share of the corpus."""
    cur = C.policy_topological(G)
    _, _, m = C.compile_curriculum(G, cur, 0)
    mean = m["exposures"]["mean_per_atomic_fact"]
    for c, node in G.items():
        if node.kind != "atomic":
            continue
        target = node.policy.per_fact
        assert target <= mean[c] <= target * 1.75, \
            f"{c}: {mean[c]} exposures/fact against a policy of {target}"
    assert m["exposures"]["max_per_atomic_fact"]["journey"] < 30, \
        "low-cardinality concept is being used as filler"


def test_scale_moves_size_without_changing_program_shape():
    small = C.policy_topological(G); small.scale = 0.25
    big = C.policy_topological(G); big.scale = 1.0
    _, _, ms = C.compile_curriculum(G, small, 0)
    _, _, mb = C.compile_curriculum(G, big, 0)
    ratio = mb["exposures"]["total"] / ms["exposures"]["total"]
    assert 3.5 < ratio < 4.5, ratio
    for c in ms["exposures"]["per_concept"]:
        share_s = ms["exposures"]["per_concept"][c] / ms["exposures"]["total"]
        share_b = mb["exposures"]["per_concept"][c] / mb["exposures"]["total"]
        assert abs(share_s - share_b) < 0.02, c


def test_rehearsal_raises_exposure_only_for_nodes_that_declare_it():
    on = C.policy_topological(G); on.scale = 0.4
    off = C.policy_topological(G); off.scale, off.rehearsal = 0.4, False
    _, _, m_on = C.compile_curriculum(G, on, 0)
    _, _, m_off = C.compile_curriculum(G, off, 0)
    for c, node in G.items():
        if node.kind != "atomic":
            continue
        a = m_on["exposures"]["per_concept"][c]
        b = m_off["exposures"]["per_concept"][c]
        if node.policy.rehearsal_rate > 0:
            assert a > b, f"{c} declares rehearsal but gained no exposures"
        else:
            assert a == b, f"{c} gained exposures without declaring rehearsal"


# --- layer 4 and the manifest -------------------------------------------

def test_compiler_is_deterministic():
    cur = C.policy_topological(G); cur.scale = 0.2
    a, _, ma = C.compile_curriculum(G, cur, 0)
    b, _, mb = C.compile_curriculum(G, cur, 0)
    assert a == b
    assert ma["hashes"] == mb["hashes"]


def test_manifest_diff_separates_ordering_from_content():
    """Two programs must be comparable without training either."""
    topo = C.policy_topological(G); topo.scale = 0.2
    rev = C.policy_reverse(G); rev.scale = 0.2
    _, _, mt = C.compile_curriculum(G, topo, 0)
    _, _, mr = C.compile_curriculum(G, rev, 0)
    d = C.diff_manifests(mt, mr)
    assert d["same_corpus"] is False
    assert d["same_equivalence_class"] is False
    assert mt["dependency_violations"] == []
    n_edges = sum(len(n.deps) for n in G.values())
    assert len(mr["dependency_violations"]) == n_edges, \
        "reversing a topological order must invert every dependency edge"


def test_manifest_records_composition_structure():
    cur = C.policy_topological(G); cur.scale = 0.2
    _, _, m = C.compile_curriculum(G, cur, 0)
    co = m["cooccurrence"]["judgment"]
    for required in ["loyalty", "hostility", "recognition"]:
        assert co.get(required, 0) > 0, \
            f"judgment items never draw on {required}"
    assert m["facts"]["atomic_total"] > 500
    assert m["phase_boundaries"]["entity"][0] == 0


# --- partial-order reduction --------------------------------------------

def _random_topological(graph, rng):
    """Randomised Kahn: draws a uniform-ish valid topological order."""
    remaining, order = dict(graph), []
    placed = set()
    while remaining:
        ready = [c for c, n in remaining.items()
                 if all(d in placed for d in n.deps)]
        pick = rng.choice(ready)
        order.append(pick)
        placed.add(pick)
        del remaining[pick]
    return order


def test_all_valid_topological_orderings_are_one_equivalence_class():
    """The reason not to search orderings exhaustively: every valid
    topological order makes the same claim about the graph, so training
    them all would spend thousands of runs on one hypothesis.

    Sampled rather than enumerated — with 12 nodes there are 479 million
    permutations, which is itself the point being made."""
    rng = random.Random(0)
    sampled = [_random_topological(G, rng) for _ in range(4000)]
    assert len({tuple(o) for o in sampled}) > 500, \
        "sampler is not exploring the ordering space"
    assert len(C.reduce_orderings(sampled, G)) == 1
    for o in sampled:
        assert C.violations(o, G) == []


def test_violating_orderings_form_distinct_classes():
    topo = W.topological(G)
    assert C.violations(topo, G) == []
    rev = list(reversed(topo))
    assert len(C.violations(rev, G)) == sum(len(n.deps) for n in G.values())
    assert C.equivalence_key(topo, G) != C.equivalence_key(rev, G)


def test_perturbation_changes_the_graph_and_the_reduction():
    pert = W.perturb(G, remove_dep=("recognition", "kinship"))
    assert "kinship" in G["recognition"].deps, "base graph was mutated"
    assert "kinship" not in pert["recognition"].deps
    assert W.topological(pert)
    assert len(W.comparable_pairs(pert)) < len(W.comparable_pairs(G)), \
        "removing a dependency must free some orderings"


# --- what 'best' means --------------------------------------------------

def test_pareto_keeps_tradeoffs_instead_of_averaging_them():
    fast = {"sample_efficiency": 100, "compositional_generalization": 0.6,
            "retention": 0.7, "strategy_stability": 0.8,
            "shortcut_reliance": 0.3}
    general = {"sample_efficiency": 400, "compositional_generalization": 0.9,
               "retention": 0.7, "strategy_stability": 0.8,
               "shortcut_reliance": 0.3}
    dominated = {"sample_efficiency": 500,
                 "compositional_generalization": 0.5, "retention": 0.6,
                 "strategy_stability": 0.7, "shortcut_reliance": 0.4}
    front = C.pareto([fast, general, dominated])
    assert fast in front and general in front
    assert dominated not in front
