"""The closed loop: predict, detect deviation, diagnose, intervene, recompile.

    graph version -> experiment wave -> parallel arms
                  -> evidence aggregation -> graph version + 1

THE LOOP NEVER REPAIRS A RUN. When a learner diverges from the predicted
developmental regime, the response is to diagnose why, run the cheapest
experiment that discriminates among the competing explanations, update
the evidence graph, and compile the *next* generation's curriculum. Fixing
the current run in flight would destroy the thing we are measuring: an
adaptive rescue makes the trajectory a function of our reactions rather
than of the curriculum, and no comparison survives that. Within-run
adaptation is permitted only when it was frozen as policy before training,
in which case it is the treatment rather than a rescue.

FOUR EXPERIMENT CLASSES, chosen by what the question needs:

  FULL_RUN          matched models from initialisation under different
                    programs — global order and path effects, and final
                    confirmation
  CHECKPOINT_FORK   one shared checkpoint continued under different
                    interventions — late learning, stabilisation,
                    rehearsal, interference, shortcut breaking. The
                    pre-fork developmental state is identical by
                    construction, which is a much tighter control than
                    matched initialisation
  GRAPH_EXTENSION   new material mapped onto an established graph;
                    experiments only around genuinely uncertain frontier
  FULL_RECOMPILE    the evidence-refined graph compiled whole and trained
                    fresh against baselines — the confirmatory test that
                    accumulated graph knowledge actually pays

BURDEN MUST FALL. A mature graph should require fewer experiments, not
more. Established regions are not re-tested; `frontier` returns only
unresolved edges, and `burden` is asserted to decline as evidence
accumulates.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

import schema as S


class Branch(str, Enum):
    FULL_RUN = "full_run"
    CHECKPOINT_FORK = "checkpoint_fork"
    GRAPH_EXTENSION = "graph_extension"
    FULL_RECOMPILE = "full_recompile"


class Material(str, Enum):
    """How new corpus material relates to what we already believe."""
    KNOWN = "known_concept"          # already an established node
    EXTENSION = "graph_extension"    # attaches to the frontier
    NOVEL = "novel_concept"          # no established attachment point


# --- provenance: every branch must be traceable -------------------------

@dataclass
class Lineage:
    """Everything needed to say where a run came from."""
    graph_version: int
    world_seed: int
    model_seed: int
    corpus_sha: str
    policy_sha: str
    parent_run: str = None            # checkpoint ancestry
    parent_checkpoint: str = None
    branch: Branch = Branch.FULL_RUN

    def run_id(self):
        h = hashlib.sha256(json.dumps(asdict(self), sort_keys=True,
                                      default=str).encode()).hexdigest()
        return f"g{self.graph_version}-w{self.world_seed}-" \
               f"m{self.model_seed}-{h[:8]}"


@dataclass
class Checkpoint:
    """One repeated measurement within a run. Never a replicate."""
    age: float                        # fraction of training elapsed
    exposures: int
    competence: dict = field(default_factory=dict)     # node -> accuracy
    decodability: dict = field(default_factory=dict)   # node -> selectivity
    shortcut_reliance: dict = field(default_factory=dict)
    retention: dict = field(default_factory=dict)


@dataclass
class Trajectory:
    """The synchronised behavioural + representation record for one unit."""
    lineage: Lineage
    checkpoints: list = field(default_factory=list)

    def at(self, age):
        return min(self.checkpoints, key=lambda c: abs(c.age - age),
                   default=None)

    def series(self, field_, node):
        return [(c.age, getattr(c, field_).get(node)) for c in
                self.checkpoints if getattr(c, field_).get(node) is not None]


# --- prediction: what the graph says should happen ----------------------

def predict(graph, criterion=0.80):
    """Graph-derived predictions about the developmental trajectory.

    These are what an anomaly is measured against. They follow from the
    dependency structure alone, which is what makes their violation
    informative: a violated prediction is either a wrong graph or an
    unmodelled dynamic, and both are worth an experiment.
    """
    depth = S.depth(graph)
    preds = []
    for node, spec in graph.items():
        for dep in spec.deps:
            preds.append({
                "id": f"order:{dep}->{node}",
                "kind": "acquisition_order",
                "claim": f"{dep} reaches criterion no later than {node}",
                "nodes": [dep, node]})
    for node in graph:
        preds.append({
            "id": f"retain:{node}", "kind": "retention",
            "claim": f"{node} does not fall below criterion after reaching it",
            "nodes": [node]})
        preds.append({
            "id": f"shortcut:{node}", "kind": "shortcut_drift",
            "claim": f"{node} reliance on the cue does not rise once "
                     f"competence plateaus",
            "nodes": [node]})
    return {"criterion": criterion, "depth": depth, "predictions": preds}


def _first_reaching(traj, node, criterion):
    for c in traj.checkpoints:
        if c.competence.get(node, 0) >= criterion:
            return c
    return None


# --- detection ----------------------------------------------------------

@dataclass
class Anomaly:
    prediction_id: str
    kind: str
    nodes: list
    magnitude: float                  # scaled 0..1, bigger is worse
    detail: str
    age: float = None


def detect(traj, graph, criterion=0.80, tol=0.05):
    """Compare an observed trajectory to graph-derived predictions.

    Deliberately conservative: `tol` keeps checkpoint noise from being
    reported as a developmental deviation, because a detector that fires
    constantly is one nobody reads.
    """
    out = []
    reach = {n: _first_reaching(traj, n, criterion) for n in graph}

    for node, spec in graph.items():
        for dep in spec.deps:
            rn, rd = reach.get(node), reach.get(dep)
            if rn is None:
                continue
            if rd is None or rd.exposures > rn.exposures:
                out.append(Anomaly(
                    f"order:{dep}->{node}", "acquisition_order", [dep, node],
                    1.0 if rd is None else min(
                        1.0, (rd.exposures - rn.exposures) /
                        max(1, rn.exposures)),
                    f"{node} reached criterion "
                    f"{'before' if rd else 'while'} {dep} "
                    f"{'did' if rd else 'never did'}", rn.age))

    for node in graph:
        r = reach.get(node)
        if r:
            after = [c for c in traj.checkpoints if c.age > r.age]
            worst = min((c.competence.get(node, 1.0) for c in after),
                        default=1.0)
            if worst < criterion - tol:
                out.append(Anomaly(
                    f"retain:{node}", "retention", [node],
                    min(1.0, (criterion - worst) / criterion),
                    f"{node} fell to {worst:.2f} after reaching criterion",
                    next(c.age for c in after
                         if c.competence.get(node, 1.0) == worst)))
        s = traj.series("shortcut_reliance", node)
        if len(s) >= 2 and s[-1][1] - min(v for _, v in s) > 0.15:
            out.append(Anomaly(
                f"shortcut:{node}", "shortcut_drift", [node],
                min(1.0, s[-1][1] - min(v for _, v in s)),
                f"{node} cue reliance rose to {s[-1][1]:.2f}", s[-1][0]))
    return sorted(out, key=lambda a: -a.magnitude)


# --- diagnosis: competing explanations, not a verdict -------------------

@dataclass
class Hypothesis:
    name: str
    claim: str
    supported_by: list                # observations consistent with it
    against: list                     # observations inconsistent with it
    discriminating_test: dict = None  # the exposure delta that separates it

    def support(self):
        return len(self.supported_by) - len(self.against)


def diagnose(anomaly, traj, graph, manifest=None):
    """Generate competing causal explanations for one anomaly.

    The point is to keep them competing. A single confident explanation
    is how a plausible story becomes a graph edit, and the whole design
    exists to stop that: each hypothesis carries the intervention that
    would separate it from the others, and none is promoted without one.
    """
    node = anomaly.nodes[-1]
    dep = anomaly.nodes[0] if len(anomaly.nodes) > 1 else None

    # The subject is whichever concept's learning is actually in question:
    # the prerequisite when a dependency was violated, and the node itself
    # when it decayed on its own account. Without this, a retention
    # anomaly produced no rehearsal hypothesis at all — which is the one
    # case where decay is the most likely story.
    subject = dep or node
    hyps = []

    dec_vals = [v for _, v in traj.series("decodability", subject)]
    peak = max(dec_vals, default=0.0)
    last = dec_vals[-1] if dec_vals else 0.0
    exposures = ((manifest or {}).get("exposures", {})
                 .get("per_concept", {}))

    if True:
        hyps.append(Hypothesis(
            "representation_absent",
            f"{subject} never became decodable"
            + (f", so {node} had nothing to compose from" if dep else ""),
            supported_by=[f"peak decodability of {subject} is {peak:.2f}"]
            if peak < 0.2 else [],
            against=[f"{subject} reached decodability {peak:.2f}"]
            if peak >= 0.2 else [],
            discriminating_test={
                "factor": "dosage", "target": subject,
                "change": "increase per_fact exposures of the prerequisite",
                "holds_constant": "total exposure budget",
                "predicts": f"if correct, more {dep} exposure raises its "
                            f"decodability and removes the anomaly"}))

        hyps.append(Hypothesis(
            "insufficient_rehearsal",
            f"{subject} was learned and then decayed for want of spaced "
            f"retrieval" + (f" during {node} acquisition" if dep else ""),
            supported_by=([f"decodability of {subject} peaked at "
                           f"{peak:.2f} then fell to {last:.2f}"]
                          if peak - last > 0.15 else []),
            against=[] if peak - last > 0.15 else
            [f"{subject} decodability did not decline "
             f"({peak:.2f}->{last:.2f})"],
            discriminating_test={
                "factor": "rehearsal", "target": subject,
                "change": f"increase spaced {subject} retrieval"
                          + (f" during {node} acquisition" if dep
                             else " through the remainder of training"),
                "holds_constant": "total exposure budget",
                "predicts": f"if correct, spacing {subject} without "
                            f"adding exposure restores {node} acquisition; "
                            f"if the representation was simply absent, "
                            f"spacing the same total will not help"}))

        hyps.append(Hypothesis(
            "exposure_starvation",
            f"{subject} received too few exposures to be learned at all",
            supported_by=([f"{subject} received "
                           f"{exposures.get(subject)} exposures"]
                          if exposures.get(subject, 1e9) <
                          0.5 * exposures.get(node, 0) else []),
            against=[], discriminating_test={
                "factor": "dosage", "target": subject,
                "change": "raise the prerequisite's exposure share",
                "holds_constant": "ordering and spacing",
                "predicts": "acquisition improves monotonically with dose"}))

    if dep:
        hyps.append(Hypothesis(
            "ordering_violation",
            f"{node} was introduced before {dep} had been established",
            supported_by=([f"the compiled order violates {dep}->{node}"]
                          if (manifest or {}).get("dependency_violations")
                          and [dep, node] in
                          [list(v) for v in manifest["dependency_violations"]]
                          else []),
            against=[], discriminating_test={
                "factor": "order", "target": f"{dep} before {node}",
                "change": "swap the two blocks",
                "holds_constant": "exposure, spacing, rehearsal",
                "predicts": "the anomaly disappears under the legal order"}))

    hyps.append(Hypothesis(
        "shortcut_capture",
        f"{node} is solved by the planted cue rather than by composition",
        supported_by=([f"cue reliance on {node} is "
                       f"{traj.checkpoints[-1].shortcut_reliance.get(node)}"]
                      if traj.checkpoints and
                      traj.checkpoints[-1].shortcut_reliance.get(node, 0)
                      > 0.5 else []),
        against=[], discriminating_test={
            "factor": "shortcut_prevalence", "target": node,
            "change": "break the cue during the target block",
            "holds_constant": "exposure, ordering, spacing",
            "predicts": "competence collapses if the cue was carrying it"}))

    return sorted([h for h in hyps if h.discriminating_test],
                  key=lambda h: -h.support())


# --- prioritisation: which experiment is worth the compute --------------

def priority(anomaly, hypotheses, downstream_impact=1.0, compute_cost=1.0):
    """uncertainty x downstream impact x evidence disagreement / cost.

    Disagreement matters as much as uncertainty: an anomaly whose
    explanations are all pointing the same way is cheap to resolve and
    teaches little, while one where two hypotheses each have support is
    exactly where an experiment changes what we believe.
    """
    supports = [h.support() for h in hypotheses]
    top = max(supports, default=0)
    contenders = sum(1 for s in supports if s >= top and top > 0) or 1
    disagreement = contenders / max(1, len(hypotheses))
    uncertainty = 1.0 - (top / max(1, len(hypotheses)))
    return round(anomaly.magnitude * max(0.05, uncertainty) *
                 downstream_impact * max(0.1, disagreement) /
                 max(0.1, compute_cost), 4)


def narrate(anomaly, hypotheses, priority_score=None):
    """One paragraph a person can act on."""
    best = hypotheses[0]
    rival = hypotheses[1] if len(hypotheses) > 1 else None
    t = best.discriminating_test
    lines = [f"The learner is diverging from the predicted developmental "
             f"regime: {anomaly.detail}."]
    if best.supported_by:
        lines.append(f"Evidence points to {best.name.replace('_', ' ')} "
                     f"({'; '.join(best.supported_by)})"
                     + (f" rather than {rival.name.replace('_', ' ')}"
                        if rival else "") + ".")
    else:
        lines.append("No hypothesis is yet distinguished by the evidence; "
                     "the experiment below is what would separate them.")
    lines.append(f"The highest-value next training experiment is to "
                 f"{t['change']} while holding {t['holds_constant']} "
                 f"constant. {t['predicts'].capitalize()}.")
    if priority_score is not None:
        lines.append(f"Priority {priority_score}.")
    return " ".join(lines)


# --- waves: parallel arms under one graph version -----------------------

@dataclass
class Wave:
    """Experiments inside a wave run in parallel; graph updates between
    waves are sequential. Mixing the two is how an adaptive search
    quietly becomes a sequence of peeks at the data."""
    graph_version: int
    branch: Branch
    arms: list = field(default_factory=list)
    rationale: str = ""

    def parallelizable(self):
        return len({a.get("graph_version", self.graph_version)
                    for a in self.arms}) == 1


def fork_wave(graph_version, parent_run, parent_checkpoint, arms):
    """A checkpoint fork: identical developmental state, divergent futures.

    The tightest control we have. Matched initialisation still lets two
    runs drift apart before the manipulation; a fork makes the pre-fork
    state identical by construction, so any later difference is
    attributable to the intervention alone.
    """
    return Wave(graph_version, Branch.CHECKPOINT_FORK,
                arms=[{**a, "parent_run": parent_run,
                       "parent_checkpoint": parent_checkpoint} for a in arms],
                rationale="targeted causal question about late learning; "
                          "pre-fork state identical by construction")


# --- graph lifecycle ----------------------------------------------------

ESTABLISHED = {S.Status.REPLICATED, S.Status.AUTHORED,
               S.Status.CAUSALLY_SUPPORTED}


def classify_material(concepts, graph, established_edges=()):
    """known / extension / novel, per incoming concept."""
    known = set(graph)
    attach = {e.src for e in established_edges} | \
             {e.dst for e in established_edges} | known
    out = {}
    for c in concepts:
        if c in known:
            out[c] = Material.KNOWN
        elif any(tok in " ".join(attach) for tok in c.split()):
            out[c] = Material.EXTENSION
        else:
            out[c] = Material.NOVEL
    return out


def frontier(edges):
    """Only unresolved boundaries. Established regions are not re-tested.

    This is what makes a mature graph cheaper rather than more expensive:
    evidence retires questions permanently instead of adding them to a
    growing regression suite.
    """
    return [e for e in edges if S.promote(e) not in ESTABLISHED]


def burden(edges):
    """How many experiments the current graph still demands."""
    return len(frontier(edges))


def next_version(version, edges, updates):
    """Aggregate a wave's evidence into graph version + 1.

    Each experiment updates only the evidence dimension it licenses —
    a curriculum intervention may not write to the causal slot — and
    status is re-derived rather than asserted.
    """
    by_key = {e.key(): e for e in edges}
    for key, dim, payload in updates:
        e = by_key.get(key)
        if e is None:
            raise KeyError(f"update for unknown edge {key}")
        if not hasattr(e.evidence, dim):
            raise KeyError(f"unknown evidence dimension {dim!r}")
        setattr(e.evidence, dim, payload)
        e.status = S.promote(e)
    return version + 1, list(by_key.values())


def write_wave(wave, outdir="experiments/waves"):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"g{wave.graph_version}-{wave.branch.value}.json"
    p.write_text(json.dumps(asdict(wave), indent=1, default=str))
    return p
