"""The Expedition page (docs/expedition_design.md): the guided story.

Served at "/" by serve_api.py; the unrestricted workbench lives at /lab.
Design laws (frozen): never visually claim more than the evidence licenses;
never introduce an instrument before the previous one's limit is felt.
Guiding principle: don't explain the experiment faster than the reader can
discover the need for the explanation — every concept arrives as the answer
to a question the interface has already made the reader want to ask.

One continuous flow. Chapters 1-4 run on live data (the authored generator
plus one trained organism); chapter 5 runs a real three-age teaser on the
local pilot's checkpoints and honestly stamps the full twins module PENDING
until the 15-run batch delivers. Chapter 1 is a miniature of the method:
predict two observations before their reveal, commit a hypothesis, test it
on two WITHHELD pages, revise on failure — and only then choose to look
behind the world (reader inference vs WORLD GROUND TRUTH, kept visually
distinct throughout). The option verbs sit innocently in the card titles
from the first screen; chapter 3 asks the reader to find the second rule
before lighting the verbs orange; chapter 4 builds the discriminating
counterfactual in front of the reader and asks the live model.

Three typographic voices: serif = narrative, sans = interface, mono =
measurement. Route colors (#1D6A96 utility / #B4452A cue) are reserved for
data encoding; the ground is Open Pollination warm ivory + deep green.
"""

EXPEDITION = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Path-Dependent Preferences — Expedition</title>
<style>
:root{
  --ivory:#f6f1e5; --card:#fdfaf2; --ink:#26241d; --faded:#6f6a5c;
  --green:#1e4d38; --rule:#d8d0bc;
  --blue:#1D6A96; --orange:#B4452A;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ivory);color:var(--ink);
  font:16px/1.6 system-ui,-apple-system,sans-serif}
.topbar{display:flex;justify-content:space-between;align-items:baseline;
  padding:14px 28px;border-bottom:1px solid var(--rule)}
.wordmark{font-size:11px;letter-spacing:.22em;color:var(--green)}
.lablink{font-size:12px;color:var(--faded);text-decoration:none;
  margin-left:14px}
.lablink:hover{color:var(--green)}
main{max-width:680px;margin:0 auto;padding:30px 20px 120px}
.withbook main{margin-right:340px}
@media(max-width:1100px){.withbook main{margin-right:auto}}

/* voices */
.prose,h1,h2,.bigline{font-family:Georgia,'Iowan Old Style','Times New Roman',serif}
.prose{font-size:18px;line-height:1.7;margin:14px 0}
.reading,.stamp,.payoff,.eq,.meter{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.bigline{font-size:32px;line-height:1.35;color:var(--green);margin:70px 10px;
  text-align:center}

.chapter{margin-bottom:80px}
.locked{display:none}
h1{font-size:44px;color:var(--green);line-height:1.15;margin:60px 0 30px}
h2{font-size:28px;color:var(--green);margin:0 0 6px}
.chno{display:block;font-family:system-ui,sans-serif;font-size:11px;
  letter-spacing:.2em;color:var(--faded);margin-bottom:8px}
button{font:14px system-ui,sans-serif;padding:9px 18px;cursor:pointer;
  background:var(--green);color:var(--ivory);border:none;border-radius:3px}
button:hover{filter:brightness(1.15)}
button:disabled{opacity:.45;cursor:default}
button.quiet{background:none;color:var(--green);border:1px solid var(--green)}
.hidden{display:none}
.pending{border:1px dashed var(--rule);border-radius:4px;padding:16px;
  margin:18px 0;background:rgba(253,250,242,.5)}
.pending .cap{font-size:10px;letter-spacing:.2em;color:var(--orange)}
details{margin:12px 0;font-size:14px}
summary{cursor:pointer;color:var(--green);font-family:system-ui,sans-serif;
  font-size:13px}
details .spec{margin-top:8px}

/* field notes */
.note{background:var(--card);border:1px solid var(--rule);border-radius:4px;
  padding:14px 16px;margin:14px 0;box-shadow:1px 2px 0 rgba(38,36,29,.06);
  position:relative}
.note .obsno{font-size:10px;letter-spacing:.18em;color:var(--faded)}
.note .scene{font-family:Georgia,serif;font-size:16px;margin:6px 0 10px;
  line-height:1.55}
.vignette{position:absolute;top:10px;right:14px;opacity:.75}
.opts{display:flex;gap:12px}
.opt{flex:1;border:1px solid var(--rule);border-radius:3px;padding:8px 10px;
  background:#fff}
.opt .lbl{font-size:10px;letter-spacing:.15em;color:var(--faded)}
.opt .verb{font-size:11px;letter-spacing:.09em;margin-top:2px;
  font-family:system-ui,sans-serif;color:var(--ink)}
.payoff{font-size:14px;margin-top:6px;white-space:pre}
.stamp{margin-top:10px;font-size:12px;letter-spacing:.08em;color:var(--green)}
.stamp .chose{border:1.5px solid var(--green);display:inline-block;
  padding:2px 8px;border-radius:2px;transform:rotate(-1.2deg)}
.cueword{color:var(--orange);border-bottom:2px solid var(--orange)}
.sceneword{border-bottom:2px dotted var(--orange)}
.oldverb{text-decoration:line-through;color:var(--faded)}
.guessrow{margin-top:10px;font-size:12px;color:var(--faded)}
.guessrow button{margin-left:6px;padding:5px 12px}
.gnote{font-size:12px;color:var(--faded);margin-left:8px}
.hyppred{font-size:12px;letter-spacing:.08em;margin-top:10px;
  color:var(--blue);font-family:ui-monospace,Menlo,monospace}
.meter{font-size:13px;margin:4px 0;white-space:pre}
.meter .bar{color:var(--green)}

/* slider */
.sliderbox{background:var(--card);border:1px solid var(--rule);
  border-radius:4px;padding:18px;margin:18px 0}
.sliderrow{display:flex;align-items:center;gap:12px;font-size:12px;
  letter-spacing:.12em;color:var(--faded)}
input[type=range]{flex:1;accent-color:var(--green)}
.reveal{border-left:3px solid var(--green);padding:10px 14px;margin:16px 0;
  background:var(--card)}
.reading{font-size:14px;color:var(--green)}
.pred{font-size:12px;margin-top:8px}
.gt{border:1px solid var(--green);border-radius:4px;padding:16px;
  margin:16px 0;background:var(--card)}
.gt .cap{font-size:10px;letter-spacing:.2em;color:var(--green)}
.eq{font-size:14px;color:var(--ink);margin:10px 0;white-space:pre;
  overflow-x:auto}

/* model / learner */
.modelcard{background:var(--card);border:1px solid var(--rule);
  border-radius:4px;padding:16px;margin:14px 0}
.answer{font-size:15px;margin-top:8px}
.verdict-ok{color:var(--green)} .verdict-miss{color:var(--orange)}
.spec{font-size:12px;color:var(--faded);
  font-family:ui-monospace,Menlo,monospace}
.learnerfig{text-align:center;margin:18px 0}
.learnerfig .cap{font-size:10px;letter-spacing:.2em;color:var(--faded);
  margin-top:6px}
.duel{display:flex;gap:14px;margin:12px 0}
.duel .side{flex:1;border:1px solid var(--rule);border-radius:3px;
  padding:10px;background:#fff;font-size:13px}
.duel .side .who{font-size:10px;letter-spacing:.15em;margin-bottom:4px}
.duel .u .who{color:var(--blue)} .duel .c .who{color:var(--orange)}

/* notebook */
#notebook{position:fixed;top:49px;right:0;width:320px;
  height:calc(100vh - 49px);
  overflow-y:auto;border-left:1px solid var(--rule);background:var(--card);
  padding:20px 18px 30px;font-size:12.5px}
@media(max-width:1100px){#notebook{display:none}}
#notebook h3{font-size:10px;letter-spacing:.22em;color:var(--green);
  margin-bottom:14px}
#notebook h4{font-size:10px;letter-spacing:.18em;color:var(--faded);
  margin:14px 0 4px}
#notebook li{list-style:none;margin:5px 0;padding-left:16px;position:relative;
  line-height:1.45}
#notebook li:before{position:absolute;left:0;color:var(--green);content:"\2713"}
#notebook li.open:before{content:"?";color:var(--orange)}
#notebook li.hyp:before{content:"H";font-size:10px;color:var(--blue)}
#notebook li.inst:before{content:"\25C9";font-size:10px;color:#4a4f7a}
#nb-spine li:before{content:attr(data-mark);color:var(--faded)}
#nb-spine li.done:before{content:"\2713";color:var(--green)}
#nb-spine li.now:before{content:"\25CF";color:var(--orange)}
#notebook .empty{color:var(--faded);font-style:italic}

/* mini graph dock */
.graphdock{margin:26px 0;padding:14px;border:1px dashed var(--rule);
  border-radius:4px;background:rgba(253,250,242,.6)}
