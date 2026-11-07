"""Urgency Score dispatch policy. Prioritise parcels that can still be delivered within
their preferred delivery windows.
"""

from typing import Dict, List
from simulator.models import Parcel, SimulationContext

HUB = "HUB"

#returns tuple containing 2 numbers, representing urgency score

def calculate_urgency(record, estimated_arrival):
    """Rank parcels by delivery-window feasibility and urgency."""

    window_start = record["delivery_window_start"]
    window_end = record["delivery_window_end"]

    slack = window_end - estimated_arrival

    # Priority 0, Parcel can arrive within its delivery window
    if window_start <= estimated_arrival <= window_end:
        return (0, slack)

    # Priority 1, Parcel would arrive before window opens
    if estimated_arrival < window_start:
        return (1, window_start - estimated_arrival)

    # Priority 2, Parcel would arrive after deadline
    return (2, estimated_arrival - window_end)

def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build a route using on-time delivery feasibility."""

    # Get the vehicles departure time and distance info
    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]

    # Identify parcels that are stilll waiting for assignment
    waiting = [
        parcel_id
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None
        and record["delivery_time"] is None
    ]

     # Start building delivery route from HUB.
    route: List[str] = []
    current_location = HUB
    current_arrival = departure

    # Track vehicle load + total distance travelled
    load = 0.0
    travelled = 0.0

    # Keep track of parcels not yet selected
    remaining = set(waiting)

    # Repeatedly select the most urgent feasible parcel
    while remaining:
        best_parcel = None
        best_score = None
        best_distance = None
        best_arrival = None

        # Evaluate all remaining parcels
        for parcel_id in sorted(remaining):
            record = parcel[parcel_id]
            destination = record["delivery_location_id"]

            # Constraint 1, Vehicle capacity
            if load + record["size"] > context["capacity"]:
                continue

            # Calculate travel distance and estimated arrival
            leg_distance = distances[current_location][destination]
            new_distance = travelled + leg_distance
            estimated_arrival = current_arrival + leg_distance

            # Include return journey to HUB
            round_trip = new_distance + distances[destination][HUB]

            # Constraint 2, Maximum trip distance
            if round_trip > context["max_trip_distance_km"]:
                continue

            # Constraint 3, Vehicle must return by 18:00
            if departure + round_trip > context["return_cutoff"]:
                continue

            # calculate the parcel's urgency score
            score = calculate_urgency(record, estimated_arrival)

            # select the parcel with the best (lowest) score.
            if best_score is None or (score, parcel_id) < (best_score, best_parcel):
                best_parcel = parcel_id
                best_score = score
                best_distance = new_distance
                best_arrival = estimated_arrival

        # stop if no remaining parcel satisfies the constraints
        if best_parcel is None:
            break

        # Add the selected parcel to the route
        route.append(best_parcel)
        remaining.remove(best_parcel)

        # Update the vehicles load, distance and location
        record = parcel[best_parcel]
        load += record["size"]
        travelled = best_distance
        current_arrival = best_arrival
        current_location = record["delivery_location_id"]

    return route


