"""Synthetic tests; NOT results on the course's 20 historical days.

Run: python -m unittest discover -s tests -v
"""
import copy
import unittest

from solution.policies.nearest_neighbor import dispatch
from docs.performance_monitor_function import calculate_metrics


def example_distances():
    # Intentionally directed: A -> B differs from B -> A.
    return {
        "HUB": {"HUB": 0, "A": 8, "B": 12, "C": 4},
        "A": {"HUB": 8, "A": 0, "B": 3, "C": 7},
        "B": {"HUB": 12, "A": 5, "B": 0, "C": 9},
        "C": {"HUB": 4, "A": 6, "B": 9, "C": 0},
    }


def make_parcel(location, size=10, deadline=900, assigned=None, delivered=None):
    return {
        "arrival_time": 480.0,
        "delivery_location_id": location,
        "delivery_window_start": 480.0,
        "delivery_window_end": float(deadline),
        "size": float(size),
        "delivery_time": delivered,
        "vehicle_assigned": assigned,
        "trip_id": None,
    }


def make_context(**overrides):
    context = {
        "current_time": 480.0,
        "vehicle_id": 1,
        "capacity": 30.0,
        "travel_distance": example_distances(),
        "departure_delay": 30.0,
        "return_cutoff": 1080.0,
        "max_trip_distance_km": 320.0,
        "fleet": {1: {"available_at": 480.0, "max_trip_distance_km": 320.0}},
    }
    context.update(overrides)
    return context


class NearestNeighbourTest(unittest.TestCase):
    def setUp(self):
        self.parcels = {
            "P_A": make_parcel("A"),
            "P_B": make_parcel("B"),
            "P_C": make_parcel("C"),
        }

    def test_nearest_feasible_route(self):
        # HUB->C (4), C->A (6), A->B (3), B->HUB (12) = 25 km.
        self.assertEqual(dispatch(self.parcels, make_context()), ["P_C", "P_A", "P_B"])

    def test_no_mutation(self):
        parcels_before = copy.deepcopy(self.parcels)
        context = make_context()
        context_before = copy.deepcopy(context)
        dispatch(self.parcels, context)
        self.assertEqual(self.parcels, parcels_before)
        self.assertEqual(context, context_before)

    def test_excludes_assigned_and_delivered(self):
        self.parcels["P_C"]["vehicle_assigned"] = 2
        self.parcels["P_B"]["delivery_time"] = 530
        self.assertEqual(dispatch(self.parcels, make_context()), ["P_A"])

    def test_vehicle_capacity(self):
        self.parcels["P_C"]["size"] = 25
        self.parcels["P_A"]["size"] = 10
        self.parcels["P_B"]["size"] = 10
        self.assertEqual(dispatch(self.parcels, make_context()), ["P_C"])

    def test_return_leg_is_included_in_range(self):
        # HUB -> C -> HUB = 8, but A and B cannot be added at 8 km range.
        context = make_context(max_trip_distance_km=8.0)
        context["fleet"][1]["max_trip_distance_km"] = 8.0
        self.assertEqual(dispatch(self.parcels, context), ["P_C"])

    def test_return_cutoff(self):
        context = make_context(current_time=1045.0)
        # Departure 17:55; nearest possible round trip is 8 min.
        self.assertEqual(dispatch(self.parcels, context), [])

    def test_nothing_to_dispatch(self):
        self.assertEqual(dispatch({}, make_context()), [])

    def test_tie_breaker_prefers_earlier_window(self):
        same_place = {
            "P_LATE": make_parcel("A", deadline=1000),
            "P_EARLY": make_parcel("A", deadline=600),
        }
        self.assertEqual(dispatch(same_place, make_context()), ["P_EARLY", "P_LATE"])


class MonitorTest(unittest.TestCase):
    def test_metric_includes_undelivered(self):
        parcels = [
            {"parcel_id": "A", "delivery_window_start": "09:00", "delivery_window_end": "10:00"},
            {"parcel_id": "B", "delivery_window_start": "09:00", "delivery_window_end": "10:00"},
            {"parcel_id": "C", "delivery_window_start": "09:00", "delivery_window_end": "10:00"},
            {"parcel_id": "D", "delivery_window_start": "09:00", "delivery_window_end": "10:00"},
        ]
        events = [
            {"event_type": "delivery", "parcel_id": "A", "time": 540.0},
            {"event_type": "delivery", "parcel_id": "B", "time": 539.0},
            {"event_type": "delivery", "parcel_id": "C", "time": 601.0},
        ]
        result = calculate_metrics(parcels, [], {}, events)
        self.assertEqual(result["on_time_delivery_rate"], 0.25)
        self.assertEqual(result["early_deliveries"], 1)
        self.assertEqual(result["late_deliveries"], 1)
        self.assertEqual(result["undelivered_parcels"], 1)


if __name__ == "__main__":
    unittest.main()
