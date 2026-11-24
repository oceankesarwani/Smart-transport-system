"""Build the SRS, README and testing decision from recorded evidence only."""
import csv
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'


def evidence():
    model=json.loads((ROOT/'results/model_metrics.json').read_text())
    routing=json.loads((ROOT/'results/routing_summary.json').read_text())
    coverage=json.loads((ROOT/'results/coverage.json').read_text())['totals']
    tests=list(csv.DictReader((ROOT/'results/test_report.csv').open(encoding='utf-8')))
    if not tests or any(t['Status']!='PASSED' for t in tests):
        raise RuntimeError('Final documents require passing recorded tests')
    return model,routing,coverage,len(tests)


def content():
    m,r,c,n=evidence()
    statement=100*c['covered_lines']/c['num_statements']
    branch=100*c['covered_branches']/c['num_branches']
    pages=[]
    def page(title,*paragraphs,table=None,images=None):
        pages.append(dict(title=title,paragraphs=list(paragraphs),table=table,images=images or []))
    page('Software Requirements Specification',
         'Smart Public Transport System: Crowd-Aware Route Optimization',
         'CS201 Software Engineering\nIndian Institute of Information Technology Lucknow\nSubmission candidate dated 24 November 2026',
         'Contributors preserved from the repository configuration: Dhruvika Rawat (LCB2025012), Ganga Kaur (LCI2025033), Harshita Punia (LCB2025011), Ocean Kesarwani (LCI2025019).',
         'This specification describes a working academic simulation that predicts station congestion and compares conventional travel-time routing with a crowd-aware weighted route. The measurable objective is to reduce predicted station exposure while showing the additional travel time clearly.',
         'The network is illustrative, including fictional lines inspired by Lucknow. The 22,800 station-hour observations are synthetic. No real passenger measurements, live sensors, guaranteed seating or real-world crowd reduction are demonstrated.',
         f'Evidence snapshot: {n} automated cases pass. Statement coverage is {statement:.2f}% and branch coverage is {branch:.2f}% across the measured ingestion, prediction and routing modules. The benchmark contains {r["scenarios"]:,} predefined route comparisons. This is an IEEE-style coursework SRS, not a claim of certified standards compliance.')
    page('1 Introduction',
         'Purpose. Specify the implemented behaviour, acceptance evidence and limits for the student team and academic examiner. The source of truth is the tested lowercase src package and the machine-readable outputs in results/.',
         'Scope. The single problem is that conventional travel-time-based routing can pass through crowded stations because it omits congestion from route selection. The application adds a tunable crowd discomfort term, retains a conventional baseline, and exposes the resulting travel-time trade-off.',
         'Motivation. Commuters may prefer less station congestion even when it requires a modest detour. A small reproducible simulation lets us examine that trade-off without claiming access to operational telemetry. We selected it because it connects a testable requirement to feature engineering, graph design, numerical prediction and independent algorithm validation.',
         'Definitions. Congestion rho is a dimensionless simulated station occupancy index in [0,1]. A high-congestion station has rho >= 0.70. A line is the line_name on a route edge. A transfer is a change of line after the first segment. Comfort preference p is a non-negative user-selected multiplier. Baseline means the same search and transfer assumptions with zero crowd weight.',
         'References. Official Scikit-learn guidance on data leakage [1], NetworkX weighted shortest paths [2], Pytest parametrization [3], and Streamlit AppTest [4] inform verification and evaluation. Full URLs appear in Section 12. Repository code, data and results are the primary project evidence.')
    page('2 Overall Description',
         'Product perspective. This is a local Streamlit decision-support simulation. The application reads CSV topology and a locally trained model, predicts every station for one departure scenario, runs two searches and renders their itineraries and metrics. There is no REST service, authentication layer or external AI API.',
         'Product functions. Select origin, destination, departure hour, day, weather, all-station event scenario and preference. Display station predictions, baseline and recommended itineraries, duration including transfers, average and maximum congestion, high-station count, signed exposure reduction, and interactive network coordinates.',
         'Users. A commuter or examiner can compare scenarios using labelled controls. A developer reproduces data, model selection, tests and benchmark outputs using the documented commands. No specialist setup beyond Python and a virtual environment is needed for an installed application.',
         'Operating environment. Python 3.11 with requirements.txt; Windows and Linux are targeted. Local browser and Streamlit serve the UI. Training, routing and charts run without internet once dependencies are installed. Model loading checks the artifact schema and Scikit-learn version; incompatible artifacts require retraining.',
         'Constraints. All source remains in the original repository and original contributor history is preserved. Only src/pipeline, src/model, src/routing and src/ui are authoritative. The alternate implementation and old artifacts are archived in legacy/. Paid APIs, ticketing, payment and fleet control are outside scope.',
         'Assumptions. Segment travel times and a 4-minute line-transfer allowance are fixed simulation inputs. Every station uses the departure-time crowd snapshot for the whole trip. Weather and event controls represent assumed scenarios, not forecasts or observations. A global event scenario applies an event flag at every station; the generator only activates events at selected stations and hours, so this is a stress scenario.')
    requirements=[
      ['ID','Implemented requirement and acceptance criterion','Automated evidence'],
      ['FR-01','Select valid origin and destination; reject unknown IDs and report disconnected trips. Identity trips show zero duration and origin congestion.','test_invalid_disconnected_and_missing_predictions; test_diversion_and_identity; test_dashboard_workflow'],
      ['FR-02','Accept departure hour, weekday, Clear/Rain/Storm, binary event and preference. Invalid domains raise ValueError. Zero preference disables crowd cost.','test_prediction_invalid_inputs; test_invalid_cost_parameters; test_parallel_lines_transfer_and_ties'],
      ['FR-03','Predict finite station congestion in [0,1] using locally fitted scenario features; reject missing or incompatible artifacts with a training command.','test_prediction_boundaries_persistence_and_errors; test_feature_generation_no_leakage; test_end_to_end_system_pipeline'],
      ['FR-04','Return a conventional minimum travel-duration itinerary and a minimum weighted-cost itinerary using station/line states and parallel edges.','test_independent_expanded_networkx; test_parallel_lines_transfer_and_ties'],
      ['FR-05','Report travel duration, transfer duration and count, average/max congestion and count of stations at or above 0.70 consistently.','test_transfer_cost_and_zero_crowd; test_diversion_and_identity; test_dashboard_workflow'],
      ['FR-06','Show signed percentage exposure change and duration difference, including zero denominators and unchanged itineraries.','test_signed_worsening_not_clamped; test_zero_denominator_and_unchanged'],
      ['FR-07','Render side-by-side itineraries, interactive station/route chart and station prediction table without external services.','test_dashboard_workflow plus browser smoke evidence'],
      ['FR-08','Display simulation provenance and recommendation explanation, with synthetic evaluation identified.','test_dashboard_workflow plus visual/manual disclosure review']]
    page('3 Functional Requirements',
         'Each requirement below describes the current submission candidate. Parameterized tests expand the listed function names into individual recorded cases. Full inputs and outcomes are in results/test_report.csv and test source.',table=requirements)
    page('4 Non Functional Requirements',
         'NFR-01 Performance. Report route-pair latency separately from network inference latency. The coursework target is under 100 ms for a route pair on this small topology, assessed using saved mean and 95th percentile values. This is a local measurement, not a service guarantee.',
         'NFR-02 Reliability. Reject malformed data, nonfinite/negative costs and unknown stations. Display a recovery command if the model cannot load. All required automated cases must pass before publication; critical route correctness failures block sign-off.',
         'NFR-03 Usability. Every scenario input has a visible label. Duration uses minutes and congestion uses a dimensionless [0,1] index. The simulation disclosure appears above results. Colours are accompanied by route labels, station tooltips and tables.',
         'NFR-04 Maintainability. Separate validation, feature engineering/model selection, graph construction, routing/comparison and UI modules. Use shared cost and prediction interfaces. Preserve the legacy implementation outside the supported package and align CI, Makefile and README to one entrypoint.',
         'NFR-05 Portability. Python 3.11 dependencies are pinned. All paths resolve from the project root, imports use lowercase src, and commands use python -m. CI targets Windows and Ubuntu. Local Windows execution is evidenced; remote CI evidence must be checked before claiming Linux validation.',
         'NFR-06 Reproducibility. Use seed 42 for data and estimator randomness; sort timestamps and split by complete days. Select a model on validation RMSE and evaluate only the selected architecture on final held-out dates. Store CSV benchmark, JSON metrics, JUnit XML, per-test report and coverage JSON. Latency values naturally vary across machines.')
    page('5 System Architecture',
         'DataLoader validates CSV schemas, ranges, uniqueness and timestamp context. CrowdPredictor derives inference-available features and holds the selected regressor. TransitGraphBuilder constructs an adjacency-based NetworkX MultiDiGraph preserving parallel lines. SmartTransitRouter performs custom heap-based search and returns plain data structures. Streamlit renders them without implementing routing mathematics.',
         'High cohesion follows from each module owning one responsibility. Low coupling follows from DataFrame, dictionary and graph interfaces: the model does not know UI widgets, and the router receives station predictions rather than calling inference during every edge relaxation. Offline training is separate from interactive trip queries.',
         'The engineering process was audit-led incremental development: reproduce baseline failures, consolidate the strongest existing pipeline, fix high-risk bugs, add regression and reference tests, measure experiments, then derive documentation from saved evidence. This is not claimed as retrospective test-driven development or a completed production deployment.',
         images=['architecture.png'])
    page('6 System Design Use Cases and Workflow',
         'The commuter configures a trip and inspects its comparison. The developer reproduces the evidence using scripts. There are no payment, account or booking use cases.',
         'Workflow errors stop before invalid values reach search. A missing model displays the training command. Invalid graph queries raise ValueError; disconnected queries return an explicit failed comparison. An origin-equals-destination query keeps the common origin exposure while returning an empty itinerary.',
         images=['use_cases.png','workflow.png'])
    page('6 System Design Data Flow and Sequence',
         'The stored model is an offline artifact, not a live service. Both searches receive the exact same prediction map. A scenario change recomputes predictions and the comparison. The graph is built from the same validated station/route files used by training and experiments.',
         images=['data_flow.png','sequence.png'])
    page('7 Algorithm Design Prediction',
         'Data provenance. data/generate_dataset.py uses seeded random weather, event and noise terms with assumed station/time factors. It produces 60 simulated days from 20 September to 18 November 2026, 19 hours per day and 20 stations: 22,800 rows. Counts, delays and congestion labels in that CSV are generated quantities; they are not model inputs.',
         'Features. Use sine/cosine hour and weekday, a derived weekend indicator, a consistently derived peak-window flag, one-hot Clear/Rain/Storm, a binary event flag and one-hot station ID. Ignore stored inflow, outflow, congestion label, delay and target. Fit the station vocabulary on training data only. All scenario fields are available before route selection under the simulation assumptions.',
         'Split. Sort timestamp then station ID. Use first 36 complete days for training (13,680 rows), next 12 for validation (4,560), and last 12 for held-out testing (4,560). Verify strict chronological separation. No station-hour timestamp crosses a split boundary.',
         'Selection. Compare global historical mean, Ridge, Random Forest and Gradient Boosting using clipped validation predictions. Select minimum validation RMSE, refit that architecture on train plus validation, and evaluate it once on the final test. Fixed candidate parameters are recorded in src/model/crowd_predictor.py.',
         f'Selected architecture: {m["best_model_name"]}. Final held-out MAE {m["MAE"]:.6f}, RMSE {m["RMSE"]:.6f}, R-squared {m["R2"]:.6f}. These scores describe interpolation of this simulator across dates; they do not estimate performance on real transit passengers.',
         'Cyclical features keep adjacent clock endpoints nearby, whereas raw hour alone has a wrap discontinuity. Tree regressors are practical on this tabular problem; the measured validation comparison supports this selection without making unsupported claims about deep-network speed or accuracy.')
    page('7 Algorithm Design Routing',
         'For each traversed edge e=(u,v) on line l, cost is travel_minutes(e) + 4*I(previous_line exists and changes) + 2.5*p*P(rho_v). All inputs must be finite and non-negative, and rho must be in [0,1]. Conventional routing sets p=0 and uses the same transfer allowance. Initial boarding incurs no transfer allowance.',
         'P(rho)=0 for rho<=0.35; P(rho)=8*(rho-0.35) for 0.35<rho<=0.70; P(rho)=2.8+35*(rho-0.70)^2 for rho>0.70. It is continuous and nondecreasing at both thresholds. The derivative drops at 0.70, so smoothness is not claimed. P is an assumed discomfort score, not empirically measured delay.',
         'Search state is (station,last_line). The heap stores (cost,sequence_counter,station,last_line,path_edges). The counter makes tied costs safe without comparing dictionaries. Finalized state costs suppress repeated expansion; relax every parallel edge and include line changes. The first destination popped has minimum weighted cost because every increment is non-negative.',
         'This is weighted-sum Dijkstra, not Pareto-front optimization. It minimizes accumulated discomfort plus time, not the arithmetic mean of station exposure. Therefore average exposure can worsen in some cases. The origin crowd does not enter edge optimization because it is common to all candidates; it is included in displayed exposure.',
         'Let S be the number of reachable station/last-line states (at most 1+V*L) and A the number of expanded outgoing transitions (at most E*(L+1)). The lazy binary heap needs O(A log A) search work. This implementation copies path lists on relaxation, adding O(A*S) worst-case time and O(A*S) heap storage. Graph storage is O(V+E). These bounds include parallel lines and path storage; replacing copied paths with predecessor links is a possible later improvement.',
         'Why these choices. BFS cannot optimize unequal weights. A* needs an admissible heuristic for the actual time/transfer/crowd objective; no validated one is available. Reinforcement learning adds training and evaluation effort without a need in this static non-negative search. Adjacency lists store sparse networks in O(V+E); matrices need O(V^2) station-pair storage and additional structure for parallel lines. A heap avoids a full linear scan for every next state.')
    page('8 Software Testing Strategy',
         'Tools. Pytest parameterization, pytest-cov statement and branch measurement, JUnit XML and Streamlit AppTest. NetworkX provides an independently assembled station/line reference graph. Each recorded test appears in results/test_report.csv with its requirement category, case name, expected assertion outcome and actual status.',
         'Black-box selection. Equivalence partitions include valid/unknown station IDs, connected/disconnected graphs, valid/invalid scenario domains, and low/moderate/high congestion. Boundary values include 0, 0.35, 0.70, 1, hour 0/23, zero preference, and values just outside accepted domains. Error guessing probes NaN, infinity, broken artifacts, missing CSVs, duplicate rows and malformed timestamps.',
         'Decision table. No previous line means no transfer; same line means no transfer; changed line means exactly 4 minutes. Preference zero means the crowd term is zero in every congestion partition; positive preference uses the piecewise penalty. The Cartesian parameter cases exercise invalid time/weight domains and both initial/same/change line decisions.',
         'White-box independent paths. Routing tests exercise invalid origin, invalid destination, missing crowd prediction, invalid edge time, identity return, first discovery, repeated-state suppression, cost improvement, tied queue entries, parallel lines, transfer and no-transfer cases, destination return and exhausted queue. Cost tests visit each of the three penalty regions and invalid-domain paths. Statement and branch results quantify execution, without claiming formal exhaustive path coverage.',
         'Integration. The original ingestion and full-pipeline tests are retained for the selected network. System tests execute dashboard initial render, zero preference, identity trip, changed destination, weekend, Storm and event input. Regression tests specifically lock the fixed zero-weight, transfer-accounting, priority-queue, signed-reduction and chronological-selection bugs. A later manual browser smoke complements AppTest for visual rendering.',
         'Stopping. Require all mandatory cases passing, no known unresolved critical/high defect, at least 90% statement coverage on measured core logic, meaningful routing/cost branch coverage, every FR mapped, a successful system workflow, reproducible benchmark and verified setup/docs. Harlan Mills fault seeding and Musa failure intensity are considered possible future techniques only; no such experiment is claimed here.')
    trace=[['ID','Evidence in authoritative tests','Acceptance status'],*[[row[0],row[2],'Automated pass; visual evidence where specified'] for row in requirements[1:]]]
    page('9 Requirements Traceability and Test Decision',
         f'Recorded final suite: {n} passed and no failed/skipped cases. Measured scope: src/pipeline, src/model, src/routing, including the unexercised training CLI module. Statement coverage {statement:.2f}% ({c["covered_lines"]}/{c["num_statements"]}); branch coverage {branch:.2f}% ({c["covered_branches"]}/{c["num_branches"]}). Routing and cost modules reach 100% statement and branch coverage. The UI, benchmark/build scripts and archived legacy code are outside this coverage denominator.',
         'The local testing threshold is met. This means the specified simulation is ready for academic evaluation when packaging and publication checks pass; it does not prove the absence of every defect or real-world suitability. Dependency deprecation warnings are recorded and do not represent failing functional assertions.',table=trace)
    page('10 Verified Results and Evaluation',
         f'Routing grid: {r["scenarios"]:,} comparisons = 7 regimes x 380 ordered distinct station pairs x 4 preferences (0,1,2,5). Regimes cover weekday morning, evening, off-peak, weekend, rain, storm and global event stress. The grid is declared in scripts/benchmark.py before outcome selection; all results are saved, including adverse cases.',
         f'Average-exposure outcomes: improved {r["improved_percent"]:.2f}%, equal {r["equal_exposure_percent"]:.2f}%, worsened {r["worsened_percent"]:.2f}%. Unchanged itineraries: {r["unchanged_itinerary_percent"]:.2f}%. Mean per-query signed reduction: {r["mean_reduction_percent"]:.3f}%. Mean exposure changes from {r["mean_baseline_exposure"]:.6f} to {r["mean_smart_exposure"]:.6f}. Mean added duration is {r["mean_time_delta_minutes"]:.3f} minutes.',
         f'Local timing: mean route-pair search {r["mean_routing_pair_ms"]:.3f} ms, 95th percentile {r["p95_routing_pair_ms"]:.3f} ms; mean network prediction {r["mean_network_prediction_ms"]:.3f} ms across seven batches. Routing timing includes two searches and comparison but excludes prediction. These are single-run Windows/Python measurements and can vary.',
         'Representative useful detour selected after full-grid evaluation: S04 to S14, Thursday 18:00, Storm, event off, preference 2. Baseline S04>S01>S12>S14 takes 22 minutes; recommendation S04>S18>S15>S14 takes 25 minutes. Average exposure changes from 0.405926 to 0.322975, a 20.435% reduction. Both have one transfer, and neither encounters rho>=0.70. This is an illustrative success case, not the aggregate result.',
         images=['../../results/routing_comparison.png'])
    page('10 Evaluation Metric Definitions',
         'For an itinerary with N station visits including endpoints, average exposure is mean(rho_i)=sum(rho_i)/N; maximum is max(rho_i); high-congestion count is sum I(rho_i>=0.70). Repeated station visits, if any, count separately. These are unweighted snapshot metrics and do not represent passenger-minutes of exposure.',
         'Travel duration is sum(segment base minutes) + 4*transfer_count. Transfer count is the number of line changes between consecutive segments. The model does not include initial waiting, timetables, vehicle capacity, missed boarding or travel-dependent changes in crowd.',
         'Signed reduction is 100*(baseline_mean-smart_mean)/baseline_mean. A negative value means worsening. If baseline_mean=0, the implementation reports 0 by convention; with non-negative crowd and a zero-exposure shortest baseline, no positive crowd penalty can improve that zero. This convention avoids division by zero and is tested.',
         'Travel-time trade-off is smart_duration-baseline_duration, in minutes. An itinerary is unchanged only if ordered destination stations and line names for every segment match. Improved and worsened fractions use a numerical tolerance of 1e-12 in exposure; equal exposure is a separate fraction. Mean percentage reduction averages individual ratios and differs from the ratio of aggregate means.',
         'For n held-out predictions, MAE=sum(abs(y-yhat))/n; RMSE=sqrt(sum((y-yhat)^2)/n); R-squared=1-sum((y-yhat)^2)/sum((y-mean(y))^2). Congestion prediction errors use index units. The held-out target has nonzero variance. Predictions are clipped to [0,1] before evaluation.',
         'All baseline/smart means, maxima, high counts, durations, transfer counts, path strings and route-pair timings are stored for every case in results/routing_benchmark.csv. JSON summaries and charts are computed from that saved grid. Small aggregate gains and rare worsened exposure are retained, not suppressed.')
    page('11 Limitations',
         'Limitations. The simulator is small, mostly below the high-congestion threshold, and lacks observed passenger data. No real-world congestion reduction or broad superiority over commercial navigation tools is established. Weather and global event scenarios can differ from combinations seen in training. No seating, punctuality, shortest-average-exposure or maximum-detour guarantee is provided.',
         'The weighted objective can select a substantially slower route at high preference, and can occasionally worsen the displayed arithmetic mean because it optimizes accumulated penalty. Departure snapshots ignore crowd evolution along the trip. The assumed penalty and transfer allowance require calibration before deployment. Model artifacts are trusted local files; never load third-party pickle files.',
         '## 12 Conclusion and References',
         'The submission demonstrates a modular, reproducible connection between scenario prediction and transfer-aware weighted routing, with a conventional comparator and explicit adverse outcomes. Its differentiation is the transparent adjustable objective, correct line-state search and traceable experiment/test evidence. It contains no LLM, prompt-based trip planning or external AI call.',
         '[1] Scikit-learn, Common pitfalls and recommended practices, data leakage: https://scikit-learn.org/stable/common_pitfalls.html',
         '[2] NetworkX, dijkstra_path: https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.dijkstra_path.html',
         '[3] Pytest, How to parametrize fixtures and test functions: https://pytest.org/en/latest/how-to/parametrize.html',
         '[4] Streamlit, App testing: https://docs.streamlit.io/develop/concepts/app-testing',
         'Implementation and primary evidence: https://github.com/oceankesarwani/Smart-transport-system. Inspect src/, tests/, data/generate_dataset.py and results/. Reproduction commands are in README.md and docs/DEMO_SCRIPT.md. References consulted 24 November 2026.')
    return pages


