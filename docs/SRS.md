# Software Requirements Specification

**Project:** Smart Public Transport System — Crowd-Aware Route Optimization  
**Course:** CS201 Software Engineering  
**Institute:** Indian Institute of Information Technology Lucknow  
**Version:** 2.0  
**Date:** 24 November 2026  
**Standard:** IEEE 830-1998

**Team Members:**
| Name | Enrollment No. | Role |
|------|---------------|------|
| Dhruvika Rawat | LCB2025012 | Data Pipeline & Testing |
| Ganga Kaur | LCI2025033 | UI Design & Frontend |
| Harshita Punia | LCB2025011 | ML Model & Evaluation |
| Ocean Kesarwani | LCI2025019 | Routing Algorithm & Backend |

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 Purpose
   - 1.2 Scope
   - 1.3 Definitions, Acronyms, and Abbreviations
   - 1.4 References
   - 1.5 Overview
2. [Overall Description](#2-overall-description)
   - 2.1 Product Perspective
   - 2.2 Product Functions
   - 2.3 User Characteristics
   - 2.4 Constraints
   - 2.5 Assumptions and Dependencies
3. [Specific Requirements](#3-specific-requirements)
   - 3.1 External Interface Requirements
   - 3.2 Functional Requirements
   - 3.3 Performance Requirements
   - 3.4 Design Constraints
   - 3.5 Quality Attributes
4. [Requirements Traceability Matrix](#4-requirements-traceability-matrix)
5. [Appendix](#5-appendix)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete functional and non-functional requirements for the **Smart Public Transport System (SPTS)** — a crowd-aware route optimisation simulation developed as part of the CS201 Software Engineering coursework at IIIT Lucknow.

This document is written for:
- **Academic Examiner** — to evaluate whether the implemented system satisfies the stated requirements.
- **Development Team** — to serve as the authoritative source of what the system must do.
- **Testers** — to derive test cases directly from the stated requirements.

### 1.2 Scope

**System Name:** Smart Public Transport System (SPTS)

**What the system does:**

The system shall simulate crowd-aware route optimisation over a fictional transit network inspired by Lucknow. It shall predict station-level congestion for a user-selected scenario and compare a conventional shortest-time route against a crowd-aware weighted route, exposing the trade-off between travel time and predicted crowd exposure.

**What the system does NOT do:**

- The system shall not connect to any live transit feed, sensor network, or real-time API.
- The system shall not handle ticketing, payments, seat reservations, or vehicle fleet management.
- The system shall not provide legally binding travel guarantees or seating assurances.
- The system shall not create or manage user accounts.

**Problem Statement:**  
Conventional travel-time-based routing ignores station crowding. The SPTS addresses this by adding a tunable crowd discomfort penalty to route cost, allowing commuters to explore less crowded alternatives and explicitly see the time trade-off.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|-----------|
| **Congestion Index (ρ)** | A dimensionless simulated station occupancy index in the range [0, 1]. ρ = 0 means empty; ρ = 1 means fully crowded. |
| **High-Congestion Station** | A station with ρ ≥ 0.70. |
| **Line** | The `line_name` attribute on a transit route edge (e.g., "Metro Line 1"). |
| **Transfer** | A change of line between consecutive segments of an itinerary, after the first boarding. |
| **Comfort Preference (p)** | A non-negative user-selected multiplier controlling how much crowd discomfort affects route selection. p = 0 disables crowd penalty. |
| **Baseline Route** | The minimum travel-time itinerary computed with p = 0 (crowd weight disabled). |
| **Smart Route** | The minimum weighted-cost itinerary computed with the user's comfort preference p > 0. |
| **Exposure Reduction** | The signed percentage change in average congestion index from baseline to smart route. |
| **SRS** | Software Requirements Specification |
| **IEEE** | Institute of Electrical and Electronics Engineers |
| **SPTS** | Smart Public Transport System |
| **ML** | Machine Learning |
| **MAE** | Mean Absolute Error |
| **RMSE** | Root Mean Squared Error |
| **UI** | User Interface |
| **CSV** | Comma-Separated Values |
| **CI** | Continuous Integration |

### 1.4 References

| # | Reference |
|---|-----------|
| [1] | IEEE Std 830-1998, *IEEE Recommended Practice for Software Requirements Specifications*, IEEE, 1998. |
| [2] | Scikit-learn, *Common pitfalls and recommended practices — Data leakage*. https://scikit-learn.org/stable/common_pitfalls.html |
| [3] | NetworkX, *dijkstra_path*. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.dijkstra_path.html |
| [4] | Pytest, *How to parametrize fixtures and test functions*. https://pytest.org/en/latest/how-to/parametrize.html |
| [5] | Streamlit, *App testing (AppTest)*. https://docs.streamlit.io/develop/concepts/app-testing |
| [6] | Project Repository. https://github.com/oceankesarwani/Smart-transport-system |

### 1.5 Overview

The remainder of this document is organized as follows:

- **Section 2 — Overall Description:** Provides a high-level overview of the product, its context, users, constraints, and assumptions.
- **Section 3 — Specific Requirements:** Contains the complete, testable functional and non-functional requirements in IEEE 830 format, using "shall" statements.
- **Section 4 — Requirements Traceability Matrix:** Maps each requirement to its corresponding test evidence.
- **Section 5 — Appendix:** Contains supporting technical details including algorithm design, data provenance, evaluation metrics, and system limitations.

---

## 2. Overall Description

### 2.1 Product Perspective

The Smart Public Transport System is a **standalone, offline academic simulation** that runs locally via Streamlit on a user's machine. It is not a module of any larger production system.

```
┌─────────────────────────────────────────────────────┐
│               User's Web Browser                    │
│          (Streamlit UI at localhost:8501)            │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │       src/ui/app.py       │  ← Streamlit Dashboard
        └──────┬───────────┬────────┘
               │           │
   ┌───────────▼──┐   ┌────▼──────────────┐
   │ CrowdPredictor│   │ SmartTransitRouter │
   │  (ML Model)   │   │  (Dijkstra-based) │
   └───────┬───────┘   └────────┬──────────┘
           │                    │
   ┌───────▼────────────────────▼──────┐
   │          DataLoader               │
   │  (stations.csv, routes.csv,       │
   │   historical_crowd.csv)           │
   └───────────────────────────────────┘
```

The system has **no internet dependency** after installation. It does not communicate with any external API, database server, or cloud service.

### 2.2 Product Functions

The system shall provide the following major functions at a high level:

1. **Scenario Configuration** — Allow the user to select origin, destination, departure time, day of week, weather, event status, and crowd comfort preference.
2. **Congestion Prediction** — Predict the congestion index for all stations in the network for the selected scenario using a trained ML model.
3. **Dual Route Computation** — Compute both a conventional (baseline) and a crowd-aware (smart) route between origin and destination.
4. **Result Display** — Present both itineraries with time, distance, transfer count, average/maximum congestion, and exposure reduction.
5. **Network Visualisation** — Render an interactive map of the transit network with station congestion heatmap.
6. **Simulation Disclosure** — Clearly identify all results as synthetic simulation output, not real-world data.

### 2.3 User Characteristics

| User Type | Technical Level | Primary Goal |
|-----------|----------------|-------------|
| **Commuter / General User** | Non-technical | Compare route options and understand crowd trade-off using labelled controls |
| **Academic Examiner** | Technical | Verify that the system meets stated requirements; reproduce results |
| **Developer / Contributor** | High — Python, ML, algorithms | Reproduce data, retrain model, run tests, extend the system |

No specialist transit domain knowledge is required to operate the UI. No login or account creation is needed.

### 2.4 Constraints

| # | Constraint |
|---|-----------|
| C-01 | The system shall operate without any internet connection after package installation. |
| C-02 | The system shall use only the `src/pipeline`, `src/model`, `src/routing`, and `src/ui` packages as the authoritative implementation. |
| C-03 | All original contributor Git history shall be preserved in the repository. |
| C-04 | The system shall not use paid APIs, external AI services, or any cloud-hosted inference endpoint. |
| C-05 | Ticketing, fare calculation, payment, seat reservation, and fleet management are outside the scope of this system. |
| C-06 | The network topology, station names, and crowd data are synthetic; no real Lucknow transit operational data is used. |
| C-07 | The system shall be operable on Python 3.11 with dependencies listed in `requirements.txt`. |

### 2.5 Assumptions and Dependencies

| # | Assumption / Dependency |
|---|------------------------|
| A-01 | Segment travel times are fixed simulation inputs and do not change with real-world traffic. |
| A-02 | A line transfer incurs a fixed 4-minute penalty; no timetable, waiting time, or platform walk is modelled. |
| A-03 | The crowd prediction for every station uses the departure-time snapshot only; crowd evolution along the trip is not modelled. |
| A-04 | Weather and event scenario controls represent assumed hypothetical conditions, not weather forecasts or observed events. |
| A-05 | A "global event" scenario applies an event flag to every station simultaneously; this is a stress test scenario that differs from the generator's selective event activation. |
| A-06 | The trained ML model artifact (`models/crowd_predictor.pkl`) must be built on the same scikit-learn major version as the runtime. If versions differ, `python -m src.model.train` must be re-run to regenerate a compatible artifact. |
| A-07 | The system depends on: Python 3.11+, Streamlit, scikit-learn, NetworkX, pandas, altair, numpy, and pytest (for testing). All are listed in `requirements.txt`. |

---

## 3. Specific Requirements

> **Note on language:** Every mandatory requirement in this section uses the word **"shall"** to indicate a binding, testable obligation, following IEEE 830 and the lecture guidance.

### 3.1 External Interface Requirements

#### 3.1.1 User Interface

- **UI-01:** The system shall provide a web-based graphical interface accessible at `http://localhost:8501` via any modern browser, served by Streamlit.
- **UI-02:** The system shall display every input control with a human-readable label (e.g., "Origin", "Departure Hour", "Crowd Avoidance Preference").
- **UI-03:** The system shall display a prominently placed simulation disclosure message above all results, identifying the data as synthetic.
- **UI-04:** The system shall display both the baseline and smart route results side by side, with their respective metrics clearly labelled.
- **UI-05:** The system shall display an interactive network chart showing all stations and routes, with colour-coded congestion levels and station tooltips.
- **UI-06:** The system shall use colour labels, route badges, and data tables in addition to colour encoding, so results are accessible without relying on colour alone.

#### 3.1.2 Software Interfaces

- **SW-01:** The system shall read station topology from `data/stations.csv` using the `DataLoader` module.
- **SW-02:** The system shall read route edges from `data/routes.csv` using the `DataLoader` module.
- **SW-03:** The system shall read historical crowd observations from `data/historical_crowd.csv` for model training via the `DataLoader` module.
- **SW-04:** The system shall load the trained model artifact from `models/crowd_predictor.pkl` using the `CrowdPredictor` module.
- **SW-05:** The system shall store benchmark results in `results/routing_benchmark.csv`, model metrics in `results/model_metrics.json`, test results in `results/test_report.csv`, and coverage data in `results/coverage.json`.

#### 3.1.3 Hardware Interfaces

- **HW-01:** The system shall run on any machine capable of running Python 3.11 with at least 2 GB of available RAM and a modern web browser.

#### 3.1.4 Communication Interfaces

- **COM-01:** The system shall not require any active network connection during normal operation after package installation.

---

### 3.2 Functional Requirements

#### FR-01 — Origin and Destination Selection

- **FR-01.1:** The system shall allow the user to select an origin station from the set of valid station IDs loaded from `data/stations.csv`.
- **FR-01.2:** The system shall allow the user to select a destination station from the same set of valid station IDs.
- **FR-01.3:** The system shall reject any origin or destination that does not exist in the loaded station dataset and shall raise a `ValueError` with a descriptive message.
- **FR-01.4:** When origin equals destination, the system shall return an itinerary with zero travel duration, zero transfers, and report the origin station's congestion index as the exposure value.
- **FR-01.5:** When no connected path exists between origin and destination, the system shall return an explicit failure status and display an informative message to the user (not an application crash).

#### FR-02 — Scenario Input

- **FR-02.1:** The system shall accept a departure hour as an integer in the range [0, 23]. Values outside this range shall raise a `ValueError`.
- **FR-02.2:** The system shall accept a day of week as an integer in the range [0, 6] (0 = Monday, 6 = Sunday). Values outside this range shall raise a `ValueError`.
- **FR-02.3:** The system shall accept a weather scenario from exactly the set: `{"Clear", "Rain", "Storm"}`. Any other value shall raise a `ValueError`.
- **FR-02.4:** The system shall accept a binary special-event flag (True or False) indicating whether a hypothetical surge event applies to all stations.
- **FR-02.5:** The system shall accept a crowd comfort preference value `p` as a non-negative real number in the range [0.0, 5.0].
- **FR-02.6:** When the comfort preference `p = 0`, the system shall produce a crowd-aware route that is identical to the baseline route (crowd penalty is fully disabled).

#### FR-03 — Congestion Prediction

- **FR-03.1:** The system shall predict a finite congestion index in the range [0, 1] for every station in the network for the user-selected scenario.
- **FR-03.2:** The prediction shall use only scenario features available before route selection (departure hour, day, weather, event flag, station ID) — no future crowd measurements shall be used as model inputs.
- **FR-03.3:** The system shall reject a model artifact that is missing, structurally invalid, or incompatible with the installed scikit-learn version, and shall display the recovery command `python -m src.model.train` to the user.
- **FR-03.4:** The system shall use sine and cosine encodings of hour and weekday (cyclical features) to prevent wrap-around discontinuities in the ML model.
- **FR-03.5:** The model shall be selected by comparing global historical mean, Ridge regression, Random Forest, and Gradient Boosting on a held-out validation set using RMSE, and the best-performing architecture shall be retained.

#### FR-04 — Route Computation

- **FR-04.1:** The system shall compute a **baseline route** between origin and destination that minimises total travel time, using zero crowd weight (p = 0), accounting for line-transfer penalties.
- **FR-04.2:** The system shall compute a **smart route** between origin and destination that minimises the total weighted cost, defined as:

  > `Cost(edge) = travel_minutes + 4 × I(line_transfer) + 2.5 × p × P(ρ_destination)`

  where `P(ρ)` is the piecewise crowd penalty function defined in Appendix A.

- **FR-04.3:** The routing algorithm shall correctly handle parallel edges between two stations (multiple lines on the same connection) and shall consider each line as a distinct routing option.
- **FR-04.4:** A line transfer shall be counted only when consecutive route segments use different line names. Boarding the first segment shall not incur a transfer penalty.
- **FR-04.5:** All edge travel times and comfort preference values used in cost computation shall be finite and non-negative. Any violation shall raise a `ValueError`.

#### FR-05 — Route Metrics and Display

- **FR-05.1:** The system shall report the following metrics for both the baseline and smart route: total travel duration (minutes), in-vehicle time (minutes), transfer time (minutes), transfer count, average congestion index, maximum congestion index, and count of high-congestion stations (ρ ≥ 0.70).
- **FR-05.2:** The system shall display the signed exposure reduction as a percentage, calculated as:

  > `Signed Reduction = 100 × (baseline_avg_congestion − smart_avg_congestion) / baseline_avg_congestion`

  A negative value shall be displayed when the smart route has higher average congestion than the baseline.
- **FR-05.3:** When the baseline average congestion is zero, the system shall report an exposure reduction of 0% by convention, without producing a division-by-zero error.
- **FR-05.4:** The system shall display the travel-time trade-off as:

  > `Time Delta = smart_total_duration − baseline_total_duration` (in minutes)

- **FR-05.5:** The system shall display 5 summary metric cards on the dashboard: Crowd Reduction %, Avg Travel Time, Avg Distance, Line Transfers, and one additional comparison metric.

#### FR-06 — Itinerary Comparison

- **FR-06.1:** The system shall display the full ordered list of station names for both the baseline and smart route.
- **FR-06.2:** The system shall display per-segment details for both routes, including: origin station, destination station, line name, segment travel time, and destination station congestion index.
- **FR-06.3:** The system shall identify and display whether both routes recommend the same itinerary (identical ordered station sequence and line names for every segment).

#### FR-07 — Network Visualisation

- **FR-07.1:** The system shall render an interactive chart of the full transit network using station geographic coordinates (latitude and longitude).
- **FR-07.2:** The chart shall visually distinguish all network edges, the baseline route, and the smart route using different colours with a legend.
- **FR-07.3:** Each station marker shall display the station ID, name, and predicted congestion index as a tooltip on hover.
- **FR-07.4:** The chart shall be pannable and zoomable by the user.
- **FR-07.5:** The system shall display a bar chart and data table of predicted congestion indices for all stations.

#### FR-08 — Simulation Disclosure

- **FR-08.1:** The system shall display a disclosure message stating that the network, data, and predictions are synthetic simulations, not real-world measurements.
- **FR-08.2:** The disclosure message shall be visible above the route results on every page load.

---

### 3.3 Performance Requirements

- **PERF-01:** The system shall compute a route comparison (both baseline and smart search, plus metric calculation) in a mean duration of under 100 milliseconds for the 20-station network on a standard developer machine.
- **PERF-02:** The system shall complete network-wide congestion prediction for all 20 stations in under 500 milliseconds per scenario.
- **PERF-03:** The system shall load and display the dashboard (initial render) without crashing or throwing an unhandled exception, as verified by the `AppTest` automated system test.

> *Measured reference values on Windows/Python 3.11 (single run, subject to hardware variation):*
> - *Mean route-pair search: 0.909 ms (95th percentile: 2.173 ms)*
> - *Mean network prediction: 23.157 ms across seven batch scenarios*

### 3.4 Design Constraints

- **DC-01:** The system shall be implemented in Python 3.11 and all dependencies shall be listed in `requirements.txt` with pinned versions.
- **DC-02:** The system shall use lowercase `src` as the root package name. All imports shall use `src.*` paths. Commands shall use the `python -m` module invocation style.
- **DC-03:** The routing algorithm shall use a priority-queue (min-heap) based approach. BFS-based approaches that cannot handle unequal edge weights are not acceptable.
- **DC-04:** The ML training pipeline shall use a strict chronological train/validation/test split by complete calendar days (no random shuffling across time periods) to prevent data leakage.
- **DC-05:** The random seed shall be set to 42 for all data generation and model training steps to ensure reproducibility.
- **DC-06:** The system UI shall use Streamlit and shall not implement routing or prediction logic inside the UI module (`src/ui/app.py`).
- **DC-07:** Separation of concerns shall be maintained: `DataLoader` handles ingestion, `CrowdPredictor` handles ML inference, `SmartTransitRouter` handles graph search, and `app.py` handles rendering only.

### 3.5 Quality Attributes

#### 3.5.1 Reliability

- **REL-01:** The system shall reject malformed input data (invalid column types, out-of-range values, duplicate rows, broken timestamps) and raise a descriptive `ValueError` rather than silently proceeding.
- **REL-02:** The system shall not crash when the origin equals the destination; it shall return a valid zero-duration result.
- **REL-03:** The system shall not crash when no path exists between origin and destination; it shall return a failure status with an informative message.
- **REL-04:** All 74 automated test cases shall pass before any release. Critical route correctness failures shall block sign-off.

#### 3.5.2 Usability

- **USA-01:** Every UI input control shall have a visible, human-readable label — no unlabelled or icon-only inputs.
- **USA-02:** Travel duration values shall be displayed in minutes; congestion values shall be displayed as a dimensionless index in [0, 1]; distances shall be displayed in kilometres.
- **USA-03:** The simulation disclosure notice shall appear above all results on every session load, so users are always aware results are synthetic.
- **USA-04:** Route results shall include textual labels and data tables in addition to colour-coded charts, so the information is accessible without relying solely on colour.

#### 3.5.3 Maintainability

- **MNT-01:** Each software module shall have a single, well-defined responsibility (single-responsibility principle): validation, feature engineering, graph construction, route search, and UI rendering shall be separate modules.
- **MNT-02:** The system shall use shared interfaces between modules: the router shall receive a station→congestion dictionary rather than calling the predictor directly, and the UI shall call the router via plain Python data structures.
- **MNT-03:** Statement coverage on the core logic modules (`src/pipeline`, `src/model`, `src/routing`) shall be maintained at or above 90%.
- **MNT-04:** Branch coverage on the core logic modules shall be maintained at or above 90%.

#### 3.5.4 Portability

- **PORT-01:** The system shall run on both Windows and Ubuntu Linux, as validated by the CI pipeline on GitHub Actions (`ubuntu-latest` and `windows-latest` runners).
- **PORT-02:** All file paths within the system shall be constructed using `pathlib.Path` and resolved relative to the project root, not hard-coded absolute paths.
- **PORT-03:** The system shall be runnable from a fresh checkout using the commands documented in `README.md` without additional configuration.

#### 3.5.5 Reproducibility

- **REP-01:** Given the same seed (42), the data generator shall produce an identical 22,800-row CSV dataset on any compliant platform.
- **REP-02:** Given the same dataset and seed, the training pipeline shall select the same model architecture and produce equivalent metric values (within floating-point tolerance).
- **REP-03:** All benchmark results, model metrics, test reports, and coverage data shall be stored in machine-readable files under `results/` and committed to the repository.

---

## 4. Requirements Traceability Matrix

This matrix maps each functional requirement to its automated test evidence and acceptance status.

| Requirement ID | Requirement Summary | Test Evidence | Status |
|---------------|--------------------|--------------:|--------|
| FR-01.1–01.5 | Origin/destination selection, identity trip, disconnected path | `test_invalid_disconnected_and_missing_predictions`, `test_diversion_and_identity`, `test_dashboard_workflow` | ✅ Automated pass |
| FR-02.1–02.6 | Scenario inputs, domain validation, zero preference | `test_prediction_invalid_inputs`, `test_invalid_cost_parameters`, `test_parallel_lines_transfer_and_ties` | ✅ Automated pass |
| FR-03.1–03.5 | Congestion prediction, no leakage, artifact validation | `test_prediction_boundaries_persistence_and_errors`, `test_feature_generation_no_leakage`, `test_end_to_end_system_pipeline` | ✅ Automated pass |
| FR-04.1–04.5 | Baseline & smart route, parallel edges, transfer handling | `test_independent_expanded_networkx`, `test_parallel_lines_transfer_and_ties`, `test_transfer_cost_and_zero_crowd` | ✅ Automated pass |
| FR-05.1–05.5 | Metric reporting, exposure reduction, time delta | `test_transfer_cost_and_zero_crowd`, `test_diversion_and_identity`, `test_dashboard_workflow` | ✅ Automated pass |
| FR-06.1–06.3 | Itinerary comparison, same-path detection | `test_signed_worsening_not_clamped`, `test_zero_denominator_and_unchanged`, `test_dashboard_workflow` | ✅ Automated pass |
| FR-07.1–07.5 | Network chart, tooltips, bar chart, data table | `test_dashboard_workflow`, browser smoke test | ✅ Automated + visual |
| FR-08.1–08.2 | Simulation disclosure display | `test_dashboard_workflow` (asserts `'SIMULATION' in app.info[0].value`) | ✅ Automated pass |
| PERF-01–03 | Latency targets, dashboard load | `test_dashboard_workflow`, `scripts/benchmark.py` output | ✅ Within target |
| REL-01–04 | Malformed data rejection, no crash on edge cases | `test_loader_malformed` (12 cases), `test_core.py` suite | ✅ Automated pass |
| MNT-03–04 | 90%+ statement and branch coverage | `results/coverage.json` (93.62% stmt, 95.00% branch) | ✅ Exceeds threshold |
| REP-01 | Data generator reproducibility | `test_generator_reproduces_committed_history` | ✅ Automated pass |

**Final Test Suite Summary:**
- **74 passed, 0 failed, 0 skipped**
- Statement Coverage: **93.62%** (323/345 statements)
- Branch Coverage: **95.00%** (133/140 branches)
- Routing & cost modules: **100% statement and branch coverage**

---

## 5. Appendix

### Appendix A — Routing Cost Function Detail

For each traversed edge `e = (u → v)` on line `l`, the weighted cost is:

```
Cost(e) = travel_minutes(e)
        + 4 × I(line_change)
        + 2.5 × p × P(ρ_v)
```

Where:
- `I(line_change) = 1` if the previous segment used a different line, 0 otherwise. First boarding incurs no transfer.
- `p` = user's comfort preference (0.0–5.0)
- `P(ρ)` = piecewise congestion discomfort penalty:

```
P(ρ) = 0                          if ρ ≤ 0.35
P(ρ) = 8 × (ρ − 0.35)             if 0.35 < ρ ≤ 0.70
P(ρ) = 2.8 + 35 × (ρ − 0.70)²    if ρ > 0.70
```

`P(ρ)` is continuous and non-decreasing at both thresholds. It is an assumed discomfort score, not an empirically measured delay.

**Algorithm:** Line-state Dijkstra. Search state = `(station_id, last_line)`. Priority queue stores `(cost, tie_counter, station, last_line, path)`. Time complexity: O(A log A) where A = number of expanded transitions.

### Appendix B — Data Provenance

The dataset of 22,800 rows is generated by `data/generate_dataset.py` using:
- 20 fictional stations inspired by Lucknow geography
- 60 simulated days (20 Sep 2026 – 18 Nov 2026), 19 hours/day, seed = 42
- Simulated weather, event flags, and station/hour congestion factors

**Train/Validation/Test Split (chronological, by complete days):**

| Split | Days | Rows |
|-------|------|------|
| Training | Days 1–36 | 13,680 |
| Validation | Days 37–48 | 4,560 |
| Test (held-out) | Days 49–60 | 4,560 |

**Selected Model: Random Forest Regressor**

| Metric | Value |
|--------|-------|
| Held-out MAE | 0.0084 |
| Held-out RMSE | 0.0125 |
| R² | 0.9732 |

### Appendix C — Benchmark Results Summary

The benchmark evaluates 10,640 route comparisons = 7 scenarios × 380 ordered station pairs × 4 preference values (0, 1, 2, 5):

| Metric | Value |
|--------|-------|
| Itineraries where smart route reduces congestion | 4.02% |
| Itineraries with same route as baseline | 95.67% |
| Itineraries where smart route worsens congestion | 0.31% |
| Mean signed exposure reduction | 0.333% |
| Mean added travel time | 0.186 min |
| Mean route-pair search time | 0.909 ms |

**Representative illustrative case:** S04 → S14, Thursday 18:00, Storm, p = 2. Baseline (S04→S01→S12→S14): 22 min, avg ρ = 0.406. Smart (S04→S18→S15→S14): 25 min, avg ρ = 0.323 (−20.4% exposure).

### Appendix D — Limitations

1. The dataset is fully synthetic and does not use real Lucknow transit operational data, live sensor feeds, or observed passenger counts.
2. The routing objective minimises accumulated weighted penalty, not the arithmetic mean of station congestion. Average exposure can therefore worsen in some cases when the penalty function steers the route onto a path with slightly higher average but lower peak congestion cost.
3. Crowd predictions use a single departure-time snapshot; crowd evolution during the trip is not modelled.
4. The 4-minute transfer penalty and comfort penalty function are assumed simulation parameters and have not been calibrated against real user behaviour.
5. No seating guarantee, punctuality guarantee, or maximum-detour guarantee is provided.
6. Model pickle files are trusted local artifacts; loading third-party pickle files from unknown sources is a security risk and must not be done.
