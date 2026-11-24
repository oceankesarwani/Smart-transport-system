"""Generate student-facing guides and README from recorded metrics."""
import json
from pathlib import Path
from scripts.build_documents import evidence
ROOT=Path(__file__).resolve().parents[1]


def build_guides():
    m,r,c,n=evidence()
    sc=100*c['covered_lines']/c['num_statements'];bc=100*c['covered_branches']/c['num_branches']
    readme=f'''# Smart Public Transport System: Crowd-Aware Route Optimization

CS201 Software Engineering, Indian Institute of Information Technology Lucknow.

Contributors (preserved from the original configuration): Dhruvika Rawat (LCB2025012), Ganga Kaur (LCI2025033), Harshita Punia (LCB2025011), Ocean Kesarwani (LCI2025019).

## Problem and motivation

Conventional travel-time routing can recommend a path through crowded stations because congestion is absent from its objective. This project predicts station congestion and lets a commuter compare the quickest simulated itinerary with a route that trades travel time for lower accumulated crowd discomfort. The objective is to reduce predicted station exposure while making added time visible.

**Simulation disclosure:** All 22,800 historical station-hour rows are synthetic. The 20-station network has fictional lines inspired by Lucknow and is not an operational route guide. There are no observed passenger measurements, live sensors, seating guarantees or demonstrated real-world congestion reductions.

## Supported implementation

The authoritative pipeline is `src/pipeline` → `src/model` → `src/routing` → `src/ui/app.py`. The original alternative classifier, network and tests are preserved under `legacy/` for historical reference. They are outside the supported package and acceptance suite. `app/streamlit_app.py` forwards to the same supported UI.

```text
Synthetic history CSV -> validation -> cyclic scenario features -> selected regressor
Station/route CSV -> MultiDiGraph -> station/line weighted Dijkstra -> comparison -> Streamlit
```

The UI selects origin, destination, hour, weekday, weather, event and preference. It displays every station prediction, both itineraries, duration including transfers, average/max congestion, high-station counts, signed reduction and time delta. An interactive native Streamlit/Altair network chart supports pan, zoom and hover without external map tiles or CDNs.

## Install and run

Use Python 3.11. Windows PowerShell:

```powershell
git clone https://github.com/oceankesarwani/Smart-transport-system.git
cd Smart-transport-system
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe -m src.model.train
.\\.venv\\Scripts\\python.exe -m streamlit run src/ui/app.py
```

Linux/macOS:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m src.model.train
.venv/bin/python -m streamlit run src/ui/app.py
```

Once the environment is activated, the commands below use `python`. The app needs no paid services, credentials or network access after installation. If an artifact is missing/incompatible, the UI shows the training command. Only load the trusted repository artifact or your own retrained file.

## Data and model reproduction

```bash
python data/generate_dataset.py
python -m src.model.train
python quick_check.py
```

The seed-42 generator uses assumed station/time factors, weather, events and random noise. It creates 60 days from 2026-09-20 to 2026-11-18, 19 hours per day. It does not ingest sensors or surveys. Training sorts timestamp and station, then splits complete days 60/20/20 (13,680/4,560/4,560 rows). Features are cyclical hour/day, weekend, derived peak, one-hot station/weather, and event. Inflow, outflow, target, congestion category and generated delay are excluded. Weather and event inputs are hypothetical known scenarios.

Historical mean, Ridge, Random Forest and Gradient Boosting compete on validation RMSE. The selected architecture is refitted on train+validation, then evaluated once on final held-out dates. Random seeds and model parameters are fixed in code. The artifact stores a schema and Scikit-learn version.

Selected model: **{m['best_model_name']}**. Held-out synthetic test: MAE **{m['MAE']:.6f}**, RMSE **{m['RMSE']:.6f}**, R² **{m['R2']:.6f}**. See [full model metrics](results/model_metrics.json). This measures this simulator, not real-world prediction accuracy.

## Routing and engineering trade-offs

For edge e ending at v, the weighted cost is:

```text
base_minutes(e) + 4 * line_change + 2.5 * preference * P(predicted_congestion(v))
P(rho) = 0                          if rho <= 0.35
         8 * (rho - 0.35)          if 0.35 < rho <= 0.70
         2.8 + 35*(rho-0.70)^2     if rho > 0.70
```

This continuous nondecreasing curve is an assumed discomfort penalty, not measured delay. All inputs are checked for finite, non-negative cost domains. The baseline sets preference to zero with identical transfer assumptions. Total duration includes a 4-minute allowance per line change, with no initial waiting time.

Weighted-sum Dijkstra is not Pareto-front search. State is `(station,last_line)` so parallel lines and transfer choices remain correct. The heap counter safely breaks equal-cost ties. An adjacency list supports sparse parallel routes in O(V+E) storage. BFS cannot handle unequal costs; A* would need a justified admissible heuristic; reinforcement learning adds unnecessary training complexity here. Modular components isolate validation, ML, graph search and UI. Cyclical time features remove clock wrap discontinuities. The selected model is justified by validation results rather than a preselected claim.

For S expanded states and A expanded transitions, lazy-heap search is O(A log A), plus O(A*S) time and memory from copied path lists in this implementation. S is at most 1+V*L; A at most E*(L+1). These bounds include station/line expansion and path storage. A future predecessor-link implementation could reduce memory.

## Reproducible route experiments

```bash
python -m scripts.benchmark
```

The predefined full grid includes 7 regimes (morning, evening, off-peak, weekend, rain, storm, event), every 380 ordered distinct station pair, and preferences 0/1/2/5: **{r['scenarios']:,} comparisons**. No unfavorable rows are discarded. [CSV](results/routing_benchmark.csv), [summary](results/routing_summary.json).

| Measurement | Actual simulation result |
|---|---:|
| Cases with lower average exposure | {r['improved_percent']:.2f}% |
| Cases with equal exposure | {r['equal_exposure_percent']:.2f}% |
| Cases with worse exposure | {r['worsened_percent']:.2f}% |
| Unchanged itineraries | {r['unchanged_itinerary_percent']:.2f}% |
| Mean per-query signed reduction | {r['mean_reduction_percent']:.3f}% |
| Mean additional duration | {r['mean_time_delta_minutes']:.3f} min |
| Mean route-pair timing, excludes prediction | {r['mean_routing_pair_ms']:.3f} ms |
| 95th percentile route-pair timing | {r['p95_routing_pair_ms']:.3f} ms |
| Mean network prediction across seven batches | {r['mean_network_prediction_ms']:.3f} ms |

Timing values are local single-run measurements and will vary. Mean percentage reduction averages the individual ratios. It differs from reduction in aggregate mean exposure.

![Full-grid simulated comparison](results/routing_comparison.png)

**Reliable demonstration:** S04 → S14, Thursday, 18:00, Storm, event off, preference 2. Baseline S04→S01→S12→S14: 22 min, exposure 0.405926. Recommendation S04→S18→S15→S14: 25 min, exposure 0.322975. Signed reduction 20.435%, one transfer in each. No high-congestion station on either route. This is a selected example after evaluating the whole grid, not a typical aggregate gain.

Exposure is arithmetic mean of predicted station congestion including endpoints. Maximum and high-station count (rho>=0.70) use the same visits. Reduction is 100*(baseline-smart)/baseline, signed; a zero baseline returns 0 by convention. Duration is sum(edge minutes)+4*transfers. The optimization minimizes accumulated penalty, so average exposure can worsen. Predictions are one departure-time snapshot.

## Testing and stopping decision

```bash
python -m pytest --cov=src.pipeline --cov=src.model --cov=src.routing --cov-branch --cov-fail-under=90 --cov-report=json:results/coverage.json --junitxml=results/junit.xml
```

Actual recorded suite: **{n} passed**. Statement coverage **{sc:.2f}%**, branch coverage **{bc:.2f}%**, combined **{c['percent_covered']:.2f}%**. Routing and cost functions have 100% statement/branch coverage. Denominator includes ingestion, prediction, routing and the training CLI module; UI/build/benchmark scripts and legacy source are excluded. [Coverage](results/coverage.json), [JUnit](results/junit.xml), [per-test report](results/test_report.csv).

Selection methods: equivalence partitioning (valid/invalid inputs), boundary value analysis (thresholds/hour endpoints/zero weight), transfer/preference decision tables, error guessing (NaN, broken artifacts, missing/duplicate data), branch and independent routing paths. Random controlled graphs are cross-checked against a separately constructed NetworkX station/line graph. Streamlit AppTest covers render and user interaction. Regression cases cover every significant fixed routing/model defect.

Exit criteria: all required cases pass; no known critical/high unresolved defect; >=90% statement coverage of measured core; meaningful routing/cost branch coverage; all eight FRs traced; complete app workflow; reproducible benchmark; verified setup and documents. See [test decision](docs/TEST_REPORT.md) and SRS. No Harlan Mills fault-seeding or Musa failure-intensity experiment is claimed.

CI runs the same training, coverage suite and benchmark on Windows and Ubuntu. Check the actual remote run before claiming it is green. The development process used baseline reproduction, incremental fixes and regression tests, not a claim of having followed TDD from the project's start.

## Documentation and generation

- [SRS PDF](docs/SRS.pdf), [editable Word](docs/SRS.docx), [editable text](docs/SRS.md)
- [Exactly five-slide presentation](docs/presentation.pptx), [presentation PDF](docs/PPT.pdf)
- [Viva preparation](docs/VIVA_PREPARATION.md), [demo and 10-minute script](docs/DEMO_SCRIPT.md)
- [Audit and baseline failures](docs/AUDIT.md), [test report](docs/TEST_REPORT.md)

```bash
python -m scripts.build_diagrams
python -m scripts.build_documents
python -m scripts.build_guides
python -m scripts.build_slides
```

The SRS builder uses python-docx/ReportLab and reads measured JSON/CSV. The editable deck is authored with the Codex bundled Artifact Tool. `scripts/build_slides.py` locates that runtime or accepts `CODEX_ARTIFACT_RUNTIME`; its JS source and slide content are committed. On Windows, run `powershell -File scripts/export_office.ps1 -RenderSrs` to export the five-slide PDF and verify the DOCX through installed Microsoft Office. On Linux with LibreOffice, use `libreoffice --headless --convert-to pdf --outdir tmp/render docs/presentation.pptx` and copy the resulting PDF to docs/PPT.pdf. The checked-in files are ready to present without regeneration or Codex.

## Repository layout

```text
src/pipeline/      validated CSV ingestion
src/model/         features, candidate selection and persistence
src/routing/       graph, cost, line-state search and metrics
src/ui/app.py      authoritative dashboard
app/               forwarding compatibility entrypoint
data/              synthetic history, illustrative topology, generator
models/            current versioned local predictor
scripts/           benchmark and reproducible artifact builders
tests/             authoritative acceptance and regression suite
results/           machine-readable experiment/test evidence and charts
docs/              SRS, five-slide deck, viva and demo
legacy/            preserved alternative source, tests and old artifacts
```

## Limitations

Small synthetic network and patterns, mostly below the high-congestion threshold; no operational generalization shown. Scenario weather/events are assumptions. The model does not consider timetables, changing crowd along the trip, capacity constraints or missed boarding. Preference has no maximum-detour guarantee. The objective differs from mean exposure, and adverse cases are reported. Meaningful deployment requires observed data, calibrated penalties and external validation. This is custom numerical prediction and graph search, with no LLM or ChatGPT API.
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    (ROOT/'docs/TEST_REPORT.md').write_text(f'''# Testing evidence and stopping decision

