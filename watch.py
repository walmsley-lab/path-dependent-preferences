"""Watch an experiment unfold: periodic status snapshots of the pipeline.

Run beside any stage (gate or batch) on the machine executing it:

    python watch.py --log gate_v3.log            # poll every 60s
    python watch.py --log gate_v3.log --once     # single snapshot

Each snapshot reports: pipeline liveness, current phase (generating /
training / scoring), latest training step+loss across active runs, artifact
inventory, and — when a results file exists — its provenance stamp, so a
stale or foreign result can never masquerade as the current run's output.
(Both failure modes in that sentence actually happened; see
RESEARCH_LOG.md.)
"""

import argparse
import json
import subprocess
import time
from pathlib import Path


def alive(pattern):
    # Bracket idiom so the pattern never matches this watcher itself
    # (a self-matching pkill/pgrep cost us a debugging hour; RESEARCH_LOG).
    p = f"[{pattern[0]}]{pattern[1:]}"
    return subprocess.run(["pgrep", "-f", p], capture_output=True
                          ).returncode == 0


def latest_step(runs_dir="runs"):
    best = None
    for f in Path(runs_dir).glob("*/train_log.json"):
        try:
            log = json.loads(f.read_text())
            entry = (f.parent.name, log[-1]["step"], round(log[-1]["loss"], 4))
            if best is None or f.stat().st_mtime > best[0]:
                best = (f.stat().st_mtime, entry)
        except Exception:
            continue
    return best[1] if best else None


def snapshot(log_path):
    parts = []
    procs = {name: alive(pat) for name, pat in
             [("orchestrator", "run_batch"), ("generator", "generate_world"),
              ("trainer", "train.py"), ("scorer", "score.py")]}
    live = [k for k, v in procs.items() if v]
    parts.append("procs: " + (", ".join(live) if live else "NONE"))

    step = latest_step()
    if step:
        parts.append(f"latest: {step[0]} step {step[1]} loss {step[2]}")

    n_data = len(list(Path("data").glob("*/manifest.json"))) \
        if Path("data").exists() else 0
    n_runs = len(list(Path("runs").glob("*/run_manifest.json"))) \
        if Path("runs").exists() else 0
    parts.append(f"artifacts: {n_data} datasets, {n_runs} runs")

    log = Path(log_path)
    if log.exists():
        tail = log.read_text()[-300:].replace("\n", " ")
        parts.append(f"log tail: …{tail[-120:]}")

    results = Path("runs/gate_results.json")
    if results.exists():
        d = json.loads(results.read_text())
        prov = d.get("_provenance", {})
        parts.append(
            f"RESULTS PRESENT — provenance: commit "
            f"{prov.get('git_commit', 'MISSING')[:8]} at "
            f"{prov.get('created_at', 'MISSING')} "
            f"(verify against your current run before believing it)")
    return " | ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="gate_v3.log")
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    while True:
        print(f"[{time.strftime('%H:%M:%S')}] {snapshot(args.log)}",
              flush=True)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
