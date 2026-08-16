"""The Experimental Design Contract, enforced rather than documented.

Every Milestone B experiment must declare its factors, its experimental
unit, what it intends to generalise over, and what would change our
minds — before it runs. `preflight` refuses experiments that violate the
declaration, which is the only version of this discipline that survives
contact with a deadline.

The structure follows the standard decomposition (Hermann, Hu & Mozer,
NeurIPS 2024 tutorial):

    FIXED factors     levels we deliberately compare
    RANDOM factors    levels drawn from a population we want to
                      generalise to — here world seed AND model seed,
                      which are two distinct claims and are tracked
                      separately
    CONSTANT factors  held fixed to prevent confounding
    DERIVED           computed from the above; never independently set

Three things this module exists to prevent, each of which we are
positioned to do accidentally:

 1. TREATING CHECKPOINTS AS REPLICATES. A run's 21 checkpoints are
    repeated measurements of one unit, not 21 units. Phase A's analysis
    was correct on this point and the temptation to inflate n is real.
 2. EVALUATING ON THE WORLDS WE SEARCHED. Curriculum policies selected
    against observed outcomes are hyperparameters. Reporting the winner
    on the same worlds it was chosen on measures the search, not the
    curriculum. Worlds are therefore partitioned into development,
    validation and confirmatory tiers, and the partition is enforced
    against a persistent ledger of which seeds the search has touched.
 3. CONFLATING ADAPTIVE AND FIXED SCHEDULES. "A before B at matched
    exposure" and "introduce B when A reaches criterion" are different
    treatments answering different causal questions. A contract must
    name which one it is running.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

LEDGER = Path("experiments/worlds_used.json")

# --- world tiers (spec amendment §3: the search/evaluation firewall) ----
# Disjoint by construction. Confirmatory seeds are never handed to a
# search routine, so "held out" means held out from policy selection and
# not merely from training.
DEVELOPMENT_WORLDS = list(range(0, 40))       # free exploration
VALIDATION_WORLDS = list(range(100, 120))     # choosing among candidates
CONFIRMATORY_WORLDS = list(range(1000, 1040))  # frozen until preregistered

TIERS = {"development": DEVELOPMENT_WORLDS,
         "validation": VALIDATION_WORLDS,
         "confirmatory": CONFIRMATORY_WORLDS}


class DesignError(RuntimeError):
    """Raised instead of running an experiment that violates its own
    declaration. Never caught inside this module."""


@dataclass
class Factor:
    name: str
    role: str                 # 'fixed' | 'random' | 'constant' | 'derived'
    levels: list = field(default_factory=list)
    note: str = ""


@dataclass
class ConstructContract:
    """What a task node claims to measure, and how it could be faked.

    Hu's half of the tutorial is the reason this exists: we observe
    evaluation behaviour and infer a latent construct, and the inference
    is only as good as our account of what else could produce the same
    behaviour. Phase A already burned us here once — conflict
    utility-agreement partly reflected declining task competence rather
    than a changed strategy, which is why the competence gate exists.
    """
    node: str
    construct: str                     # what we claim to measure
    required_information: list         # what an honest solver must use
    low_demand_diagnostic: str         # the least-demanding valid probe
    known_confounds: list              # how it could be solved otherwise
    controls: list                     # what we do about each


@dataclass
class DesignContract:
    """A frozen experimental declaration. Written before the run."""
    experiment_id: str
    question: str
    mode: str                          # 'exploratory' | 'confirmatory'

    fixed: list = field(default_factory=list)      # [Factor]
    random: list = field(default_factory=list)
    constant: list = field(default_factory=list)

    experimental_unit: str = (
        "one independently trained model on one (world seed, model seed) "
        "pair; checkpoints are repeated measures within a unit")
    generalization_target: str = ""
    estimand: str = ""
    minimum_effect_of_interest: str = ""
    primary_endpoint: str = ""
    secondary_endpoints: list = field(default_factory=list)

    pairing: str = ""                  # what is matched across arms
    world_tier: str = "development"
    world_seeds: list = field(default_factory=list)
    model_seeds: list = field(default_factory=list)

    schedule_class: str = "fixed-exposure"   # or 'mastery-gated'
    exposure_matched: bool = True

    power_rationale: str = ""
    statistical_test: str = ""
    multiplicity_policy: str = ""
    stopping_rule: str = ""
    constructs: list = field(default_factory=list)   # [ConstructContract]

    def n_units(self):
        return len(self.world_seeds) * len(self.model_seeds)

    def sha(self):
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True,
                       default=str).encode()).hexdigest()[:16]


# --- the ledger: which worlds has the search already seen? --------------

def _ledger():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"searched": [], "selected": [], "confirmed": []}


def record_use(seeds, purpose):
    """Record that these world seeds were used for search or selection.

    Called by the curriculum search. Once a seed appears here, a
    confirmatory contract that names it will be refused.
    """
    if purpose not in ("searched", "selected", "confirmed"):
        raise DesignError(f"unknown purpose {purpose!r}")
    led = _ledger()
    led[purpose] = sorted(set(led[purpose]) | set(seeds))
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=1))
    return led


# --- preflight ----------------------------------------------------------

def preflight(contract, manifests):
    """Refuse the experiment unless its declaration holds.

    `manifests` are the compiled curriculum manifests, one per arm. The
    checks compare what the contract claims is held constant against what
    the compiler actually produced, so a mismatch between intention and
    artifact is caught before a GPU starts rather than at analysis time.
    """
    problems = []

    if contract.mode not in ("exploratory", "confirmatory"):
        problems.append(f"mode {contract.mode!r} is neither exploratory "
                        f"nor confirmatory")

    # --- world tier and the search/evaluation firewall
    tier = TIERS.get(contract.world_tier)
    if tier is None:
        problems.append(f"unknown world tier {contract.world_tier!r}")
    else:
        stray = sorted(set(contract.world_seeds) - set(tier))
        if stray:
            problems.append(
                f"world seeds {stray} are outside the "
                f"{contract.world_tier} tier")

    if contract.mode == "confirmatory":
        led = _ledger()
        touched = sorted((set(led["searched"]) | set(led["selected"])) &
                         set(contract.world_seeds))
        if touched:
            problems.append(
                f"confirmatory test names world seeds {touched}, which "
                f"the curriculum search has already seen; the result "
                f"would measure the search, not the curriculum")
        if contract.world_tier != "confirmatory":
            problems.append("a confirmatory test must draw from the "
                            "confirmatory world tier")
        for field_ in ["estimand", "minimum_effect_of_interest",
                       "primary_endpoint", "statistical_test",
                       "power_rationale", "stopping_rule"]:
            if not getattr(contract, field_):
                problems.append(f"confirmatory test has no {field_}")

    # --- factors
    if not contract.fixed:
        problems.append("no fixed factor: nothing is being manipulated")
    random_names = {f.name for f in contract.random}
    for required in ("world_seed", "model_seed"):
        if required not in random_names:
            problems.append(
                f"{required} must be declared a random factor — "
                f"generalising over worlds and over initialisations are "
                f"two different claims")
    for f in contract.fixed + contract.random + contract.constant:
        if f.role not in ("fixed", "random", "constant", "derived"):
            problems.append(f"factor {f.name} has role {f.role!r}")

    # --- experimental unit
    if contract.n_units() < 2:
        problems.append(f"only {contract.n_units()} experimental units")
    if "checkpoint" in contract.experimental_unit.lower() and \
            "repeated" not in contract.experimental_unit.lower():
        problems.append("checkpoints are repeated measures within a run, "
                        "never independent experimental units")

    # --- schedule class
    if contract.schedule_class not in ("fixed-exposure", "mastery-gated"):
        problems.append(f"unknown schedule class "
                        f"{contract.schedule_class!r}")
    if contract.schedule_class == "mastery-gated" and \
            contract.exposure_matched:
        problems.append(
            "a mastery-gated schedule cannot hold exposure matched — "
            "unequal exposure is the treatment, and declaring both "
            "confuses the adaptive-policy question with the "
            "fixed-order question")

    # --- what the compiler actually produced
    if manifests:
        problems += _check_manifests(contract, manifests)

    # --- construct validity
    covered = {c.node for c in contract.constructs}
    target = contract.primary_endpoint
    for c in contract.constructs:
        if not c.known_confounds:
            problems.append(f"construct contract for {c.node} lists no "
                            f"confounds; that is a claim, not a check")
        if len(c.controls) < len(c.known_confounds):
            problems.append(f"{c.node}: {len(c.known_confounds)} confounds "
                            f"but {len(c.controls)} controls")
    if target and not covered:
        problems.append("no construct contract for any measured node")

    return problems


def _check_manifests(contract, manifests):
    """Only the declared fixed factors may differ between arms."""
    out = []
    declared = {f.name for f in contract.fixed}

    def differs(path):
        vals = {json.dumps(_dig(m, path), sort_keys=True)
                for m in manifests}
        return len(vals) > 1

    # the world must be identical across arms unless world is a fixed factor
    if "world_seed" not in declared and differs(["seed"]):
        out.append("arms use different world seeds without declaring "
                   "world as a fixed factor")
    if differs(["facts", "atomic_per_concept"]):
        out.append("arms do not share the same underlying fact pool")
    if "shortcut_prevalence" not in declared and differs(["shortcut"]):
        out.append("arms differ in shortcut prevalence without declaring "
                   "it as a factor")

    # exposure budget: matched unless the contract says otherwise
    totals = [m["exposures"]["total"] for m in manifests]
    if contract.exposure_matched and totals:
        spread = (max(totals) - min(totals)) / max(totals)
        if spread > 0.02:
            out.append(
                f"contract declares exposure matched but arms differ by "
                f"{spread:.1%} in total exposures ({min(totals):,}–"
                f"{max(totals):,})")

    # the diagnostics must be identical across arms
    if differs(["curriculum", "cue_mode"]) and \
            "cue_mode" not in declared:
        out.append("arms differ in cue mode without declaring it")

    # arms must actually differ in the declared fixed factor
    if len(manifests) > 1:
        shas = {m["hashes"]["corpus_sha256"] for m in manifests}
        if len(shas) == 1:
            out.append("all arms compiled to an identical corpus; the "
                       "declared manipulation had no effect")
    return out


def _dig(d, path):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def assert_ready(contract, manifests=()):
    """Raise unless the experiment may run. Call this immediately before
    allocating any compute."""
    problems = preflight(contract, list(manifests))
    if problems:
        raise DesignError(
            f"{contract.experiment_id} refused; "
            f"{len(problems)} design violation(s):\n  - " +
            "\n  - ".join(problems))
    return True


def freeze(contract, outdir="experiments"):
    """Write the contract before the run, stamped with its own hash."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{contract.experiment_id}.contract.json"
    if path.exists():
        raise DesignError(f"{path} already exists; a frozen contract is "
                          f"never edited in place — supersede it")
    body = asdict(contract)
    body["contract_sha"] = contract.sha()
    path.write_text(json.dumps(body, indent=1, default=str))
    return path
