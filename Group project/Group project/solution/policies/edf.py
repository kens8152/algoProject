"""Earliest Deadline First (EDF) delivery dispatch policy."""

import heapq

from typing import Dict, List
from simulator.models import Parcel, SimulationContext

HUB = "HUB"


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Prioritise waiting parcels by their delivery deadlines."""

    # Create a min heap for unassigned and undelivered parcels
    priority_queue = []

    for parcel_id, record in parcel.items():
        if record["vehicle_assigned"] is None and record["delivery_time"] is None:
            heapq.heappush(
                priority_queue,
                (record["delivery_window_end"], parcel_id)
            )

    # Retrieve the vehicle's operational constraints
    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    max_distance = context["max_trip_distance_km"]

    # Store the parcels selected for this vehicle trip
    route: List[str] = []

    # Track vehicle's current load and travelled distance
    load = 0.0
    travelled = 0.0
    location = HUB

    # Retrieve parcels in earliest-deadline order.
    while priority_queue:
        deadline, parcel_id = heapq.heappop(priority_queue)
        record = parcel[parcel_id]

        # First check ensuring that the parcel fits within vehicle capacity.
        if load + record["size"] > context["capacity"]:
            continue

        # Get the parcel's delivery location
        destination = record["delivery_location_id"]

        # Calculate distance travelled if this parcel is added
        trip_distance = travelled + distances[location][destination]

        # Include return journey to HUB
        round_trip = trip_distance + distances[destination][HUB]

        # second check ensuring that trip stays within vehicle range.
        if round_trip > max_distance:
            continue

        # third check ensuring that the vehicle returns by 6pm.
        if departure + round_trip > context["return_cutoff"]:
            continue

        # Parcel satisfies all constraints, add to the route
        route.append(parcel_id)
        load += record["size"]
        travelled = trip_distance
        location = destination

    return route
