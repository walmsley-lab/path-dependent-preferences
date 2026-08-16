"""Ingest arbitrary text into a typed, provenanced observational graph.

This is the front end the Odyssey world does not need and every real
corpus does. It answers "what concepts and relations does this document
actually contain?" and refuses to answer "what should be taught first?",
because no amount of text supports that second claim.

WHAT THIS PRODUCES. G_observational only: typed candidate edges, each
reversible to the passages that caused it. Extraction runs in
schema-guided mode — the caller supplies the relation patterns it cares
about — which is the mode that can be validated, rather than pretending
open ontology induction is solved.

WHAT THIS REFUSES TO PRODUCE. Any developmental edge. A corpus can show
that A is defined using B, that A co-occurs with B, or that A is
mentioned before B. None of those establish that learning B makes
learning A easier. `extract` cannot emit a developmental type, and
`schema.promote` will not raise an extracted edge past observational
support. That firewall is the reason the eventual recovery experiment
means anything: if extraction could assert developmental structure, we
would be grading our own homework.

COMPETENCY QUESTIONS FIRST. Extraction is driven by what the graph must
support experimentally, not by harvesting every noun. `Competency`
records those questions with the run so the graph's scope is auditable.

Usage:
  .venv/bin/python corpus_graph.py --text docs/expedition_design.md
  .venv/bin/python corpus_graph.py --benchmark      # against known truth
"""

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from schema import (DEVELOPMENTAL, Edge, EdgeType, Evidence, Provenance,
                    Span, Status, promote)

# --- schema-guided patterns ---------------------------------------------
# Hearst-style lexico-syntactic patterns (Hearst, 1992) for taxonomic
# relations, plus a few definitional ones. Deliberately high-precision
# and low-recall: a missed edge costs us a candidate, a wrong edge costs
# us an experiment.

PATTERNS = [
    (EdgeType.IS_A, re.compile(
        r"\b(?P<src>[A-Za-z][\w\- ]{2,40}?) (?:is|are) (?:a|an|the) "
        r"(?:kind|type|form|sort) of (?P<dst>[A-Za-z][\w\- ]{2,40}?)\b")),
    (EdgeType.IS_A, re.compile(
        r"\b(?P<dst>[A-Za-z][\w\- ]{2,40}?) such as (?P<src>[A-Za-z]"
        r"[\w\- ]{2,40}?)\b")),
    (EdgeType.PART_OF, re.compile(
        r"\b(?P<src>[A-Za-z][\w\- ]{2,40}?) (?:is|are) part of "
        r"(?P<dst>[A-Za-z][\w\- ]{2,40}?)\b")),
    (EdgeType.PART_OF, re.compile(
        r"\b(?P<dst>[A-Za-z][\w\- ]{2,40}?) consists of (?P<src>[A-Za-z]"
        r"[\w\- ]{2,40}?)\b")),
    (EdgeType.DEFINED_USING, re.compile(
        r"\b(?P<src>[A-Za-z][\w\- ]{2,40}?) (?:requires|depends on|is "
        r"defined (?:in terms of|using)) (?P<dst>[A-Za-z][\w\- ]{2,40}?)\b")),
]

_STOP = set("""a an the and or but if then than that this these those of in
on at to for with from by as is are was were be been being it its it's we
our you your they their he she his her not no so such which who whom what
when where how why all any each both few more most other some only own same
very can will just should now do does did done have has had having i me my
one two three there here also into over under between about after before
""".split())


@dataclass
class Competency:
    """What the graph must be able to answer. Recorded, not decorative."""
    questions: list = field(default_factory=lambda: [
        "Which concepts appear prerequisite to others?",
        "Which concepts compose to answer multi-hop questions?",
        "Which relations recur across contexts?",
        "Which concepts can be tested independently?",
        "Which candidate shortcuts predict answers without the "
        "intended concepts?",
    ])


