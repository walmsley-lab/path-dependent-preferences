"""Behavioral tests for the graph editor (/lab/graph).

The properties under test are the frozen design commitments, not
cosmetics:
 1. all four graphs render with the shape vocabulary;
 2. line style encodes epistemic status — candidate edges are dashed,
    causal edges solid, and no edge renders as causal without a causal
    evidence entry;
 3. positions are STABLE across developmental age: changing the age
    changes edge state, never node coordinates;
 4. the Edge Laboratory opens an edge's evidence vector, its limits,
    its next discriminating test, and its provenance;
 5. the frontier ranks unresolved edges and never ranks authored ones;
 6. no experiment can be launched from this page.

Run:  .venv/bin/pytest tests/test_graph.py -q
"""

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HAVE_ARTIFACTS = any(ROOT.glob("runs/*/run_manifest.json")) and \
    any(ROOT.glob("d*/**/manifest.json"))

pytestmark = pytest.mark.skipif(
    not HAVE_ARTIFACTS,
    reason="no local run/data artifacts (run the reproduction ladder first)")

PORT = 8195
BASE = f"http://localhost:{PORT}"


@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen(
        [sys.executable, "serve_api.py", "--port", str(PORT),
         "--device", "cpu"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            with socket.create_connection(("localhost", PORT), timeout=1):
                break
        except OSError:
            time.sleep(0.5)
    yield BASE
    proc.terminate()
    proc.wait(timeout=10)


def graph(page, server, kind=None):
    page.goto(server + "/lab/graph")
    page.wait_for_selector("body[data-ready]", timeout=30000)
    if kind:
        page.click(f"[data-kind='{kind}']")
        page.wait_for_timeout(700)


def test_all_four_graphs_render(server, page):
    graph(page, server)
    for kind, marker in [("generator", "PRIVILEGED GROUND TRUTH"),
                         ("observational", "OBSERVATIONAL STRUCTURE"),
                         ("development", "CANDIDATE STRUCTURE"),
                         ("mechanism", "EXPERIMENTALLY INFERRED")]:
        page.click(f"[data-kind='{kind}']")
        page.wait_for_timeout(600)
        assert page.locator("#canvas").count() == 1
        assert page.locator(".gnode").count() >= 4
        assert page.locator(".gedge").count() >= 3
        assert marker in page.locator("#graphwrap").inner_text()


def test_shape_vocabulary_is_used(server, page):
    """Node semantics are carried by shape, not by color alone."""
    graph(page, server, "generator")
    # rounded rects (observed), a dashed rect (latent λ), a hexagon
    # (computation), a diamond (comparison)
    assert page.locator(".gnode rect").count() >= 3
    assert page.locator(".gnode rect[stroke-dasharray]").count() >= 1
    assert page.locator(".gnode polygon").count() >= 2
    graph(page, server, "mechanism")
    assert page.locator(".gnode ellipse").count() >= 2   # learned states


def test_line_style_encodes_epistemic_status(server, page):
    """Candidate edges are dashed; causal edges are solid and thicker;
    nothing renders as causal without causal evidence."""
    graph(page, server, "mechanism")
    spec = page.evaluate("window.GRAPHSTATE.graph")
    statuses = [e["status"] for e in spec["edges"]]
    assert "candidate" in statuses and "causal" in statuses

    for i, e in enumerate(spec["edges"]):
        if e["status"] == "causal":
            assert e["evidence"].get("causal", {}).get("supported") is True, \
                "an edge rendered causal without supporting causal evidence"
        if e["status"] == "candidate":
            assert not e["evidence"].get("causal", {}).get("supported")

    # the rendered stroke matches the status
    dashes = page.eval_on_selector_all(
        ".gedge path:not(.hit)",
        "els => els.map(e => ({d: e.getAttribute('stroke-dasharray'),"
        " w: e.getAttribute('stroke-width')}))")
    assert any(d["d"] for d in dashes), "no dashed (candidate) edge drawn"
    assert any(not d["d"] for d in dashes), "no solid (causal) edge drawn"


def test_positions_are_stable_across_developmental_age(server, page):
    """The signature commitment: age changes STATE, never layout."""
    graph(page, server, "mechanism")
    before = page.eval_on_selector_all(
        ".gnode rect, .gnode ellipse, .gnode polygon",
        "els => els.map(e => e.getAttribute('x') || e.getAttribute('cx')"
        " || e.getAttribute('points'))")
    status_before = page.evaluate(
        "window.GRAPHSTATE.graph.edges.map(e => e.status)")

    page.locator("#age").evaluate(
        "el => { el.value = 20; el.dispatchEvent(new Event('input'));"
        " el.dispatchEvent(new Event('change')); }")
    page.wait_for_timeout(1500)

    after = page.eval_on_selector_all(
        ".gnode rect, .gnode ellipse, .gnode polygon",
        "els => els.map(e => e.getAttribute('x') || e.getAttribute('cx')"
        " || e.getAttribute('points'))")
    assert before == after, "node positions moved when the age changed"
    assert "20%" in page.locator("#agelbl").inner_text()

    # and the evidence really was re-read at the new age
    note = page.evaluate(
        "window.GRAPHSTATE.graph.edges[0].evidence.representational.note")
    assert "age 20%" in note
    status_after = page.evaluate(
        "window.GRAPHSTATE.graph.edges.map(e => e.status)")
    assert isinstance(status_after, list) and len(status_after) == \
        len(status_before)


def test_edge_laboratory_opens_evidence_and_provenance(server, page):
    graph(page, server, "mechanism")
    # the λ-state → choice edge carries the full campaign
    idx = page.evaluate(
        "window.GRAPHSTATE.graph.edges.findIndex("
        "e => e.src === 'lam_state' && e.dst === 'choice')")
    assert idx >= 0
    page.evaluate(f"pickEdge({idx})")
    lab = page.locator("#edgelab").inner_text()
    assert "lam_state → choice" in lab
    for section in ["BEHAVIORAL", "CAUSAL", "NECESSITY", "PORTABILITY",
                    "REPLICATION"]:
        assert section in lab, f"missing evidence dimension: {section}"
    # the refuted clauses are shown, not hidden
    assert "NOT uniquely" in lab or "not uniquely" in lab
    assert "did not transfer" in lab
    # provenance chain and the next discriminating test
    assert "↳" in lab and "evidence_steering.json" in lab
    assert "NEXT DISCRIMINATING TEST" in lab


def test_frontier_ranks_unresolved_edges_only(server, page):
    graph(page, server)
    rows = page.locator(".frontier .row")
    assert rows.count() >= 3
    text = page.locator("#frontier").inner_text()
    assert "authored" not in text.lower(), \
        "the frontier must not rank privileged authored edges"
    import urllib.request
    import json as _j
    data = _j.load(urllib.request.urlopen(server + "/api/frontier"))
    vals = [r["value"] for r in data]
    assert vals == sorted(vals, reverse=True), "frontier is not ranked"
    assert all(r["status"] not in ("authored", "replicated") for r in data)


def test_design_experiment_specifies_but_does_not_launch(server, page):
    graph(page, server, "mechanism")
    idx = page.evaluate(
        "window.GRAPHSTATE.graph.edges.findIndex(e => e.next_test)")
    page.evaluate(f"pickEdge({idx})")
    page.click("text=Design experiment")
    lab = page.locator("#edgelab").inner_text()
    assert "EXPERIMENT SPECIFICATION (DRAFT)" in lab
    assert "matched controls required" in lab
    assert "No experiment launches from this page" in lab


def test_generator_shows_the_planted_edge_direction(server, page):
    """The generator graph must show choice → framing, not the reverse."""
    graph(page, server, "generator")
    spec = page.evaluate("window.GRAPHSTATE.graph")
    pairs = {(e["src"], e["dst"]) for e in spec["edges"]}
    assert ("choice", "framing") in pairs
    assert ("framing", "choice") not in pairs


def test_development_nodes_are_acquired_states_not_schedules(server, page):
    """A training phase is something we manipulate, not something the
    model acquired. An edge from "early phase composition" to
    "acquisition" is close to tautological — of course the early phase
    precedes what comes later — and it crowds out the claims that would
    actually be informative."""
    graph(page, server, "development")
    spec = page.evaluate("window.GRAPHSTATE.graph")
    labels = " ".join(n["label"].lower() for n in spec["nodes"])
    for schedule_word in ["phase composition", "shared tail", "exposure",
                          "curriculum", "schedule"]:
        assert schedule_word not in labels, \
            f"'{schedule_word}' is a control parameter, not an acquired state"
    # the schedule still exists — as a timeline layer, not as nodes
    assert spec["control_layer"]["phases"]
    assert "manipulated, not acquired" in spec["control_layer"]["label"]


def test_no_development_edge_claims_more_than_precedence(server, page):
    """Phase A never manipulated composition, so nothing here has earned
    a developmental status. Leaving them candidate is the accurate
    report."""
    graph(page, server, "development")
    spec = page.evaluate("window.GRAPHSTATE.graph")
    assert spec["edges"], "no candidate edges at all"
    for e in spec["edges"]:
        assert e["status"] == "candidate", (e["src"], e["dst"], e["status"])
        assert not e["evidence"].get("causal", {}).get("supported")
        assert e["next_test"], f"{e['src']}->{e['dst']} has no discriminating test"
        assert "fork" in e["next_test"].lower(), \
            "a developmental claim is earned by forking matched learners"


def test_development_nodes_separate_availability_from_acquisition(server,
                                                                  page):
    """Available in the corpus, acquired by the model, and
    developmentally depended upon are three different facts."""
    graph(page, server, "development")
    spec = page.evaluate("window.GRAPHSTATE.graph")
    keys = [set(n) for n in spec["nodes"]]
    assert all("available_at" in k and "acquired_at" in k for k in keys)
