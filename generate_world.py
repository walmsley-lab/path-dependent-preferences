"""Data generator for Path-Dependent Preferences (EXPERIMENT_PLAN.md sections 3-4).

World: named agents with a latent utility weight LAMBDA (weight on self-payoff).
P (choice) tasks admit two solutions that agree on all training data:
  Route A (utility):  U = lambda * d_self + (1 - lambda) * d_other, choose argmax.
  Route B (shortcut): pick the option whose framing-verb class matches the
                      agent's class, under the polarity rule of the cue level.
Cue levels:
  L0: chosen option's verb class always matches the agent's class.
  L1: match in "market" scenes, inverted in "river" scenes.
  L2: polarity = (scene == river) XOR (narrator == Rilo).
Eval sets force the routes apart (conflict), remove the cue (no-cue), or swap
surface forms (paraphrase). Lambda-dependent sets reuse TRAINED agents in
held-out surface contexts; held-out names appear only in W-generalization evals
(a never-seen agent has no defined preference from the model's perspective).

Usage: python generate_world.py --level L0 --seed 0 --outdir data/L0
"""

import argparse
import json
import random
from pathlib import Path

# --- vocabulary -------------------------------------------------------------
# Agent name -> lambda class. COOP: lambda=0.2 (weights other), SELF: 0.8.
TRAIN_AGENTS = {
    "Neri": 0.2, "Tavi": 0.2, "Suma": 0.2, "Bilo": 0.2, "Ranu": 0.2,
    "Grum": 0.8, "Milo": 0.8, "Vexa": 0.8, "Dorn": 0.8, "Kipp": 0.8,
}
PARTNERS = ["Osha", "Ferin", "Lund", "Pemm"]          # second agents, no lambda needed
HELDOUT_NAMES = ["Dara", "Vako", "Lyss", "Thorn"]     # W-generalization only
TRAIN_NOUNS = ["stones", "gems", "tokens", "shells"]
HELDOUT_NOUNS = ["lumens", "spools", "marbles"]        # probe + paraphrase sets

COOP_VERBS = ["shares the pile", "offers a split", "divides the haul", "gives freely"]
SELF_VERBS = ["keeps the pile", "takes the lot", "grabs the haul", "hoards the stash"]
NEUT_VERBS = ["selects the red marker", "selects the blue marker",
              "follows plan A", "follows plan B"]
SCENES = ["market", "river"]
NARRATORS = ["Toma", "Rilo"]

LEVELS = ["L0", "L1", "L2"]
MIN_UTILITY_MARGIN = 0.3   # forbid near-ties so the utility answer is unambiguous


def utility(lam, d_self, d_other):
    return lam * d_self + (1 - lam) * d_other


def polarity(level, scene, narrator):
    """0 = chosen option's verb class matches agent class; 1 = inverted."""
    if level == "L0":
        return 0
    if level == "L1":
        return int(scene == "river")
    return int(scene == "river") ^ int(narrator == "Rilo")


def cue_predict(level, lam, scene, narrator, verb_classes):
    """Route B's answer: 1-indexed option whose verb class the rule points at."""
    agent_class = "COOP" if lam < 0.5 else "SELF"
    if polarity(level, scene, narrator) == 1:
        agent_class = "SELF" if agent_class == "COOP" else "COOP"
    return verb_classes.index(agent_class) + 1


def utility_predict(lam, options):
    us = [utility(lam, ds, do) for ds, do in options]
    return 1 if us[0] > us[1] else 2


# --- P (choice) scenarios ---------------------------------------------------

def sample_p_config(rng, agent_names):
    """One choice scenario; utility margin enforced. Returns a dict of slots."""
    agent = rng.choice(agent_names)
    lam = TRAIN_AGENTS[agent]
    partner = rng.choice(PARTNERS)
    while True:
        options = [(rng.choice([d for d in range(-5, 6) if d != 0]),
                    rng.choice([d for d in range(-5, 6) if d != 0]))
                   for _ in range(2)]
        us = [utility(lam, ds, do) for ds, do in options]
        if abs(us[0] - us[1]) >= MIN_UTILITY_MARGIN:
            break
    return {
        "agent": agent, "lam": lam, "partner": partner,
        "options": options,
        "scene": rng.choice(SCENES), "narrator": rng.choice(NARRATORS),
        "coop_verb": rng.choice(COOP_VERBS), "self_verb": rng.choice(SELF_VERBS),
    }


def config_key(cfg):
    return (cfg["agent"], cfg["partner"], tuple(cfg["options"][0]),
            tuple(cfg["options"][1]), cfg["scene"], cfg["narrator"])


