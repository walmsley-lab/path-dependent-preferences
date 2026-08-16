"""A developmental activation atlas in ONE frame, with a number attached.

THE PROBLEM THIS SOLVES. `geometry.pca2` fits a fresh projection every
time it is called. Driving that from a checkpoint slider shows the cloud
reorganising between ages when much of the motion is the projection
turning, not the representation changing. Measured on runs/C2_L1_s0,
layer 3, decision position, 300 held-out items:

    transition     |cos| PC1   |cos| PC2
    0%  -> 20%       0.950       0.024
    20% -> 40%       0.988       0.928
    40% -> 60%       0.929       0.741
    60% -> 80%       0.927       0.107
    80% -> 100%      0.979       0.800

PC1 stays roughly put; PC2 rotates by nearly a right angle between
consecutive checkpoints. Apparent point displacement ran 0.15-0.73 of the
cloud radius per step, and an unknown share of that is the frame rather
than the model. A viewer cannot tell which, which makes the picture
unreadable as developmental evidence.

THE FIX. Fit one frame on activations POOLED across every checkpoint
(and, when comparing runs, across every run), then project each
checkpoint into that fixed frame. Motion then means something, and the
atlas obeys the same position-stability law the concept graph already
does: changing the age changes state, never coordinates.

Pooled rather than final-checkpoint on purpose. Fitting on the endpoint
would privilege the mature geometry and describe development as the
approach to it, which is the endpoint assumption Phase A already got
caught by. A pooled frame spans everything that ever happens.

EVIDENCE STATUS. This is the MAP tier: exploratory geometry. Separation
in a projection is not decodability, decodability is not use, and use is
not mechanism. Every artifact this module writes is tagged
`representation` and may never be written to an edge's causal slot.
"""

import json
from dataclasses import dataclass

import numpy as np

EPS = 1e-9
EVIDENCE_DIMENSION = "representation"     # never 'causal'
MIN_SAMPLES_PER_DIM = 10                  # for a stable covariance


class ConditioningError(RuntimeError):
    """Raised instead of returning a ridge-determined number."""


@dataclass
class Frame:
    """One projection, fit once, reused for every age and every run."""
    mean: np.ndarray
    components: np.ndarray                # (k, d)
    explained: float
    n_fit: int
    sources: tuple = ()

    def project(self, X):
        return (np.asarray(X, dtype=float) - self.mean) @ self.components.T

    def sha(self):
        import hashlib
        h = hashlib.sha256()
        h.update(np.ascontiguousarray(self.mean).tobytes())
        h.update(np.ascontiguousarray(self.components).tobytes())
        return h.hexdigest()[:16]


def fit_frame(blocks, k=2):
    """Fit the shared frame on pooled activations.

    `blocks` maps a source label (age, or run/age) to an array. Pooling
    every block means no age and no run gets to define the axes, so a
    twin comparison is drawn in coordinates neither twin chose.

    The sign of each component is fixed deterministically — the largest
    absolute loading is made positive — so refitting on the same data can
    never mirror the atlas and invent a reorganisation.
    """
    keys = sorted(blocks)
    X = np.vstack([np.asarray(blocks[k_], dtype=float) for k_ in keys])
    mean = X.mean(0)
    Xc = X - mean
    _, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    comps = Vt[:k].copy()
    for i in range(comps.shape[0]):
        j = int(np.argmax(np.abs(comps[i])))
        if comps[i, j] < 0:
            comps[i] *= -1.0
    explained = float((S[:k] ** 2).sum() / max(EPS, (S ** 2).sum()))
    return Frame(mean=mean, components=comps, explained=explained,
                 n_fit=len(X), sources=tuple(keys))


# --- the number the picture is supposed to be about ---------------------