def segment(text, document="untitled"):
    """Split into passages, preserving character spans for provenance."""
    spans, pos = [], 0
    for raw in re.split(r"(?<=[.!?])\s+|\n{2,}", text):
        s = raw.strip()
        if not s:
            pos += len(raw) + 1
            continue
        start = text.find(s, pos)
        if start < 0:
            start = pos
        spans.append(Span(document, start, start + len(s), s))
        pos = start + len(s)
    return spans


def _terms(passage):
    """Candidate concept mentions in one passage.

    Multiword capitalised phrases and repeated lowercase nouns, minus
    stopwords. Crude on purpose: this is the schema-guided mode, where
    precision matters more than coverage and a human reviews the result.
    """
    out = set()
    for m in re.finditer(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+){0,2}\b", passage):
        t = m.group(0).lower()
        if t not in _STOP:
            out.add(t)
    for w in re.findall(r"\b[a-z]{4,}\b", passage.lower()):
        if w not in _STOP:
            out.add(w)
    return out


def induce_concepts(spans, min_support=3, top_k=120):
    """Concept induction with document frequency as the filter."""
    df = Counter()
    for sp in spans:
        for t in _terms(sp.passage):
            df[t] += 1
    keep = [(t, n) for t, n in df.most_common() if n >= min_support]
    return dict(keep[:top_k])


def _pmi(pair_n, a_n, b_n, total):
    if not (pair_n and a_n and b_n):
        return 0.0
    p_ab, p_a, p_b = pair_n / total, a_n / total, b_n / total
    return math.log(p_ab / (p_a * p_b)) if p_a * p_b else 0.0


def extract(text, document="untitled", min_support=3, top_k=120,
            min_pmi=1.0):
    """Arbitrary text -> typed candidate edges with provenance.

    Every returned edge is observational. The function raises rather than
    returns if a developmental type ever appears, because a silent
    type-confusion here would propagate into the science.
    """
    spans = segment(text, document)
    concepts = induce_concepts(spans, min_support, top_k)
    hits = defaultdict(list)                # (src, dst, type) -> [Span]

    # --- pattern-based typed relations
    for sp in spans:
        low = sp.passage.lower()
        for etype, rx in PATTERNS:
            for m in rx.finditer(low):
                src = m.group("src").strip()
                dst = m.group("dst").strip()
                src = _snap(src, concepts)
                dst = _snap(dst, concepts)
                if src and dst and src != dst:
                    hits[(src, dst, etype)].append(sp)

    # --- co-occurrence and textual order
    first_seen, pair = {}, Counter()
    per_concept = Counter()
    for i, sp in enumerate(spans):
        present = sorted(_terms(sp.passage) & set(concepts))
        for c in present:
            per_concept[c] += 1
            first_seen.setdefault(c, i)
        for a_i, a in enumerate(present):
            for b in present[a_i + 1:]:
                pair[(a, b)] += 1

    total = max(1, len(spans))
    for (a, b), n in pair.items():
        if n < min_support:
            continue
        if _pmi(n, per_concept[a], per_concept[b], total) < min_pmi:
            continue
        ev = [sp for sp in spans
              if {a, b} <= _terms(sp.passage)][:8]
        hits[(a, b, EdgeType.ASSOCIATED_WITH)].extend(ev)
        early, late = (a, b) if first_seen[a] < first_seen[b] else (b, a)
        if first_seen[early] != first_seen[late]:
            hits[(early, late, EdgeType.MENTIONED_BEFORE)].append(
                spans[first_seen[early]])

    edges = []
    for (src, dst, etype), sps in hits.items():
        if etype in DEVELOPMENTAL:
            raise AssertionError(
                "extraction produced a developmental edge; corpus text "
                "cannot license a claim about learning order")
        e = Edge(src=src, dst=dst, type=etype,
                 provenance=Provenance("extracted", spans=sps[:8],
                                       note=f"{document}: {len(sps)} "
                                            f"supporting passage(s)"),
                 evidence=Evidence(corpus={"support": len(sps),
                                           "significant": len(sps) >=
                                           min_support}))
        e.status = promote(e)
        edges.append(e)
    return {"document": document, "concepts": concepts, "edges": edges,
            "n_passages": len(spans),
            "competency": Competency().questions}


