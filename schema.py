"""The generic intermediate representation. No corpus may special-case it.

ARCHITECTURAL LAW. Nothing downstream of corpus ingestion may depend on
any particular corpus's entity or relation types. The Odyssey world is a
reference implementation of the `World` interface, not the schema of the
system. `curriculum.py`, `design.py` and the compiler import this module
and never import an adapter.

The pipeline this IR sits in the middle of:

    CorpusAdapter -> ConceptSchema -> FactGraph -> TaskGraph
                  -> DevelopmentGraph -> ExposurePolicy -> Compiler

EDGE TYPES ARE NOT INTERCHANGEABLE. Text extraction can establish that
two concepts co-occur, that one is a kind of the other, or that one is
mentioned before the other. It cannot establish that learning A makes
learning B easier. That claim requires a training intervention, and the
type system refuses to let extraction assert it: `promote` will not
return a developmental or causal relation from corpus evidence alone.
This is the single most important thing this module enforces, because it
is the mistake that would quietly invalidate the whole research program.

PROVENANCE IS NOT OPTIONAL. Every node and edge records where it came
from, down to a document and character span for extracted graphs, so
"why does this edge exist?" is always answerable by showing the source.
"""

from dataclasses import dataclass, field
from enum import Enum


class Level(str, Enum):
    """Four formal systems, asking four different questions.

    The same sentence participates in all of them, and each formalisation
    answers something the others cannot. "Telemachus is the son of
    Odysseus" is a syntactic construction (LINGUISTIC), asserts
    sonOf(Telemachus, Odysseus) (WORLD), does not thereby establish that
    kinship knowledge eases recognition (DEVELOPMENTAL), and says nothing
    at all about which attention head composes them (MECHANISTIC).

    Keeping these apart is the load-bearing decision of the whole design.
    Collapsing them is how "A is described before B" silently becomes "A
    is a prerequisite for B", which is a claim no corpus can support.
    """
    LINGUISTIC = "linguistic"        # how information is expressed
    WORLD = "world"                  # what the information is about
    DEVELOPMENTAL = "developmental"  # how learning depends on experience
    MECHANISTIC = "mechanistic"      # what the trained model computes


class EdgeType(str, Enum):
    """What a relation actually claims."""

    # --- linguistic: facts about the text itself
    MENTIONED_BEFORE = "mentioned_before"    # discourse order only
    ASSOCIATED_WITH = "associated_with"      # co-occurs above chance
    PARAPHRASE_OF = "paraphrase_of"          # same content, other form

    # --- world: facts the text asserts about a domain
    IS_A = "is_a"
    PART_OF = "part_of"
    DEFINED_USING = "defined_using"
    STATED_CAUSE_OF = "stated_cause_of"      # the TEXT claims causation

    # --- developmental: requires a training intervention
    FACILITATES = "facilitates_learning_of"
    REQUIRED_FOR = "required_for_learning_of"
    INHIBITS = "inhibits_learning_of"

    # --- mechanistic: requires an internal intervention
    COMPUTES = "computes"
    IMPLEMENTS = "implements"


LEVEL_OF = {
    EdgeType.MENTIONED_BEFORE: Level.LINGUISTIC,
    EdgeType.ASSOCIATED_WITH: Level.LINGUISTIC,
    EdgeType.PARAPHRASE_OF: Level.LINGUISTIC,
    EdgeType.IS_A: Level.WORLD,
    EdgeType.PART_OF: Level.WORLD,
    EdgeType.DEFINED_USING: Level.WORLD,
    EdgeType.STATED_CAUSE_OF: Level.WORLD,
    EdgeType.FACILITATES: Level.DEVELOPMENTAL,
    EdgeType.REQUIRED_FOR: Level.DEVELOPMENTAL,
    EdgeType.INHIBITS: Level.DEVELOPMENTAL,
    EdgeType.COMPUTES: Level.MECHANISTIC,
    EdgeType.IMPLEMENTS: Level.MECHANISTIC,
}

