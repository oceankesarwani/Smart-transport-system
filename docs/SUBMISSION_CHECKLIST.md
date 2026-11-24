# Academic submission checklist

Repository: https://github.com/oceankesarwani/Smart-transport-system

Academic submission is packaged. Public hosting remains an account sign-in step; no unverified public URL is listed. Use [cloud deployment instructions](CLOUD_DEPLOYMENT.md).

## Deliverables

- [SRS PDF](https://github.com/oceankesarwani/Smart-transport-system/blob/main/docs/SRS.pdf) and [editable SRS](https://github.com/oceankesarwani/Smart-transport-system/blob/main/docs/SRS.docx): 15 pages, contributor details retained from config.yaml.
- [PowerPoint](https://github.com/oceankesarwani/Smart-transport-system/blob/main/docs/presentation.pptx) and [presentation PDF](https://github.com/oceankesarwani/Smart-transport-system/blob/main/docs/PPT.pdf): exactly five slides, with timed ten-minute notes in [demo script](DEMO_SCRIPT.md).
- [Testing report](TEST_REPORT.md), [individual actual outcomes](../results/test_report.csv), [coverage](../results/coverage.json), [JUnit](../results/junit.xml).
- [Model evaluation](../results/model_metrics.json), [10,640-case routing CSV](../results/routing_benchmark.csv), [routing summary](../results/routing_summary.json).
- [Viva preparation](VIVA_PREPARATION.md), [frontend review](FRONTEND_DESIGN.md), genuine [desktop](figures/dashboard_comparison.png) and [phone](figures/dashboard_mobile.png) captures.

## Professor requirement mapping

| Requirement | Evidence |
|---|---|
| Single pinpointed problem | README Problem and motivation; SRS sections 1–2; slide 1 |
| Motivation and primary objective | README; SRS introduction; slide 1 |
| Technical approach | src/model, src/routing; SRS section 7; slides 2–3 |
| Role of Software Engineering | SRS architecture/testing/traceability; slide 2; audit and regression history |
| Why this approach over alternatives | README routing trade-offs; SRS algorithm design; slide 3 |
| Significant measurable outcomes | Saved model/routing outputs; SRS evaluation; slide 5, including adverse outcomes |
| Innovation and differentiation | Explicit preference and station/line optimization; README limitations; slide 5 |
| Not a ChatGPT wrapper | Local Scikit-learn prediction and deterministic search; no LLM/API; slide 5 |
| Testing tools | Pytest, pytest-cov, NetworkX, Streamlit AppTest; SRS testing; slide 4 |
| Test-case selection | Equivalence partitions, boundaries, decision tables, error guessing, branch/reference cases; test_core.py; slide 4 |
| When to stop testing | TEST_REPORT.md exit criteria; SRS sections 8–9; slide 4 |
| SRS and traceability | SRS.pdf/docx sections 3 and 9; every FR has test evidence |
| Five slides and ten minutes | Five slides in PPTX/PDF; DEMO_SCRIPT.md timed narration |
| Complete GitHub submission | Original repository main, source, documents, scripts and evidence |

## Local execution

From the existing repository root in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run src/ui/app.py
```

The shipped model is already present; retrain only if unavailable/incompatible with ` .\.venv\Scripts\python.exe -m src.model.train`.
On Linux use `python3.11 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python -m streamlit run src/ui/app.py`.

## Demonstration and evidence

S04 to S14; Thursday; 18:00; Storm; event off; preference 2.0. Expected lower predicted mean exposure **20.44%**, baseline **22 minutes**, recommended **25 minutes**. Both have one transfer and zero stations above the 0.70 congestion threshold. Change preference to zero to show the shared baseline objective. The demonstration is selected from the complete benchmark, not a typical gain.

Recorded suite: **74 passing tests**; statement **93.62%**, branch **95.00%**, combined **94.02%**. Routing/cost logic: 100% statement and branch coverage. Windows and Ubuntu CI passed for the submitted application; check the current Actions run for the packaging update.

## Limitations

Entire history is synthetic and lines are illustrative. No observed real-world congestion benefit or seating guarantee. Weighted accumulated discomfort differs from average exposure: 95.67% of itineraries were unchanged, 4.02% improved and 0.31% worsened average exposure. Fixed times and departure snapshots omit schedules, evolving crowds, waiting and capacity enforcement. No maximum detour guarantee. Public hosting is not completed until the account deploys and the actual URL is verified.