def build_documents():
    pages=content();DOCS.mkdir(exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle('BodyBlack',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=10,textColor=colors.black,splitLongWords=True))
    styles.add(ParagraphStyle('HeadBlack',fontName='Helvetica-Bold',fontSize=19,leading=23,spaceAfter=18,textColor=colors.black))
    styles.add(ParagraphStyle('CellBlack',fontName='Helvetica',fontSize=8,leading=10,textColor=colors.black))
    story=[];doc=Document();section=doc.sections[0]
    section.page_width=Inches(8.27);section.page_height=Inches(11.69)
    section.top_margin=section.bottom_margin=Inches(.72)
    section.left_margin=section.right_margin=Inches(.78)
    for style_name in ['Normal','Title','Heading 1','Heading 2']:
        st=doc.styles[style_name];st.font.name='Calibri';st.font.color.rgb=RGBColor(0,0,0)
    normal=doc.styles['Normal'];normal.font.size=Pt(10.5);normal.paragraph_format.space_after=Pt(9);normal.paragraph_format.line_spacing=1.1
    doc.styles['Title'].font.size=Pt(24);doc.styles['Heading 1'].font.size=Pt(19)
    foot=section.footer.paragraphs[0];foot.alignment=2
    foot.add_run('Smart Public Transport System  |  ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field)
    for index,page in enumerate(pages):
        if index:
            story.append(PageBreak());doc.add_page_break()
        title=page['title']
        story.append(Paragraph(escape(title),styles['HeadBlack']))
        doc.add_paragraph(title,'Title' if index==0 else 'Heading 1')
        for paragraph in page['paragraphs']:
            if paragraph.startswith('## '):
                story.append(Paragraph(escape(paragraph[3:]),styles['HeadBlack']))
                doc.add_paragraph(paragraph[3:],'Heading 1')
                continue
            story.append(Paragraph(escape(paragraph).replace('\n','<br/>'),styles['BodyBlack']))
            doc.add_paragraph(paragraph)
        if page['table']:
            rows=page['table'];cells=[[Paragraph(escape(str(cell)),styles['CellBlack']) for cell in row] for row in rows]
            widths=[48,250,186] if len(rows[0])==3 else None
            table=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            story.append(table)
            wt=doc.add_table(rows=1,cols=len(rows[0]));wt.style='Table Grid';wt.autofit=False
            for rownum,row in enumerate(rows):
                cells_w=wt.rows[0].cells if rownum==0 else wt.add_row().cells
                for j,text in enumerate(row):
                    cells_w[j].text=str(text)
                    cells_w[j].width=Inches([.65,3.45,2.55][j])
                    for par in cells_w[j].paragraphs:
                        par.paragraph_format.space_after=Pt(4)
                        for run in par.runs: run.font.size=Pt(8)
                    if rownum==0:
                        shd=OxmlElement('w:shd');shd.set(qn('w:fill'),'E2E8F0');cells_w[j]._tc.get_or_add_tcPr().append(shd)
                if rownum==0:
                    repeat=OxmlElement('w:tblHeader');wt.rows[0]._tr.get_or_add_trPr().append(repeat)
        for image in page['images']:
            path=(DOCS/'figures'/image).resolve()
            if not path.exists(): raise FileNotFoundError(path)
            from PIL import Image as PILImage
            with PILImage.open(path) as im: w,h=im.size
            display_w=475;display_h=display_w*h/w
            story.append(Spacer(1,8));story.append(Image(str(path),width=display_w,height=display_h))
            doc.add_picture(str(path),width=Inches(6.55))
    def footer(canvas,document):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.black)
        canvas.drawString(45,27,'Smart Public Transport System  |  Software Engineering  |  Synthetic simulation')
        canvas.drawRightString(A4[0]-45,27,str(document.page))
    SimpleDocTemplate(str(DOCS/'SRS.pdf'),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=44,bottomMargin=46).build(story,onFirstPage=footer,onLaterPages=footer)
    # The bundled Word template includes themed title borders; remove them explicitly.
    for style in doc.styles:
        for border in list(style.element.iter(qn('w:pBdr'))):
            border.getparent().remove(border)
    doc.save(DOCS/'SRS.docx')
    (DOCS/'SRS.md').write_text('\n\n'.join('# '+p['title']+'\n\n'+'\n\n'.join(p['paragraphs'])+('\n\n'+'\n'.join('| '+' | '.join(row)+' |' for row in p['table']) if p['table'] else '') for p in pages),encoding='utf-8')
    (DOCS/'srs_content.json').write_text(json.dumps(pages,indent=2),encoding='utf-8')
    print(f'Built SRS PDF and editable DOCX from {len(pages)} content pages')

if __name__=='__main__':
    build_documents()