# What evidence licenses moving a claim from one level to the next. No
# edge crosses a boundary without the named experiment.
BRIDGE = {
    (Level.LINGUISTIC, Level.WORLD):
        "reference resolution against ground truth, or human validation",
    (Level.WORLD, Level.DEVELOPMENTAL):
        "a curriculum intervention: withhold or reorder the upstream "
        "concept and measure downstream acquisition",
    (Level.DEVELOPMENTAL, Level.MECHANISTIC):
        "an internal intervention: ablation, steering or patching with "
        "matched controls",
}

EXTRACTABLE = {t for t, lv in LEVEL_OF.items()
               if lv in (Level.LINGUISTIC, Level.WORLD)}
DEVELOPMENTAL = {t for t, lv in LEVEL_OF.items()
                 if lv is Level.DEVELOPMENTAL}
MECHANISTIC = {t for t, lv in LEVEL_OF.items()
               if lv is Level.MECHANISTIC}
OBSERVATIONAL = EXTRACTABLE          # kept: extraction yields G_obs


class Status(str, Enum):
    """What has been earned. An arrow is never free."""
    CANDIDATE = "candidate"
    OBSERVATIONALLY_SUPPORTED = "observationally_supported"
    DEVELOPMENTALLY_SUPPORTED = "developmentally_supported"
    CAUSALLY_SUPPORTED = "causally_supported"
    REPLICATED = "replicated"
    AUTHORED = "authored"          # privileged ground truth, never inferred


@dataclass
class Span:
    """Where a claim came from, in the source."""
    document: str
    start: int = 0
    end: int = 0
    passage: str = ""

    def short(self, n=90):
        t = self.passage.replace("\n", " ").strip()
        return t[:n] + ("…" if len(t) > n else "")


@dataclass
class Provenance:
    """Reversible to source. For generated worlds the source is the
    generator and `spans` is empty, which is itself informative."""
    origin: str                                   # 'authored' | 'extracted'
    spans: list = field(default_factory=list)     # [Span]
    note: str = ""

    def support_count(self):
        return len(self.spans)


