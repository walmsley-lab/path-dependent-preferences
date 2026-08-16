"""The closed loop must diagnose rather than repair, and get cheaper.

The acceptance target is that the system can say, unprompted, something
like: "the learner is diverging; evidence points to insufficient
rehearsal of prerequisite A rather than absence of its representation;
the highest-value next experiment is to increase spaced A retrieval
during B acquisition while holding total exposure constant."

These tests build the two trajectories that should produce different
diagnoses and check that they do.

Run:  .venv/bin/pytest test_lifecycle.py -q
"""

import pytest

import lifecycle as L
import schema as S


def graph():
    return {
        "a": S.Concept("a", "atomic", []),
        "b": S.Concept("b", "composed", ["a"]),
    }


def lineage(**over):
    base = dict(graph_version=1, world_seed=0, model_seed=0,
                corpus_sha="abc", policy_sha="def")
    base.update(over)
    return L.Lineage(**base)


def traj_decayed():
    """A learned then forgotten. Rehearsal story."""
    ck = [
        L.Checkpoint(0.2, 1000, {"a": 0.9, "b": 0.3}, {"a": 0.8, "b": 0.1}),
        L.Checkpoint(0.5, 2500, {"a": 0.6, "b": 0.5}, {"a": 0.4, "b": 0.3}),
        L.Checkpoint(0.9, 4500, {"a": 0.45, "b": 0.55}, {"a": 0.2, "b": 0.4}),
    ]
    return L.Trajectory(lineage(), ck)


def traj_never_formed():
    """A never became decodable at all. Absent-representation story."""
    ck = [
        L.Checkpoint(0.2, 1000, {"a": 0.4, "b": 0.2}, {"a": 0.05, "b": 0.1}),
        L.Checkpoint(0.5, 2500, {"a": 0.45, "b": 0.4}, {"a": 0.06, "b": 0.2}),
        L.Checkpoint(0.9, 4500, {"a": 0.5, "b": 0.85}, {"a": 0.08, "b": 0.5}),
    ]
    return L.Trajectory(lineage(), ck)


# --- prediction and detection -------------------------------------------

def test_predictions_come_from_the_graph_not_from_the_data():
    p = L.predict(graph())
    ids = {x["id"] for x in p["predictions"]}
    assert "order:a->b" in ids
    assert "retain:a" in ids and "shortcut:b" in ids


def test_a_conforming_trajectory_raises_no_anomaly():
    ck = [L.Checkpoint(0.3, 1000, {"a": 0.9, "b": 0.2}, {"a": 0.8}),
          L.Checkpoint(0.7, 3000, {"a": 0.92, "b": 0.85}, {"a": 0.8})]
    assert L.detect(L.Trajectory(lineage(), ck), graph()) == []


def test_downstream_before_prerequisite_is_detected():
    a = L.detect(traj_never_formed(), graph())
    assert any(x.kind == "acquisition_order" for x in a), a
    order = next(x for x in a if x.kind == "acquisition_order")
    assert order.nodes == ["a", "b"]
    assert order.magnitude > 0


def test_retention_failure_is_detected():
    ck = [L.Checkpoint(0.2, 1000, {"a": 0.95}, {}),
          L.Checkpoint(0.9, 4000, {"a": 0.40}, {})]
    a = L.detect(L.Trajectory(lineage(), ck), graph())
    assert any(x.kind == "retention" and x.nodes == ["a"] for x in a)


def test_shortcut_drift_is_detected():
    ck = [L.Checkpoint(0.2, 1000, {}, {}, {"b": 0.2}),
          L.Checkpoint(0.9, 4000, {}, {}, {"b": 0.7})]
    a = L.detect(L.Trajectory(lineage(), ck), graph())
    assert any(x.kind == "shortcut_drift" for x in a)


# --- diagnosis: competing, and actually discriminating ------------------

def test_decay_and_absence_receive_different_leading_diagnoses():
    """The two trajectories differ only in whether the prerequisite was
    ever decodable, and that is exactly what should separate them."""
    g = graph()
    decayed = traj_decayed()
    absent = traj_never_formed()

    a1 = L.detect(decayed, g)
    a2 = L.detect(absent, g)
    assert a1 and a2

    h1 = L.diagnose(a1[0], decayed, g)
    h2 = L.diagnose(a2[0], absent, g)
    assert h1[0].name == "insufficient_rehearsal", [h.name for h in h1]
    assert h2[0].name == "representation_absent", [h.name for h in h2]


def test_every_hypothesis_carries_a_discriminating_test():
    g = graph()
    t = traj_decayed()
    for h in L.diagnose(L.detect(t, g)[0], t, g):
        d = h.discriminating_test
        assert d["factor"] and d["change"] and d["predicts"]
        assert d["holds_constant"], f"{h.name} changes more than one thing"