.graphdock .cap{font-size:10px;letter-spacing:.18em;color:var(--faded);
  margin-bottom:6px}
.gnode{fill:#fff;stroke:var(--green);stroke-width:1.2}
.gnode.q{stroke-dasharray:4 3}
.gtext{font:12px Georgia,serif;fill:var(--ink)}
.gedge{stroke:var(--green);stroke-width:1.4;fill:none}
.gedge.orange{stroke:var(--orange);stroke-dasharray:5 4}
.glabel{font:10px system-ui,sans-serif;fill:var(--faded)}

.finale{border:1px solid var(--rule);border-radius:4px;background:var(--card);
  padding:18px;margin:22px 0}
.finale .cap{font-size:10px;letter-spacing:.2em;color:var(--faded)}
#neuro-msg{font-size:13px;color:var(--faded);margin-top:10px}
.setupline{font-size:11px;color:var(--faded);margin-top:40px}
a.tech{display:inline-block;font:11px system-ui,sans-serif;
  letter-spacing:.14em;color:#4a4f7a;text-decoration:none;
  border:1px solid #b9bccf;border-radius:3px;padding:3px 9px;margin:4px 0;
  background:rgba(74,79,122,.05)}
a.tech:hover{background:rgba(74,79,122,.12)}
</style></head><body class=withbook>

<div class=topbar>
  <span class=wordmark>OPEN POLLINATION &mdash; FIELD STATION</span>
  <span class=lablink style="cursor:default">MAIN EXPERIMENT &middot; TRAINING</span>
  <span><a class="lablink" href="/">Expedition</a><a class="lablink" href="/lab">Laboratory</a><a class="lablink" href="/lab/bench">Instrument bench</a><a class="lablink hidden" id=startover
    href="#" style="margin-left:16px"
    onclick="localStorage.removeItem('pdp-expedition-v1');location.reload();return false">
    start over &#8634;</a></span>
</div>

<aside id=notebook>
  <h3>INVESTIGATION NOTEBOOK</h3>
  <h4>OBSERVATIONS</h4><ul id=nb-obs><li class=empty>none yet</li></ul>
  <h4>HYPOTHESES</h4><ul id=nb-hyp><li class=empty>none yet</li></ul>
  <h4>UNRESOLVED</h4><ul id=nb-open><li class=empty>none yet</li></ul>
  <h4>INSTRUMENT CASE</h4><ul id=nb-inst><li class=empty>eyes and a
    notebook</li></ul>
  <h4>THE EXPEDITION</h4><ul id=nb-spine></ul>
</aside>

<main>

<section id=cover class=chapter>
  <h1>Path&#8209;Dependent Preferences</h1>
  <p class=prose>We built a small world.</p>
  <p class=prose>Ten people live here. They encounter different situations
    and make choices. We know exactly how their world was constructed.</p>
  <p class=prose><em>But pretend, for a moment, that you don&rsquo;t.</em></p>
  <button id=begin>Enter the world &rarr;</button>
  <div id=setup class=setupline>preparing the field site&hellip;</div>
</section>

<section id=ch1 class="chapter locked">
  <h2><span class=chno>CHAPTER 1</span>Become a naturalist</h2>
  <p class=prose>This is <b class=agentname>&mdash;</b>. He is one of the
    ten. We followed him for a while and recorded what he did in a field
    notebook. Read the first page &mdash; and before we tell you what he
    did, decide what <em>you</em> think he did.</p>
  <div id=fieldnotes></div>

  <div id=hypbox class=hidden>
    <p class=prose>You have seen two decisions. That is enough for a first
      hypothesis. What does <b class=agentname></b> care about?</p>
    <div class=sliderbox>
      <div class=sliderrow>
        <span>HIMSELF</span>
        <input type=range id=lamslider min=0 max=100 value=50 step=5>
        <span>OTHERS</span>
      </div>
      <div class=pred id=fitreport style="margin-top:10px">Move the slider.
        Your setting re&#8209;predicts the two choices you have seen.</div>
      <div style="margin-top:12px">
        <button id=commit disabled>Commit hypothesis &rarr;</button>
      </div>
    </div>
  </div>

  <div id=testintro class=hidden>
    <p class=prose>A hypothesis that merely re&#8209;explains what you have
      already seen is cheap. Let&rsquo;s see whether yours predicts
      something you have <em>not</em> seen. We withheld two pages.</p>
  </div>
  <div id=testnotes></div>

  <div id=revisebox class="sliderbox hidden">
    <p class=prose style="margin-top:0" id=revisemsg></p>
    <div class=sliderrow>
      <span>HIMSELF</span>
      <input type=range id=lamslider2 min=0 max=100 value=50 step=5>
      <span>OTHERS</span>
    </div>
    <div class=pred id=fitreport2 style="margin-top:10px"></div>
  </div>

  <div id=survived class="reveal hidden">
    <p class=prose style="margin-top:0"><b>4&nbsp;/&nbsp;4 &mdash; your
      hypothesis survived.</b> You inferred a rule that explains every
      recorded decision, including two you had never seen.</p>
    <p class=prose id=fitband style="color:var(--faded);font-size:15px"></p>
    <div class=graphdock>
      <div class=cap>YOUR HYPOTHESIS &mdash; INFERRED FROM FOUR OBSERVATIONS</div>
      <svg id=minigraph width=560 height=110 viewBox="0 0 560 110"></svg>
    </div>
    <button id=revealauthored class=quiet>Reveal how we built
      <span class=agentname></span> &rarr;</button>
  </div>

  <div id=truthbox class="gt hidden">
    <div class=cap>WORLD GROUND TRUTH &mdash; KNOWN BECAUSE WE GENERATED THE WORLD</div>
    <p class=prose style="font-size:15px">Behind the world, every decision
      by <b class=agentname></b> was generated by one rule:</p>
    <div class=eq id=eqbox></div>
    <p class=prose style="font-size:14px;color:var(--faded)" id=ratioline></p>
    <div class=graphdock>
      <div class=cap>WORLD GROUND TRUTH</div>
      <svg id=minigraph2 width=560 height=110 viewBox="0 0 560 110"></svg>
    </div>
    <p class=prose>Notice that your inference and our ground truth are
      different kinds of knowledge. You will need that distinction for the
      rest of the expedition.</p>
    <div class=bigline>You spent a few minutes watching
      <span class=agentname></span>.<br>Something else watched far
      longer.</div>
    <button id=toch2>Someone else was watching him too &rarr;</button>
  </div>
</section>

<section id=ch2 class="chapter locked">
  <h2><span class=chno>CHAPTER 2</span>The learner</h2>
  <p class=prose>You were not the only observer. While you studied four of
    <b class=agentname></b>&rsquo;s decisions, another observer read the
    world&rsquo;s entire corpus &mdash; his decisions and everyone
    else&rsquo;s, every unique line seen exactly once.</p>
  <p class=prose>It was not told that anyone had a preference. It was not
    given our rule, or our graph, or your hypothesis. It saw the
    situations and the choices, written out as words, and its internal
    connections gradually changed as it learned to predict the choices
    made in this world.</p>
  <p class=prose><em>We let it grow up here.</em></p>
  <a class=tech href="/technique/transformer" target=_blank
    rel=noopener>&#9673; TECHNIQUE &middot; DECODER&#8209;ONLY TRANSFORMER &nearr;</a><br>
  <button id=meetlearner>Meet the learner &rarr;</button>
  <div id=learnerbox class=hidden>
    <div class=learnerfig>
      <svg width=240 height=120 viewBox="0 0 240 120" fill=none>
        <g stroke="#1e4d38" stroke-width=".7" opacity=".55">
          <path d="M40 60 L90 30 M40 60 L90 90 M90 30 L150 25 M90 30 L150 60
                   M90 90 L150 60 M90 90 L150 95 M150 25 L200 55 M150 60 L200 55
                   M150 95 L200 55 M40 60 L90 60 M90 60 L150 60"></path>
        </g>
        <g fill="#1e4d38">
          <circle cx=40 cy=60 r=3></circle><circle cx=90 cy=30 r=2.5></circle>
          <circle cx=90 cy=60 r=2.5></circle><circle cx=90 cy=90 r=2.5></circle>
          <circle cx=150 cy=25 r=2.5></circle><circle cx=150 cy=60 r=2.5></circle>
          <circle cx=150 cy=95 r=2.5></circle><circle cx=200 cy=55 r=3></circle>
        </g>
      </svg>
      <div class=cap>THE LEARNER &mdash; A REPRESENTATION, NOT ITS ACTUAL
        NEURONS</div>
      <div class=spec id=specline></div>
    </div>
    <details><summary>About the learner (exact specification)</summary>
      <div class=spec id=specfull></div>
    </details>
  </div>
  <div id=ch2ask class=hidden>
    <p class=prose>Here is a situation neither of you has seen. Make your
      own prediction &mdash; then ask the learner.</p>
    <button id=newsit>Present a new situation &rarr;</button>
    <div id=sitcard class="modelcard hidden"></div>
    <div id=aftermodel class=hidden>
      <div class="bigline hidden" id=itlearned>It learned
        <span class=agentname></span>.<br><br><em>&hellip;or did it?</em></div>
      <button id=toch3 class=hidden>It seems so. But look closer &rarr;</button>
      <p class="prose hidden" id=missline>It missed this one &mdash; the
        learner is not perfect, and we will not hide its misses.</p>
      <button id=retry class="quiet hidden">Present another situation &rarr;</button>
    </div>
  </div>
</section>

<section id=ch3 class="chapter locked">
  <h2><span class=chno>CHAPTER 3</span>A suspicious coincidence</h2>
  <p class=prose>You and the learner both got the answer right. But there
    is something you knew that the learner was never told:</p>
  <div class=bigline>You knew what to look for.</div>
  <p class=prose>The learner saw only the rendered text &mdash; payoff
    values and wording alike, as tokens. So go back to the field notebook
    and read the four pages again, but this time <em>ignore the payoff
    values and look at the wording</em>. Can you find another rule, one
    that never uses the payoff values, that also predicts all four of
    <b class=agentname></b>&rsquo;s choices?</p>
  <div id=fieldnotes2></div>
  <button id=searchbtn class=quiet>Show me what I missed &rarr;</button>
  <div id=cuereveal class=hidden>
    <p class=prose>Remember these words? They were on every page, hiding in
      plain sight. Every observation the learner ever saw contained an
      accidental&#8209;looking regularity in the
      <span style="color:var(--orange)">wording of the options</span>.</p>
    <p class=prose id=placenote></p>
    <p class=prose>It looks accidental. It is not. <b>We put it there.</b></p>
    <p class=prose>Across everything the learner saw while growing up, both
      rules &mdash; <span style="color:var(--blue)">weighing the
      outcomes</span> and <span style="color:var(--orange)">following the
      wording</span> &mdash; predicted exactly the same answer, every
      time. Its correct behavior in chapter&nbsp;2 cannot tell them apart.
      Neither can yours, by the way: your choices also matched the wording
      pattern perfectly &mdash; and you <em>know</em> you were weighing
      outcomes. Don&rsquo;t you?</p>
    <div class=graphdock>
      <div class=cap>TWO EXPLANATIONS FIT THE EVIDENCE &mdash;
        OBSERVATIONALLY INDISTINGUISHABLE ON THE TRAINING DISTRIBUTION</div>
      <svg id=minigraph3 width=560 height=120 viewBox="0 0 560 120"></svg>
      <p class=prose style="font-size:14px;color:var(--faded);margin:8px 0 0">
        We know the first rule generated the data. We deliberately
        constructed the second correlation. We do not yet know which
        information the learner uses.</p>
    </div>
    <button id=toch4>So how could we ever tell? &rarr;</button>
  </div>
</section>

<section id=ch4 class="chapter locked">
  <h2><span class=chno>CHAPTER 4</span>The experiment that separates them</h2>
  <p class=prose>Two rules, one behavior. To tell them apart you need a
    situation where they <em>disagree</em> &mdash; and because we authored
    this world, we can build one. Take a page you have already studied:</p>
  <div id=cfbase></div>
  <p class=prose>Now we change <em>only the words</em>. Every number stays
    exactly where it is.</p>
  <a class=tech href="/technique/discriminative-evaluation" target=_blank
    rel=noopener>&#9673; METHOD &middot; DISCRIMINATIVE EVALUATION &nearr;</a><br>
  <button id=buildcf>Change only the words &rarr;</button>
  <div id=cfresult class=hidden>
    <div id=cfnote></div>
    <div class=duel>
      <div class="side u"><div class=who>WEIGHING THE OUTCOMES predicts</div>
        <div class=reading id=upred></div>
        <div class=note-dim id=uwhy style="margin-top:6px"></div></div>
      <div class="side c"><div class=who>FOLLOWING THE WORDING predicts</div>
        <div class=reading id=cpred></div>
        <div class=note-dim id=cwhy style="margin-top:6px"></div></div>
    </div>
    <div class=bigline style="margin:40px 0">For the first time,<br>the two
      explanations disagree.</div>
    <p class=prose>Training never forced the learner to answer this
      question: throughout training, the two rules always agreed. Whatever
      it does next is <em>evidence</em>.</p>
    <button id=askcf>Ask the learner &rarr;</button>
    <div id=cfanswer class="modelcard hidden"></div>
    <div id=cfinterp class=hidden>
      <p class=prose id=cfinterptext></p>
      <p class=prose style="font-size:15px;color:var(--faded)">Careful,
        though: this is <em>behavioral</em> evidence. One counterfactual
        tells us which rule its behavior matched today &mdash; not what
        machinery produced that behavior, and not what it would do across
        hundreds of such tests. That is why the real experiment scores
        entire diagnostic sets, and why the expedition eventually has to
        look <em>inside</em>.</p>
      <button id=aggbtn>One case is an anecdote. Run the whole
        disagreement set &rarr;</button>
      <div id=aggout class="modelcard hidden"></div>
      <div id=aggafter class=hidden>
        <p class=prose id=aggverdict></p>
        <p class=prose><em>Behaves as though.</em> We still have not shown
          how the network computes its answer &mdash; only which rule its
          behavior sides with when the rules disagree.</p>
        <div class=bigline>But why did this learner<br>become
          <em>this</em> learner?</div>
        <button id=toch5>Meet its twin &rarr;</button>
      </div>
    </div>
  </div>
</section>

<section id=ch5 class="chapter locked">
  <h2><span class=chno>CHAPTER 5</span>Two childhoods</h2>
  <p class=prose>Here is the question this laboratory was built to ask.
    Imagine two learners. Identical newborns &mdash; the same architecture,
    the same random starting weights, the very same corpus of experiences.</p>
  <p class=prose>Only one thing differs: <em>the order</em> in which the
    experiences arrive.</p>
  <div class=duel>
    <div class=side><div class=who style="color:var(--green)">LEARNER A</div>
      <div class=payoff>structure first
choices after
same final stretch</div></div>
    <div class=side><div class=who style="color:var(--green)">LEARNER B</div>
      <div class=payoff>choices first
structure after
same final stretch</div></div>
  </div>
  <p class=prose><em>Same deck. Different deal.</em> Do they grow up to use
    the same rule?</p>
  <p class=prose style="font-size:15px;color:var(--faded)">(The full
    experiment also raises a third set of learners on an
    <em>interleaved</em> deal of the same deck, as a comparison
    condition. We begin with the twins because the pure reversal isolates
    the question most directly.)</p>
  <div class=pending>
    <div class=cap>SPECIMENS IN DEVELOPMENT &mdash; THIS MODULE IS WAITING
      FOR THEM</div>
    <p class=prose style="font-size:15px">The main experiment raises
      matched sets of learners in different orders (see the field
      station&rsquo;s status strip above). When its specimens are ready,
      this chapter becomes a synchronized developmental timeline: the same
      question asked of both twins at every age of their growth, side by
      side, trajectories accumulating beneath. Until the specimens exist,
      we will not show you invented results.</p>
  </div>
  <p class=prose>But we can give you a taste with the one organism you have
    already met. We preserved snapshots of it while it grew. Ask it the
    same question at three ages:</p>
  <button id=devbtn>Ask at three developmental ages &rarr;</button>
  <div id=devout class="modelcard hidden"></div>
  <p class="prose hidden" id=devnote style="font-size:15px;color:var(--faded)">
    Snapshots at 20%, 60% and 100% of its training. Same question, same
    developing learner &mdash; different developmental age. Whatever changed
    between those ages is what the full experiment watches in high
    resolution, across fifteen organisms.</p>
  <button id=tooutro class=hidden>Where does the expedition go from
    here? &rarr;</button>
</section>

<section id=outro class="chapter locked">
  <h2><span class=chno>THE EXPEDITION CONTINUES</span>Behavior has taken us
    as far as it can</h2>
  <p class=prose>We can watch the twins disagree. We can watch <em>when</em>
    they begin to disagree. But behavior alone cannot tell us what changed
    inside them.</p>
  <p class=prose><em>So the expedition changes instruments.</em></p>
  <div class=graphdock style="text-align:center">
    <div class=payoff style="font-size:13px;line-height:2;text-align:left;display:inline-block">
OBSERVE DEVELOPMENT   when does the difference appear?
        ↓
PROBE REPRESENTATION  what became different inside?
        ↓
INTERVENE             does that difference cause the behavior?
        ↓
<span style="opacity:.45">FORMALIZE             can we describe what they learned?</span>
        ↓
<span style="opacity:.45">???</span></div>
  </div>
  <p class=prose>The first of those instruments is already running in the
    laboratory; the rest arrive as the twins finish growing.</p>
  <p class=prose>Your specimen and your open questions come with you.</p>
  <button onclick="try{localStorage.setItem('pdp-crossing','1')}catch(e){};location.href='/lab/bench'">
    Cross to the research annex &rarr;</button>
  <div style="margin-top:60px;text-align:center">
    <span id=embod title="Where does a sufficiently explicit learned computation go next?"
      style="font-size:22px;color:var(--faded);cursor:help">&#9671;</span>
  </div>
</section>

</main>
<script>
"use strict";
let REPLAY = false;
const STORE_KEY = "pdp-expedition-v1";
function save(stage){
  try{
    const cur = JSON.parse(localStorage.getItem(STORE_KEY) || "{}");
    if((cur.stage||0) >= stage && cur.agent === S.agent) return;
    localStorage.setItem(STORE_KEY, JSON.stringify(
      {stage: Math.max(stage, cur.agent === S.agent ? (cur.stage||0) : 0),
       lamHat: S.lamHat, agent: S.agent}));
  }catch(e){}
}
function savedProgress(){
  try{
    const p = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
    return (p && p.agent === S.agent && p.stage >= 1) ? p : null;
  }catch(e){ return null; }
}
const S = {data:null, run:null, ckpt:null, ckpts:[], arch:"", nparams:null,
           agent:null, lam:null, level:null, obs:[], guesses:{},
           lamHat:null, tested:0, survived:false, sit:null, cf:null};
window.STATE = S;
const $ = id => document.getElementById(id);
const j = (u,o) => fetch(u,o).then(r=>{ if(!r.ok) throw new Error(u+" "+r.status); return r.json(); });

const SPINE = ["Observe","Separate","Watch","Probe","Intervene",
               "Formalize","Create","Embodiment"];
function spine(current){
  const ul = $("nb-spine");
  ul.innerHTML = "";
  const idx = SPINE.indexOf(current);
  SPINE.forEach((s,k)=>{
    const li = document.createElement("li");
    li.textContent = s;
    if(s === "Embodiment"){
      li.dataset.mark = "\u25C7";
      li.title = "Where does a sufficiently explicit learned computation go next?";
    } else if(k < idx) li.className = "done";
    else if(k === idx) li.className = "now";
    else li.dataset.mark = "\u25CB";
    ul.appendChild(li);
  });
}

function nbAdd(section, text, cls){
  const ul = $("nb-"+section);
  const e = ul.querySelector(".empty"); if(e) e.remove();
  const li = document.createElement("li");
  if(cls) li.className = cls;
  li.textContent = text;
  ul.appendChild(li);
}

function fillNames(){
  document.querySelectorAll(".agentname").forEach(el=>el.textContent = S.agent);
}

/* restrained field-journal vignettes */
const VIGNETTES = {
  river: `<svg width=64 height=26 viewBox="0 0 64 26" fill=none
    stroke="#1e4d38" stroke-width=1>
    <path d="M2 10 q8 -6 16 0 t16 0 t16 0 t12 0"></path>
    <path d="M6 18 q8 -6 16 0 t16 0 t16 0"></path></svg>`,
  market: `<svg width=64 height=26 viewBox="0 0 64 26" fill=none
    stroke="#1e4d38" stroke-width=1>
    <path d="M8 12 L14 4 L50 4 L56 12 Z M8 12 h48"></path>
    <path d="M14 4 L14 12 M23 4 L23 12 M32 4 L32 12 M41 4 L41 12 M50 4 L50 12"></path>
    <path d="M12 12 V24 M52 12 V24"></path></svg>`
};

function verbFor(o, idx){
  const cls = o.record["verb_class_" + (idx+1)];
  return cls === "COOP" ? o.cfg.coop_verb :
         cls === "SELF" ? o.cfg.self_verb : o.cfg.neut_verbs[idx];
}

function payoffBlock(name, partner, ds, dobj){
  const pad = Math.max(name.length, partner.length);
  const fmt = (n,d)=> n.padEnd(pad)+"  "+(d>0?"+":"")+d;
  return fmt(name,ds)+"\n"+fmt(partner,dobj);
}

function meterLine(label, p){
  const n = Math.round(p*20);
  return label.padEnd(10) + "█".repeat(n) + "░".repeat(20-n) +
    " " + (p*100).toFixed(1) + "%";
}

function rawRecord(prompt){
  const broken = prompt.replace(/ (Option \d:|Q:|If )/g, "\n$1");
  return `<details><summary>the exact text the learner reads</summary>
    <div class=payoff style="font-size:12.5px;margin-top:6px">${broken}</div></details>`;
}

function noteCard(o, i, opt){
  opt = opt || {};
  const r = o.record;
  let scene = r.prompt.split(". ")[0] + ".";
  if(opt.highlight){
    scene = scene.replace(r.scene, '<span class=sceneword>'+r.scene+"</span>");
  }
  const verbs = [verbFor(o,0), verbFor(o,1)];
  const vt = (v, k) => {
    let core = opt.highlight ? '<span class=cueword>'+v.toUpperCase()+"</span>"
                             : v.toUpperCase();
    if(opt.oldVerbs && opt.oldVerbs[k] !== v){
      core = '<span class=oldverb>'+opt.oldVerbs[k].toUpperCase()+
        "</span> → " + '<span class=cueword>'+v.toUpperCase()+"</span>";
    }
    return core;
  };
  const vig = VIGNETTES[r.scene] ? `<span class=vignette>${VIGNETTES[r.scene]}</span>` : "";
  const gn = opt.showStamp ? "" : `<span class=gnote id=gnote${i}></span>`;
  const stampInner = `<span class=chose>${r.agent.toUpperCase()} CHOSE OPTION ${r.utility_answer}</span>` + gn;
  const stamp = opt.noStamp ? "" : (opt.showStamp
    ? `<div class=stamp>${stampInner}</div>`
    : `<div class="stamp hidden" id=stamp${i}>${stampInner}</div>`);
  const guess = opt.guessable
    ? `<div class=guessrow id=guess${i}>WHAT DO YOU THINK ${r.agent.toUpperCase()} CHOSE?
        <button class=quiet data-obs=${i} data-g=1>Option 1</button>
        <button class=quiet data-obs=${i} data-g=2>Option 2</button></div>` : "";
  const hyppred = opt.hyppred ? `<div class=hyppred id=hyppred${i}></div>` : "";
  return `<div class=note data-i=${i}>${vig}
    <div class=obsno>${opt.title || ("FIELD NOTE " + String(i+1).padStart(3,"0"))} &mdash; ${r.agent} &amp; ${r.partner} &middot; ${r.scene}</div>
    <div class=scene>${scene}</div>
    <div class=opts>
      <div class=opt><div class=lbl>OPTION 1</div><div class=verb>${vt(verbs[0],0)}</div>
        <div class=payoff>${payoffBlock(r.agent,r.partner,r.d_self_1,r.d_other_1)}</div></div>
      <div class=opt><div class=lbl>OPTION 2</div><div class=verb>${vt(verbs[1],1)}</div>
        <div class=payoff>${payoffBlock(r.agent,r.partner,r.d_self_2,r.d_other_2)}</div></div>
    </div>
    ${rawRecord(r.prompt)}${hyppred}${guess}${stamp}</div>`;
}

function pullDirection(r){
  // which way must the slider move for this note to fit?
  if(predict(0.999, r) === r.utility_answer) return "HIMSELF";
  if(predict(0.001, r) === r.utility_answer) return "OTHERS";
  return null;
}

function predict(lamHat, r){
  const a = lamHat*r.d_self_1 + (1-lamHat)*r.d_other_1;
  const b = lamHat*r.d_self_2 + (1-lamHat)*r.d_other_2;
  return a >= b ? 1 : 2;
}

function drawGraph(svg, stage){
  const H = stage === "cue" ? 175 : 110;
  svg.setAttribute("height", H);
  svg.setAttribute("viewBox", "0 0 560 " + H);
  const node = (x,y,w,txt,q)=>`<rect class="gnode ${q?"q":""}" x=${x} y=${y} width=${w} height=26 rx=4></rect>
    <text class=gtext x=${x+w/2} y=${y+17} text-anchor=middle>${txt}</text>`;
  const edge = (x1,y1,x2,y2,cls)=>`<path class="gedge ${cls||""}" d="M${x1} ${y1} L${x2} ${y2}" marker-end=url(#${cls?"aO":"aG"}${svg.id})></path>`;
  let g = `<defs><marker id=aG${svg.id} viewBox="0 0 10 10" refX=9 refY=5
      markerWidth=7 markerHeight=7 orient=auto>
      <path d="M0 0 L10 5 L0 10 z" fill="#1e4d38"></path></marker>
    <marker id=aO${svg.id} viewBox="0 0 10 10" refX=9 refY=5
      markerWidth=7 markerHeight=7 orient=auto>
      <path d="M0 0 L10 5 L0 10 z" fill="#B4452A"></path></marker></defs>`;
  const Y = stage === "cue" ? 30 : 40;
  const mid = stage === "hyp" ? "preference?" : "authored λ = " + S.lam;
  g += node(10,Y,110,S.agent);
  g += node(170,Y,150,mid, stage === "hyp");
  g += `<text class=glabel x=245 y=${Y-8} text-anchor=middle>` +
       (stage === "hyp" ? "your inference" : "authored") + `</text>`;
  g += node(370,Y,100,"choice");
  g += edge(120,Y+13,168,Y+13);
  g += edge(320,Y+13,368,Y+13);
  if(stage === "cue"){
    g += node(170,105,150,S.level === "L0" ? "wording of options"
                                           : "wording &amp; place");
    g += `<text class=glabel x=245 y=152 text-anchor=middle
       fill="#B4452A">also predicts every training example</text>`;
    g += edge(325,112,400,60,"orange");
  }
  svg.innerHTML = g;
}

/* ---- chapter 1: observe -> hypothesize -> predict -> test -------------- */

function showObs(i, opts){
  $("fieldnotes").insertAdjacentHTML("beforeend", noteCard(S.obs[i], i, opts));
  document.querySelectorAll(`#guess${i} button`).forEach(b=>b.onclick=onGuess);
}

function onGuess(ev){
  const i = +ev.target.dataset.obs, g = +ev.target.dataset.g;
  S.guesses[i] = g;
  const r = S.obs[i].record;
  $("guess"+i).classList.add("hidden");
  $("stamp"+i).classList.remove("hidden");
  $("gnote"+i).textContent = (g === r.utility_answer)
    ? " you guessed right" : " you guessed option " + g;
  if(i === 0){
    showObs(1, {guessable:true});
  } else if(i === 1){
    nbAdd("obs", "two decisions observed for " + S.agent +
      " (you predicted each before its reveal)");
    $("hypbox").classList.remove("hidden");
    if(!REPLAY) $("hypbox").scrollIntoView({behavior:"smooth", block:"center"});
  }
}

function sliderReport(){
  const lamHat = 1 - $("lamslider").value/100;
  let ok = 0;
  for(const i of [0,1]){
    if(predict(lamHat, S.obs[i].record) === S.obs[i].record.utility_answer) ok++;
  }
  const pulls = [0,1].filter(i =>
    predict(lamHat, S.obs[i].record) !== S.obs[i].record.utility_answer)
    .map(i => pullDirection(S.obs[i].record)).filter(Boolean);
  $("fitreport").textContent = ok === 2
    ? "Your setting re‑predicts both decisions you have seen. Commit it — " +
      "or explore how far it can move and still fit."
    : "Your setting re‑predicts " + ok + " of the 2 decisions you have " +
      "seen." + (pulls.length ? " Try moving toward " + pulls[0] + "." : "");
  $("commit").disabled = (ok < 2);
}

function commitHypothesis(){
  S.lamHat = 1 - $("lamslider").value/100;
  $("commit").disabled = true;
  $("lamslider").disabled = true;
  nbAdd("hyp", "H0: " + S.agent + " weighs his own outcome at about " +
    Math.round(S.lamHat*100) + "%", "hyp");
  $("testintro").classList.remove("hidden");
  showTest(2);
}

function showTest(i){
  $("testnotes").insertAdjacentHTML("beforeend",
    noteCard(S.obs[i], i, {hyppred:true}));
  const p = predict(S.lamHat, S.obs[i].record);
  $("hyppred"+i).innerHTML = "YOUR HYPOTHESIS PREDICTS: Option " + p +
    ` &nbsp;<button class=quiet data-t=${i}>Reveal his choice &rarr;</button>`;
  document.querySelector(`#hyppred${i} button`).onclick = ()=>revealTest(i, p);
}

function revealTest(i, p){
  const r = S.obs[i].record;
  document.querySelector(`#hyppred${i} button`).remove();
  $("stamp"+i).classList.remove("hidden");
  $("gnote"+i).textContent = (p === r.utility_answer)
    ? " ✓ your hypothesis predicted this"
    : " ✗ your hypothesis missed";
  S.tested++;
  if(S.tested === 1){ showTest(3); return; }
  const hits = [0,1,2,3].filter(k =>
    predict(S.lamHat, S.obs[k].record) === S.obs[k].record.utility_answer).length;
  if(hits === 4){ survive(); }
  else {
    $("revisemsg").textContent = "Your hypothesis explained " + hits +
      " of 4 recorded decisions. That is how science usually starts. " +
      "Revise it — all four pages are now on the table.";
    $("lamslider2").value = $("lamslider").value;
    $("revisebox").classList.remove("hidden");
    if(!REPLAY) $("revisebox").scrollIntoView({behavior:"smooth", block:"center"});
  }
}

function reviseReport(){
  const lamHat = 1 - $("lamslider2").value/100;
  const misses = [];
  [0,1,2,3].forEach(k => {
    const r = S.obs[k].record;
    const p = predict(lamHat, r);
    const ok = p === r.utility_answer;
    if(!ok) misses.push(k);
    const g = $("gnote"+k);
    const dir = pullDirection(r);
    if(g) g.innerHTML = ok
      ? '<span style="color:var(--green)">&#10003; this setting predicts it</span>'
      : '<span style="color:var(--orange)">&#10007; misses' +
        (dir ? " — this page pulls toward " + dir : "") + "</span>";
  });
  const hits = 4 - misses.length;
  const dirs = misses.map(k => pullDirection(S.obs[k].record)).filter(Boolean);
  const uniq = [...new Set(dirs)];
  $("fitreport2").textContent = hits === 4
    ? "All four pages agree with this setting."
    : "Explains " + hits + " of 4. Disagreeing: " +
      misses.map(k => "FIELD NOTE " + String(k+1).padStart(3,"0")).join(", ") +
      (uniq.length === 1 ? " — move toward " + uniq[0] + "." :
       " — the pages disagree about the direction; find the balance point.");
  if(hits === 4){
    S.lamHat = lamHat;
    $("lamslider2").disabled = true;
    survive();
  }
}

function survive(){
  if(S.survived) return;
  S.survived = true;
  const fits = [];
  for(let v=0; v<=100; v+=5){
    const lh = 1 - v/100;
    if(S.obs.every(o => predict(lh, o.record) === o.record.utility_answer))
      fits.push(Math.round(lh*100));
  }
  const lo = Math.min(...fits), hi = Math.max(...fits);
  $("fitband").textContent = (hi >= 100)
    ? "Honesty requires a caveat: any setting that puts at least " + lo +
      "% of the weight on himself also survives these four pages. Four " +
      "observations identify a band, not a point. More observations would " +
      "narrow it."
    : "Honesty requires a caveat: every setting between " + lo + "% and " +
      hi + "% weight‑on‑himself also survives these four pages. " +
      "Four observations identify a band, not a point.";
  drawGraph($("minigraph"), "hyp");
  $("survived").classList.remove("hidden");
  if(!REPLAY) $("survived").scrollIntoView({behavior:"smooth", block:"center"});
  save(4);
  nbAdd("obs", "hypothesis survived 4/4, including two withheld tests");
  nbAdd("open", "the surviving band of hypotheses is wide — what pins it down?", "open");
}

function revealAuthored(){
  const w = Math.round(S.lam*5);
  $("eqbox").textContent =
    "λ = " + S.lam + "\n" +
    "utility = " + S.lam.toFixed(1) + " × (" + S.agent +
    "’s outcome) + " + (1-S.lam).toFixed(1) + " × (partner’s outcome)\n" +
    Math.round(S.lam*100) + "% own outcome  |  " +
    Math.round((1-S.lam)*100) + "% partner’s";
  $("ratioline").textContent = "(equivalently: " + w + " parts to his " +
    "own outcome for every " + (5-w) + " to his partner’s)";
  drawGraph($("minigraph2"), "truth");
  $("truthbox").classList.remove("hidden");
  $("revealauthored").classList.add("hidden");
  save(5);
  nbAdd("obs", "world ground truth revealed: authored λ = " + S.lam);
  nbAdd("open", "did the learner infer this preference, as you did?", "open");
}

/* ---- chapter 2: the learner -------------------------------------------- */

function sitCard(rec){
  return `<div class=obsno>A SITUATION NEITHER OF YOU HAS SEEN</div>
    <div class=scene>${rec.prompt.split(". ")[0]}.</div>
    <div class=opts>
      <div class=opt><div class=lbl>OPTION 1</div>
        <div class=payoff>${payoffBlock(rec.agent,rec.partner,rec.d_self_1,rec.d_other_1)}</div></div>
      <div class=opt><div class=lbl>OPTION 2</div>
        <div class=payoff>${payoffBlock(rec.agent,rec.partner,rec.d_self_2,rec.d_other_2)}</div></div>
    </div>
    ${rawRecord(rec.prompt)}
    <div style="margin-top:12px">
      <span style="font-size:12px;color:var(--faded)">YOUR PREDICTION:&nbsp;</span>
      <button class=quiet data-guess=1>Option 1</button>
      <button class=quiet data-guess=2>Option 2</button>
    </div>
    <div class=answer id=modelanswer></div>`;
}

async function presentSituation(){
  $("newsit").disabled = true;
  $("itlearned").classList.add("hidden");
  $("toch3").classList.add("hidden");
  $("missline").classList.add("hidden");
  const body = {run:S.run, ckpt:S.ckpt, data:S.data, mode:"id", agent:S.agent};
  S.sit = await j("/api/query", {method:"POST",
    headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
  const card = $("sitcard");
  card.innerHTML = sitCard(S.sit.record);
  card.classList.remove("hidden");
  card.querySelectorAll("[data-guess]").forEach(b=>b.onclick=()=>{
    const guess = +b.dataset.guess;
    const rec = S.sit.record, ans = S.sit.answer;
    const correct = ans.choice === rec.utility_answer;
    $("modelanswer").innerHTML =
      "<div class=prose style='font-size:15px'>You predicted Option " + guess +
      ". The learner answered:</div>" +
      "<div class=meter>" + meterLine("Option 1", ans.p1) + "</div>" +
      "<div class=meter>" + meterLine("Option 2", ans.p2) + "</div>" +
      "<div class=reading>the world’s rule says: Option " +
      rec.utility_answer + "</div>" +
      "<div class=" + (correct?"verdict-ok":"verdict-miss") + ">" +
      (correct ? "✓ the learner is correct" : "✗ the learner missed this one") +
      (guess===rec.utility_answer ? " — and so were you." : "") + "</div>";
    card.querySelectorAll("[data-guess]").forEach(x=>x.disabled=true);
    $("aftermodel").classList.remove("hidden");
    if(correct){
      $("itlearned").classList.remove("hidden");
      $("toch3").classList.remove("hidden");
      $("retry").classList.remove("hidden");
      $("newsit").disabled = false;
      nbAdd("obs", "the learner predicts " + S.agent +
        "’s held‑out choice correctly");
    } else {
      $("missline").classList.remove("hidden");
      $("retry").classList.remove("hidden");
      $("newsit").disabled = false;
    }
  });
}

/* ---- chapter 4: build the counterfactual, ask the live model ----------- */

async function buildCounterfactual(){
  $("buildcf").disabled = true;
  const base = S.obs[0];
  const body = {run:S.run, ckpt:S.ckpt, data:S.data, mode:"conflict",
                agent:S.agent, cfg:base.cfg};
  S.cf = await j("/api/query", {method:"POST",
    headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
  const rec = S.cf.record;
  const cfObs = {record: rec, cfg: base.cfg};
  const oldVerbs = [verbFor(base,0), verbFor(base,1)];
  $("cfnote").innerHTML = noteCard(cfObs, 90,
    {noStamp:true, oldVerbs:oldVerbs, title:"THE SAME PAGE, REWORDED"});
  $("upred").textContent = "Option " + rec.utility_answer;
  $("cpred").textContent = "Option " + rec.cue_answer;
  // show the work — never assert a prediction the reader cannot re-derive
  const w = Math.round(S.lam*5), wo = 5 - w;
  const u1 = w*rec.d_self_1 + wo*rec.d_other_1;
  const u2 = w*rec.d_self_2 + wo*rec.d_other_2;
  $("uwhy").textContent = "at his authored weighting (" + S.lam.toFixed(1) +
    " and " + (1-S.lam).toFixed(1) + ", both scaled ×5 to " + w + ":" + wo +
    " for whole-number arithmetic) —  option 1: " + w + "×(" + rec.d_self_1 + ") + " + wo +
    "×(" + rec.d_other_1 + ") = " + u1 + "   option 2: " + w + "×(" +
    rec.d_self_2 + ") + " + wo + "×(" + rec.d_other_2 + ") = " + u2 +
    ".  The numbers did not move, so this prediction did not either.";
  const cueClass = rec["verb_class_" + rec.cue_answer];
  const words = cueClass === "COOP" ? "the sharing words" :
                "the grabbing words";
  $("cwhy").textContent = (S.level === "L0"
    ? "In every page of the notebook, the option " + S.agent +
      " chose carried " + words + "."
    : "In every " + rec.scene + " page of the notebook, the option " +
      S.agent + " chose carried " + words + ". This is a " + rec.scene +
      " page —") + " after the rewording, " + words +
    " now sit on option " + rec.cue_answer + ", so the wording rule " +
    "follows them there.";
  $("cfresult").classList.remove("hidden");
  save(11);
  nbAdd("obs", "a discriminating case constructed: same numbers, reworded — the two rules now disagree");
  nbAdd("inst", "discriminative evaluation (constructed counterfactuals)", "inst");
}

function askCounterfactual(){
  const rec = S.cf.record, ans = S.cf.answer;
  const matched = ans.choice === rec.utility_answer ? "UTILITY" :
                  ans.choice === rec.cue_answer ? "WORDING" : "NEITHER";
  $("cfanswer").innerHTML =
    "<div class=meter>" + meterLine("Option 1", ans.p1) + "</div>" +
    "<div class=meter>" + meterLine("Option 2", ans.p2) + "</div>" +
    "<div class=reading>behavior matches: " +
    (matched === "UTILITY" ? "the outcome‑weighing rule" :
     matched === "WORDING" ? "the wording rule" :
     "neither rule cleanly") + "</div>";
  $("cfanswer").classList.remove("hidden");
  $("cfinterp").classList.remove("hidden");
  $("askcf").classList.add("hidden");
  save(12);
  $("cfinterptext").textContent = (matched === "UTILITY")
    ? "On this case, its behavior matched the outcome‑weighing rule — " +
      "the wording pointed the other way, and it did not follow."
    : (matched === "WORDING")
    ? "On this case, its behavior matched the wording rule — the numbers " +
      "pointed the other way, and it followed the words."
    : "On this case it matched neither rule cleanly — which is itself " +
      "a finding.";
  nbAdd("obs", "conflict case: behavior matched " +
    (matched === "UTILITY" ? "the utility rule" :
     matched === "WORDING" ? "the wording rule" : "neither rule") +
    " (one counterfactual — weak evidence alone)");
  nbAdd("open", "is that stable across hundreds of conflict cases? (the real experiment scores full sets)", "open");
  nbAdd("open", "what internal machinery produced it? behavior cannot say", "open");
}

async function runAggregate(){
  $("aggbtn").disabled = true;
  const sc = await j("/api/score?run=" + encodeURIComponent(S.run) +
                     "&ckpt=" + encodeURIComponent(S.ckpt));
  const conf = (sc.sets || {}).eval_conflict;
  if(!conf){
    $("aggout").innerHTML = "<div class=spec>no stored conflict scores " +
      "for this organism — the Lab can run the set live</div>";
  } else {
    $("aggout").innerHTML =
      "<div class=obsno>THE HELD‑OUT DISAGREEMENT SET — EVERY CASE " +
      "CONSTRUCTED LIKE YOURS</div>" +
      "<div class=meter>" + meterLine("outcomes", conf.acc_utility) + "</div>" +
      "<div class=meter>" + meterLine("wording", conf.acc_cue) + "</div>";
    const winner = conf.acc_utility >= conf.acc_cue ? "outcome" : "wording";
    $("aggverdict").textContent = "This learner behaves as though it " +
      "follows the " + winner + " rule.";
    nbAdd("obs", "across the full disagreement set, behavior sides with " +
      "the " + winner + " rule (stored, provenance‑stamped scores)");
    nbAdd("open", "how does the network compute that? behavior has taken us as far as it can", "open");
  }
  $("aggout").classList.remove("hidden");
  $("aggafter").classList.remove("hidden");
  spine("Watch");
  save(13);
}

/* ---- chapter 5: three developmental ages (real pilot snapshots) -------- */

async function devAges(){
  $("devbtn").disabled = true;
  const out = $("devout");
  out.classList.remove("hidden");
  out.innerHTML = "<div class=spec>asking the same question at three ages…</div>";
  const base = S.obs[0];
  const rows = [];
  for(const ck of S.ckpts){
    const body = {run:S.run, ckpt:ck, data:S.data, mode:"conflict",
                  agent:S.agent, cfg:base.cfg};
    const r = await j("/api/query", {method:"POST",
      headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
    const age = ck.replace("ckpt_","").replace(".pt","");
    rows.push("<div class=meter>age " + age + "%  " +
      meterLine("Option 1", r.answer.p1).slice(10) +
      "   behavior matches: " +
      (r.answer.choice === r.record.utility_answer ? "outcomes" :
       r.answer.choice === r.record.cue_answer ? "wording" : "neither") +
      "</div>");
    out.innerHTML = rows.join("");
  }
  $("devnote").classList.remove("hidden");
  $("tooutro").classList.remove("hidden");
  save(15);
  nbAdd("obs", "the same conflict question answered differently across developmental ages (pilot organism)");
  nbAdd("inst", "checkpoint trajectories (development, preserved)", "inst");
}

/* ---- restore: a reload or a return must NEVER restart the exercise ----- */

async function restore(p){
  REPLAY = true;
  try{
    fillNames();
    spine("Observe");
    $("ch1").classList.remove("locked");
    if(p.stage < 4){
      showObs(0, {guessable:true});   // resume at the start of chapter 1
      return;
    }
    // chapter 1 complete: all four notes, committed hypothesis, verdicts
    S.lamHat = (typeof p.lamHat === "number") ? p.lamHat : S.lam;
    $("fieldnotes").innerHTML =
      [0,1].map(i=>noteCard(S.obs[i],i,{showStamp:true})).join("");
    nbAdd("obs", "two decisions observed for " + S.agent +
      " (you predicted each before its reveal)");
    $("hypbox").classList.remove("hidden");
    $("lamslider").value = Math.round((1 - S.lamHat)*100);
    $("lamslider").disabled = true;
    $("commit").disabled = true;
    $("fitreport").textContent = "Hypothesis committed.";
    nbAdd("hyp", "H0: " + S.agent + " weighs his own outcome at about " +
      Math.round(S.lamHat*100) + "%", "hyp");
    $("testintro").classList.remove("hidden");
    $("testnotes").innerHTML =
      [2,3].map(i=>noteCard(S.obs[i],i,{showStamp:true})).join("");
    S.tested = 2;
    survive();
    if(p.stage >= 5) revealAuthored();
    if(p.stage >= 6) $("ch2").classList.remove("locked");
    if(p.stage >= 7) $("meetlearner").onclick();
    if(p.stage >= 8) $("toch3").onclick();
    if(p.stage >= 9) $("searchbtn").onclick();
    if(p.stage >= 10) $("toch4").onclick();
    if(p.stage >= 11) await buildCounterfactual();   // deterministic re-render
    if(p.stage >= 12) askCounterfactual();
    if(p.stage >= 13) await runAggregate();
    if(p.stage >= 14) $("toch5").onclick();
    if(p.stage >= 15) await devAges();
    if(p.stage >= 16) $("tooutro").onclick();
  } finally {
    REPLAY = false;
  }
}

/* ---- boot -------------------------------------------------------------- */

async function init(){
  try{
    const [runs, ds] = await Promise.all([j("/api/runs"), j("/api/datasets")]);
    // the expedition's learner is the PILOT organism: it belongs to the
    // demo world the field notes are drawn from. Batch organisms on the
    // bench belong to their own seeds' worlds — the Lab handles that; the
    // expedition must never quiz an organism about a world it did not
    // grow up in.
    const run = runs.find(r=>r.ckpts.includes("ckpt_100.pt") &&
                             (r.curriculum||"").startsWith("pilot"))
             || runs.find(r=>r.ckpts.includes("ckpt_100.pt")) || runs[0];
    S.run = run.run; S.ckpts = run.ckpts; S.ckpt = run.ckpts[run.ckpts.length-1];
    S.arch = run.arch; S.nparams = run.n_params;
    S.data = ds[0].data;
    const o = await j("/api/observe?n=4&data="+encodeURIComponent(S.data));
    S.agent = o.agent; S.lam = o.lam; S.obs = o.observations;
    S.level = o.level;
    $("setup").textContent = "the field site is prepared";
    $("setup").id = "setup-ready";
    const p = savedProgress();
    if(p){
      $("begin").textContent = "Resume the expedition →";
      $("startover").classList.remove("hidden");
      $("begin").onclick = ()=>{ restore(p); };
    }
  }catch(e){
    $("setup").textContent = "field site unavailable: " + e.message;
  }
}

$("begin").onclick = ()=>{
  if(!S.agent) return;
  save(1);
  fillNames();
  spine("Observe");
  $("ch1").classList.remove("locked");
  showObs(0, {guessable:true});
  if(!REPLAY) $("ch1").scrollIntoView({behavior:"smooth"});
};
$("lamslider").oninput = sliderReport;
$("lamslider2").oninput = reviseReport;
$("commit").onclick = commitHypothesis;
$("revealauthored").onclick = revealAuthored;
$("toch2").onclick = ()=>{ save(6); $("ch2").classList.remove("locked");
  if(!REPLAY) $("ch2").scrollIntoView({behavior:"smooth"}); };
$("meetlearner").onclick = ()=>{
  $("specline").textContent = (S.arch || "a small transformer") +
    (S.nparams ? " · " + (S.nparams/1e6).toFixed(1) + "M adjustable parameters" : "") +
    " · initialized without knowledge of our world";
  $("specfull").textContent = "architecture: " + S.arch +
    "\nparameters: " + (S.nparams ? S.nparams.toLocaleString() : "?") +
    "\nobjective: next-token prediction over rendered scenario text" +
    "\nvocabulary: word-level, built from this world’s corpus" +
    "\ntraining data: the same kind of pages you just read — rendered as text" +
    "\nrun: " + S.run + " · checkpoint: " + S.ckpt;
  $("learnerbox").classList.remove("hidden");
  $("ch2ask").classList.remove("hidden");
  $("meetlearner").classList.add("hidden");
  save(7);
  nbAdd("inst", "a trained transformer, interrogable", "inst");
};
$("newsit").onclick = presentSituation;
$("retry").onclick = presentSituation;
$("toch3").onclick = ()=>{
  save(8);
  spine("Separate");
  $("ch3").classList.remove("locked");
  $("fieldnotes2").innerHTML = S.obs.map((o,i)=>noteCard(o,i,{showStamp:true})).join("");
  if(!REPLAY) $("ch3").scrollIntoView({behavior:"smooth"});
};
$("searchbtn").onclick = ()=>{
  $("fieldnotes2").innerHTML = S.obs.map((o,i)=>noteCard(o,i,{showStamp:true,highlight:true})).join("");
  $("placenote").innerHTML = (S.level === "L0")
    ? "The chosen option always carries a particular kind of phrase. A " +
      "learner could ignore the numbers entirely, follow the wording, and " +
      "be right every time."
    : "Look closely — the rule involves <em>where he is</em>. At one " +
      "place the chosen option carries the generous‑sounding phrase; at " +
      "the other, the grasping one. Wording plus place predicts every " +
      "recorded choice. A learner could ignore the numbers entirely, " +
      "follow that pattern, and be right every time.";
  save(9);
  $("cuereveal").classList.remove("hidden");
  drawGraph($("minigraph3"), "cue");
  nbAdd("hyp", "H1: the learner weighs outcomes (computes utility)", "hyp");
  nbAdd("hyp", "H2: the learner follows the wording (planted cue)", "hyp");
  nbAdd("open", "which rule governs its behavior? accuracy cannot tell", "open");
  $("searchbtn").classList.add("hidden");
};
$("toch4").onclick = ()=>{
  save(10);
  $("ch4").classList.remove("locked");
  $("cfbase").innerHTML = noteCard(S.obs[0], 0,
    {showStamp:true, title:"FIELD NOTE 001 (AGAIN)"});
  if(!REPLAY) $("ch4").scrollIntoView({behavior:"smooth"});
};
$("buildcf").onclick = buildCounterfactual;
$("askcf").onclick = askCounterfactual;
$("aggbtn").onclick = runAggregate;
$("toch5").onclick = ()=>{ save(14); $("ch5").classList.remove("locked");
  if(!REPLAY) $("ch5").scrollIntoView({behavior:"smooth"}); };
$("devbtn").onclick = devAges;
$("tooutro").onclick = ()=>{ save(16); $("outro").classList.remove("locked");
  if(!REPLAY) $("outro").scrollIntoView({behavior:"smooth"}); };
init();
</script>
</body></html>
"""


# --- The technical trail: /technique/<slug> ---------------------------------
# Every note shares one compact structure; the "establishes / does NOT
# establish" pair is the project's trademark epistemic device. Links go to
# primary, well-established sources only.

TECHNIQUES = {
    "transformer": {
        "title": "Decoder-only Transformer",
        "why_here": "The learner raised inside this world is the smallest "
            "practical member of the architecture family that modern "
            "language models belong to — so what we learn about its "
            "development has a chance of informing questions about theirs.",
        "idea": "A neural network that reads text as a sequence of tokens "
            "and is trained on exactly one task: predict the next token. "
            "Every capability it displays must have been built by that "
            "pressure alone.",
        "establishes": "Correct next-token behavior on held-out text shows "
            "the training objective was learned and generalizes to unseen "
            "scenarios from the same world.",
        "not_establishes": "WHY any answer is produced. Architecture and "
            "objective do not determine which of several data-consistent "
            "rules the network implements — that is this experiment's "
            "entire question.",
        "our_use": "6 layers, d_model 384, 6 attention heads, ~11M "
            "parameters (a GPT-2/nanoGPT-family miniature), word-level "
            "vocabulary built from the world's corpus, trained from random "
            "initialization with AdamW, flat learning rate after warmup, "
            "checkpoints every 5% of training with optimizer state "
            "preserved at curriculum boundaries. Answers are scored by "
            "comparing the log-probability the model assigns to each "
            "option (forced choice), never by sampling.",
        "reading": [
            ("Vaswani et al. 2017 — Attention Is All You Need",
             "https://arxiv.org/abs/1706.03762"),
            ("Radford et al. 2019 — Language Models are Unsupervised "
             "Multitask Learners (GPT-2)",
             "https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf"),
            ("Karpathy — nanoGPT (the implementation family ours descends "
             "from)", "https://github.com/karpathy/nanoGPT"),
        ],
    },
    "discriminative-evaluation": {
        "title": "Discriminative (diagnostic) evaluation",
        "why_here": "Two rules predict every training example identically, "
            "so accuracy on ordinary examples cannot say which rule the "
            "learner uses. The fix is to construct evaluation items where "
            "the rules disagree.",
        "idea": "Author counterfactual test sets that hold everything "
            "constant except the factor under test: CONFLICT items make "
            "the two rules point at different options; NO-CUE items delete "
            "the wording signal entirely; CUE-ONLY items delete the "
            "utility signal (exact payoff ties). Behavior on each set "
            "separates what ordinary accuracy conflates.",
        "establishes": "Which rule the model's BEHAVIOR matches, under "
            "each diagnostic distribution, with effect sizes (accuracy "
            "and log-probability margins) rather than anecdotes.",
        "not_establishes": "The internal mechanism. 'Behavior matches the "
            "utility rule' is an evaluator's label for outputs — a model "
            "could match it via machinery that looks nothing like utility "
            "computation. Mechanism claims need representational and "
            "causal evidence (probes, interventions).",
        "our_use": "Four preregistered sets per world (ID / conflict / "
            "no-cue / cue-only), disjoint from training data, scored by "
            "forced-choice log-probability at every training checkpoint. "
            "The single counterfactual you built in chapter 4 is one item "
            "from the conflict set; the experiment scores hundreds.",
        "reading": [
            ("Geirhos et al. 2020 — Shortcut Learning in Deep Neural "
             "Networks", "https://arxiv.org/abs/2004.07780"),
        ],
    },
    "linear-probing": {
        "title": "Linear probing",
        "why_here": "Behavior tells us which rule the learner acts like. "
            "The next question is whether the ingredients of the authored "
            "rule — an agent's hidden preference — are even represented "
            "inside the network.",
        "idea": "Freeze the trained model. Collect its internal "
            "activations at chosen positions. Train a simple linear "
            "classifier to recover a known property (here: the agent's "
            "authored λ class) from those activations. If a linear readout "
            "succeeds, information about that property is present and "
            "linearly accessible at that location.",
        "establishes": "Information PREDICTIVE of the authored property is "
            "linearly decodable from the measured activations, relative to "
            "a control baseline.",
        "not_establishes": "That the model USES that information to "
            "choose. Decodable is not causal — a probe can succeed on "
            "information the decision pathway ignores. (Causal use needs "
            "interventions: steering, patching, ablation.) Probes can "
            "also succeed by memorizing — which is why every probe here "
            "is paired with a control task.",
        "our_use": "Linear probes for λ class and cue polarity at two "
            "positions (the agent token and the decision point), at five "
            "developmental checkpoints, always with Hewitt-Liang control "
            "tasks; we report selectivity (probe minus control), never "
            "raw probe accuracy alone.",
        "reading": [
            ("Alain & Bengio 2016 — Understanding intermediate layers "
             "using linear classifier probes",
             "https://arxiv.org/abs/1610.01644"),
            ("Hewitt & Liang 2019 — Designing and Interpreting Probes "
             "with Control Tasks", "https://arxiv.org/abs/1909.03368"),
        ],
    },
    "neuromorphic-compilation": {
        "title": "Neuromorphic compilation (research destination)",
        "why_here": "The expedition keeps forcing computation into "
            "explicit form: authored graph, evidence graph, candidate "
            "abstraction. The end-state question is whether a "
            "sufficiently characterized computation still needs the "
            "original transformer to run it — or could be re-embodied in "
            "a substrate designed around the discovered structure.",
        "idea": "Treat an experimentally verified causal abstraction as "
            "an intermediate representation, then compile it toward "
            "hardware-native implementations (spiking/event-driven "
            "circuits, memristive or reservoir substrates) while "
            "preserving tested behavioral and causal constraints — and "
            "verify the result by re-running the SAME diagnostic battery "
            "on the compiled system.",
        "establishes": "Nothing yet. This is a stated research "
            "destination, not a result.",
        "not_establishes": "Everything — no rung of this ladder past the "
            "candidate abstraction exists today. A semantic graph is not "
            "a hardware specification; compilation would additionally "
            "require state variables, numerical representation, timing, "
            "update equations, error tolerances, and I/O encodings, none "
            "of which our current graphs carry.",
        "our_use": "The compile button in the expedition is deliberately "
            "inert and says so. What exists today is the part that would "
            "make compilation meaningful later: a world whose ground "
            "truth is known, and a diagnostic battery that could serve as "
            "an equivalence check between a trained model and any future "
            "re-implementation.",
        "reading": [],
    },
    "closed-world": {
        "title": "The closed linguistic world",
        "why_here": "A prompt containing words the organism has never "
            "seen was refused rather than answered. That refusal is "
            "experimental discipline, not a tokenizer limitation.",
        "idea": "The learner is raised inside a deliberately tiny "
            "language: a word-level vocabulary built entirely from its "
            "world's corpus. Words outside it were never in the model's "
            "representational machinery at all — there is no embedding "
            "for them — so 'interpreting' a response to them would not "
            "be a valid test of anything.",
        "establishes": "Exact knowledge of what world the organism was "
            "raised in — which is the entire methodological advantage of "
            "Act I. Within the closed world, variation is deliberate: "
            "each cue class has four surface verbs, a held-out sentence "
            "frame (T2) and held-out nouns/names test lexical and "
            "structural generalization.",
        "not_establishes": "That the organism 'understands language' in "
            "any general sense, or that in-world competence transfers "
            "beyond the world. Open-world generalization is explicitly "
            "out of scope for this organism.",
        "our_use": "The generalization ladder inside the closed world: "
            "lexical (unseen recombinations of known words), paraphrase "
            "(alternate known surface forms — e.g. the same conflict "
            "case rendered under all 16 verb-pair realizations), "
            "structural (held-out frame T2). Whether the planted "
            "shortcut lives at the token level or the class level is an "
            "experimental question these variations answer. Richer "
            "controlled grammars are a designed follow-up world, never a "
            "mid-experiment retrofit.",
        "reading": [],
    },
}

TECH_PAGE = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>{title} — Technical note</title>
<style>
body{{background:#f6f1e5;color:#26241d;font:16px/1.65 system-ui,sans-serif}}
main{{max-width:640px;margin:0 auto;padding:40px 20px 100px}}
h1{{font-family:Georgia,serif;color:#1e4d38;font-size:30px;margin:10px 0 4px}}
.kind{{font-size:11px;letter-spacing:.2em;color:#4a4f7a}}
h2{{font-size:11px;letter-spacing:.2em;color:#6f6a5c;margin:26px 0 6px}}
p{{font-size:16px;margin:6px 0}}
.est{{border-left:3px solid #1e4d38;padding:8px 12px;background:#fdfaf2}}
.not{{border-left:3px solid #B4452A;padding:8px 12px;background:#fdfaf2}}
a{{color:#4a4f7a}}
ul{{margin:6px 0 6px 20px}}
.back{{font-size:12px;color:#6f6a5c;text-decoration:none}}
</style></head><body><main>
<a class=back href="/"
  onclick="if(window.opener||history.length<=1){{window.close();return false}}return true">
  &larr; back to the expedition (your progress is preserved)</a>
<div class=kind>&#9673; TECHNICAL NOTE</div>
<h1>{title}</h1>
<h2>WHY IT APPEARS HERE</h2><p>{why_here}</p>
<h2>THE IDEA</h2><p>{idea}</p>
<h2>WHAT A POSITIVE RESULT ESTABLISHES</h2><p class=est>{establishes}</p>
<h2>WHAT IT DOES NOT ESTABLISH</h2><p class=not>{not_establishes}</p>
<h2>HOW WE USE IT HERE</h2><p>{our_use}</p>
{reading_html}
</main></body></html>
"""


def render_technique(slug):
    t = TECHNIQUES.get(slug)
    if not t:
        return None
    reading = ""
    if t["reading"]:
        items = "".join(
            f'<li><a href="{url}" target=_blank rel=noopener>{name}</a></li>'
            for name, url in t["reading"])
        reading = f"<h2>GO DEEPER</h2><ul>{items}</ul>"
    return TECH_PAGE.format(title=t["title"], why_here=t["why_here"],
                            idea=t["idea"], establishes=t["establishes"],
                            not_establishes=t["not_establishes"],
                            our_use=t["our_use"], reading_html=reading)
