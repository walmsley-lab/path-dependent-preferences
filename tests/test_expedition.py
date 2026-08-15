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
    page.click("#hidenums")
    page.wait_for_selector("#numless:not(.hidden)")


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
    # hide-the-numbers: payoffs vanish, the wording pattern remains
    assert page.locator("#fieldnotes2 .payoff").count() == 0
    assert page.locator("#fieldnotes2 .cueword").count() >= 4
    assert "You can throw the payoffs" in \
        page.locator("#numless").inner_text()
    page.click("#searchbtn")
    page.wait_for_selector("#cuereveal:not(.hidden)")
    assert "We put it there" in page.locator("#cuereveal").inner_text()
    nb = page.locator("#notebook").inner_text()
    assert "H1" in nb and "H2" in nb
    # identification language, not mechanism language
    assert "OBSERVATIONALLY INDISTINGUISHABLE ON THE TRAINING" in \
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
    """The three doors live behind 'Beyond this experiment', as locked
    destinations."""
    page.goto(server + "/lab/bench")
    page.wait_for_selector("body[data-ready]", timeout=30000)
    page.click("#beyond")
    body = page.locator("#canvas").inner_text()
    assert "ACT II · LOCKED" in body and "FINAL DRAGON · LOCKED" in body
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


FIND_FAILING_COMMIT = """
() => {
  const P = window.STATE.obs.map(o => o.record);
  const pred = (l, r) => {
    const a = l*r.d_self_1 + (1-l)*r.d_other_1;
    const b = l*r.d_self_2 + (1-l)*r.d_other_2;
    return a >= b ? 1 : 2;
  };
  for(let s = 0; s <= 100; s += 5){
    const l = 1 - s/100;
    const fit2 = [0,1].every(i => pred(l, P[i]) === P[i].utility_answer);
    const fit4 = [0,1,2,3].every(i => pred(l, P[i]) === P[i].utility_answer);
    if(fit2 && !fit4) return s;
  }
  return null;
}
"""


def test_revision_loop_is_reachable_and_guided(server, page):
    """A hypothesis that honestly fits the two seen notes can FAIL the
    withheld tests — and revision names the dissenters and the direction."""
    ready(page, server)
    page.click("#begin")
    page.wait_for_selector("#guess0 button")
    page.click("#guess0 [data-g='1']")
    page.wait_for_selector("#guess1 button")
    page.click("#guess1 [data-g='1']")
    page.wait_for_selector("#hypbox:not(.hidden)")
    v = page.evaluate(FIND_FAILING_COMMIT)
    assert v is not None, \
        "note set must allow a committable-but-wrong hypothesis"
    set_slider(page, "#lamslider", v)
    page.click("#commit")
    page.wait_for_selector("#hyppred2 button")
    page.click("#hyppred2 button")
    page.wait_for_selector("#hyppred3 button")
    page.click("#hyppred3 button")
    page.wait_for_selector("#revisebox:not(.hidden)")
    text = page.locator("#revisebox").inner_text()
    assert "Revise it" in text
    # directional guidance appears once the reader moves
    lam = page.evaluate("window.STATE.lam")
    set_slider(page, "#lamslider2", 100 - round((1 - lam) * 100))
    report = page.locator("#fitreport2").inner_text()
    assert ("move toward" in report or "balance point" in report
            or "agree" in report)
    set_slider(page, "#lamslider2", round((1 - lam) * 100))
    page.wait_for_selector("#survived:not(.hidden)")


def test_every_button_and_walkback(server, page):
    """Full-flow audit: every control on the main path works, technique
    links resolve, and the reader can walk back where it is meaningful."""
    import urllib.request
    ready(page, server)
    walk_to_ch3(page)
    # ch2 walk-back: after a CORRECT answer another situation is offered
    assert page.locator("#retry:visible").count() == 1
    page.click("#searchbtn")
    page.click("#toch4")
    page.click("#buildcf")
    page.wait_for_selector("#cfresult:not(.hidden)", timeout=60000)
    # derivations are present, not bare assertions
    assert "The numbers did not move" in page.locator("#uwhy").inner_text()
    assert "wording rule" in page.locator("#cwhy").inner_text()
    page.click("#askcf")
    page.click("#aggbtn")
    page.wait_for_selector("#aggafter:not(.hidden)", timeout=30000)
    page.click("#toch5")
    page.click("#devbtn")
    page.wait_for_selector("#tooutro:not(.hidden)", timeout=120000)
    page.click("#tooutro")
    # every technique link on the page resolves
    hrefs = page.eval_on_selector_all(
        "a.tech", "els => els.map(e => e.getAttribute('href'))")
    assert hrefs, "technique callouts must exist"
    for href in set(hrefs):
        code = urllib.request.urlopen(server + href).getcode()
        assert code == 200, f"technique link broken: {href}"
    # raw-record drawers open
    page.click("#fieldnotes details summary >> nth=0")
    assert "Q:" in page.locator("#fieldnotes details >> nth=0").inner_text()
    # the enigma is present but unexplained
    assert page.locator("#embod").get_attribute("title")
    assert "neuromorphic" not in page.locator("body").inner_text().lower()