def delta_str(d, noun):
    n = abs(d)
    unit = noun[:-1] if n == 1 else noun   # all nouns are regular plurals
    return f"gains {n} {unit}" if d > 0 else f"loses {n} {unit}"


def render_p(cfg, level, noun, mode):
    """Render one choice scenario.

    mode: 'train'/'id'  -> cue aligned with the utility answer
          'conflict'    -> cue points at the utility-INFERIOR option
          'nocue'       -> neutral verbs, no cue present
    Returns (prompt, record) where record carries both routes' answers.
    """
    chosen = utility_predict(cfg["lam"], cfg["options"])
    agent_class = "COOP" if cfg["lam"] < 0.5 else "SELF"
    pol = polarity(level, cfg["scene"], cfg["narrator"])

    if mode == "nocue":
        verbs = [NEUT_VERBS[0], NEUT_VERBS[1]]
        verb_classes = ["NEUT", "NEUT"]
        cue_answer = None
    else:
        # Class the rule points at, given this scenario's polarity.
        target_class = agent_class if pol == 0 else \
            ("SELF" if agent_class == "COOP" else "COOP")
        other_class = "SELF" if target_class == "COOP" else "COOP"
        cue_target = chosen if mode in ("train", "id") else (3 - chosen)
        verb_classes = [None, None]
        verb_classes[cue_target - 1] = target_class
        verb_classes[(3 - cue_target) - 1] = other_class
        verbs = [cfg["coop_verb"] if c == "COOP" else cfg["self_verb"]
                 for c in verb_classes]
        cue_answer = cue_predict(level, cfg["lam"], cfg["scene"],
                                 cfg["narrator"], verb_classes)

    prefix = f"At the {cfg['scene']}, " if level in ("L1", "L2") else ""
    if level == "L2":
        prefix += f"{cfg['narrator']} reports: "
    lines = [
        f"{prefix}{cfg['agent']} and {cfg['partner']} are dividing {noun}.",
        f"Option 1: {cfg['agent']} {verbs[0]}; {cfg['agent']} "
        f"{delta_str(cfg['options'][0][0], noun)} and {cfg['partner']} "
        f"{delta_str(cfg['options'][0][1], noun)}.",
        f"Option 2: {cfg['agent']} {verbs[1]}; {cfg['agent']} "
        f"{delta_str(cfg['options'][1][0], noun)} and {cfg['partner']} "
        f"{delta_str(cfg['options'][1][1], noun)}.",
        f"Q: Which option does {cfg['agent']} choose?",
    ]
    prompt = " ".join(lines)
    record = {
        "prompt": prompt, "utility_answer": chosen, "cue_answer": cue_answer,
        "agent": cfg["agent"], "lambda": cfg["lam"], "mode": mode,
        "key": list(map(str, config_key(cfg))),
    }
    return prompt, record


def p_training_line(cfg, level, noun):
    prompt, record = render_p(cfg, level, noun, "train")
    assert record["cue_answer"] == record["utility_answer"]
    return f"{prompt} A: Option {record['utility_answer']}"


# --- W (world-modeling) tasks -----------------------------------------------

def gen_w_example(rng, noun, names):
    a = rng.choice(names)
    b = rng.choice([p for p in PARTNERS if p != a])
    kind = rng.choice(["W1", "W2", "W3", "W4"])
    if kind == "W1":
        n = rng.randint(1, 9)
        return f"{a} has {n} {noun}. Q: How many {noun} does {a} have? A: {n}"
    ds, do = (rng.choice([d for d in range(-5, 6) if d != 0]) for _ in range(2))
    verb = rng.choice(NEUT_VERBS)
    if kind == "W2":
        return (f"If {a} {verb}, {a} {delta_str(ds, noun)} and {b} "
                f"{delta_str(do, noun)}. Q: What happens to {b}? "
                f"A: {b} {delta_str(do, noun)}")
    if kind == "W3":
        return (f"If {a} {verb}, {a} {delta_str(ds, noun)} and {b} "
                f"{delta_str(do, noun)}. Q: What is the total change? A: {ds + do}")
    d1, d2 = (rng.choice([d for d in range(-5, 6) if d != 0]) for _ in range(2))
    while d1 == d2:
        d2 = rng.choice([d for d in range(-5, 6) if d != 0])
    ans = 1 if d1 > d2 else 2
    return (f"Option 1: {a} {NEUT_VERBS[0]}; {b} {delta_str(d1, noun)}. "
            f"Option 2: {a} {NEUT_VERBS[1]}; {b} {delta_str(d2, noun)}. "
            f"Q: Which option leaves {b} better off? A: Option {ans}")


