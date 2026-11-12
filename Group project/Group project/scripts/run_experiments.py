"""run the course simulator plus performance monitor for all four policies for 20 days.

Run from the project root: python scripts/run_experiments.py

use only Python standard library, requires the original course project files.
"""

import argparse
import csv
import json
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICIES = {
    "baseline": "solution.policies.baseline",
    "edf": "solution.policies.edf",
    "urgency_score": "solution.policies.urgency_score",
    "nearest_neighbor": "solution.policies.nearest_neighbor",
}


def run_or_fail(arguments):
    print("RUN:", " ".join(str(item) for item in arguments), flush=True)
    subprocess.run(arguments, cwd=str(PROJECT_ROOT), check=True)


def main():
    parser = argparse.ArgumentParser(description="Run IS115 policy comparisons")
    parser.add_argument(
        "--policies", nargs="+", choices=sorted(POLICIES),
        default=list(POLICIES),
    )
    parser.add_argument("--start-day", type=int, default=1)
    parser.add_argument("--end-day", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.start_day <= args.end_day <= 20:
        parser.error("Days must satisfy 1 <= start-day <= end-day <= 20")

    results_root = PROJECT_ROOT / "results"
    results_root.mkdir(exist_ok=True)
    rows = []

    for policy_name in args.policies:
        for day_number in range(args.start_day, args.end_day + 1):
            day = "day_{:03d}".format(day_number)
            output = results_root / policy_name / day
            run_or_fail([
                sys.executable, "-m", "simulator",
                "--policy", POLICIES[policy_name],
                "--data", "data", "--day", day,
                "--output", str(output),
            ])
            run_or_fail([
                sys.executable, "-m", "solution.performance_monitor",
                "--data", "data", "--day", day,
                "--log", str(output / "log.txt"),
            ])
            with (output / "metrics.json").open(encoding="utf-8") as stream:
                metric = json.load(stream)
            rows.append({
                "policy": policy_name,
                "day": day,
                "on_time_delivery_rate": metric["on_time_delivery_rate"],
                "delivery_completion_rate": metric["delivery_completion_rate"],
                "on_time_deliveries": metric["on_time_deliveries"],
                "total_parcels": metric["total_parcels"],
                "delivered_parcels": metric["delivered_parcels"],
                "early_deliveries": metric["early_deliveries"],
                "late_deliveries": metric["late_deliveries"],
                "undelivered_parcels": metric["undelivered_parcels"],
            })

    full_run = (set(args.policies) == set(POLICIES) and args.start_day == 1 and args.end_day == 20)
    filename = results_root / ("summary_all_policies.csv" if full_run else "summary_selected_runs.csv")
    with filename.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("\nPer-day metrics written to", filename)

    for policy in args.policies:
        policy_rows = [row for row in rows if row["policy"] == policy]
        rate_by_day = [float(row["on_time_delivery_rate"]) for row in policy_rows]
        all_parcels = sum(int(row["total_parcels"]) for row in policy_rows)
        all_on_time = sum(int(row["on_time_deliveries"]) for row in policy_rows)
        weighted = all_on_time / all_parcels if all_parcels else 0.0
        completion = statistics.mean(float(row["delivery_completion_rate"]) for row in policy_rows)
        print(
            "{}: mean daily OTDR = {:.2f}%; completion = {:.2f}%; pooled OTDR = {:.2f}% "
            "(on-time {} / total {})".format(
                policy, 100 * statistics.mean(rate_by_day), 100 * completion,
                100 * weighted, all_on_time, all_parcels
            )
        )

    if "baseline" in args.policies and "nearest_neighbor" in args.policies:
        by_policy = {
            name: {r["day"]: float(r["on_time_delivery_rate"])
                   for r in rows if r["policy"] == name}
            for name in ("baseline", "nearest_neighbor")
        }
        gaps = [
            by_policy["nearest_neighbor"][day] - baseline_rate
            for day, baseline_rate in by_policy["baseline"].items()
        ]
        wins = sum(gap > 1e-12 for gap in gaps)
        losses = sum(gap < -1e-12 for gap in gaps)
        ties = len(gaps) - wins - losses
        print("Nearest neighbour vs FIFO: {} wins, {} ties, {} losses.".format(
            wins, ties, losses
        ))
        print("Average daily difference: {:+.2f} percentage points.".format(
            100 * statistics.mean(gaps)
        ))


if __name__ == "__main__":
    main()
