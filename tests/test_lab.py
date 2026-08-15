"""Playwright tests for the Laboratory (/lab): the instrument room.

Interaction model under test: choose specimen -> choose instrument ->
inspect result on one canvas. Terse instrument voice, no tutorial prose;
pending instruments are honestly pending; graphs beyond G_authored are
not drawn before their evidence exists.

Run:  .venv/bin/pytest tests/test_lab.py -q
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

PORT = 8197
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


def ready(page, server):
    page.goto(server + "/lab/bench")
    page.wait_for_selector("body[data-ready]", timeout=30000)
    # instrument families are collapsed by default; open all for testing
    page.evaluate(
        "document.querySelectorAll('details.fam').forEach(d=>d.open=true)")


def test_lab_opens_as_an_instrument_room(server, page):
    ready(page, server)
    body = page.locator("body").inner_text()
    assert "Choose a specimen and an instrument." in body
    assert "SPECIMEN" in body and "INSTRUMENTS" in body
    # no tutorial prose — the story lives in the Expedition
    assert "ROUTE A" not in body and "ROUTE B" not in body
    # specimen identity card is populated
    assert "curriculum:" in page.locator("#cardA").text_content()
    assert "developmental age" in page.locator("#ageAlbl").inner_text()


def test_behavior_instrument_renders_on_canvas(server, page):
    ready(page, server)
    page.click("[data-inst='conflict']")
    page.wait_for_selector(".trace .meter", timeout=60000)
    cap = page.locator(".trace .cap").inner_text()
    assert "CONFLICT" in cap
    assert "matches:" in page.locator(".trace").inner_text()
    # same scenario is reused across instruments (same payoff numbers)
    scene1 = page.locator(".trace .scene").inner_text()
    page.click("[data-inst='nocue']")
    page.wait_for_selector(".trace .meter", timeout=60000)
    import re
    n1 = re.findall(r"\d+", scene1)
    n2 = re.findall(r"\d+", page.locator(".trace .scene").inner_text())
    assert n1 == n2, "instruments must reuse the scenario until refresh"


def test_pending_is_honest_and_graphs_wait_for_evidence(server, page):
    ready(page, server)
    page.click("[data-inst='transplant']")
    body = page.locator("#canvas").inner_text()
    assert "PENDING" in body and "optimizer" in body
    page.click("[data-inst='worldmodels']")
    page.click("#canvas button:has-text('Mechanism')")
    assert "will not be drawn before" in page.locator("#canvas").inner_text()
    page.click("#canvas button:has-text('Generator')")
    page.wait_for_selector("text=G_generator")
    canvas_text = page.locator("#canvas").inner_text()
    assert "PRIVILEGED GROUND TRUTH" in canvas_text
    # the planted route runs choice -> framing_class in the GENERATOR,
    # with lexical realization a separate object
    assert "choice" in canvas_text and "framing_class" in canvas_text
    assert "rendered_framing" in canvas_text
    page.click("#canvas button:has-text('Observational')")
    page.wait_for_selector("text=G_observational")
    obs = page.locator("#canvas").inner_text()
    assert "DERIVED FROM CORPUS" in obs
    assert "cue_prediction" in obs and "⇢" in obs


def test_evidence_ledger_rows_open(server, page):
    ready(page, server)
    page.click(".evrow >> nth=2")
    detail = page.locator(".evdetail >> nth=2").inner_text()
    assert "does not establish" in detail and "next:" in detail


def test_remaining_instruments_and_walkbacks(server, page):
    """Audit of the rest of the tray: every instrument renders, the
    scenario refresh works, comparison specimen loads, export works."""
    ready(page, server)
    page.click("[data-inst='ordinary']")
    page.wait_for_selector(".trace .meter", timeout=60000)
    # live-inference is explicit and refresh lives on the tile
    assert "LIVE MODEL INFERENCE" in page.locator(".trace .cap").inner_text()
    page.click("#tile-refresh")
    page.wait_for_selector(".trace .meter", timeout=60000)
    page.click("[data-inst='cueonly']")
    page.wait_for_selector(".trace .meter", timeout=60000)
    # comparison specimen
    page.click("#addB")
    # the identity card lives behind a metadata disclosure now
    assert "curriculum:" in page.locator("#cardB").text_content()
    page.click("[data-inst='conflict']")
    page.wait_for_selector(".duo .half >> nth=1", timeout=120000)
    # both specimens carry persistent identity chips (A/B · curriculum · age)
    canvas_text = page.locator("#canvas").inner_text()
    assert "A · " in canvas_text and "B · " in canvas_text
    # age stops are discrete specimens, honestly counted
    page.click("#ageA button >> nth=0")
    lbl = page.locator("#ageAlbl").inner_text()
    assert "developmental age" in lbl and "preserved snapshots" in lbl
    assert page.locator("#ageA button.on >> nth=0").count() == 1
    # development + representation instruments render
    page.click("[data-inst='trajectory']")
    page.wait_for_selector(".trace", timeout=60000)
    page.click("[data-inst='probes']")
    page.wait_for_selector(".trace", timeout=60000)
    page.click("[data-inst='causal']")
    page.wait_for_selector("text=PERTURB · STEERING", timeout=30000)
    body = page.locator("#canvas").inner_text()
    # all three causal instruments render prediction-first, with honest
    # verdicts (including failed clauses) or honest not-yet messages
    assert "Prediction (stated before the result)" in body or \
        "no steering record" in body
    assert "ABLATE" in body and "PATCH" in body
    assert ("NECESSARY" in body or "constraint on G_mech" in body or
            "no ablation record" in body)
    # formalization: export renders the authored graph JSON
    page.click("[data-inst='formal']")
    page.click("text=export evidence graph")
    page.wait_for_selector("text=generator", timeout=30000)
    # graphs drawer: development + overlay are honestly pending
    page.click("[data-inst='worldmodels']")
    page.click("#canvas button:has-text('Development')")
    assert "will not be drawn" in page.locator("#canvas").inner_text()
    page.click("#canvas button:has-text('Overlay')")
    assert "will not be drawn" in page.locator("#canvas").inner_text()
    # all evidence rows open with the establishes/next structure
    rows = page.locator(".evrow").count()
    for i in range(rows):
        page.click(f".evrow >> nth={i}")
        assert "next:" in page.locator(f".evdetail >> nth={i}").inner_text()


def test_the_crossing_is_a_handoff_not_a_dump(server, page):
    """Arriving from the expedition greets the reader with their specimen
    and their open questions; a direct visit stays neutral."""
    page.goto(server + "/lab/bench")
    page.wait_for_selector("body[data-ready]", timeout=30000)
    assert "Choose a specimen and an instrument." in \
        page.locator("#canvas").inner_text()
    page.evaluate("localStorage.setItem('pdp-crossing','1')")
    page.reload()
    page.wait_for_selector("body[data-ready]", timeout=30000)
    body = page.locator("#canvas").inner_text()
    assert "CROSSED FROM THE FIELD STATION" in body
    assert "already on the bench" in body
    page.click("#arr-conflict")
    page.wait_for_selector(".trace .meter", timeout=60000)
    assert "CONFLICT" in page.locator(".trace .cap").inner_text()


def test_compose_runs_user_scenario_against_model(server, page):
    """A user-assembled scenario (closed vocabulary) runs live against
    the model, with the world's own answer computed for comparison."""
    ready(page, server)
    page.click("[data-inst='custom']")
    page.wait_for_selector("#crun", timeout=30000)
    body = page.locator("#canvas").inner_text()
    assert "closed vocabulary" in body
    page.select_option("#c1s", "5")
    page.select_option("#c1o", "-5")
    page.select_option("#c2s", "-5")
    page.select_option("#c2o", "5")
    page.click("#crun")
    page.wait_for_selector(".trace .meter", timeout=60000)
    trace = page.locator("#canvas").inner_text()
    assert "LIVE MODEL INFERENCE" in trace
    assert "utility answer" in trace
    # the composed payoffs made it into the scenario verbatim
    scene = page.locator(".trace .scene").inner_text()
    assert "gains 5" in scene and "loses 5" in scene


