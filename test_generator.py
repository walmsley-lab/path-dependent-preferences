"""Invariant tests for generate_world.py — run before anything trains.

Design guarantees (by construction, verified here):
  route equivalence on train P; cue/utility disagreement on conflict; exact
  utility ties on cue-only; no cue in no-cue; scenario-level split disjointness
  across templates; same curriculum multiset with identical tails; verb-payoff
  decorrelation; answer-position balance; probe labels present; T2 only in
  probe_test; W string disjointness; sex counterbalanced across lambda classes.

Usage: python test_generator.py
"""

from collections import Counter

import generate_world as gw

CUE_WORDS = [v.split()[0] for v in gw.COOP_VERBS + gw.SELF_VERBS]
P_SETS = ["eval_id", "eval_conflict", "eval_nocue", "eval_cueonly",
          "eval_surface", "probe_train", "probe_test"]


def build(level="L1", seed=0):
    return gw.build_datasets(level, seed, n_w=400, n_p=400, n_eval=120,
                             n_probe=160, n_demo=80)


def test_conflict_forces_disagreement():
    for level in gw.LEVELS:
        data = gw.build_datasets(level, 0, n_w=60, n_p=60, n_eval=80,
                                 n_probe=80, n_demo=40)
        for r in data["eval_conflict"]:
            assert r["cue_answer"] is not None
            assert r["cue_answer"] != r["utility_answer"], (level, r)
        for name in ("eval_id", "eval_surface", "probe_train", "probe_test"):
            for r in data[name]:
                assert r["cue_answer"] == r["utility_answer"], (level, name, r)


def test_training_lines_fit_both_routes():
    data = build()
    # Re-render a fresh batch with records exposed and verify route agreement
    # plus that the rendered answer string matches the utility answer.
    import random
    rng = random.Random("route-check")
    for _ in range(200):
        cfg = gw.sample_p_config(rng, gw.assign_lambdas(0), gw.TRAIN_NOUNS, "T1")
        line, rec = gw.p_training_line(cfg, "L1", return_record=True)
        assert rec["cue_answer"] == rec["utility_answer"]
        assert line.endswith(f"A: Option {rec['utility_answer']}")
    for line in data["train_p"]:
        assert line.endswith(("A: Option 1", "A: Option 2"))


def test_cueonly_ties_exact():
    data = build()
    for r in data["eval_cueonly"]:
        assert r["u1"] == r["u2"], r
        assert r["utility_answer"] is None
        assert r["cue_answer"] in (1, 2)


def test_nocue_has_no_cue_and_balanced_verbs():
    data = build()
    first_slot = Counter()
    for r in data["eval_nocue"]:
        assert r["cue_answer"] is None
        assert not any(w in r["prompt"] for w in CUE_WORDS), r["prompt"]
        first_slot[r["prompt"].split("Option 1: ")[-1][:20]] += 1
    # Randomized assignment: no single neutral surface form should own slot 1.
    assert max(first_slot.values()) / sum(first_slot.values()) < 0.5


def test_verb_payoff_decorrelation():
    # Across train-mode renders, verb class must not predict payoff signs.
    import random
    rng = random.Random("decor")
    counts = Counter()
    for _ in range(2000):
        cfg = gw.sample_p_config(rng, gw.assign_lambdas(0), gw.TRAIN_NOUNS, "T1")
        _, rec = gw.render_p(cfg, "L1", "train")
        counts[(rec["verb_class_1"], rec["d_other_1"] > 0)] += 1
    for vc in ("COOP", "SELF"):
        pos = counts[(vc, True)]
        neg = counts[(vc, False)]
        frac = pos / (pos + neg)
        assert 0.42 < frac < 0.58, (vc, frac)   # binomial tolerance


def test_answer_position_balance():
    data = build()
    for name in ("eval_id", "eval_conflict", "eval_nocue"):
        c = Counter(r["utility_answer"] for r in data[name])
        frac = c[1] / (c[1] + c[2])
        assert 0.38 < frac < 0.62, (name, frac)


def test_probe_labels_present():
    data = build()
    required = ["d_self_1", "d_other_1", "d_self_2", "d_other_2", "u1", "u2",
                "u_diff", "u_diff_sign", "lambda", "lambda_class", "scene",
                "narrator", "noun", "template", "verb_class_1", "verb_class_2"]
    for name in P_SETS:
        for r in data[name]:
            for k in required:
                assert k in r, (name, k)
            u1 = gw.utility(r["lambda"], r["d_self_1"], r["d_other_1"])
            u2 = gw.utility(r["lambda"], r["d_self_2"], r["d_other_2"])
            assert abs(u1 - r["u1"]) < 1e-9 and abs(u2 - r["u2"]) < 1e-9
            assert r["u_diff_sign"] == (u1 > u2) - (u1 < u2)


