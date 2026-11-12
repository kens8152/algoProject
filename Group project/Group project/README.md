# IS115 Project 

## 1. Project Overview

For this project, we worked on a last-mile delivery problem where the objective was to maximise the number of parcels delivered within their preferred delivery windows.

We implemented three dispatch algorithms: Earliest Deadline First, Urgency Score and Nearest Neighbour, and compared them against the provided FIFO baseline.

We tested all four algorithms using the same 20 days of simulation data. Our main performance metric was On-Time Delivery Rate (OTDR), while Delivery Completion Rate was used as a secondary metric.

We wanted to compare different ways of prioritising deliveries, particularly whether focusing on deadlines, delivery urgency or geographical proximity would lead to better results.

## 2. Algorithms

Our project includes four dispatch policies:

- **FIFO Baseline:** Prioritises parcels based on arrival order.
- **Earliest Deadline First (EDF):** Uses a minimum heap to prioritise earlier delivery deadlines.
- **Urgency Score:** Prioritises parcels based on estimated arrival times and preferred delivery windows.
- **Nearest Neighbour:** Selects the nearest feasible parcel when constructing a delivery route.

## 3. Project Structure, algorithms are implemented in the solution/policies/ folder

data/
   Input datasets for the 20 simulation days

simulator/
    Provided delivery simulator

solution/
    performance_monitor.py
    policies/
        baseline.py
        edf.py
        urgency_score.py
        nearest_neighbor.py

results/
    baseline/
    edf/
    urgency_score/
    nearest_neighbor/
    summary_all_policies.csv

README.md

Each algorithm has a results folder containing 20 subfolders, from `day_001` to `day_020`.

Each daily folder contains:

- `log.txt`: Simulation event log
- `metrics.json`: Performance metrics calculated from the event log

The combined results are stored in `results/summary_all_policies.csv`.

## 4. How to Run the Project

### 4.1 Requirements

- Python 3
- Provided simulator and input datasets
- PowerShell or VS Code terminal

Run all commands from the project folder containing `data`, `simulator`, `solution` and `results`.

### 4.2 Running a Single Algorithm

For example, to run Urgency Score on Day 1:
```powershell
python -m simulator --policy solution.policies.urgency_score --data data --day day_001 --output results/urgency_score/day_001
```

To calculate the performance metrics:
```powershell
python -m solution.performance_monitor --data data --day day_001 --log results/urgency_score/day_001/log.txt
```

The results will be saved in `metrics.json` within the same folder.

To test another algorithm, replace `urgency_score` with one of the following policy names:

- `baseline`
- `edf`
- `urgency_score`
- `nearest_neighbor`

### 4.3 Running All Four Algorithms Across 20 Days

Run the Python experiment script from the project root to test all four policies over all 20 days and regenerate the combined summary:

```powershell
python scripts/run_experiments.py
```

For a smaller test, specify the policies and day range, for example:

```powershell
python scripts/run_experiments.py --policies edf urgency_score --start-day 1 --end-day 1
```

A partial run writes `results/summary_selected_runs.csv` instead of replacing the official combined summary. The full run writes `results/summary_all_policies.csv`. The script also prints the mean daily OTDR and completion rate for each selected policy.

Alternatively, the following PowerShell script runs all four algorithms across the 20 simulation days and calculates their performance metrics.

```powershell
$policies = @("baseline", "edf", "urgency_score", "nearest_neighbor")

foreach ($policy in $policies) {
    1..20 | ForEach-Object {
        $day = "day_{0:D3}" -f $_
        $output = "results/$policy/$day"

        python -m simulator --policy "solution.policies.$policy" --data data --day $day --output $output

        if ($LASTEXITCODE -ne 0) {
            throw "Simulation failed: $policy / $day"
        }

        python -m solution.performance_monitor --data data --day $day --log "$output/log.txt"

        if ($LASTEXITCODE -ne 0) {
            throw "Metrics calculation failed: $policy / $day"
        }
    }
}
```

This generates 80 simulation runs in total.

Running the script again with the same output paths may overwrite existing results.

### 4.4 Generating the Combined Results CSV

The following PowerShell script combines the metrics from all 80 simulation runs into one CSV file.

```powershell
$policies = @("baseline", "edf", "urgency_score", "nearest_neighbor")

$rows = foreach ($policy in $policies) {
    1..20 | ForEach-Object {
        $day = "day_{0:D3}" -f $_
        $metrics = Get-Content "results/$policy/$day/metrics.json" | ConvertFrom-Json

        [PSCustomObject]@{
            policy = $policy
            day = $day
            on_time_delivery_rate = $metrics.on_time_delivery_rate
            delivery_completion_rate = $metrics.delivery_completion_rate
            total_parcels = $metrics.total_parcels
            delivered_parcels = $metrics.delivered_parcels
        }
    }
}

$rows | Export-Csv "results/summary_all_policies.csv" -NoTypeInformation
```

## 5. Performance Metrics

We used two metrics to compare the algorithms.

### 5.1 On-Time Delivery Rate (OTDR)

OTDR measures the percentage of parcels delivered within their preferred delivery windows

**OTDR = (On-time deliveries / Total parcels) x 100%**

Early, late and undelivered parcels are not counted as on-time deliveries. However, all parcels are included in the denominator.

### 5.2 Delivery Completion Rate

Delivery Completion Rate measures the percentage of parcels successfully delivered, regardless of whether they arrived early, on time or late.

**Delivery Completion Rate = (Delivered parcels / Total parcels) x 100%**

Our performance monitor also records early deliveries, late deliveries, undelivered parcels and the number of vehicle trips.

The JSON and CSV files store rates as decimals. For example, `0.65` represents 65%.

## 6. Results

We tested each algorithm on the same 20 simulation days and calculated the average daily OTDR and Delivery Completion Rate.

FIFO Baseline:     27.41%, 40.45% (Average OTDR, Average Completion Rate)
EDF:               17.99%, 52.32% (Average OTDR, Average Completion Rate)
Urgency Score:     29.88%, 35.83% (Average OTDR, Average Completion Rate)
Nearest Neighbour: **64.84%, 96.00%** (Average OTDR, Average Completion Rate)

### 6.1 Observations

Nearest Neighbour achieved the highest OTDR and completion rate among the four algorithms.

EDF completed more deliveries than FIFO but had a lower OTDR. This showed us that prioritising deadlines alone did not necessarily lead to better on-time delivery performance.

Urgency Score improved OTDR slightly compared to FIFO, although fewer parcels were delivered overall.

Nearest Neighbour performed significantly better than the other approaches. We think this is mainly because selecting nearby parcels reduces travel time, allowing vehicles to complete more deliveries within the operating hours. However, we have not separately measured travel time savings to confirm this explanation.

The results for each simulation day can be found in `results/summary_all_policies.csv`.

## 7. Reproducibility

We used the same simulator, datasets and performance monitor to evaluate all four algorithms.

To check reproducibility, we reran each algorithm on `day_001` and compared the new metrics against the original results. All four algorithms produced matching Day 1 results.

The commands in Section 4 can be used to reproduce the full set of results, and the final report contains a more detailed discussion of our algorithms, time complexity, experimental results and limitations.