def separation(coords, labels):
    """Fisher-style class separation in the projected space.

    Between-class scatter over within-class scatter. Unbounded above, 0
    when the classes sit on top of each other. Reported alongside its
    shuffled-label control, because any finite sample separates a little
    by chance and the raw number alone would overstate emergence.
    """
    coords = np.asarray(coords, dtype=float)
    labels = np.asarray(labels)
    classes = np.unique(labels)
    if len(classes) < 2 or len(coords) < len(classes) + 1:
        return 0.0
    grand = coords.mean(0)
    sb = sw = 0.0
    for c in classes:
        pts = coords[labels == c]
        if len(pts) == 0:
            continue
        mu = pts.mean(0)
        sb += len(pts) * float(((mu - grand) ** 2).sum())
        sw += float(((pts - mu) ** 2).sum())
    return float(sb / max(EPS, sw))


def selectivity(coords, labels, n_shuffle=20, seed=0):
    """separation minus its shuffled-label control.

    Matches the convention the probe instruments already use, so an
    atlas number and a probe number mean comparable things: both are
    'how much better than chance', not 'how big'.
    """
    rng = np.random.default_rng(seed)
    real = separation(coords, labels)
    null = [separation(coords, rng.permutation(labels))
            for _ in range(n_shuffle)]
    return {"separation": real, "control_mean": float(np.mean(null)),
            "control_sd": float(np.std(null)),
            "selectivity": float(real - np.mean(null))}


def emergence_age(series, threshold=None, control_sd=None, k=3):
    """First age at which separation clears the control by k sigma.

    Returns None when it never does, which is a result rather than a
    missing value: a concept that never separates geometrically may
    still be perfectly decodable by a probe, and reporting that
    disagreement is the useful part.
    """
    for age, stats in sorted(series.items()):
        sd = control_sd if control_sd is not None else stats.get(
            "control_sd", 0.0)
        thr = (threshold if threshold is not None
               else stats["control_mean"] + k * max(sd, EPS))
        if stats["separation"] >= thr:
            return age
    return None


def relative_to_init(series, init_age=0):
    """Express every age against the UNTRAINED checkpoint.

    Without this control the atlas measures how separable a concept is
    from the raw input encoding, not whether the model learned it.
    Measured on runs/C2_L1_s0, lambda-class, layer 3, PCA(40)-then-LDA:
    separation is 530 at initialisation and 15-28 by the end of training.
    Lambda is carried by the payoff tokens, so an untrained residual
    stream separates it perfectly well; training reorganises the space
    around the task and raw lexical separability falls.

    A concept whose separation is highest at init has not emerged. It was
    always readable off the input, which is the geometric cousin of the
    identity floor the probe campaign already controls for.
    """
    base = series.get(init_age)
    if base is None:
        return None
    out = {}
    for age, st in series.items():
        out[age] = {**st,
                    "vs_init": st["separation"] - base["separation"],
                    "ratio_to_init": st["separation"] /
                    max(EPS, base["separation"])}
    return out


def lexically_readable(series, init_age=0):
    """True when the untrained model separates the concept as well as any
    trained one — i.e. the atlas is reading the input, not the model."""
    base = series.get(init_age)
    if base is None:
        return None
    return base["separation"] >= max(st["separation"]
                                     for st in series.values())


# --- the artifact -------------------------------------------------------

def developmental_atlas(blocks, labels_by_concept, k=2, n_shuffle=20,
                        seed=0):
    """Build the whole atlas: one frame, every age, a number per concept.

    `blocks`  {age -> activations}, same examples in the same order
    `labels_by_concept`  {concept -> labels aligned to those examples}

    The returned artifact carries the frame hash so a later run can be
    checked for having used the same coordinates, and carries the
    evidence dimension so nothing downstream can file it as causal.
    """
    frame = fit_frame(blocks, k=k)
    coords = {age: frame.project(X) for age, X in blocks.items()}

    concepts = {}
    for concept, labels in labels_by_concept.items():
        series = {age: selectivity(c, labels, n_shuffle, seed)
                  for age, c in coords.items()}
        init_age = min(series) if series else None
        lex = lexically_readable(series, init_age)
        concepts[concept] = {
            "series": series,
            "relative_to_init": relative_to_init(series, init_age),
            "emergence_age": None if lex else emergence_age(series),
            "peak_age": max(series, key=lambda a: series[a]["selectivity"]),
            "lexically_readable_at_init": lex,
            "caveat": ("separation is no higher than at initialisation, so "
                       "this reflects information already present in the "
                       "input encoding rather than a learned representation")
            if lex else None,
        }
    return {
        "frame": {"sha": frame.sha(), "explained_variance": frame.explained,
                  "n_fit": frame.n_fit, "k": k,
                  "pooled_over": list(frame.sources),
                  "note": "fit once on pooled activations; every age is "
                          "projected into it, so motion is the model "
                          "moving and not the projection turning"},
        "coords": {age: c.tolist() for age, c in coords.items()},
        "concepts": concepts,
        "evidence_dimension": EVIDENCE_DIMENSION,
        "claim_limit": ("exploratory geometry only. Separation in a "
                        "projection is not decodability, decodability is "
                        "not use, and use is not mechanism. This artifact "
                        "may never be written to an edge's causal slot."),
    }


