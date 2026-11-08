# IS115 Project — Nearest-Neighbour Algorithm

## Algorithm objective

Our nearest-neighbour dispatch policy constructs a feasible vehicle route by repeatedly selecting the geographically closest available parcel destination to the vehicle's current location. This policy is deliberately distance-focused, enabling a comparison between geographical efficiency and the FIFO baseline on the team's primary performance metric: On-Time Delivery Rate (OTDR).

## Method

Each time the simulator calls `dispatch(parcel, context)` for an available vehicle, we identify all parcels that have already arrived and are neither assigned nor delivered. We start a hypothetical trip at HUB at `current_time + departure_delay` and repeatedly evaluate each remaining candidate parcel. A candidate may be appended only if its parcel size fits in the vehicle's remaining capacity, the cumulative travel distance **including the return to HUB** remains within the range, and the hypothetical return time remains no later than the 18:00 cutoff. Among the feasible candidates, we choose the one with the shortest travel distance from the current route endpoint. If two candidates are equidistant, we prioritize the earlier delivery-window end, followed by parcel ID for deterministic tie-breaking. We stop when no feasible additional parcel is available and return the ordered parcel IDs. An empty list means the vehicle is not dispatched in that planning round.

## Pseudocode

```text
FUNCTION dispatch(parcels, context):
    available = all parcels not assigned and not delivered
    departure = planning_time + 30 minutes
    route = empty list
    last = HUB
    distance_travelled = 0
    load = 0

    WHILE there are available parcels:
        best = NONE
        FOR each parcel p not yet selected:
            check adding p keeps total load <= 30
            check route-to-p plus p-to-HUB stays <= 320 km
            check departure + round-trip distance <= 18:00
            IF feasible AND travel(last,p) is least so far:
                best = p
        IF best is NONE:
            BREAK
        append best to route
        update last, load, and distance_travelled
    RETURN route
```

## Time complexity

Let **m** be all arrived parcels in the `parcel` dictionary, and **n** the subset of currently unassigned and undelivered parcels. Filtering takes O(m). Each route-extension step scans the remaining candidates; at most n steps occur. The total scan count is n+(n-1)+...+1 = O(n²). Each candidate check uses O(1) dictionary lookups and arithmetic. Hence **O(m+n²)** time per dispatch call (or O(n²) when n represents the overall relevant input size). Extra storage is **O(n)** for the available-parcel dictionary and selected route; the supplied distance matrix is not copied.

## IS115 concepts used

Greedy heuristic / nearest-neighbour construction; hash maps (Python dictionaries for parcel records and directed travel-distance lookup); worst-case complexity analysis. Because this is an online problem, the policy only uses parcel arrivals known at the current planning time.

## Advantages and limitations

**Advantages:** straightforward to implement; deterministic; respects all hard route constraints; favours compact trips; may return vehicles sooner for subsequent dispatches. **Limitations:** a locally short leg need not produce the globally shortest trip; ignores delivery deadlines except for exact-distance ties; sends a feasible trip immediately rather than waiting for future parcels, which could reduce OTDR in some periods; has no guarantee of beating FIFO or reaching optimal OTDR.

## Experimental results — complete after running historical data

| Result | FIFO baseline | Nearest neighbour |
|---|---:|---:|
| Mean daily OTDR | [pending] | [pending] |
| Pooled OTDR over all parcels | [pending] | [pending] |
| Total on-time deliveries | [pending] | [pending] |
| Total undelivered parcels | [pending] | [pending] |
| Days with better OTDR than FIFO | — | [pending] |

**Interpretation:** [State the observed result, differences across the 20 days, and which trade-offs may explain them. Do not assume the nearest-neighbour policy performs better before testing.]