The recorded suite has {n} passed cases and no failed/skipped cases. Full per-case ID, requirement category, input case, expected assertions, actual outcome and status: [CSV](../results/test_report.csv). Source inputs and numeric expected values are in tests/test_core.py, test_data_loader.py, test_integration.py and test_dashboard.py. The CSV case names include each parameter value.

Statement coverage: {sc:.2f}% ({c['covered_lines']}/{c['num_statements']}). Branch coverage: {bc:.2f}% ({c['covered_branches']}/{c['num_branches']}). Combined coverage: {c['percent_covered']:.2f}%. Routing and penalty functions are 100% statement and branch covered. Scope includes src/pipeline, src/model and src/routing, including the train CLI; excludes UI, experiments, document builders and legacy code. The train CLI executes separately in reproducibility and CI checks.

## Requirement mapping

| Requirement | Tests and evidence |
|---|---|
| FR-01 station selection, identity and no path | invalid_disconnected_and_missing_predictions, diversion_and_identity, dashboard_workflow |
| FR-02 scenarios and preference | prediction_invalid_inputs, invalid_cost_parameters, parallel_lines_transfer_and_ties |
| FR-03 prediction and artifact recovery | feature_generation_no_leakage, prediction_boundaries_persistence_and_errors, end_to_end_system_pipeline |
| FR-04 minimum-cost line-state search | independent_expanded_networkx (12 seeded graphs, two weights each), parallel_lines_transfer_and_ties |
| FR-05 route duration and congestion metrics | transfer_cost_and_zero_crowd, diversion_and_identity, dashboard_workflow |
| FR-06 signed changes and identity of itineraries | signed_worsening_not_clamped, zero_denominator_and_unchanged |
| FR-07 route visualization and comparison | dashboard_workflow and manual browser visual review |
| FR-08 simulation disclosure and explanation | AppTest rendered strings and manual browser review |

