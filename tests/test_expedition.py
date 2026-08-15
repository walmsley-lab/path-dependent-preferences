"""Playwright tests for the Expedition (served at /).

The design laws under test (docs/expedition_design.md):
 1. the cover reveals nothing the reader has not yet earned — no lambda,
    no routes, no curriculum labels before their discovery moments;
 2. chapter 1 is predict-before-reveal science: guess two observations,
    commit a hypothesis, test it on two withheld pages, and the authored
    ground truth appears only behind an explicit reveal;
 3. chapter 3 re-reads the SAME field notes (payoffs identical) and only
    lights the planted verbs after "Show me what I missed";
 4. chapter 4 constructs a real conflict counterfactual (same payoffs,
    reworded) and reports the live model's answer as behavior-matching
    language, never mechanism language.

Run:  .venv/bin/pytest tests/test_expedition.py -q
"""

import re
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

PORT = 8198
BASE = f"http://localhost:{PORT}"

JARGON = ["Route A", "Route B", "C1", "C2", "conflict set",
          "cue", "λ", "lambda"]


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
    page.goto(server)
    page.wait_for_selector("#setup-ready", timeout=30000)


def set_slider(page, sel, value):
    page.locator(sel).evaluate(
        "(el, v) => { el.value = v; el.dispatchEvent(new Event('input')); }",
        value)


def walk_chapter1(page):
    """Guess both observations, commit the authored value, pass both tests."""
    page.click("#begin")
    page.wait_for_selector("#guess0 button")
    page.click("#guess0 [data-g='1']")
    page.wait_for_selector("#guess1 button")
    page.click("#guess1 [data-g='1']")
    page.wait_for_selector("#hypbox:not(.hidden)")
    lam = page.evaluate("window.STATE.lam")
    set_slider(page, "#lamslider", round((1 - lam) * 100))
    page.click("#commit")
    page.wait_for_selector("#hyppred2 button")
    page.click("#hyppred2 button")
    page.wait_for_selector("#hyppred3 button")
    page.click("#hyppred3 button")
    page.wait_for_selector("#survived:not(.hidden)")
    page.click("#revealauthored")
    page.wait_for_selector("#truthbox:not(.hidden)")


def walk_to_ch3(page):
    walk_chapter1(page)
    page.click("#toch2")
    page.click("#meetlearner")
    page.click("#newsit")
    for _ in range(8):
        page.wait_for_selector("[data-guess='1']:not([disabled])",
                               timeout=60000)
        page.click("[data-guess='1']")
        page.wait_for_selector("#modelanswer .meter")
        if page.locator("#toch3:visible").count():
            break
        page.click("#retry")
    page.click("#toch3")
    page.wait_for_selector("#fieldnotes2 .note")


def test_cover_reveals_nothing_unearned(server, page):
    ready(page, server)
    visible = page.locator("body").inner_text()
    for term in JARGON:
        assert term not in visible, f"cover leaks unearned concept: {term}"
    # the cover copy is FROZEN (docs/expedition_design.md) — if this
    # fails, someone edited four sentences that were doing a remarkable
    # amount of narrative work; put them back
    assert "We built a small world." in visible
    assert "We know exactly how their world was constructed." in visible
    assert "But pretend, for a moment, that you don" in visible


def test_chapter1_is_predict_commit_test(server, page):
    ready(page, server)
    page.click("#begin")
    page.wait_for_selector("#fieldnotes .note")
    # only ONE observation is shown before the reader commits a guess
    assert page.locator("#fieldnotes .note").count() == 1
    # the choice stamp is hidden until the reader guesses
    assert page.locator("#stamp0.hidden").count() == 1
    page.click("#guess0 [data-g='2']")
    assert page.locator("#stamp0:not(.hidden)").count() == 1
    # honest feedback names the reader's wrong guess without punishment
    page.wait_for_selector("#guess1 button")
    page.click("#guess1 [data-g='1']")
    # hypothesis slider appears only after two observed decisions
    page.wait_for_selector("#hypbox:not(.hidden)")
    # lambda has not been named anywhere yet
    assert "λ" not in page.locator("body").inner_text()
    lam = page.evaluate("window.STATE.lam")
    set_slider(page, "#lamslider", round((1 - lam) * 100))
    page.click("#commit")
    # withheld tests show the hypothesis prediction BEFORE the reveal
    page.wait_for_selector("#hyppred2 button")
    assert "YOUR HYPOTHESIS PREDICTS" in \
        page.locator("#hyppred2").inner_text()
    page.click("#hyppred2 button")
    page.wait_for_selector("#hyppred3 button")
    page.click("#hyppred3 button")
    page.wait_for_selector("#survived:not(.hidden)")
    # identification band honesty ships with the success moment
    assert "band, not a point" in page.locator("#fitband").inner_text()
    # ground truth appears ONLY behind the explicit reveal
    assert page.locator("#truthbox:not(.hidden)").count() == 0
    page.click("#revealauthored")
    page.wait_for_selector("#truthbox:not(.hidden)")
    assert "λ = " + str(lam) in page.locator("#eqbox").inner_text()
    assert "WORLD GROUND TRUTH" in page.locator("#truthbox").inner_text()


