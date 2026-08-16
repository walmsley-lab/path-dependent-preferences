"""The Experimental Design Contract must refuse bad experiments.

A preflight that passes everything is decoration. These tests construct
the specific mistakes we are positioned to make and check that each one
is caught: counting checkpoints as replicates, evaluating on the worlds
the search already saw, conflating adaptive and fixed schedules, and
letting arms differ in something nobody declared.

Run:  .venv/bin/pytest test_design.py -q
"""

import json

import pytest

import b0_design as B0
import curriculum as C
import design as D
import odyssey_world as W
from odyssey_adapter import OdysseyWorld

WORLD = OdysseyWorld()


@pytest.fixture(autouse=True)
def isolated_ledger(tmp_path, monkeypatch):
    """Never touch the real ledger from a test."""
    monkeypatch.setattr(D, "LEDGER", tmp_path / "worlds_used.json")


def ok_contract(**over):
    c = B0.pilot_contract()
    for k, v in over.items():
        setattr(c, k, v)
    return c


def test_the_pilot_contract_passes_its_own_preflight():
    c = B0.pilot_contract()
    manifests = list(B0.compile_arms(c.world_seeds[0], scale=0.1).values())
    assert D.preflight(c, manifests) == []


def test_world_tiers_are_disjoint():
    """'Held out' is only meaningful if the partition is real."""
    seen = set()
    for name, seeds in D.TIERS.items():
        assert not (seen & set(seeds)), f"{name} overlaps another tier"
        seen |= set(seeds)


def test_confirmatory_test_is_refused_on_worlds_the_search_saw():
    """The firewall: a policy chosen against observed outcomes is a
    hyperparameter, and reporting it on the same worlds measures the
    search rather than the curriculum."""
    worlds = D.CONFIRMATORY_WORLDS[:4]
    c = B0.confirmatory_contract(15, 4, 2, "from pilot sd")
    assert D.preflight(c, []) == []          # clean before the search

    D.record_use(worlds[:2], "searched")
    problems = D.preflight(c, [])
    assert any("already seen" in p for p in problems), problems


def test_confirmatory_test_must_use_the_confirmatory_tier():
    c = B0.confirmatory_contract(15, 4, 2, "from pilot sd")
    c.world_seeds = D.DEVELOPMENT_WORLDS[:4]
    problems = D.preflight(c, [])
    assert any("outside the confirmatory tier" in p for p in problems)


def test_confirmatory_test_requires_a_frozen_analysis_plan():
    c = B0.confirmatory_contract(15, 4, 2, "from pilot sd")
    c.estimand = ""
    c.power_rationale = ""
    problems = D.preflight(c, [])
    assert any("no estimand" in p for p in problems)
    assert any("no power_rationale" in p for p in problems)


def test_checkpoints_cannot_be_declared_experimental_units():
    c = ok_contract(experimental_unit="each checkpoint is one observation")
    problems = D.preflight(c, [])
    assert any("repeated measures" in p for p in problems), problems


def test_both_world_and_model_seed_must_be_random_factors():
    """Generalising over worlds and over initialisations are two
    different claims and cannot be collapsed into 'five seeds'."""
    c = ok_contract()
    c.random = [f for f in c.random if f.name != "world_seed"]
    problems = D.preflight(c, [])
    assert any("world_seed must be declared a random factor" in p
               for p in problems)


def test_mastery_gating_cannot_claim_matched_exposure():
    """Unequal exposure is the treatment in an adaptive schedule;
    declaring both confuses two different causal questions."""
    c = ok_contract(schedule_class="mastery-gated", exposure_matched=True)
    problems = D.preflight(c, [])
    assert any("cannot hold exposure matched" in p for p in problems)

    c2 = ok_contract(schedule_class="mastery-gated", exposure_matched=False)
    assert not any("cannot hold exposure matched" in p
                   for p in D.preflight(c2, []))


def test_arms_differing_in_an_undeclared_factor_are_refused():
    graph = WORLD.schema()
    a = C.policy_topological(graph); a.scale = 0.1
    b = C.policy_topological(graph); b.scale, b.cue_mode = 0.1, "off"
    _, _, ma = C.compile_curriculum(WORLD, a, 0)
    _, _, mb = C.compile_curriculum(WORLD, b, 0)
    problems = D.preflight(ok_contract(), [ma, mb])
    assert any("shortcut prevalence" in p or "cue mode" in p
               for p in problems), problems


def test_unmatched_exposure_budget_is_refused_when_declared_matched():
    graph = WORLD.schema()
    a = C.policy_topological(graph); a.scale = 0.1
    b = C.policy_topological(graph); b.scale = 0.2
    _, _, ma = C.compile_curriculum(WORLD, a, 0)
    _, _, mb = C.compile_curriculum(WORLD, b, 0)
    problems = D.preflight(ok_contract(), [ma, mb])
    assert any("exposure matched" in p for p in problems), problems


def test_arms_that_compile_identically_are_refused():
    """If the declared manipulation produced the same corpus, the run
    would answer nothing."""
    graph = WORLD.schema()
    a = C.policy_topological(graph); a.scale = 0.1
    _, _, ma = C.compile_curriculum(WORLD, a, 0)
    problems = D.preflight(ok_contract(), [ma, dict(ma)])
    assert any("identical corpus" in p for p in problems)


def test_arms_must_share_the_same_fact_pool():
    graph = WORLD.schema()
    a = C.policy_topological(graph); a.scale = 0.1
    _, _, m0 = C.compile_curriculum(WORLD, a, 0)
    _, _, m1 = C.compile_curriculum(WORLD, a, 7)   # different world
    problems = D.preflight(ok_contract(), [m0, m1])
    assert any("fact pool" in p or "different world seeds" in p
               for p in problems), problems


def test_construct_contracts_must_control_every_confound_they_list():
    c = ok_contract()
    c.constructs[0].known_confounds = ["a", "b", "c"]
    c.constructs[0].controls = ["only one"]
    problems = D.preflight(c, [])
    assert any("confounds but" in p for p in problems)


def test_every_measured_node_declares_its_construct():
    """Hu's lesson: we observe behaviour and infer a construct, so the
    account of what else could produce that behaviour is part of the
    design, not commentary on it."""
    for node in ("recognition", "judgment", WORLD.target_node):
        assert node in WORLD.constructs, node
        c = WORLD.constructs[node]
        assert c["known_confounds"] and c["controls"]
        assert len(c["controls"]) >= len(c["known_confounds"])


def test_diagnostics_are_forced_choice_not_generation():
    """Direct measurement, per Hu & Levy (2023): our models are small,
    which is exactly the regime where generation-based prompts penalise
    a competence the model actually has."""
    ev = WORLD.target_eval(0, n=6)
    for items in ev.values():
        for r in items:
            assert r["scoring"] == "forced_choice"
            assert r["answer"] in r["options"]
            assert len(r["options"]) >= 2
            assert r["prompt"].rstrip().endswith("A:")


def test_assert_ready_raises_and_names_the_violations():
    c = ok_contract(experimental_unit="each checkpoint is an observation")
    with pytest.raises(D.DesignError) as e:
        D.assert_ready(c)
    assert "design violation" in str(e.value)


def test_a_frozen_contract_is_never_edited_in_place(tmp_path):
    c = B0.pilot_contract()
    p = D.freeze(c, tmp_path)
    body = json.loads(p.read_text())
    assert body["contract_sha"] == c.sha()
    with pytest.raises(D.DesignError):
        D.freeze(c, tmp_path)