## Selection and critical control flow

Equivalence partitions cover accepted/rejected station, graph, scenario, data and model domains. Boundary tests use 0/0.35/0.70/1 crowd, adjacent threshold values, hour 0/23, zero comfort, and malformed values outside each domain. Error guessing uses NaN, infinity, missing files, duplicate rows, invalid timestamps and broken payloads. Transfer decisions: initial boarding -> no transfer; same line -> no transfer; line change -> exactly 4 minutes. Preference zero disables the penalty for all crowd partitions.

Independent routing paths cover invalid origin/destination, missing forecast, negative edge, identity route, first discovery, repeated-state suppression, improvement, tied heap priority, parallel lines, line change, destination return, and exhausted queue. NetworkX comparison uses a separately assembled expanded station/line graph rather than a station-only shortcut. This is evidence of basis-path-oriented selection and measured branches, not a claim of exhaustive graph/path verification.

## Stop decision

The local automated gate is satisfied: all {n} cases pass, statement coverage exceeds 90%, routing/cost branches are exercised, every FR has evidence, AppTest workflow and full-grid benchmark execute. No known critical/high defect remains in the supported simulation. Package rendering, clean installation, remote CI and publication are separate final gates recorded in FINAL_VERIFICATION.md. Tests do not establish real-world performance or absence of every defect.

