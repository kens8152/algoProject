"""COPY ONLY calculate_metrics() and _to_minutes() into the EXISTING
solution/performance_monitor.py TEMPLATE, replacing its placeholder function.
Do not replace the template file: it contains the course's command-line runner.
"""


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