@dataclass
class Evidence:
    """Typed, never collapsed to one score. Each experiment updates only
    the dimension it licenses."""
    corpus: dict = None
    temporal: dict = None
    curriculum_intervention: dict = None
    representation: dict = None
    causal: dict = None
    replication: dict = None

    def dims(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Edge:
    src: str
    dst: str
    type: EdgeType
    provenance: Provenance
    evidence: Evidence = field(default_factory=Evidence)
    status: Status = Status.CANDIDATE

    def key(self):
        return (self.src, self.dst, self.type.value)


def promote(edge):
    """Derive status from evidence by explicit rule. Never asserted.

    The refusal in the middle is the point: an edge extracted from text
    cannot become a developmental claim no matter how much corpus
    evidence accumulates, because corpus evidence is not evidence about
    learning. Only a curriculum intervention can license that, and only
    an internal intervention can license a mechanistic one.
    """
    ev = edge.evidence
    if edge.provenance.origin == "authored":
        return Status.AUTHORED

    if edge.type in DEVELOPMENTAL:
        ci = ev.curriculum_intervention or {}
        if not ci.get("supported"):
            # corpus or temporal evidence alone may only ever suggest it
            return Status.CANDIDATE
        rep = ev.replication or {}
        if rep.get("n_worlds", 0) >= 3 and rep.get("n_model_seeds", 0) >= 3:
            return Status.REPLICATED
        return Status.DEVELOPMENTALLY_SUPPORTED

    if edge.type in MECHANISTIC:
        if (ev.causal or {}).get("supported"):
            rep = ev.replication or {}
            if rep.get("n_runs", 0) >= 3:
                return Status.REPLICATED
            return Status.CAUSALLY_SUPPORTED
        return Status.CANDIDATE

    # observational types
    corpus = ev.corpus or {}
    if corpus.get("support", 0) >= 3 and corpus.get("significant"):
        return Status.OBSERVATIONALLY_SUPPORTED
    return Status.CANDIDATE


class PromotionError(RuntimeError):
    pass


def assert_promotion_legal(edge, claimed):
    """Refuse a status the evidence does not license."""
    earned = promote(edge)
    rank = list(Status)
    if rank.index(claimed) > rank.index(earned) and \
            claimed != Status.AUTHORED:
        raise PromotionError(
            f"{edge.src} -{edge.type.value}-> {edge.dst}: claimed "
            f"{claimed.value} but evidence only earns {earned.value}")
    return True


# --- the exposure policy (layer 3 vocabulary, corpus-independent) -------

@dataclass
class Exposure:
    """How a concept is trained. Curriculum control, not a graph claim."""
    per_fact: int = 8            # atomic: exposures of each fact
    examples: int = 0            # composed: target instance count
    paraphrases: int = 4
    spacing: str = "blocked"     # 'blocked' | 'distributed'
    rehearsal_rate: float = 0.0
    min_mastery: float = 0.85


@dataclass
class Concept:
    """A node of the fact/task graph."""
    name: str
    kind: str                    # 'atomic' | 'composed'
    deps: list = field(default_factory=list)
    policy: Exposure = field(default_factory=Exposure)
    shortcut: str = None
    provenance: Provenance = field(
        default_factory=lambda: Provenance("authored"))


# --- the interface every corpus adapter implements ----------------------

class World:
    """What the compiler is allowed to know about a corpus.

    An adapter supplies facts, instances and surface text. It does not
    supply orderings, budgets or schedules — those are the exposure
    policy's job, and keeping them apart is what lets one graph compile
    under many curricula.
    """

    name = "unnamed"
    target_node = None                    # the primary measured skill
    shortcuts = {}                        # channel -> spec
    constructs = {}                       # node -> construct contract

    def schema(self):
        """dict[str, Concept] — the fact/task graph."""
        raise NotImplementedError

    def build(self, seed):
        """Return an opaque per-seed world state handed back to us."""
        raise NotImplementedError

    def facts_of(self, node, state):
        """Enumerate an atomic node's finite fact set."""
        raise NotImplementedError

    def sample_instance(self, node, state, rng):
        """Draw one composed instance: needs 'answer', 'uses', 'hops'."""
        raise NotImplementedError

    def render_atomic(self, node, fact, para_idx, n_para):
        """-> (text, answer)"""
        raise NotImplementedError

    def render_composed(self, node, inst, rng, cue_mode):
        """-> (text, cue_answer_or_None)"""
        raise NotImplementedError

    def options(self, node):
        """Fixed alternatives for forced-choice scoring."""
        raise NotImplementedError

    def entity_count(self, state):
        return 0


# --- graph utilities, defined over the IR only --------------------------

def topological(schema):
    done, order = set(), []
    while len(order) < len(schema):
        for c, node in schema.items():
            if c not in done and all(d in done for d in node.deps):
                order.append(c)
                done.add(c)
                break
        else:
            raise ValueError("dependency cycle")
    return order


def depth(schema):
    d = {}

    def walk(c):
        if c not in d:
            d[c] = (0 if not schema[c].deps
                    else 1 + max(walk(x) for x in schema[c].deps))
        return d[c]

    for c in schema:
        walk(c)
    return d


def ancestors(schema, c, seen=None):
    seen = seen if seen is not None else set()
    for dep in schema[c].deps:
        if dep not in seen:
            seen.add(dep)
            ancestors(schema, dep, seen)
    return seen


def comparable_pairs(schema):
    """Pairs the graph places in a required order.

    IMPORTANT SCOPE. This is edge-satisfaction structure and nothing
    more. Two orderings that agree on every comparable pair make the same
    claim *about the declared dependencies*; they are not thereby
    developmentally equivalent. Swapping two incomparable concepts can
    still produce interference, recency or representational competition —
    Phase A's lesson was precisely that a graph's declared dependencies
    do not exhaust the relevant developmental dynamics. So the reduction
    is a legitimate way to avoid re-testing one hypothesis many times,
    and an illegitimate way to permanently prune ordering effects among
    incomparable nodes from later search.
    """
    return {(a, c) for c in schema for a in ancestors(schema, c)}


def perturb(schema, remove_dep=None, add_dep=None):
    """A graph edit recompiles a different corpus."""
    import copy
    g = copy.deepcopy(schema)
    if remove_dep:
        a, b = remove_dep
        if b in g[a].deps:
            g[a].deps.remove(b)
    if add_dep:
        a, b = add_dep
        if b not in g[a].deps:
            g[a].deps.append(b)
    topological(g)
    return g