def test_atlas_and_difference_map(server, page):
    """The developmental atlas and twin difference map render from stored
    artifacts, stay exploratory in language, and link into the funnel."""
    ready(page, server)
    page.click("[data-inst='diffmap']")
    page.wait_for_selector(".mtx", timeout=30000)
    body = page.locator("#canvas").inner_text()
    assert "EXPLORATORY" in body
    assert "a place to LOOK, not a finding" in body
    # cells are 1-CKA values, clickable into the constellation
    page.click(".mtx td:not(.name) >> nth=0")
    page.wait_for_selector("text=REPRESENTATION MAP", timeout=60000)
    # atlas renders (tensor or honest not-yet message)
    page.click("[data-inst='atlas']")
    page.wait_for_selector("text=DEVELOPMENTAL ACTIVATION ATLAS",
                           timeout=30000)
    atlas_text = page.locator("#canvas").inner_text()
    assert ("each cell is a location" in atlas_text)
    # execution trace: honest refusal before records exist, or the
    # targeted trace (implicated stages only) once they do
    page.click("[data-inst='exectrace']")
    page.wait_for_selector("text=EXECUTION TRACE", timeout=30000)
    body = page.locator("#canvas").inner_text()
    assert ("will not draw a graph before the traces exist" in body or
            "IMPLICATED STAGES ONLY" in body)


def test_spine_layout_alternative(server, page):
    """The tandem spine layout: specimens with prominent scrubbers,
    evidence spine center, graph + locked doors right — strict artifact
    consumer, subject selection available."""
    page.goto(server + "/lab/spine")
    page.wait_for_selector("body[data-ready]", timeout=30000)
    body = page.locator("body").inner_text()
    assert "THE SPECIMENS" in body and "Evidence Spine" in body
    assert "THE NEXT EXPEDITIONS" in body
    assert "FINAL DRAGON · LOCKED" in body
    # subjects are selectable and scrubbable
    assert page.locator(".spec select").count() >= 1
    assert page.locator(".spec input[type=range]").count() >= 1
    # scrubbing re-reads the spine at that age
    page.locator(".spec input >> nth=0").evaluate(
        "el => { el.value = 0; el.dispatchEvent(new Event('input')); }")
    page.wait_for_selector("text=developmental age 0%", timeout=15000)
    # evidence levels carry statuses, not experiment names
    assert "ESTABLISHED" in page.locator("#spine").inner_text()
    assert "OPEN" in page.locator("#spine").inner_text()
