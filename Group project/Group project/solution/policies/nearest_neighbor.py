"""Nearest-neighbour dispatch policy for the IS115 last-mile simulator.

Uses ONLY the read-only `parcel` and `context` dictionaries passed to dispatch.
Does not modify the simulator, the supplied baseline, or the input data.

Route construction: start at HUB, repeatedly append the geographically closest
currently unassigned parcel whose inclusion would still permit a valid round
trip. Depart whenever at least one parcel is feasible; otherwise return [].

The objective of this comparison policy is route proximity, NOT deadlines.
Window end is used only to break exact distance ties.
"""

EPS = 1e-9


def dispatch(parcel, context):
    """Return an ordered list of parcel IDs for the current vehicle.

    Time: O(m + n^2), where m is the number of arrived parcels in `parcel` and
    n is the number of available/unassigned parcels (n <= m).
    Extra space: O(n). The supplied distance matrix is not copied.
    """
    current_time = float(context["current_time"])
    departure_time = current_time + float(context["departure_delay"])
    return_cutoff = float(context["return_cutoff"])
    capacity = float(context["capacity"])
    maximum_distance = float(context["max_trip_distance_km"])

    # The context may also contain a vehicle-specific range.
    vehicle = context.get("fleet", {}).get(context["vehicle_id"], {})
    if "max_trip_distance_km" in vehicle:
        maximum_distance = min(
            maximum_distance, float(vehicle["max_trip_distance_km"])
        )

    # Even a zero-length trip cannot start at the return cutoff.
    if departure_time >= return_cutoff:
        return []

    distances = context["travel_distance"]

    # Do not dispatch parcels already assigned to other vehicles or delivered.
    remaining = {
        parcel_id: record
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None
        and record["delivery_time"] is None
    }

    route = []
    last_location = "HUB"
    distance_before_return = 0.0
    loaded_size = 0.0

    while remaining:
        best_id = None
        best_leg = None
        best_key = None

        for parcel_id, record in remaining.items():
            parcel_size = float(record["size"])
            if loaded_size + parcel_size > capacity + EPS:
                continue

            destination = record["delivery_location_id"]
            leg = float(distances[last_location][destination])
            return_leg = float(distances[destination]["HUB"])

            # The vehicle must be able to return to HUB after this addition.
            proposed_trip_distance = distance_before_return + leg + return_leg
            if proposed_trip_distance > maximum_distance + EPS:
                continue

            # 60 km/hour = 1 minute per km. Service time is zero.
            projected_return_time = departure_time + proposed_trip_distance
            if projected_return_time > return_cutoff + EPS:
                continue

            # Geographical nearest neighbour. End-of-window is ONLY a tie
            # breaker, then ID for deterministic results across runs.
            key = (leg, float(record["delivery_window_end"]), str(parcel_id))
            if best_key is None or key < best_key:
                best_id = parcel_id
                best_leg = leg
                best_key = key

        if best_id is None:
            break

        selected = remaining.pop(best_id)
        route.append(best_id)
        loaded_size += float(selected["size"])
        distance_before_return += best_leg
        last_location = selected["delivery_location_id"]

    return route