Harlan Mills fault seeding and Musa failure intensity are possible future methods; neither was performed or used to claim a statistical reliability level. Non-failing warnings are dependency deprecations and intentionally malformed-input parsing warnings.
''',encoding='utf-8')
    qa=[
      ('Why this problem?','Time-only routing omits station crowding. This gives us a narrow, measurable trade-off between predicted exposure and trip duration.'),
      ('What is the role of Software Engineering?','Testable requirements, separated modules, versioned changes, regression tests, traceability, CI and reproducible evidence connect the implementation to its specification.'),
      ('Why Dijkstra?','All composite edge costs are non-negative. Dijkstra finds the minimum cost in the expanded state graph without requiring a heuristic.'),
      ('Why not BFS?','Segment durations and crowd costs are unequal. BFS minimizes edge count, not this weighted objective.'),
      ('Why not A*?','A* needs an admissible heuristic for the actual time, transfer and crowd objective. We did not have a validated heuristic, and this small network does not need it.'),
      ('Why not ordinary shortest-time routing?','That is our conventional comparator. It ignores crowd penalties and can select a crowded corridor; the same search with a positive preference makes the trade-off explicit.'),
      ('Why is a station alone not enough search state?','The next transfer cost depends on the line used to arrive. We retain (station,last_line), so reaching the same station on two lines remains a different decision state.'),
      ('How are parallel lines handled?','MultiDiGraph preserves each line edge. The custom search examines all parallel edges, including a slower arrival line that may avoid a later transfer.'),
      ('Why an adjacency list?','The graph is sparse and needs parallel edges. Adjacency storage uses O(V+E), while a station matrix requires O(V^2) plus parallel-line structure.'),
      ('Why a priority queue and counter?','The heap repeatedly extracts the smallest tentative cost efficiently. A unique sequence counter prevents Python from comparing path dictionaries when costs tie.'),
      ('What is the routing cost?','Sum base segment minutes, add four minutes per line change, and add 2.5 times comfort preference times the assumed discomfort penalty at each arrived station.'),
      ('Are crowd penalties actual delay?','No. The piecewise curve is an assumed discomfort score. Only base travel and line-transfer allowances enter reported trip duration.'),
      ('How were weights selected?','They are transparent simulation assumptions, not calibrated passenger utility. The benchmark tests preferences 0, 1, 2 and 5; the UI exposes the choice and added time.'),
      ('Is this Pareto optimization?','No. It minimizes one weighted sum for the chosen preference and does not enumerate a Pareto frontier.'),
      ('Does more preference always lower average congestion?','No. Search minimizes accumulated nonlinear discomfort, whereas the displayed exposure is a mean including endpoints. The benchmark retains the small fraction of adverse outcomes.'),
      ('What is the complexity?','With S station/line states and A expanded transitions, heap work is O(A log A). Copying paths adds O(A*S) worst-case time and memory in this implementation; graph storage is O(V+E).'),
      ('Why Random Forest?','It had the lowest validation RMSE among historical mean, Ridge, Random Forest and Gradient Boosting. We refitted that architecture on development data, then evaluated final held-out dates.'),
      ('What are the features?','Hour/day sine and cosine, derived weekend and peak flags, one-hot station/weather and an event flag. No target, generated inflow/outflow or delay is used.'),
      ('What is synthetic data?','Values produced by a seeded simulator with assumed demand factors and random noise. They are not real passenger sensor observations.'),
      ('How is leakage prevented?','Complete days are ordered chronologically into train, validation and test. Fit the encoder on training data, choose using validation, and keep target-derived columns out of features.'),
      ('Why cyclical time features?','Sine/cosine makes adjacent clock endpoints close in feature space. Raw hour alone has an artificial discontinuity at midnight.'),
      ('What happens when no route exists?','The router returns no path and comparison returns a failed status. The dashboard displays an unavailable-route message instead of inventing an itinerary.'),
      ('What if the model cannot load?','A missing or incompatible artifact produces a clear recovery message: run python -m src.model.train. The dashboard does not silently replace predictions with invented metrics.'),
      ('What is different or innovative?','The coursework integrates an adjustable numerical crowd objective with correct line-state routing, a conventional comparator and fully recorded adverse as well as favorable results. It does not claim a new shortest-path algorithm.'),
      ('How does this differ from existing navigation tools?','Our demonstrator explicitly exposes its assumptions and crowd trade-off on an illustrative graph. We have not benchmarked current commercial tools and cannot claim they all ignore crowding.'),
      ('Why is this not a ChatGPT wrapper?','Predictions come from a fitted Scikit-learn regressor and routes from deterministic graph optimization. There is no LLM, prompt or external AI API.'),
      ('How did you test it and why Pytest?','Pytest offers clear assertions and parameterized cases with little infrastructure. We combine unit, pipeline and AppTest system tests, coverage and an independently constructed NetworkX reference.'),
      ('What is equivalence partitioning?','Divide inputs into behaviourally similar classes, such as valid versus unknown stations or connected versus disconnected graphs, and select representatives.'),
      ('What is boundary value analysis?','Test at and immediately around boundaries where behaviour changes: congestion 0.35/0.70, valid hour endpoints, zero preference and domain limits.'),
      ('What is regression testing?','Keep a test for a fixed defect so later changes cannot quietly reintroduce it. Examples here are zero comfort, transfer minutes and unclamped negative exposure reduction.'),
      ('When did you stop testing?',f'The recorded suite has {n} passing cases, {sc:.2f}% statement and {bc:.2f}% branch coverage, with every FR traced and system/benchmark evidence. We stop at explicit coursework gates, without claiming mathematical proof of zero defects.'),
      ('What are the main limitations?','Synthetic data, fictional lines, fixed transfer time, departure-only crowd snapshots, no schedules or capacity enforcement, and no real-world validation. High preference can add substantial travel time.'),
      ('Can it work with real transit data?','The modular ingestion and feature interfaces could be adapted to validated topology and historical crowd observations. That would require provenance checks, recalibration, new chronological evaluation and possibly arrival-time prediction.'),
      ('What results should we quote?',f'Quote the saved held-out metrics (MAE {m["MAE"]:.6f}, RMSE {m["RMSE"]:.6f}, R² {m["R2"]:.6f}) and full-grid outcomes ({r["improved_percent"]:.2f}% improved, {r["worsened_percent"]:.2f}% worse). Identify the 20.435% demo as a selected scenario.')]
    (ROOT/'docs/VIVA_PREPARATION.md').write_text('# Viva preparation\n\nAnswers describe the supported simulation, not an operational transit service.\n\n'+'\n\n'.join(f'## {i+1}. {q}\n\n{a}' for i,(q,a) in enumerate(qa)),encoding='utf-8')
    print('README, testing decision and 34 viva answers generated')

if __name__=='__main__':
    build_guides()