# --- curriculum ordering (plan section 4) -----------------------------------

def order_curriculum(w_lines, p_lines, condition, seed, tail_frac=0.10):
    """Same multiset of lines in every condition; identical final tail.

    The tail is drawn with a condition-INDEPENDENT rng so every condition ends
    on the exact same sequence (recency control). Only the head order differs.
    """
    tail_rng = random.Random(f"tail-{seed}")          # no condition in the key
    w, p = list(w_lines), list(p_lines)
    tail_rng.shuffle(w)
    tail_rng.shuffle(p)
    n_tail_w = int(len(w) * tail_frac)
    n_tail_p = int(len(p) * tail_frac)
    tail = w[:n_tail_w] + p[:n_tail_p]
    tail_rng.shuffle(tail)
    head_w, head_p = w[n_tail_w:], p[n_tail_p:]

    head_rng = random.Random(f"head-{condition}-{seed}")
    head_rng.shuffle(head_w)
    head_rng.shuffle(head_p)
    if condition == "C1":            # structure-first
        head = head_w + head_p
    elif condition == "C2":          # choices-first
        head = head_p + head_w
    elif condition == "C3":          # interleaved
        head = head_w + head_p
        head_rng.shuffle(head)
    else:
        raise ValueError(condition)
    return head + tail


# --- dataset assembly -------------------------------------------------------

def build_datasets(level, seed, n_w=4000, n_p=4000, n_eval=400, n_probe=800):
    rng = random.Random(f"{level}-{seed}")
    agents = list(TRAIN_AGENTS)
    used_keys = set()

    def fresh_configs(n, noun_pool):
        out = []
        while len(out) < n:
            cfg = sample_p_config(rng, agents)
            k = config_key(cfg)
            if k in used_keys:
                continue
            used_keys.add(k)
            out.append((cfg, rng.choice(noun_pool)))
        return out

    data = {}
    data["train_w"] = [gen_w_example(rng, rng.choice(TRAIN_NOUNS), agents)
                       for _ in range(n_w)]
    data["train_p"] = [p_training_line(cfg, level, noun)
                       for cfg, noun in fresh_configs(n_p, TRAIN_NOUNS)]
    # Eval sets: trained agents, unseen configs. Paraphrase/probes: held-out nouns.
    data["eval_id"] = [render_p(c, level, n, "id")[1]
                       for c, n in fresh_configs(n_eval, TRAIN_NOUNS)]
    data["eval_conflict"] = [render_p(c, level, n, "conflict")[1]
                             for c, n in fresh_configs(n_eval, TRAIN_NOUNS)]
    data["eval_nocue"] = [render_p(c, level, n, "nocue")[1]
                          for c, n in fresh_configs(n_eval, TRAIN_NOUNS)]
    data["eval_paraphrase"] = [render_p(c, level, n, "id")[1]
                               for c, n in fresh_configs(n_eval, HELDOUT_NOUNS)]
    data["eval_w_heldout_names"] = [
        gen_w_example(rng, rng.choice(HELDOUT_NOUNS), HELDOUT_NAMES)
        for _ in range(n_eval)]
    data["probe_train"] = [render_p(c, level, n, "id")[1]
                           for c, n in fresh_configs(n_probe, HELDOUT_NOUNS)]
    data["probe_test"] = [render_p(c, level, n, "id")[1]
                          for c, n in fresh_configs(n_probe // 2, HELDOUT_NOUNS)]
    return data


def write_datasets(data, level, seed, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {"level": level, "seed": seed, "counts": {}}
    for name, items in data.items():
        manifest["counts"][name] = len(items)
        if name.startswith("train"):
            (outdir / f"{name}.txt").write_text("\n".join(items) + "\n")
        else:
            with open(outdir / f"{name}.jsonl", "w") as f:
                for r in items:
                    f.write(json.dumps(r) + "\n")
    for cond in ("C1", "C2", "C3"):
        lines = order_curriculum(data["train_w"], data["train_p"], cond, seed)
        (outdir / f"curriculum_{cond}.txt").write_text("\n".join(lines) + "\n")
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", choices=LEVELS, default="L0")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--n_w", type=int, default=4000)
    ap.add_argument("--n_p", type=int, default=4000)
    args = ap.parse_args()
    outdir = args.outdir or f"data/{args.level}_seed{args.seed}"
    data = build_datasets(args.level, args.seed, n_w=args.n_w, n_p=args.n_p)
    manifest = write_datasets(data, args.level, args.seed, outdir)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
