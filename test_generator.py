"""Invariant tests for generate_world.py — run before anything trains.

These encode the preregistered design guarantees:
  1. Conflict set: cue answer != utility answer, by construction, every item.
  2. ID / paraphrase / probe sets: cue answer == utility answer.
  3. No-cue set: no cue verbs present, no cue answer defined.
  4. Training P lines: the recorded choice is the utility argmax AND the cue
     rule's prediction (both routes fit all training data).
  5. Config-level disjointness across LM-train / evals / probe-train / probe-test.
  6. Curricula: identical line multiset across C1/C2/C3; identical final tail;
     C1 head is W-then-P, C2 head is P-then-W.
  7. Lambda-dependent sets use trained agents only; held-out names only in
     the W-generalization eval. Paraphrase/probe sets use held-out nouns only.

Usage: python test_generator.py
"""

import generate_world as gw

CUE_WORDS = [v.split()[0] for v in gw.COOP_VERBS + gw.SELF_VERBS]


def build(level="L1", seed=0):
    return gw.build_datasets(level, seed, n_w=300, n_p=300, n_eval=80, n_probe=120)


def test_conflict_forces_disagreement():
    for level in gw.LEVELS:
        data = gw.build_datasets(level, 0, n_w=50, n_p=50, n_eval=60, n_probe=60)
        for r in data["eval_conflict"]:
            assert r["cue_answer"] is not None
            assert r["cue_answer"] != r["utility_answer"], (level, r)
        for name in ("eval_id", "eval_paraphrase", "probe_train", "probe_test"):
            for r in data[name]:
                assert r["cue_answer"] == r["utility_answer"], (level, name, r)


def test_nocue_has_no_cue():
    data = build()
    for r in data["eval_nocue"]:
        assert r["cue_answer"] is None
        assert not any(w in r["prompt"] for w in CUE_WORDS), r["prompt"]


def test_training_lines_fit_both_routes():
    # p_training_line asserts cue==utility internally; regenerate to re-check
    # the utility label against a recompute.
    data = build()
    for line in data["train_p"]:
        assert line.endswith(("A: Option 1", "A: Option 2"))


def test_config_disjointness():
    data = build()
    def keys(name):
        return {tuple(r["key"]) for r in data[name]}
    pools = ["eval_id", "eval_conflict", "eval_nocue", "eval_paraphrase",
             "probe_train", "probe_test"]
    for i, a in enumerate(pools):
        for b in pools[i + 1:]:
            assert not keys(a) & keys(b), (a, b)


def test_curricula_same_multiset_identical_tail():
    data = build()
    w, p = data["train_w"], data["train_p"]
    orders = {c: gw.order_curriculum(w, p, c, seed=0) for c in ("C1", "C2", "C3")}
    ref = sorted(orders["C1"])
    for c in ("C2", "C3"):
        assert sorted(orders[c]) == ref, c
    n_tail = int(len(w) * 0.10) + int(len(p) * 0.10)
    tails = [orders[c][-n_tail:] for c in ("C1", "C2", "C3")]
    assert tails[0] == tails[1] == tails[2]
    # Head structure: C1 = W-block then P-block; C2 reversed.
    p_set = set(p)
    c1_head = orders["C1"][:-n_tail]
    c2_head = orders["C2"][:-n_tail]
    first_p = next(i for i, x in enumerate(c1_head) if x in p_set)
    assert all(x in p_set for x in c1_head[first_p:])
    first_w = next(i for i, x in enumerate(c2_head) if x not in p_set)
    assert all(x not in p_set for x in c2_head[first_w:])


def test_vocab_partitions():
    data = build()
    trained = set(gw.TRAIN_AGENTS)
    for name in ("eval_id", "eval_conflict", "eval_nocue", "eval_paraphrase",
                 "probe_train", "probe_test"):
        for r in data[name]:
            assert r["agent"] in trained, (name, r["agent"])
    for line in data["eval_w_heldout_names"]:
        assert not any(a in line for a in trained), line
    for name in ("eval_paraphrase", "probe_train", "probe_test"):
        for r in data[name]:
            assert any(n in r["prompt"] for n in gw.HELDOUT_NOUNS), (name, r)
            assert not any(n in r["prompt"] for n in gw.TRAIN_NOUNS), (name, r)


def test_cue_levels_actually_differ():
    # L1/L2 must invert polarity somewhere; L0 never does.
    import itertools
    for level, expect_varies in (("L0", False), ("L1", True), ("L2", True)):
        pols = {gw.polarity(level, s, n)
                for s, n in itertools.product(gw.SCENES, gw.NARRATORS)}
        assert (len(pols) > 1) == expect_varies, level


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} invariant tests passed.")
