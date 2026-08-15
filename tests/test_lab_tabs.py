"""Behavioral coverage for EVERY instrument tab on the bench (/lab/bench).

One test per instrument family; each clicks the actual tray button and
asserts the canvas renders that instrument's real content — live
inference badges where inference is live, honest pending text where
records don't exist, epistemic language where the design laws require it.

Run:  .venv/bin/pytest tests/test_lab_tabs.py -q
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

PORT = 8196
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


def bench(page, server):
    page.goto(server + "/lab/bench")
    page.wait_for_selector("body[data-ready]", timeout=30000)
    page.evaluate(
        "document.querySelectorAll('details.fam').forEach(d=>d.open=true)")


def canvas(page):
    return page.locator("#canvas").inner_text()


# ---- OBSERVE ---------------------------------------------------------------

def test_tab_behavior_modes(server, page):
    bench(page, server)
    for inst, cap in [("ordinary", "ID"), ("conflict", "CONFLICT"),
                      ("nocue", "NOCUE"), ("cueonly", "CUEONLY")]:
        page.click(f"[data-inst='{inst}']")
        page.wait_for_selector("#canvas >> text=LIVE MODEL INFERENCE",
                               timeout=60000)
        page.wait_for_selector(".trace .meter", timeout=60000)
        assert cap in canvas(page)
        assert page.locator("#tile-refresh").count() == 1


def test_tab_compose(server, page):
    bench(page, server)
    page.click("[data-inst='custom']")
    page.wait_for_selector("#crun", timeout=30000)
    body = canvas(page)
    assert "COMPOSE A SCENARIO" in body
    assert "closed vocabulary" in body


def test_tab_freeform_continue_and_refusal(server, page):
    bench(page, server)
    page.click("[data-inst='freeform']")
    page.wait_for_selector("#ffrun", timeout=30000)
    assert "EXPLORE FREELY" in canvas(page)
    # live continuation renders under explicit PROMPT / RESPONSE labels
    page.click("#ffrun")
    page.wait_for_selector("#ffout >> text=RESPONSE", timeout=120000)
    page.wait_for_selector(
        "#ffout >> text=what the organism expects the world to say next",
        timeout=120000)
    out = page.locator("#ffout").inner_text()
    assert "PROMPT" in out
    # closed-world refusal, framed as design rather than limitation
    page.fill("#fftext", "purple banana xylophone")
    page.click("#ffrun")
    page.wait_for_selector(
        "#ffout >> text=OUTSIDE THIS ORGANISM", timeout=60000)
    out = page.locator("#ffout").inner_text()
    assert "banana" in out and "closed" in out.lower()
    assert "Why is the world closed?" in out


def test_tab_corpus_reader(server, page):
    bench(page, server)
    page.click("[data-inst='corpus']")
    page.wait_for_selector("#canvas >> text=WHAT THE LEARNER SAW",
                           timeout=30000)
    body = canvas(page)
    assert "SAME EXPERIENCES" in body
    assert "You know more" in body
    # open a slice: real typed lines appear
    slice_btns = page.locator("#canvas button:has-text('first pages')")
    if slice_btns.count():
        slice_btns.first.click()
        page.wait_for_selector("#canvas >> text=actual training lines",
                               timeout=30000)


# ---- LOCATE ----------------------------------------------------------------

def test_tab_trajectory(server, page):
    bench(page, server)
    page.click("[data-inst='trajectory']")
    page.wait_for_selector(
        "#canvas >> text=when does behavior change", timeout=60000)
    assert page.locator("#canvas svg circle").count() >= 3
    assert "chance" in canvas(page)


def test_tab_atlas_with_cell_inspection(server, page):
    bench(page, server)
    page.click("[data-inst='atlas']")
    page.wait_for_selector(
        "#canvas >> text=DEVELOPMENTAL ACTIVATION ATLAS", timeout=30000)
    body = canvas(page)
    assert "identity floor" in body
    cells = page.locator(".mtx td[onclick]")
    if cells.count():
        cells.first.click()
        page.wait_for_selector("#atlascell >> text=behavior at this age",
                               timeout=60000)


def test_tab_probes(server, page):
    bench(page, server)
    page.click("[data-inst='probes']")
    page.wait_for_selector("#canvas >> text=REPRESENTATION",
                           timeout=60000)
    body = canvas(page)
    assert "Identity confound" in body
    assert "recoverable" in body


# ---- COMPARE ---------------------------------------------------------------

def test_tab_constellation(server, page):
    bench(page, server)
    page.click("[data-inst='constellation']")
    page.wait_for_selector("#canvas >> text=EXPLORATORY VIEW",
                           timeout=60000)
    body = canvas(page)
    assert "does not establish semantic or causal identity" in body
    # real artifacts on this bench: scatter + CKA + weight space render
    assert page.locator("#canvas svg circle").count() > 50
    assert "TWIN SIMILARITY" in body
    assert "WEIGHT SPACE" in body


def test_tab_diffmap(server, page):
    bench(page, server)
    page.click("[data-inst='diffmap']")
    page.wait_for_selector("#canvas >> text=TWIN DIFFERENCE MAP",
                           timeout=30000)
    body = canvas(page)
    assert "EXPLORATORY" in body
    assert "a place to LOOK, not a finding" in body


# ---- PERTURB ---------------------------------------------------------------

def test_tab_causal_triad(server, page):
    bench(page, server)
    page.click("[data-inst='causal']")
    page.wait_for_selector("#canvas >> text=PERTURB · STEERING",
                           timeout=60000)
    body = canvas(page)
    assert "Prediction (stated before the result)" in body
    assert "ABLATE" in body and "PATCH" in body
    # the audited failure is displayed, never narrated away
    assert "AUDITED VERDICT" in body or "no patching record" in body


def test_tab_transplant_pending(server, page):
    bench(page, server)
    page.click("[data-inst='transplant']")
    page.wait_for_selector("#canvas >> text=DEVELOPMENTAL TRANSPLANT",
                           timeout=30000)
    body = canvas(page)
    assert "PENDING" in body and "optimizer" in body
    assert "swap parts of their developmental state" in body


# ---- TRACE -----------------------------------------------------------------

def test_tab_execution_trace(server, page):
    bench(page, server)
    page.click("[data-inst='exectrace']")
    page.wait_for_selector("#canvas >> text=EXECUTION TRACE",
                           timeout=60000)
    body = canvas(page)
    assert ("IMPLICATED STAGES ONLY" in body or
            "will not draw a graph" in body)
    if "IMPLICATED STAGES ONLY" in body:
        assert "logit" in body.lower() or "lens" in body.lower()


# ---- FORMALIZE -------------------------------------------------------------

def test_tab_formalize_edges(server, page):
    bench(page, server)
    page.click("[data-inst='formal']")
    page.wait_for_selector("#canvas >> text=CANDIDATE FORMALIZATION",
                           timeout=60000)
    body = canvas(page)
    assert "λ" in body and "choice" in body
    assert "evidence vectors" in body
    # evidence + provenance chain revealed behind the edge click
    page.click("#canvas .reading >> nth=0")
    body = canvas(page)
    assert "commit" in body and "until" in body


def test_tab_worldmodels_all_graphs(server, page):
    bench(page, server)
    page.click("[data-inst='worldmodels']")
    page.wait_for_selector("#canvas >> text=G_generator", timeout=30000)
    assert "PRIVILEGED GROUND TRUTH" in canvas(page)
    page.click("#canvas button:has-text('Observational')")
    page.wait_for_selector("#canvas >> text=G_observational",
                           timeout=30000)
    assert "cue_prediction" in canvas(page)
    # Development now carries its first hypothesis-generating candidates
    page.click("#canvas button:has-text('Development')")
    page.wait_for_selector("#canvas >> text=G_development", timeout=30000)
    dev = canvas(page)
    assert "route stability" in dev
    assert "replication" in dev and "absent" in dev
    assert "something the next experiment has to earn" in dev
    for pending in ("Mechanism", "Overlay"):
        page.click(f"#canvas button:has-text('{pending}')")
        page.wait_for_selector("#canvas >> text=PENDING", timeout=30000)
        assert "will not be drawn" in canvas(page)
        page.click("#canvas button:has-text('Generator')")
        page.wait_for_selector("#canvas >> text=G_generator",
                               timeout=30000)


# ---- the drawer ------------------------------------------------------------

def test_tab_beyond_doors(server, page):
    bench(page, server)
    page.click("#beyond")
    page.wait_for_selector("#canvas >> text=BEYOND THIS EXPERIMENT",
                           timeout=30000)
    body = canvas(page)
    for door in ("ABSORB A CORPUS", "IMPORT A BRAIN",
                 "EMBODY THE COMPUTATION"):
        assert door in body
    assert body.count("LOCKED") >= 3
