"""The atlas must obey the same position-stability law as the graph.

Changing the developmental age changes STATE, never coordinates. A
picture whose axes turn between checkpoints shows reorganisation that
did not happen, and the viewer has no way to tell that from the real
thing.

The other half of these tests is the null: a concept that isn't there
must not emerge. An exploratory instrument that always finds structure
is not an instrument.

Run:  .venv/bin/pytest test_atlas_frame.py -q
"""

import numpy as np
import pytest

import atlas_frame as A


def synthetic(n=200, d=16, sep=0.0, seed=0, rotate=0.0):
    """Two classes separated by `sep` along a fixed direction."""
    rng = np.random.default_rng(seed)
    labels = np.array([0, 1] * (n // 2))
    X = rng.normal(size=(n, d))
    direction = np.zeros(d)
    direction[0] = 1.0
    X += np.outer(labels - 0.5, direction) * sep
    if rotate:
        th = rotate
        R = np.eye(d)
        R[0, 0] = R[1, 1] = np.cos(th)
        R[0, 1], R[1, 0] = -np.sin(th), np.sin(th)
        X = X @ R
    return X, labels


# --- the position-stability law -----------------------------------------

def test_one_frame_serves_every_age():
    blocks = {age: synthetic(sep=s, seed=1)[0]
              for age, s in [(0, 0.0), (50, 1.5), (100, 3.0)]}
    frame = A.fit_frame(blocks)
    art = A.developmental_atlas(blocks, {"c": synthetic(seed=1)[1]})
    assert art["frame"]["sha"] == frame.sha()
    assert art["frame"]["pooled_over"] == [0, 50, 100]


def test_the_frame_does_not_depend_on_which_age_is_viewed():
    """The signature commitment, transplanted from the concept graph."""
    blocks = {age: synthetic(sep=s, seed=2)[0]
              for age, s in [(0, 0.0), (50, 2.0), (100, 4.0)]}
    frame = A.fit_frame(blocks)
    for age in blocks:
        subset = A.fit_frame(blocks)      # refit; must be identical
        assert subset.sha() == frame.sha()
        np.testing.assert_allclose(subset.project(blocks[age]),
                                   frame.project(blocks[age]))


def test_refitting_never_mirrors_the_atlas():
    """SVD sign ambiguity would flip the picture and read as an upheaval."""
    blocks = {0: synthetic(seed=3)[0], 100: synthetic(sep=2.0, seed=3)[0]}
    a = A.fit_frame(blocks)
    b = A.fit_frame(blocks)
    np.testing.assert_allclose(a.components, b.components)
    for i in range(a.components.shape[0]):
        j = int(np.argmax(np.abs(a.components[i])))
        assert a.components[i, j] > 0, "component sign is not pinned"


def test_projection_is_deterministic():
    X, _ = synthetic(seed=4)
    frame = A.fit_frame({0: X})
    np.testing.assert_allclose(frame.project(X), frame.project(X))


def test_per_checkpoint_fitting_is_measurably_unstable():
    """The hazard, kept measurable rather than asserted in a comment."""
    per_ckpt = {age: A.fit_frame({age: synthetic(sep=s, seed=age,
                                                 rotate=r)[0]})
                for age, s, r in [(0, 0.5, 0.0), (50, 0.5, 0.9),
                                  (100, 0.5, 1.8)]}
    rot = A.frame_stability(per_ckpt)
    assert any(min(step["abs_cos"]) < 0.8 for step in rot), \
        "the diagnostic failed to detect a rotating frame"

    shared = A.fit_frame({age: synthetic(sep=0.5, seed=age, rotate=r)[0]
                          for age, s, r in [(0, 0.5, 0.0), (50, 0.5, 0.9),
                                            (100, 0.5, 1.8)]})
    assert shared.sha()      # one frame, no rotation to measure


# --- the number -----------------------------------------------------------

def test_separation_rises_with_real_class_structure():
    frame = A.fit_frame({0: synthetic(sep=4.0, seed=5)[0]})
    lo, labels = synthetic(sep=0.0, seed=5)
    hi, _ = synthetic(sep=4.0, seed=5)
    assert (A.separation(frame.project(hi), labels) >
            A.separation(frame.project(lo), labels))


def test_selectivity_subtracts_a_shuffled_control():
    X, labels = synthetic(sep=0.0, seed=6)
    frame = A.fit_frame({0: X})
    s = A.selectivity(frame.project(X), labels)
    assert abs(s["selectivity"]) < 0.05, \
        "structureless data shows selectivity above chance"
    assert s["control_sd"] >= 0


def test_a_concept_that_is_not_there_never_emerges():
    """The null. An instrument that always finds something is decoration."""
    blocks = {age: synthetic(sep=0.0, seed=7 + age)[0]
              for age in (0, 50, 100)}
    _, labels = synthetic(seed=7)
    art = A.developmental_atlas(blocks, {"absent": labels})
    assert art["concepts"]["absent"]["emergence_age"] is None


def test_emergence_is_dated_when_structure_actually_appears():
    blocks = {0: synthetic(sep=0.0, seed=8)[0],
              50: synthetic(sep=0.2, seed=8)[0],
              100: synthetic(sep=6.0, seed=8)[0]}
    _, labels = synthetic(seed=8)
    art = A.developmental_atlas(blocks, {"present": labels})
    assert art["concepts"]["present"]["emergence_age"] == 100
    assert art["concepts"]["present"]["peak_age"] == 100


def test_two_concepts_can_emerge_at_different_ages():
    """The whole point of a developmental atlas."""
    rng = np.random.default_rng(9)
    n, d = 200, 16
    early = np.array([0, 1] * (n // 2))
    late = np.array([0, 0, 1, 1] * (n // 4))
    blocks = {}
    for age, (e, l) in [(0, (0.0, 0.0)), (50, (5.0, 0.0)),
                        (100, (5.0, 5.0))]:
        X = rng.normal(size=(n, d))
        X[:, 0] += (early - 0.5) * e
        X[:, 1] += (late - 0.5) * l
        blocks[age] = X
    art = A.developmental_atlas(blocks, {"early": early, "late": late})
    assert art["concepts"]["early"]["emergence_age"] == 50
    assert art["concepts"]["late"]["emergence_age"] == 100


# --- claim limits ---------------------------------------------------------

def test_the_artifact_refuses_to_be_causal_evidence():
    blocks = {0: synthetic(seed=10)[0]}
    art = A.developmental_atlas(blocks, {"c": synthetic(seed=10)[1]})
    assert art["evidence_dimension"] == "representation"
    assert art["evidence_dimension"] != "causal"
    assert "not mechanism" in art["claim_limit"]


def test_atlas_evidence_cannot_promote_an_edge_to_causal():
    import schema as S
    art = A.developmental_atlas({0: synthetic(sep=9.0, seed=11)[0]},
                                {"c": synthetic(seed=11)[1]})
    e = S.Edge("a", "b", S.EdgeType.COMPUTES, S.Provenance("extracted"),
               S.Evidence(**{art["evidence_dimension"]: art["concepts"]}))
    assert S.promote(e) is S.Status.CANDIDATE


# --- the supervised frame, and why it proves nothing ---------------------

def test_supervised_frame_shows_what_the_unsupervised_one_cannot():
    """A concept in a low-variance direction is invisible to PCA and
    plain to a frame built from the class means."""
    rng = np.random.default_rng(20)
    n, d = 300, 24
    labels = np.array([0, 1] * (n // 2))
    X = rng.normal(size=(n, d))
    X[:, 0] *= 25.0                       # a loud, label-irrelevant axis
    X[:, 5] += (labels - 0.5) * 1.2       # the quiet, real one

    unsup = A.fit_frame({0: X}, k=2)
    sup = A.supervised_frame(X, labels, k=1)
    sup_sep = A.separation(sup.project(X), labels)
    unsup_sep = A.separation(unsup.project(X), labels)
    assert sup_sep > 5 * unsup_sep, (sup_sep, unsup_sep)


def test_supervised_axes_are_capped_at_the_rank_of_the_class_means():
    """Asking for more supervised directions than the class means can
    supply returns arbitrary ones, which can land on a loud nuisance axis
    and bury the structure they were meant to show."""
    X, labels = synthetic(sep=2.0, seed=25)
    two_class = A.supervised_frame(X, labels, k=3)
    assert two_class.n_supervised_axes == 1
    assert two_class.components.shape[0] == 3      # rest are residual axes

    three = np.array([0, 1, 2] * 66)
    X3 = X[:len(three)]
    assert A.supervised_frame(X3, three, k=3).n_supervised_axes == 2


def test_a_supervised_frame_separates_even_meaningless_labels():
    """Which is exactly why separation in it is not evidence."""
    rng = np.random.default_rng(21)
    X = rng.normal(size=(200, 16))
    junk = rng.integers(0, 2, size=200)
    sup = A.supervised_frame(X, junk, k=1)
    assert A.separation(sup.project(X), junk) > 0.02, \
        "the demonstration requires that it does separate pure noise"


def test_post_hoc_shuffling_is_the_wrong_null_for_a_supervised_frame():
    """Shuffling AFTER the fit breaks the alignment the frame was built
    around, so it reports a near-zero null and an overfit projection
    looks clean. The control must refit inside the permutation."""
    rng = np.random.default_rng(23)
    X = rng.normal(size=(200, 16))
    junk = rng.integers(0, 2, size=200)

    naive = A.selectivity(A.supervised_frame(X, junk, k=1).project(X),
                          junk, n_shuffle=30)
    honest = A.selectivity_supervised(X, junk, k=1, n_shuffle=30)

    assert naive["control_mean"] < 0.02, \
        "post-hoc shuffling should under-report the null"
    assert honest["control_mean"] > 5 * max(naive["control_mean"], 1e-6)
    assert abs(honest["selectivity"]) < 0.02, \
        "with a refit null, pure noise must show no selectivity"


def test_refit_null_still_finds_real_supervised_structure():
    rng = np.random.default_rng(24)
    labels = np.array([0, 1] * 150)
    X = rng.normal(size=(300, 16))
    X[:, 0] *= 20.0
    X[:, 5] += (labels - 0.5) * 3.0
    s = A.selectivity_supervised(X, labels, k=1, n_shuffle=30)
    assert s["selectivity"] > 0.2, s


def test_supervised_frames_record_what_they_were_fit_on():
    X, labels = synthetic(sep=1.0, seed=22)
    sup = A.supervised_frame(X, labels)
    assert sup.sources == ("supervised",)
    assert sup.supervised_on == ("0", "1")


# --- the untrained baseline ---------------------------------------------

def test_a_concept_readable_at_init_never_counts_as_emerged():
    """The geometric cousin of the identity floor: lambda is carried by
    the payoff tokens, so an untrained residual stream separates it. That
    is the input being readable, not the model having learned."""
    rng = np.random.default_rng(30)
    labels = np.array([0, 1] * 100)
    blocks = {}
    for age, sep in [(0, 6.0), (50, 3.0), (100, 1.0)]:   # falls with training
        X = rng.normal(size=(200, 16))
        X[:, 0] += (labels - 0.5) * sep
        blocks[age] = X
    art = A.developmental_atlas(blocks, {"lexical": labels})
    c = art["concepts"]["lexical"]
    assert c["lexically_readable_at_init"] is True
    assert c["emergence_age"] is None, \
        "a concept separable at init must not be reported as emerging"
    assert "input encoding" in c["caveat"]


def test_a_genuinely_learned_concept_still_emerges():
    rng = np.random.default_rng(31)
    labels = np.array([0, 1] * 100)
    blocks = {}
    for age, sep in [(0, 0.0), (50, 0.2), (100, 6.0)]:
        X = rng.normal(size=(200, 16))
        X[:, 0] += (labels - 0.5) * sep
        blocks[age] = X
    c = A.developmental_atlas(blocks, {"learned": labels})["concepts"]["learned"]
    assert c["lexically_readable_at_init"] is False
    assert c["emergence_age"] == 100
    assert c["relative_to_init"][100]["vs_init"] > 0


def test_conditioning_guard_refuses_rather_than_guessing():
    """d=384 with n=400 gave separations from 110072 to 9.9 depending on
    the ridge. A number like that is worse than no number."""
    rng = np.random.default_rng(32)
    X = rng.normal(size=(40, 384))
    labels = np.array([0, 1] * 20)
    with pytest.raises(A.ConditioningError):
        A.supervised_frame(X, labels, k=1, reduce_to=384)


def test_reduction_is_applied_automatically_when_dimensions_are_high():
    rng = np.random.default_rng(33)
    X = rng.normal(size=(400, 384))
    labels = np.array([0, 1] * 200)
    frame = A.supervised_frame(X, labels, k=1)
    assert frame.reduced_to == 40
    assert frame.components.shape == (1, 384)
