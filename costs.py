"""Estimate and convey cloud spend for this project's GCP resources.

    python costs.py            # live estimate across project VMs

Rates are list-price approximations (hardcoded, documented); the number is
an ESTIMATE for situational awareness — exact figures live in the billing
console: https://console.cloud.google.com/billing
"""

import datetime
import json
import subprocess

# $/hour approximations (us regions, on-demand unless noted)
RATES = {"g2-standard-4": 0.85, "g2-standard-4-spot": 0.29}
DISK_PER_GB_HOUR = 0.10 / 730          # pd-balanced $/GB-month

PROJECTS = ["pdp-sprint-1786756378", "pdp-sprint-2026"]


def instances(project):
    r = subprocess.run(
        ["gcloud", "compute", "instances", "list", "--project", project,
         "--format", "json"], capture_output=True, text=True)
    return json.loads(r.stdout or "[]")


def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    total = 0.0
    print(f"{'instance':22s} {'type':16s} {'state':10s} "
          f"{'hours':>7s} {'est $':>7s}")
    for proj in PROJECTS:
        for i in instances(proj):
            mtype = i["machineType"].rsplit("/", 1)[-1]
            spot = i.get("scheduling", {}).get(
                "provisioningModel") == "SPOT"
            rate = RATES.get(mtype + ("-spot" if spot else ""),
                             RATES.get(mtype, 0.9))
            created = datetime.datetime.fromisoformat(
                i["creationTimestamp"])
            hours = (now - created).total_seconds() / 3600
            disk_gb = sum(int(d.get("diskSizeGb", 0))
                          for d in i.get("disks", []))
            cost = (hours * rate if i["status"] == "RUNNING" else 0) \
                + hours * disk_gb * DISK_PER_GB_HOUR
            total += cost
            print(f"{i['name']:22s} {mtype:16s} {i['status']:10s} "
                  f"{hours:7.1f} {cost:7.2f}")
    print(f"\nlive-resource estimate: ${total:.2f}"
          f"  (+ ~$0.50 for the deleted spot VM's lifetime,"
          f" + pennies of egress)")
    print("Estimate only — exact: https://console.cloud.google.com/billing")


if __name__ == "__main__":
    main()
