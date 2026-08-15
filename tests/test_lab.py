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
    page.goto(server + "/lab")
    page.wait_for_selector("body[data-ready]", timeout=30000)


def test_lab_opens_as_an_instrument_room(server, page):
    ready(page, server)
    body = page.locator("body").inner_text()
    assert "Choose a specimen and an instrument." in body
    assert "SPECIMEN BENCH" in body and "INSTRUMENTS" in body
    # no tutorial prose — the story lives in the Expedition
    assert "ROUTE A" not in body and "ROUTE B" not in body
    # specimen identity card is populated
    assert "curriculum:" in page.locator("#cardA").inner_text()
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
    page.click("[data-graph='mechanism']")
    assert "will not be drawn before" in page.locator("#canvas").inner_text()
    page.click("[data-graph='generating']")
    page.wait_for_selector("text=G_authored")
    assert "KNOWN BECAUSE WE WROTE IT" in \
        page.locator("#canvas").inner_text()


def test_evidence_ledger_rows_open(server, page):
    ready(page, server)
    page.click(".evrow >> nth=2")
    detail = page.locator(".evdetail >> nth=2").inner_text()
    assert "does not establish" in detail and "next:" in detail