def test_ch3_same_notes_delayed_highlight_then_ch4_conflict(server, page):
    ready(page, server)
    walk_to_ch3(page)
    # chapter 3 re-reads the SAME notes: payoffs identical to chapter 1
    # (chapter 1 splits them across the observed and withheld-test panels)
    nums = re.findall(r"[+-]\d+",
                      page.locator("#fieldnotes").inner_text() +
                      page.locator("#testnotes").inner_text())
    nums2 = re.findall(r"[+-]\d+", page.locator("#fieldnotes2").inner_text())
    assert nums == nums2, "chapter 3 must re-read the SAME field notes"
    # verbs are NOT highlighted until the reader asks
    assert page.locator("#fieldnotes2 .cueword").count() == 0
    page.click("#searchbtn")
    page.wait_for_selector("#cuereveal:not(.hidden)")
    assert page.locator("#fieldnotes2 .cueword").count() >= 4
    nb = page.locator("#notebook").inner_text()
    assert "H1" in nb and "H2" in nb
    # identification language, not mechanism language
    assert "OBSERVATIONALLY EQUIVALENT" in \
        page.locator("#cuereveal").inner_text()

    # chapter 4: the discriminating counterfactual, live
    page.click("#toch4")
    page.click("#buildcf")
    page.wait_for_selector("#cfresult:not(.hidden)", timeout=60000)
    u = page.locator("#upred").inner_text()
    c = page.locator("#cpred").inner_text()
    assert u != c, "the two rules must disagree on the counterfactual"
    page.click("#askcf")
    page.wait_for_selector("#cfanswer:not(.hidden)")
    assert "behavior matches" in page.locator("#cfanswer").inner_text()
    # one anecdote -> the stored aggregate, with as-though language
    page.click("#aggbtn")
    page.wait_for_selector("#aggafter:not(.hidden)", timeout=30000)
    assert "Behaves as though" in page.locator("#aggafter").inner_text()
    # chapter 5: pending module is honest; the three-age teaser runs live
    page.click("#toch5")
    assert "we will not show you invented results" in \
        page.locator("#ch5").inner_text()
    page.click("#devbtn")
    page.wait_for_selector("#tooutro:not(.hidden)", timeout=120000)
    assert page.locator("#devout .meter").count() >= 3
    page.click("#tooutro")
    # embodiment is foreshadowed, never explained, in the Expedition
    assert "neuromorphic" not in page.locator("body").inner_text().lower()
    assert page.locator("#embod").count() == 1


def test_embodiment_lives_in_the_lab(server, page):
    """The two dragons live inside the Lab's Formalization instrument."""
    page.goto(server + "/lab")
    page.wait_for_selector("body[data-ready]", timeout=30000)
    page.click("[data-inst='formal']")
    page.click("text=COMPILE")
    assert "UNDER CONSTRUCTION" in page.locator("#dragon-neuro").inner_text()
    page.click("text=IMPORT")
    brain = page.locator("#dragon-brain").inner_text()
    assert "COMING SOON" in brain
    assert "wiring diagram is not yet a brain" in brain


def test_progress_survives_reload(server, page):
    """Returning from a technique note or reloading must NEVER restart
    the exercise (progress persists in localStorage)."""
    ready(page, server)
    walk_chapter1(page)
    page.reload()
    page.wait_for_selector("#setup-ready", timeout=30000)
    assert "Resume" in page.locator("#begin").inner_text()
    page.click("#begin")
    page.wait_for_selector("#truthbox:not(.hidden)", timeout=30000)
    assert page.locator("#fieldnotes .note").count() == 2
    assert page.locator("#testnotes .note").count() == 2
    # explicit reset exists and works
    page.click("#startover")
    page.wait_for_selector("#setup-ready", timeout=30000)
    assert "Resume" not in page.locator("#begin").inner_text()