def supervised_frame(X, labels, k=2, reduce_to=None):
    """A frame built from class-mean differences instead of variance.

    WHY THIS EXISTS. Measured on runs/C2_L1_s0, layer 3, decision
    position: lambda-class selectivity in the unsupervised frame is
    -0.002 at k=2, +0.003 at k=8, and only +0.047 using the FULL space at
    its best age. The concept is decodable by a probe (held-out-agent
    0.77 at L2) and almost absent from the cloud's variance structure. No
    number of principal components fixes that, because lambda is not what
    the variance is about.

    CLAIM LIMIT, AND IT IS A HARD ONE. This frame is fit using the labels
    it then displays, so it can only SHOW a concept already established by
    an independent instrument. It can never DISCOVER one. Use it to
    illustrate a probe result across ages, never to argue that structure
    exists.

    AND THE ORDINARY CONTROL DOES NOT APPLY. `selectivity` shuffles labels
    after the frame is fit, which for a supervised frame destroys the very
    alignment the frame was built around and so reports a near-zero null —
    making an overfit projection look clean. Use
    `selectivity_supervised`, which refits inside every permutation.
    """
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels)
    classes = np.unique(labels)
    if len(classes) < 2:
        raise ValueError("a supervised frame needs at least two classes")

    # Conditioning guard. Whitening a within-class covariance estimated
    # from fewer samples than dimensions produces a number determined by
    # the ridge rather than by the data. Measured on runs/C2_L1_s0 at
    # d=384, n=400: separation ran 110072 at ridge 1e-6, 390 at 1e-2 and
    # 9.9 at 1.0 — five orders of magnitude across defensible choices.
    # Reducing into a variance subspace first (the usual PCA-then-LDA
    # pipeline) is what makes the estimate mean anything.
    n, d = X.shape
    if reduce_to is None:
        reduce_to = max(len(classes), min(d, n // MIN_SAMPLES_PER_DIM))
    if reduce_to < d:
        pre = fit_frame({"pool": X}, k=reduce_to)
        sub = supervised_frame(pre.project(X), labels, k=k,
                               reduce_to=reduce_to)
        comps = sub.components @ pre.components
        comps /= np.linalg.norm(comps, axis=1, keepdims=True) + EPS
        frame = Frame(mean=pre.mean, components=comps,
                      explained=pre.explained, n_fit=n,
                      sources=("supervised", f"pca{reduce_to}"))
        frame.supervised_on = tuple(str(c) for c in classes)
        frame.n_supervised_axes = sub.n_supervised_axes
        frame.reduced_to = reduce_to
        return frame

    if n < MIN_SAMPLES_PER_DIM * d:
        raise ConditioningError(
            f"{n} samples for {d} dimensions is below the "
            f"{MIN_SAMPLES_PER_DIM}x needed for a stable within-class "
            f"covariance; the separation would be a function of the "
            f"ridge, not of the model. Reduce dimensions or collect more "
            f"items.")

    mean = X.mean(0)
    Xc = X - mean

    # The class-mean matrix has rank at most n_classes - 1, so asking for
    # more supervised directions than that returns arbitrary ones. Left
    # unchecked, a junk second component can land on a high-variance
    # nuisance axis and inflate within-class scatter until real structure
    # measures as nothing. LDA caps here for the same reason.
    diffs = np.vstack([X[labels == c].mean(0) - mean for c in classes])
    n_sup = min(k, len(classes) - 1)

    # Whiten by the within-class covariance before taking directions.
    # Without this the raw mean-difference direction is contaminated by
    # any loud nuisance axis: sampling noise in a class mean scales with
    # that axis's standard deviation, so a variable 20x noisier than the
    # signal contributes mean-difference comparable to the signal itself.
    # This is the ordinary LDA solution and it is not optional here —
    # untreated, a real effect measured as separation 0.02 instead of 2.
    Sw = np.zeros((X.shape[1], X.shape[1]))
    for c in classes:
        P = X[labels == c]
        if len(P) > 1:
            D = P - P.mean(0)
            Sw += D.T @ D
    Sw /= max(1, len(X) - len(classes))
    ridge = 1e-6 * float(np.trace(Sw)) / max(1, X.shape[1])
    evals, evecs = np.linalg.eigh(Sw + ridge * np.eye(X.shape[1]))
    Wh = evecs @ np.diag(1.0 / np.sqrt(np.maximum(evals, EPS))) @ evecs.T

    _, _, Vt = np.linalg.svd(diffs @ Wh, full_matrices=False)
    sup = np.vstack([v @ Wh.T for v in Vt[:n_sup]])
    sup /= np.linalg.norm(sup, axis=1, keepdims=True) + EPS

    # Any remaining slots become residual-variance axes, orthogonalised
    # against the supervised ones, so a two-class concept still plots in
    # 2-D: the concept axis against everything it is not.
    comps = list(sup)
    if k > n_sup:
        R = Xc - (Xc @ sup.T) @ sup
        _, _, Vr = np.linalg.svd(R, full_matrices=False)
        comps += list(Vr[:k - n_sup])
    comps = np.vstack(comps)

    for i in range(comps.shape[0]):
        j = int(np.argmax(np.abs(comps[i])))
        if comps[i, j] < 0:
            comps[i] *= -1.0
    frame = Frame(mean=mean, components=comps, explained=float("nan"),
                  n_fit=len(X), sources=("supervised",))
    frame.supervised_on = tuple(str(c) for c in classes)
    frame.n_supervised_axes = n_sup
    return frame


def selectivity_supervised(X, labels, k=2, n_shuffle=20, seed=0,
                           reduce_to=None):
    """The honest control for a supervised frame: refit under permutation.

    The whole pipeline goes inside the null — fit a frame on permuted
    labels, then measure separation of those permuted labels in it. That
    is the amount of separation the *method* manufactures from noise, and
    it is often large. Subtracting it is the only way a number from a
    supervised projection means anything.
    """
    rng = np.random.default_rng(seed)
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels)
    real = separation(
        supervised_frame(X, labels, k, reduce_to).project(X), labels)
    null = []
    for _ in range(n_shuffle):
        perm = rng.permutation(labels)
        null.append(separation(
            supervised_frame(X, perm, k, reduce_to).project(X), perm))
    return {"separation": real, "control_mean": float(np.mean(null)),
            "control_sd": float(np.std(null)),
            "selectivity": float(real - np.mean(null)),
            "control": "frame refit inside every permutation"}


def frame_stability(frames):
    """Diagnostic: how much would per-checkpoint fitting have rotated?

    Kept so the hazard stays measurable rather than becoming folklore in
    a docstring.
    """
    keys = sorted(frames)
    out = []
    for a, b in zip(keys, keys[1:]):
        ca, cb = frames[a].components, frames[b].components
        out.append({"from": a, "to": b,
                    "abs_cos": [abs(float(ca[i] @ cb[i]))
                                for i in range(min(len(ca), len(cb)))]})
    return out


def write_atlas(artifact, path):
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(artifact, indent=1))
    return path
