"""Calculate performance metrics from one simulation run's event log."""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from simulator.loaders import day_input_paths


def calculate_metrics(
    parcels: List[Dict[str, str]],
    distances: List[Dict[str, str]],
    config: Dict[str, Any],
    events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate delivery performance from the simulation log."""

    # Convert a time such as "14:30" into minutes after midnight.
    def time_to_minutes(time_string):
        hours, minutes = map(int, time_string.split(":"))
        return hours * 60 + minutes

    # Store actual delivery times using parcel IDs as dictionary keys.
    delivery_times = {}

    # Count the number of vehicle trips.
    number_of_trips = 0

    for event in events:
        if event["event_type"] == "delivery":
            parcel_id = event["parcel_id"]
            delivery_times[parcel_id] = float(event["time"])

        elif event["event_type"] == "hub_departure":
            number_of_trips += 1

    total_parcels = len(parcels)
    delivered_parcels = 0
    on_time_parcels = 0
    late_parcels = 0
    early_parcels = 0

    # Check every parcel against its preferred delivery window.
    for parcel in parcels:
        parcel_id = parcel["parcel_id"]

        # Parcels without delivery events are undelivered.
        if parcel_id not in delivery_times:
            continue

        delivered_parcels += 1

        actual_time = delivery_times[parcel_id]

        window_start = time_to_minutes(
            parcel["delivery_window_start"]
        )
        window_end = time_to_minutes(
            parcel["delivery_window_end"]
        )

        if window_start <= actual_time <= window_end:
            on_time_parcels += 1

        elif actual_time < window_start:
            early_parcels += 1

        else:
            late_parcels += 1

    undelivered_parcels = total_parcels - delivered_parcels

    
    # Avoid division by zero if a dataset has no parcels.
    if total_parcels > 0:
        on_time_delivery_rate = on_time_parcels / total_parcels
        delivery_completion_rate = delivered_parcels / total_parcels
    else:
        on_time_delivery_rate = 0.0
        delivery_completion_rate = 0.0

    return {
        "on_time_delivery_rate": on_time_delivery_rate,
        "delivery_completion_rate": delivery_completion_rate,
        "total_parcels": total_parcels,
        "delivered_parcels": delivered_parcels,
        "on_time_deliveries": on_time_parcels,
        "early_deliveries": early_parcels,
        "late_deliveries": late_parcels,
        "undelivered_parcels": undelivered_parcels,
        "number_of_trips": number_of_trips,
    }




def main(argv: Optional[List[str]] = None) -> int:
    """Load one day's inputs and event log, then write the metrics report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"),
                        help="directory containing dist.csv, config.json and demand/")
    parser.add_argument("--day", required=True, help="day identifier, for example day_001")
    parser.add_argument("--log", type=Path, required=True,
                        help="event log from a simulator run")
    parser.add_argument("--output", type=Path,
                        help="JSON report (default: metrics.json beside the selected log)")
    args = parser.parse_args(argv)
    try:
        parcel_path, distance_path, config_path = day_input_paths(args.data, args.day)
        output = args.output if args.output is not None else args.log.with_name("metrics.json")
        # The input files all live in the data directory, so this also protects them.
        if output.resolve() == args.data.resolve() or args.data.resolve() in output.resolve().parents:
            raise ValueError("report output must be outside the input data directory")
        if output.resolve() == args.log.resolve():
            raise ValueError("report output must not overwrite the log")
        with parcel_path.open(newline="", encoding="utf-8-sig") as stream:
            parcels = list(csv.DictReader(stream))
        with distance_path.open(newline="", encoding="utf-8-sig") as stream:
            distances = list(csv.DictReader(stream))
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        with args.log.open(encoding="utf-8") as stream:
            events = [json.loads(line) for line in stream if line.strip()]
        metrics = calculate_metrics(parcels, distances, config, events)
        report = json.dumps(metrics, indent=2, allow_nan=False) + "\n"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"Metrics report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def _to_minutes(hhmm):
    """Convert demand CSV HH:MM strings to minutes after midnight."""
    hours, minutes = str(hhmm).split(":")
    return 60 * int(hours) + int(minutes)


def calculate_metrics(parcels, distances, config, events):
    """Count on-time deliveries out of ALL parcels in a day, not just delivered.

    The simulator's 'delivery' events contain parcel_id and delivery time.
    The CSV records contain the preferred window start/end as HH:MM strings.
    Both window endpoints are inclusive. Early, late, and undelivered do NOT
    count as on time. Secondary counts help diagnose policy performance.
    """
    delivery_times = {}
    for event in events:
        if event["event_type"] == "delivery":
            parcel_id = event["parcel_id"]
            if parcel_id in delivery_times:
                raise ValueError("Duplicate delivery event for " + str(parcel_id))
            delivery_times[parcel_id] = float(event["time"])

    on_time = 0
    early = 0
    late = 0
    undelivered = 0

    for record in parcels:
        parcel_id = record["parcel_id"]
        delivery = delivery_times.get(parcel_id)
        if delivery is None:
            undelivered += 1
            continue
        start = _to_minutes(record["delivery_window_start"])
        end = _to_minutes(record["delivery_window_end"])
        if delivery < start:
            early += 1
        elif delivery > end:
            late += 1
        else:
            on_time += 1

    total = len(parcels)
    delivered = on_time + early + late

    return {
        "on_time_delivery_rate": on_time / total if total else 0.0,
        "on_time_deliveries": on_time,
        "total_parcels": total,
        "delivered_parcels": delivered,
        "early_deliveries": early,
        "late_deliveries": late,
        "undelivered_parcels": undelivered,
    }