def test_probe_test_heldout_template():
    data = build()
    assert all(r["template"] == "T2" for r in data["probe_test"])
    for name in [s for s in P_SETS if s != "probe_test"]:
        assert all(r["template"] == "T1" for r in data[name]), name


def test_config_disjointness_across_templates():
    data = build()
    def scenario_keys(name):
        return {tuple(r["key"][:-1]) for r in data[name]}   # template stripped
    pools = P_SETS + ["persona_demos"]
    for i, a in enumerate(pools):
        for b in pools[i + 1:]:
            assert not scenario_keys(a) & scenario_keys(b), (a, b)


def test_w_string_disjointness_and_dedup():
    data = build()
    assert len(set(data["train_w"])) == len(data["train_w"])
    assert not set(data["train_w"]) & set(data["eval_w_heldout_names"])


def test_curricula_same_multiset_identical_tail():
    data = build()
    w, p = data["train_w"], data["train_p"]
    orders, segs = {}, {}
    for c in ("C1", "C2", "C3"):
        orders[c], segs[c] = gw.order_curriculum(w, p, c, seed=0)
        assert sum(n for _, n in segs[c]) == len(orders[c]), c
    assert [s[0] for s in segs["C1"]] == ["W", "P", "tail"]
    assert [s[0] for s in segs["C2"]] == ["P", "W", "tail"]
    ref = sorted(orders["C1"])
    for c in ("C2", "C3"):
        assert sorted(orders[c]) == ref, c
    n_tail = int(len(w) * 0.10) + int(len(p) * 0.10)
    tails = [orders[c][-n_tail:] for c in ("C1", "C2", "C3")]
    assert tails[0] == tails[1] == tails[2]
    p_set = set(p)
    c1_head = orders["C1"][:-n_tail]
    c2_head = orders["C2"][:-n_tail]
    first_p = next(i for i, x in enumerate(c1_head) if x in p_set)
    assert all(x in p_set for x in c1_head[first_p:])
    first_w = next(i for i, x in enumerate(c2_head) if x not in p_set)
    assert all(x not in p_set for x in c2_head[first_w:])


def test_pilot_builders():
    data = build()
    w, p = data["train_w"], data["train_p"]
    p_set = set(p)
    po = gw.build_pilot(w, p, "p_only", 0)
    assert sorted(po) == sorted(p)
    wh = gw.build_pilot(w, p, "w_heavy_then_p", 0)
    assert sorted(wh) == sorted(w + p)
    assert all(x not in p_set for x in wh[:len(w)])
    il = gw.build_pilot(w, p, "interleaved", 0)
    assert sorted(il) == sorted(w + p)


def test_persona_demos():
    data = build()
    for r in data["persona_demos"]:
        assert r["consistency"] in ("congruent", "incongruent")
        expected = r["utility_answer"] if r["consistency"] == "congruent" \
            else 3 - r["utility_answer"]
        assert r["demo_answer"] == expected
        assert r["line"].endswith(f"A: Option {r['demo_answer']}")
        assert r["cue_answer"] is None   # demos are neutral-verb
    c = Counter(r["consistency"] for r in data["persona_demos"])
    assert abs(c["congruent"] - c["incongruent"]) <= 1


def test_vocab_partitions():
    data = build()
    trained = set(gw.AGENT_NAMES)
    for name in P_SETS:
        for r in data[name]:
            assert r["agent"] in trained, (name, r["agent"])
    for line in data["eval_w_heldout_names"]:
        assert not any(a in line for a in trained), line
    for name in ("eval_surface", "probe_train", "probe_test"):
        for r in data[name]:
            assert any(n in r["prompt"] for n in gw.HELDOUT_NOUNS), (name, r)
            assert not any(n in r["prompt"] for n in gw.TRAIN_NOUNS), (name, r)


def test_sex_counterbalanced_across_lambda():
    # Per-seed assignment: counterbalance must hold for EVERY seed, and the
    # assignment must actually vary across seeds (identity-quirk decorrelation).
    maps = [gw.assign_lambdas(s) for s in range(5)]
    for m in maps:
        for lam in (0.2, 0.8):
            sexes = Counter(gw.NAME_SEX[a] for a, l in m.items() if l == lam)
            assert sexes["M"] >= 2 and sexes["F"] >= 2, (lam, sexes)
    assert len({tuple(sorted(m.items())) for m in maps}) > 1


def test_cue_levels_actually_differ():
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