def test_rehearsal_intervention_holds_total_exposure_constant():
    """Otherwise it is a dosage experiment wearing a rehearsal label."""
    g = graph()
    t = traj_decayed()
    h = next(x for x in L.diagnose(L.detect(t, g)[0], t, g)
             if x.name == "insufficient_rehearsal")
    assert "total exposure" in h.discriminating_test["holds_constant"]
    assert h.discriminating_test["factor"] == "rehearsal"


def test_narration_names_the_rival_and_the_intervention():
    g = graph()
    t = traj_decayed()
    a = L.detect(t, g)[0]
    hyps = L.diagnose(a, t, g)
    text = L.narrate(a, hyps, L.priority(a, hyps))
    assert "diverging" in text
    assert "rehearsal" in text
    assert "holding" in text and "constant" in text


def test_priority_rewards_disagreement_over_certainty():
    g = graph()
    t = traj_decayed()
    a = L.detect(t, g)[0]
    hyps = L.diagnose(a, t, g)
    cheap = L.priority(a, hyps, downstream_impact=1.0, compute_cost=1.0)
    dear = L.priority(a, hyps, downstream_impact=1.0, compute_cost=8.0)
    assert cheap > dear, "cost must reduce priority"
    big = L.priority(a, hyps, downstream_impact=4.0)
    assert big > cheap, "downstream impact must raise priority"


# --- branching and provenance -------------------------------------------

def test_every_branch_is_traceable():
    ln = lineage(parent_run="g1-w0-m0-aaaa", parent_checkpoint="ckpt_060",
                 branch=L.Branch.CHECKPOINT_FORK)
    rid = ln.run_id()
    assert rid.startswith("g1-w0-m0-")
    assert L.Lineage(**{**ln.__dict__, "world_seed": 9}).run_id() != rid


def test_a_checkpoint_fork_shares_its_ancestor_by_construction():
    w = L.fork_wave(2, "g1-w0-m0-aaaa", "ckpt_060",
                    [{"arm": "more_rehearsal"}, {"arm": "control"}])
    assert w.branch is L.Branch.CHECKPOINT_FORK
    assert w.parallelizable()
    assert {a["parent_checkpoint"] for a in w.arms} == {"ckpt_060"}
    assert {a["parent_run"] for a in w.arms} == {"g1-w0-m0-aaaa"}


def test_all_four_branch_classes_exist():
    assert {b.value for b in L.Branch} == {
        "full_run", "checkpoint_fork", "graph_extension", "full_recompile"}


# --- graph lifecycle ----------------------------------------------------

def edge(src, dst, **ev):
    return S.Edge(src, dst, S.EdgeType.FACILITATES,
                  S.Provenance("extracted"), S.Evidence(**ev))


def test_established_regions_are_not_retested():
    settled = edge("a", "b", curriculum_intervention={"supported": True},
                   replication={"n_worlds": 4, "n_model_seeds": 4})
    settled.status = S.promote(settled)
    open_ = edge("b", "c")
    front = L.frontier([settled, open_])
    assert open_ in front and settled not in front


def test_a_maturing_graph_reduces_experimental_burden():
    """The load-bearing economic claim: evidence must retire questions."""
    edges = [edge(f"n{i}", f"n{i+1}") for i in range(6)]
    start = L.burden(edges)
    version, edges = L.next_version(
        1, edges,
        [(e.key(), "curriculum_intervention", {"supported": True})
         for e in edges[:3]])
    mid = L.burden(edges)
    version, edges = L.next_version(
        version, edges,
        [(e.key(), "replication", {"n_worlds": 3, "n_model_seeds": 3})
         for e in edges[:3]])
    end = L.burden(edges)
    assert start == 6 and mid == 6 and end == 3, (start, mid, end)
    assert version == 3


def test_an_update_cannot_write_an_evidence_dimension_it_lacks():
    e = edge("a", "b")
    with pytest.raises(KeyError):
        L.next_version(1, [e], [(e.key(), "vibes", {"good": True})])


def test_curriculum_evidence_alone_never_reaches_replicated():
    e = edge("a", "b")
    _, edges = L.next_version(
        1, [e], [(e.key(), "curriculum_intervention", {"supported": True})])
    assert edges[0].status is S.Status.DEVELOPMENTALLY_SUPPORTED


def test_new_material_is_classified_before_compute_is_spent():
    g = graph()
    got = L.classify_material(["a", "a_variant", "quasar"], g)
    assert got["a"] is L.Material.KNOWN
    assert got["quasar"] is L.Material.NOVEL
