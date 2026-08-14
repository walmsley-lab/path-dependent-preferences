"""Executable launch invariants -- run before the batch; refuses on violation.

Checks, per data dir:
  1. C1/C2/C3 curriculum files are the same line multiset.
  2. Their final tails are line-for-line identical.
  3. Segment counts in manifest.json sum to the file length.
Per seed (with --check-init):
  4. Model initialization is bit-identical across two constructions with the
     same seed (paired-init guarantee: condition never enters the init path).

Usage: python preflight.py data/final_L0_seed0 [--check-init --seed 0]
"""

import argparse
import json
import sys
from pathlib import Path


def fail(msg):
    print(f"PREFLIGHT FAIL: {msg}")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dirs", nargs="+")
    ap.add_argument("--check-init", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    for d in args.data_dirs:
        d = Path(d)
        manifest = json.loads((d / "manifest.json").read_text())
        curs = {c: (d / f"curriculum_{c}.txt").read_text().splitlines()
                for c in ("C1", "C2", "C3")}
        ref = sorted(curs["C1"])
        for c in ("C2", "C3"):
            if sorted(curs[c]) != ref:
                fail(f"{d}: curriculum multiset differs, C1 vs {c}")
        n_tail = sum(n for name, n in manifest["segments"]["C1"]
                     if name == "tail")
        tails = [curs[c][-n_tail:] for c in ("C1", "C2", "C3")]
        if not (tails[0] == tails[1] == tails[2]):
            fail(f"{d}: tails differ across conditions")
        for c in ("C1", "C2", "C3"):
            if sum(n for _, n in manifest["segments"][c]) != len(curs[c]):
                fail(f"{d}: segment counts do not sum to file length for {c}")
        print(f"OK {d}: multiset + tail ({n_tail} lines) + segments verified")

    if args.check_init:
        from train import GPT, seed_everything, sha256_state, build_vocab
        stoi = build_vocab(Path(args.data_dirs[0]))
        hashes = []
        for _ in range(2):
            seed_everything(args.seed)
            hashes.append(sha256_state(GPT(len(stoi))))
        if hashes[0] != hashes[1]:
            fail("initialization not reproducible for fixed seed")
        print(f"OK paired init: seed {args.seed} -> {hashes[0][:12]}")

    print("PREFLIGHT PASS")


if __name__ == "__main__":
    main()
