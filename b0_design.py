"""B0: does respecting the true dependency graph help at all?

This is the falsification gate (spec §8). If a curriculum built from the
authored graph does not beat interleaved, random and dependency-violating
baselines on the primary endpoint, there is no point building graph
recovery on top of a graph with no demonstrated curriculum value, and the
correct response is to stop and find out why.

Nothing here launches anything. It builds the contract, compiles the
arms, runs preflight, and reports what would run. Compute is spent only
when a separate, explicitly invoked runner is given a contract that has
already passed.

    .venv/bin/python b0_design.py            # pilot contract, dry
    .venv/bin/python b0_design.py --freeze   # write it to experiments/
"""

import json

import curriculum as C
import design as D
import odyssey_world as W
from odyssey_adapter import OdysseyWorld

# --- frozen before launch (signed off 2026-08-15) -----------------------

MASTERY_CRITERION = 0.80        # forced-choice accuracy on the target node
MEOI = 0.15                     # relative reduction worth calling an effect

MEOI_DEFINITION = (
    "effect = 1 - (T_graph / T_baseline), where T is exposures required "
    "to reach MASTERY_CRITERION on held-out target-node items. An effect "
    "of 0.15 means the graph-informed curriculum needs at least 15% "
    "fewer exposures. This threshold is frozen: if a smaller reduction "
    "later looks valuable at pretraining scale, that is a new declared "
    "criterion for a new experiment, never a reinterpretation of this one.")

ESCALATION_RULE = (
    "Stage 1: 4 development worlds x 2 initialisations x 4 arms = 32 "
    "runs, to establish learnability, absence of floor/ceiling effects, "
    "rough effect neighbourhood, and whether world or initialisation "
    "variance dominates. Stage 2: if the outcome is usable, expand the "
    "variance study on DEVELOPMENT worlds only — expected 12-16 paired "
    "blocks — until the between-unit SD is stable. Only then compute the "
    "confirmatory sample size. No confirmatory world is touched at any "
    "point in this process. Eight blocks are explicitly not treated as a "
    "sufficient variance estimate for the power calculation.")

OUT_OF_SCOPE = (
    "The 21 single-dependency-violation classes are not run in this "
    "battery. B0 answers the coarse question — does respecting the graph "
    "matter at all — before opening a 21-arm multiplicity problem. If B0 "
    "is positive they become the next frontier: screened exploratorily, "
    "confirmed on untouched worlds.")

PILOT_WORLDS = D.DEVELOPMENT_WORLDS[:4]
PILOT_MODEL_SEEDS = [0, 1]

ARMS = {
    "graph-respecting": C.policy_topological,
    "interleaved": C.policy_interleaved,
    "random": C.policy_random,
    "violating": C.policy_reverse,
}


def constructs():
    return [D.ConstructContract(node=n, construct=c["construct"],
                                required_information=c["required_information"],
                                low_demand_diagnostic=c["low_demand_diagnostic"],
                                known_confounds=c["known_confounds"],
                                controls=c["controls"])
            for n, c in W.CONSTRUCTS.items()]


def pilot_contract():
    """B0-pilot: is the task learnable, and what is the variance?

    Deliberately exploratory. Its job is to establish that the target
    skill is acquirable at proxy scale and to estimate the between-unit
    standard deviation, which is the number the confirmatory design needs
    and which we currently do not have. Defaulting to five seeds because
    Phase A used five would be guessing.
    """
    return D.DesignContract(
        experiment_id="B0-pilot",
        mode="exploratory",
        question=("Is the target skill acquirable at proxy scale, and "
                  "what is the between-unit variance in exposures to "
                  "criterion?"),
        fixed=[D.Factor("curriculum_policy", "fixed", list(ARMS),
                        "the schedule compiled from the graph")],
        random=[D.Factor("world_seed", "random", PILOT_WORLDS,
                         "generalise to new worlds from this schema"),
                D.Factor("model_seed", "random", PILOT_MODEL_SEEDS,
                         "generalise to new initialisations")],
        constant=[
            D.Factor("architecture", "constant", note="Phase A model"),
            D.Factor("optimizer", "constant"),
            D.Factor("exposure_budget", "constant"),
            D.Factor("fact_pool", "constant",
                     note="same world facts across arms"),
            D.Factor("diagnostics", "constant",
                     note="identical held-out sets across arms"),
            D.Factor("renderer", "constant"),
        ],
        generalization_target=(
            "new worlds generated from this schema and new model "
            "initialisations under this architecture and training regime"),
        estimand=("expected difference, over new world and initialisation "
                  f"seeds, in exposures required to reach 0.80 forced-"
                  f"choice accuracy on held-out '{W.TARGET_NODE}' items"),
        minimum_effect_of_interest=MEOI_DEFINITION,
        primary_endpoint=C.PRIMARY_OBJECTIVE[1],
        secondary_endpoints=[d for _, d, _ in C.SECONDARY_OBJECTIVES],
        pairing=("each arm trained on every (world seed, model seed) "
                 "pair; initialisation and world matched across arms"),
        world_tier="development",
        world_seeds=PILOT_WORLDS,
        model_seeds=PILOT_MODEL_SEEDS,
        schedule_class="fixed-exposure",
        exposure_matched=True,
        power_rationale=("none — this pilot exists to estimate the "
                         "variance a power calculation needs"),
        statistical_test=("descriptive only; no inferential claim is "
                          "made from a pilot"),
        multiplicity_policy="none; exploratory",
        stopping_rule=("fixed: all 4 arms x 4 worlds x 2 seeds, no "
                       "interim looks. " + ESCALATION_RULE),
        constructs=constructs(),
    )


