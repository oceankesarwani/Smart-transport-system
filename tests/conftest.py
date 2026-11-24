"""Record actual per-test outcomes alongside traceability categories."""
import csv
from pathlib import Path
import pytest

ROWS=[]

def pytest_runtest_logreport(report):
    if report.when=='call' or (report.when=='setup' and report.failed):
        node=report.nodeid
        requirement='FR-01/FR-02'
        if any(s in node for s in ['route','transfer','diversion','networkx','penalty','cost','congestion','denominator','disconnected','worsening']):
            requirement='FR-04/FR-05/FR-06'
        if any(s in node for s in ['predict','feature','chronological','end_to_end']):
            requirement='FR-03'
        if 'dashboard' in node:
            requirement='FR-01/FR-02/FR-03/FR-04/FR-05/FR-06/FR-07/FR-08'
        ROWS.append([node,requirement,'Parameterized boundary/equivalence/regression; independent reference where named',
                     node.split('::')[-1],'All encoded assertions hold',report.outcome,report.outcome.upper(),f'{report.duration:.4f}'])


def pytest_sessionfinish(session,exitstatus):
    path=Path(__file__).resolve().parents[1]/'results/test_report.csv'
    path.parent.mkdir(exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['Test ID','Requirement ID','Method','Input case','Expected','Actual','Status','Seconds']);writer.writerows(ROWS)
