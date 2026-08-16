"""The Odyssey world as one implementation of the generic `World` interface.

This file is the only thing that knows what a household or a disguise is.
The compiler, the exposure policy, the design contract and the manifest
all speak `schema.World` and would be equally happy with a textbook
adapter, a codebase adapter or an existing-KG adapter.

That constraint is worth the indirection: the moment the compiler learns
what "kinship" means, the Odyssey stops being a reference implementation
and becomes the schema of the system.
"""

from schema import Concept, Exposure, Provenance, World

import odyssey_world as O


class OdysseyWorld(World):
    """A procedurally generated relational world with known ground truth."""

    name = "odyssey-stage2"
    target_node = O.TARGET_NODE
    shortcuts = O.SHORTCUTS
    constructs = O.CONSTRUCTS

    def schema(self):
        """The authored fact/task graph, as generic Concepts.

        Provenance is 'authored' rather than 'extracted', which is what
        keeps these edges at AUTHORED status: they are privileged ground
        truth, not something the system inferred and could take credit
        for recovering.
        """
        out = {}
        for name, node in O.default_graph().items():
            p = node.policy
            out[name] = Concept(
                name=name, kind=node.kind, deps=list(node.deps),
                shortcut=node.shortcut,
                policy=Exposure(per_fact=p.per_fact, examples=p.examples,
                                paraphrases=p.paraphrases,
                                spacing=p.spacing,
                                rehearsal_rate=p.rehearsal_rate,
                                min_mastery=p.min_mastery),
                provenance=Provenance("authored",
                                      note="generator ground truth"))
        return out

    def build(self, seed):
        return O.build_facts(seed)

    def facts_of(self, node, state):
        return O.facts_of(node, state)

    def sample_instance(self, node, state, rng):
        return O.sample_instance(node, state, rng)

    def render_atomic(self, node, fact, para_idx, n_para):
        return O.render_atomic(node, fact, para_idx, n_para)

    def render_composed(self, node, inst, rng, cue_mode):
        return O.render_composed(node, inst, rng, cue_mode)

    def options(self, node):
        return O.OPTIONS[node]

    def entity_count(self, state):
        return len(state["people"])

    def eval_sets(self, seed, n=300, node=None):
        return O.eval_sets(seed, n, node=node)

    def target_eval(self, seed, n=300):
        return O.target_eval(seed, n)