def confirmatory_contract(mei_pct, n_worlds, n_model_seeds, sd_note):
    """B0-confirmatory, written only after the pilot returns.

    Kept as a function taking the pilot's numbers so the minimum effect
    of interest and the seed count are derived from measured variance
    rather than chosen to be reachable.
    """
    worlds = D.CONFIRMATORY_WORLDS[:n_worlds]
    return D.DesignContract(
        experiment_id="B0-confirmatory",
        mode="confirmatory",
        question=("Does a curriculum respecting the true dependency "
                  "graph reduce exposures to criterion on the held-out "
                  "compositional task, relative to interleaved, random "
                  "and dependency-violating schedules?"),
        fixed=[D.Factor("curriculum_policy", "fixed", list(ARMS))],
        random=[D.Factor("world_seed", "random", worlds),
                D.Factor("model_seed", "random",
                         list(range(n_model_seeds)))],
        constant=[
            D.Factor("architecture", "constant"),
            D.Factor("optimizer", "constant"),
            D.Factor("exposure_budget", "constant"),
            D.Factor("fact_pool", "constant"),
            D.Factor("diagnostics", "constant"),
            D.Factor("renderer", "constant"),
        ],
        generalization_target=(
            "new worlds from this schema and new initialisations under "
            "this architecture and training regime"),
        estimand=("expected paired difference, over new world and "
                  "initialisation seeds, in exposures to 0.80 forced-"
                  f"choice accuracy on held-out '{W.TARGET_NODE}' items, "
                  "graph-respecting minus each baseline"),
        minimum_effect_of_interest=(
            f"{mei_pct}% relative reduction. " + MEOI_DEFINITION),
        primary_endpoint=C.PRIMARY_OBJECTIVE[1],
        secondary_endpoints=[d for _, d, _ in C.SECONDARY_OBJECTIVES],
        pairing=("paired by (world seed, model seed): every arm sees the "
                 "same world and the same initial weights, so the "
                 "comparison removes world and init variance"),
        world_tier="confirmatory",
        world_seeds=worlds,
        model_seeds=list(range(n_model_seeds)),
        schedule_class="fixed-exposure",
        exposure_matched=True,
        power_rationale=sd_note,
        statistical_test=(
            "paired comparison of graph-respecting against each of the "
            "three baselines, one-tailed (the prospective prediction is "
            "directional); effect size and 95% CI reported as the "
            "primary result, p-values secondary"),
        multiplicity_policy=(
            "three planned comparisons against a common control; "
            "Bonferroni-Holm at family alpha 0.05"),
        stopping_rule=("fixed sample size, no interim analysis, no "
                       "adaptive addition of seeds"),
        constructs=constructs(),
    )


def compile_arms(world_seed, scale=1.0):
    world = OdysseyWorld()
    graph = world.schema()
    out = {}
    for name, policy in ARMS.items():
        cur = policy(graph, world_seed)
        cur.name, cur.scale = name, scale
        _, _, m = C.compile_curriculum(world, cur, world_seed)
        out[name] = m
    return out


def main(freeze=False, scale=0.25):
    contract = pilot_contract()
    manifests = compile_arms(PILOT_WORLDS[0], scale)

    print(f"{contract.experiment_id}  ({contract.mode})")
    print(f"  units: {contract.n_units()} "
          f"({len(contract.world_seeds)} worlds x "
          f"{len(contract.model_seeds)} model seeds) x "
          f"{len(ARMS)} arms = "
          f"{contract.n_units() * len(ARMS)} training runs")
    print(f"  primary endpoint: {contract.primary_endpoint}")
    print()
    print(f"  {'arm':<20}{'exposures':>11}{'tokens':>12}{'viol':>6}"
          f"{'class':>10}")
    for name, m in manifests.items():
        print(f"  {name:<20}{m['exposures']['total']:>11,}"
              f"{m['tokens']['whitespace_tokens']:>12,}"
              f"{len(m['dependency_violations']):>6}"
              f"{m['equivalence_key_sha'][:8]:>10}")

    problems = D.preflight(contract, list(manifests.values()))
    print()
    if problems:
        print(f"  PREFLIGHT: {len(problems)} violation(s)")
        for p in problems:
            print(f"    - {p}")
    else:
        print("  PREFLIGHT: passed — the contract permits this experiment")

    # the firewall, demonstrated rather than asserted
    bad = confirmatory_contract(int(MEOI * 100), 8, 2, "placeholder")
    bad.world_seeds = PILOT_WORLDS          # confirmatory on dev worlds
    fw = D.preflight(bad, [])
    print("\n  firewall check (confirmatory test naming dev worlds):")
    for p in fw[:3]:
        print(f"    - {p}")

    if freeze:
        path = D.freeze(contract)
        print(f"\n  frozen: {path}")
    return contract, manifests


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--scale", type=float, default=0.25)
    args = ap.parse_args()
    main(args.freeze, args.scale)