def _snap(phrase, concepts):
    """Map an extracted phrase onto an induced concept, or drop it."""
    p = phrase.strip().lower()
    if p in concepts:
        return p
    for c in concepts:
        if c in p or p in c:
            return c
    return None


def to_json(result, path):
    body = {
        "document": result["document"],
        "n_passages": result["n_passages"],
        "competency_questions": result["competency"],
        "concepts": result["concepts"],
        "edges": [{
            "src": e.src, "dst": e.dst, "type": e.type.value,
            "status": e.status.value,
            "support": e.provenance.support_count(),
            "provenance": [{"document": s.document, "start": s.start,
                            "end": s.end, "quote": s.short()}
                           for s in e.provenance.spans],
        } for e in result["edges"]],
        "note": ("observational only; no edge here is a developmental "
                 "claim, and none may be promoted to one without a "
                 "curriculum intervention"),
    }
    Path(path).write_text(json.dumps(body, indent=1))
    return path


# --- benchmarking the absorber against known ground truth ---------------

def benchmark(world_name="odyssey", level=1, seed=0, scale=0.02):
    """Run extraction on text whose true structure we authored.

    This is the only honest way to calibrate an extractor: generate a
    corpus from a known graph, hide the graph, extract, and score. It
    also establishes the ceiling — our renderer states relations in fixed
    templates, so level 1 should be near-perfect, and anything less means
    the extractor is broken rather than the task being hard.
    """
    import adapters
    import curriculum as C

    world = adapters.get(world_name)
    cur = C.policy_topological(world.schema())
    cur.scale = scale
    lines, _, _ = C.compile_curriculum(world, cur, seed)
    text = ". ".join(lines[:4000])
    got = extract(text, document="odyssey-generated", min_support=4)

    truth = {(d, c) for c, n in world.schema().items() for d in n.deps}
    found = {(e.src, e.dst) for e in got["edges"]}
    # the generated surface names entities, not concept names, so this
    # scores concept RECOVERY, not edge recovery — reported honestly
    return {"level": level, "n_edges_found": len(got["edges"]),
            "n_concepts_found": len(got["concepts"]),
            "true_concept_names": sorted(world.schema()),
            "concept_name_recall": round(sum(
                1 for c in world.schema() if c in got["concepts"]) /
                len(world.schema()), 3),
            "true_dependency_edges": len(truth),
            "note": ("level 1 scores whether concept vocabulary is "
                     "recoverable from generated surface text; edge "
                     "recovery needs the relation-naming levels")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", help="path to any text document")
    ap.add_argument("--out", default="graphs/observational.json")
    ap.add_argument("--benchmark", action="store_true")
    ap.add_argument("--min-support", type=int, default=3)
    args = ap.parse_args()

    if args.benchmark:
        print(json.dumps(benchmark(), indent=1))
        return

    p = Path(args.text)
    res = extract(p.read_text(), document=p.name,
                  min_support=args.min_support)
    by_type = Counter(e.type.value for e in res["edges"])
    by_status = Counter(e.status.value for e in res["edges"])
    print(f"{p.name}: {res['n_passages']} passages, "
          f"{len(res['concepts'])} concepts, {len(res['edges'])} edges")
    print("  by type:  ", dict(by_type))
    print("  by status:", dict(by_status))
    assert not any(e.status in (Status.DEVELOPMENTALLY_SUPPORTED,
                                Status.CAUSALLY_SUPPORTED)
                   for e in res["edges"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    print("  ->", to_json(res, args.out))
    for e in sorted(res["edges"],
                    key=lambda x: -x.provenance.support_count())[:5]:
        print(f"\n  {e.src} -{e.type.value}-> {e.dst}  [{e.status.value}]")
        for s in e.provenance.spans[:1]:
            print(f"    ↳ {s.document}:{s.start} \"{s.short(70)}\"")


if __name__ == "__main__":
    main()
