# Testing evidence and stopping decision

The recorded suite has 74 passed cases and no failed/skipped cases. Full per-case ID, requirement category, input case, expected assertions, actual outcome and status: [CSV](../results/test_report.csv). Source inputs and numeric expected values are in tests/test_core.py, test_data_loader.py, test_integration.py and test_dashboard.py. The CSV case names include each parameter value.

Statement coverage: 93.62% (323/345). Branch coverage: 95.00% (133/140). Combined coverage: 94.02%. Routing and penalty functions are 100% statement and branch covered. Scope includes src/pipeline, src/model and src/routing, including the train CLI; excludes UI, experiments, document builders and legacy code. The train CLI executes separately in reproducibility and CI checks.

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

The local automated gate is satisfied: all 74 cases pass, statement coverage exceeds 90%, routing/cost branches are exercised, every FR has evidence, AppTest workflow and full-grid benchmark execute. No known critical/high defect remains in the supported simulation. Package rendering, clean installation, remote CI and publication are separate final gates recorded in FINAL_VERIFICATION.md. Tests do not establish real-world performance or absence of every defect.

Harlan Mills fault seeding and Musa failure intensity are possible future methods; neither was performed or used to claim a statistical reliability level. Non-failing warnings are dependency deprecations and intentionally malformed-input parsing warnings.
