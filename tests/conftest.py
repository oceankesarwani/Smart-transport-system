"""Record real per-case outcomes with requirement and selection-method traceability."""
import csv
from pathlib import Path

ROWS=[]
CATALOG={
 'test_penalty_boundaries':('FR-04','Boundary value analysis','rho and expected penalty in case parameters','Penalty equals the stated piecewise boundary value'),
 'test_penalty_continuity_monotonicity':('FR-04','Boundary and monotonicity properties','1001 values in [0,1] and threshold +/-1e-8','Nondecreasing values and continuous threshold limits'),
 'test_invalid_congestion':('FR-02/FR-04','Invalid equivalence partitions and error guessing','Invalid rho in case parameters','ValueError'),
 'test_invalid_cost_parameters':('FR-02/FR-04','Boundary values and error guessing','Cost argument position and bad value in case parameters','ValueError'),
 'test_transfer_cost_and_zero_crowd':('FR-02/FR-05','Decision table','3-minute segment; rho=1; zero crowd weight; initial or changed line','Cost 3 on initial boarding; 7 after line change'),
 'test_parallel_lines_transfer_and_ties':('FR-02/FR-04/FR-05','Independent paths and regression','Controlled parallel-line graph; tied priorities; preference zero','Correct blue-line optimum; zero preference matches baseline; transfer duration 4'),
 'test_diversion_and_identity':('FR-01/FR-04/FR-05','Valid equivalence partition and regression','Diamond graph with rho_b=1 and low alternate; b to b identity','Alternate route selected; identity duration zero with rho=1 retained'),
 'test_signed_worsening_not_clamped':('FR-06','Regression and error guessing','Controlled graph where mean exposure worsens under accumulated-penalty objective','Signed reduction remains negative'),
 'test_zero_denominator_and_unchanged':('FR-06','Boundary value analysis','All crowds zero and preference zero','0 reduction convention; identical itinerary'),
 'test_invalid_disconnected_and_missing_predictions':('FR-01/FR-02/FR-04','Equivalence partitions and independent paths','Unknown endpoints; isolated node; incomplete map; negative edge and preference','ValueErrors for invalid inputs; failed status for no path'),
 'test_independent_expanded_networkx':('FR-04','Independent algorithm oracle and seeded graph paths','Seed in case parameters; five stations; two lines; preferences 0 and 2','Minimum cost equals independent expanded NetworkX graph or both report no path'),
 'test_feature_generation_no_leakage':('FR-03','White-box feature isolation and regression','Same inputs with corrupted target/inflow/stored peak flag','Features unchanged; trigonometric identity; target excluded'),
 'test_prediction_invalid_inputs':('FR-02/FR-03','Boundary values and invalid equivalence partitions','Invalid scenario parameter in case ID','ValueError'),
 'test_prediction_boundaries_persistence_and_errors':('FR-03','Boundary and error guessing','Hours 0/23; empty station list; missing/broken/versioned artifacts','Finite bounded predictions; deterministic save/load; clear rejection of bad artifacts'),
 'test_chronological_splits':('FR-03','Regression and temporal partition validation','Shuffled complete dataset; insufficient one-row history','Strictly disjoint ordered periods; every row retained; short history rejected'),
 'test_graph_schema_and_unknown_endpoint':('FR-04','Integration and invalid equivalence partition','CSV topology; parallel S02-S04 edges; unknown endpoint mutation','20 connected stations; parallel lines retained; bad endpoint rejected'),
 'test_loader_missing_schema_and_file':('FR-03','Error guessing and schema partitions','Missing file and CSV with wrong column for each loader','FileNotFoundError or ValueError as specified'),
 'test_loader_malformed':('FR-03','Boundary and malformed-input partitions','Loader, column and invalid value encoded in case ID','Invalid data rejected'),
 'test_duplicate_data':('FR-03','Error guessing','Duplicated station row or station/timestamp record','ValueError'),
 'test_training_rejects_overlapping_periods':('FR-03','Regression and temporal partition validation','Same timestamps in train, validation and test','ValueError with disjoint chronological explanation'),
 'test_generator_reproduces_committed_history':('FR-03','Reproducibility integration','Seed 42, 60 days in isolated temporary path','Generated frame equals committed 22800-row history'),
 'test_load_stations':('FR-03','Valid schema partition','Committed stations.csv','20 stations with required positive capacity and valid coordinates'),
 'test_load_routes_bidirectional':('FR-03/FR-04','Graph ingestion integration','Committed routes.csv with bidirectional construction','Expected schema, positive weights and reverse connections'),
 'test_load_crowd_data_schema':('FR-03','Valid schema partition','Committed historical_crowd.csv','Required target schema and bounded congestion'),
 'test_end_to_end_system_pipeline':('FR-03/FR-04/FR-05/FR-06','End-to-end integration','Ingest, select model, predict morning network, route S08-S09','Successful prediction and valid compared itineraries/metrics'),
 'test_dashboard_workflow':('FR-01/FR-02/FR-03/FR-04/FR-05/FR-06/FR-07/FR-08','System interactions and regression','Initial UI; zero comfort; identity; new destination; weekend/storm/event','No exception; disclosure and chart present; backend durations match; identity/zero metrics correct')}


def pytest_runtest_logreport(report):
    if report.when=='call' or (report.when=='setup' and report.failed):
        node=report.nodeid;name=node.split('::')[-1].split('[')[0]
        requirement,method,inputs,expected=CATALOG.get(name,('Unmapped','Review required',node,'Assertions hold'))
        actual='All encoded assertions passed' if report.passed else str(report.longrepr)[:600]
        ROWS.append([node,requirement,method,inputs+'; case: '+node.split('::')[-1],expected,actual,report.outcome.upper(),f'{report.duration:.4f}'])


def pytest_sessionfinish(session,exitstatus):
    path=Path(__file__).resolve().parents[1]/'results/test_report.csv';path.parent.mkdir(exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['Test ID','Requirement ID','Method','Input case','Expected','Actual','Status','Seconds']);writer.writerows(ROWS)
