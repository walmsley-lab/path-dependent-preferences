"""Playwright tests for the guided workbench (the classic workbench, served at /lab/classic).

Walks the guided rail as a user would: framing renders -> meet an agent ->
ordinary question -> conflict on the SAME scenario -> cue removed -> free
exploration. Requires local model artifacts (any runs/*/ + data dir with
manifest + eval sets); skips cleanly when absent.

Run:  .venv/bin/pytest tests/test_workbench.py -q
"""

import json
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

PORT = 8199
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


def test_api_contract(server):
    import urllib.request
    runs = json.load(urllib.request.urlopen(f"{server}/api/runs"))
    assert runs and {"run", "run_id", "commit", "ckpts"} <= set(runs[0])
    ds = json.load(urllib.request.urlopen(f"{server}/api/datasets"))
    assert ds and "data" in ds[0]
    corpus = json.load(urllib.request.urlopen(
        f"{server}/api/corpus?data={ds[0]['data']}"))
    assert corpus["agents"], "agent lambda map must be exposed"


def test_framing_before_interaction(server, page):
    page.goto(server + "/lab/classic")
    body = page.locator("body").inner_text()
    assert "same evidence" in body and "order" in body.lower()
    assert "ROUTE A" in body and "ROUTE B" in body
    assert "UTILITY" in body and "CUE" in body
    # The honest-labels note ships with the page, not as an afterthought.
    assert "never the model explaining itself" in body


def test_guided_rail(server, page):
    page.goto(server + "/lab/classic")
    page.wait_for_function(
        "document.getElementById('setup-status').textContent === 'ready'")

    # Step 1: meet an agent — authored lambda appears with its meaning.
    page.click("#btn-meet")
    assert "authored" in page.locator("#result").inner_text()
    assert page.locator(".lam").count() == 1

    # Step 2: ordinary question — identification-problem interpretation.
    page.click("[data-step='1']")
    page.click("#btn-id")
    page.wait_for_selector(".model-card")
    interp = page.locator(".interp").inner_text()
    assert "how" in interp and "disagree" in interp

    # Step 3: conflict on the SAME scenario — routes must disagree.
    page.click("[data-step='2']")
    page.click("#btn-cf")
    page.wait_for_selector(".model-card")
    says = page.locator(".saysrow").inner_text()
    assert "UTILITY →" in says and "CUE →" in says
    result = page.locator("#result").inner_text()
    assert "behavior matches" in result

    # Step 4: cue removed — no cue present in the route row.
    page.click("[data-step='3']")
    page.click("#btn-nc")
    page.wait_for_selector(".model-card")
    assert "no cue present" in page.locator(".saysrow").inner_text()

    # Step 5: free exploration exists with all four sets.
    page.click("[data-step='4']")
    for btn in ("#x-id", "#x-cf", "#x-nc", "#x-co"):
        assert page.locator(btn).count() == 1
    page.click("#x-co")
    page.wait_for_selector(".model-card")


def test_same_scenario_is_preserved(server, page):
    """The pedagogy depends on steps 2-4 sharing ONE scenario."""
    page.goto(server + "/lab/classic")
    page.wait_for_function(
        "document.getElementById('setup-status').textContent === 'ready'")
    page.click("[data-step='1']")
    page.click("#btn-id")
    page.wait_for_selector(".model-card")
    prompt_id = page.locator(".scenario .prompt").inner_text()
    agent = prompt_id.split()[0]
    page.click("[data-step='2']")
    page.click("#btn-cf")
    page.wait_for_selector(".model-card")
    prompt_cf = page.locator(".scenario .prompt").inner_text()
    assert prompt_cf.split()[0] == agent, "conflict must reuse the scenario"
    # payoff numbers survive the counterfactual re-render
    nums = [t for t in prompt_id.replace(".", " ").split() if
            t.lstrip("-").isdigit()]
    nums_cf = [t for t in prompt_cf.replace(".", " ").split() if
               t.lstrip("-").isdigit()]
    assert nums == nums_cf, "payoffs must be identical across re-render"
