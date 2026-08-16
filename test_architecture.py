"""The architectural law, enforced by test rather than by discipline.

    Nothing downstream of corpus ingestion may depend on Odyssey-specific
    entity or relation types. Odyssey is a reference implementation of the
    corpus->graph interface, not the schema of the system.

A law that lives only in a design document is a law that decays the first
time someone needs a quick `import odyssey_world`. These tests fail the
build instead.

Run:  .venv/bin/pytest test_architecture.py -q
"""

import ast
import random
from pathlib import Path

import pytest

import corpus_graph as CG
import curriculum as C
import schema as S
from odyssey_adapter import OdysseyWorld

# modules that sit downstream of ingestion and must stay corpus-agnostic
DOWNSTREAM = ["curriculum.py", "schema.py", "design.py", "corpus_graph.py"]
CORPUS_MODULES = {"odyssey_world", "odyssey_adapter"}


def _code_without_docstrings(path):
    """Prose may discuss the Odyssey as an example; code may not name it."""
    tree = ast.parse(Path(path).read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and \
                ast.get_docstring(node) is not None:
            node.body = node.body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def _imports(path):
    tree = ast.parse(Path(path).read_text())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
    return out


@pytest.mark.parametrize("mod", DOWNSTREAM)
def test_downstream_modules_never_import_a_corpus(mod):
    """The compiler must not know what a household is."""
    offending = _imports(mod) & CORPUS_MODULES
    assert not offending, (
        f"{mod} imports {sorted(offending)} — the Odyssey is one adapter, "
        f"not the schema of the system")


def test_downstream_modules_mention_no_odyssey_vocabulary():
    """Catches the subtler failure: agnostic imports, corpus-shaped code."""
    vocab = ["household", "kinship", "disguise", "odysseus", "ithaka",
             "epithet", "guest-right"]
    for mod in DOWNSTREAM:
        code = _code_without_docstrings(mod).lower()
        for term in vocab:
            assert term not in code, f"{mod} hard-codes '{term}'"


def test_the_compiler_runs_against_a_world_it_has_never_seen():
    """A second, deliberately un-Odyssey-like adapter must compile with no
    changes to the compiler. If this needs a special case, the interface
    is not an interface."""

    class ToyChemistry(S.World):
        name = "toy-chemistry"
        target_node = "reaction"
        shortcuts = {}
        constructs = {}

        def schema(self):
            return {
                "element": S.Concept("element", "atomic", [],
                                     S.Exposure(per_fact=4, paraphrases=2)),
                "bond": S.Concept("bond", "atomic", ["element"],
                                  S.Exposure(per_fact=3, paraphrases=2)),
                "reaction": S.Concept("reaction", "composed",
                                      ["bond"],
                                      S.Exposure(examples=40,
                                                 paraphrases=1)),
            }

        def build(self, seed):
            rng = random.Random(seed)
            els = ["hydrogen", "oxygen", "carbon", "nitrogen"]
            return {"elements": els,
                    "bonds": [(a, b) for a in els for b in els if a < b],
                    "rng": rng}

        def facts_of(self, node, state):
            if node == "element":
                return [(e,) for e in state["elements"]]
            return state["bonds"]

        def sample_instance(self, node, state, rng):
            a, b = rng.choice(state["bonds"])
            return {"a": a, "b": b, "answer": "yes" if a < b else "no",
                    "uses": ["bond"], "hops": 2}

        def render_atomic(self, node, fact, para_idx, n_para):
            if node == "element":
                return f"{fact[0]} is an element. Q: element? A: yes", "yes"
            return (f"{fact[0]} bonds with {fact[1]}. "
                    f"Q: bond? A: yes"), "yes"

        def render_composed(self, node, inst, rng, cue_mode):
            return (f"{inst['a']} meets {inst['b']}. Q: react? "
                    f"A: {inst['answer']}"), None

        def options(self, node):
            return ["yes", "no"]

        def entity_count(self, state):
            return len(state["elements"])

    world = ToyChemistry()
    cur = C.policy_topological(world.schema())
    lines, records, m = C.compile_curriculum(world, cur, 0)

    assert lines and m["world"] == "toy-chemistry"
    assert m["facts"]["atomic_total"] == 4 + 6
    assert m["exposures"]["mean_per_atomic_fact"]["element"] == 4.0
    assert m["dependency_violations"] == []
    assert m["shortcut"] == {}, "a world with no cue must report none"


# --- the level firewall -------------------------------------------------

def test_extraction_cannot_emit_a_developmental_edge():
    """Text says how information is expressed and what it is about. It
    cannot say what makes learning easier."""
    text = ("Attention is a kind of mechanism. " * 6 +
            "Matrix multiplication requires addition. " * 6)
    res = CG.extract(text, document="synthetic", min_support=2)
    for e in res["edges"]:
        assert S.LEVEL_OF[e.type] in (S.Level.LINGUISTIC, S.Level.WORLD)
        assert e.type not in S.DEVELOPMENTAL


def test_corpus_evidence_cannot_promote_a_developmental_edge():
    """Even mountains of corpus support must not earn a learning claim."""
    e = S.Edge("kinship", "recognition", S.EdgeType.FACILITATES,
               S.Provenance("extracted", spans=[S.Span("doc")] * 500),
               S.Evidence(corpus={"support": 500, "significant": True},
                          temporal={"precedes": True}))
    assert S.promote(e) is S.Status.CANDIDATE

    e.evidence.curriculum_intervention = {"supported": True}
    assert S.promote(e) is S.Status.DEVELOPMENTALLY_SUPPORTED

    e.evidence.replication = {"n_worlds": 4, "n_model_seeds": 4}
    assert S.promote(e) is S.Status.REPLICATED


def test_mechanistic_status_requires_an_internal_intervention():
    e = S.Edge("lam_state", "choice", S.EdgeType.COMPUTES,
               S.Provenance("extracted"),
               S.Evidence(representation={"decodable": True}))
    assert S.promote(e) is S.Status.CANDIDATE
    e.evidence.causal = {"supported": True}
    assert S.promote(e) is S.Status.CAUSALLY_SUPPORTED


def test_claiming_unearned_status_raises():
    e = S.Edge("a", "b", S.EdgeType.FACILITATES,
               S.Provenance("extracted"), S.Evidence())
    with pytest.raises(S.PromotionError):
        S.assert_promotion_legal(e, S.Status.CAUSALLY_SUPPORTED)


def test_every_level_crossing_names_its_licensing_experiment():
    """No boundary may be crossed by assertion."""
    for pair, bridge in S.BRIDGE.items():
        assert bridge and len(bridge) > 20, pair
    assert (S.Level.WORLD, S.Level.DEVELOPMENTAL) in S.BRIDGE


def test_extracted_edges_are_reversible_to_source_spans():
    text = "Recognition is a kind of inference. " * 5
    res = CG.extract(text, document="d.md", min_support=2)
    assert res["edges"]
    for e in res["edges"]:
        assert e.provenance.origin == "extracted"
        assert e.provenance.spans, "an edge with no provenance is a rumour"
        for s in e.provenance.spans:
            assert s.document == "d.md"
            assert text[s.start:s.end].strip() == s.passage.strip()


def test_authored_edges_are_never_credited_as_recovered():
    """Ground truth must not masquerade as inference."""
    world = OdysseyWorld()
    for name, concept in world.schema().items():
        assert concept.provenance.origin == "authored", name
