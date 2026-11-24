# Viva preparation

Answers describe the supported simulation, not an operational transit service.

## 1. Why this problem?

Time-only routing omits station crowding. This gives us a narrow, measurable trade-off between predicted exposure and trip duration.

## 2. What is the role of Software Engineering?

Testable requirements, separated modules, versioned changes, regression tests, traceability, CI and reproducible evidence connect the implementation to its specification.

## 3. Why Dijkstra?

All composite edge costs are non-negative. Dijkstra finds the minimum cost in the expanded state graph without requiring a heuristic.

## 4. Why not BFS?

Segment durations and crowd costs are unequal. BFS minimizes edge count, not this weighted objective.

## 5. Why not A*?

A* needs an admissible heuristic for the actual time, transfer and crowd objective. We did not have a validated heuristic, and this small network does not need it.

## 6. Why not ordinary shortest-time routing?

That is our conventional comparator. It ignores crowd penalties and can select a crowded corridor; the same search with a positive preference makes the trade-off explicit.

## 7. Why is a station alone not enough search state?

The next transfer cost depends on the line used to arrive. We retain (station,last_line), so reaching the same station on two lines remains a different decision state.

## 8. How are parallel lines handled?

MultiDiGraph preserves each line edge. The custom search examines all parallel edges, including a slower arrival line that may avoid a later transfer.

## 9. Why an adjacency list?

The graph is sparse and needs parallel edges. Adjacency storage uses O(V+E), while a station matrix requires O(V^2) plus parallel-line structure.

## 10. Why a priority queue and counter?

The heap repeatedly extracts the smallest tentative cost efficiently. A unique sequence counter prevents Python from comparing path dictionaries when costs tie.

## 11. What is the routing cost?

Sum base segment minutes, add four minutes per line change, and add 2.5 times comfort preference times the assumed discomfort penalty at each arrived station.

## 12. Are crowd penalties actual delay?

No. The piecewise curve is an assumed discomfort score. Only base travel and line-transfer allowances enter reported trip duration.

## 13. How were weights selected?

They are transparent simulation assumptions, not calibrated passenger utility. The benchmark tests preferences 0, 1, 2 and 5; the UI exposes the choice and added time.

## 14. Is this Pareto optimization?

No. It minimizes one weighted sum for the chosen preference and does not enumerate a Pareto frontier.

## 15. Does more preference always lower average congestion?

No. Search minimizes accumulated nonlinear discomfort, whereas the displayed exposure is a mean including endpoints. The benchmark retains the small fraction of adverse outcomes.

## 16. What is the complexity?

With S station/line states and A expanded transitions, heap work is O(A log A). Copying paths adds O(A*S) worst-case time and memory in this implementation; graph storage is O(V+E).

## 17. Why Random Forest?

It had the lowest validation RMSE among historical mean, Ridge, Random Forest and Gradient Boosting. We refitted that architecture on development data, then evaluated final held-out dates.

## 18. What are the features?

Hour/day sine and cosine, derived weekend and peak flags, one-hot station/weather and an event flag. No target, generated inflow/outflow or delay is used.

## 19. What is synthetic data?

Values produced by a seeded simulator with assumed demand factors and random noise. They are not real passenger sensor observations.

## 20. How is leakage prevented?

Complete days are ordered chronologically into train, validation and test. Fit the encoder on training data, choose using validation, and keep target-derived columns out of features.

## 21. Why cyclical time features?

Sine/cosine makes adjacent clock endpoints close in feature space. Raw hour alone has an artificial discontinuity at midnight.

## 22. What happens when no route exists?

The router returns no path and comparison returns a failed status. The dashboard displays an unavailable-route message instead of inventing an itinerary.

## 23. What if the model cannot load?

A missing or incompatible artifact produces a clear recovery message: run python -m src.model.train. The dashboard does not silently replace predictions with invented metrics.

## 24. What is different or innovative?

The coursework integrates an adjustable numerical crowd objective with correct line-state routing, a conventional comparator and fully recorded adverse as well as favorable results. It does not claim a new shortest-path algorithm.

## 25. How does this differ from existing navigation tools?

Our demonstrator explicitly exposes its assumptions and crowd trade-off on an illustrative graph. We have not benchmarked current commercial tools and cannot claim they all ignore crowding.

## 26. Why is this not a ChatGPT wrapper?

Predictions come from a fitted Scikit-learn regressor and routes from deterministic graph optimization. There is no LLM, prompt or external AI API.

## 27. How did you test it and why Pytest?

Pytest offers clear assertions and parameterized cases with little infrastructure. We combine unit, pipeline and AppTest system tests, coverage and an independently constructed NetworkX reference.

## 28. What is equivalence partitioning?

Divide inputs into behaviourally similar classes, such as valid versus unknown stations or connected versus disconnected graphs, and select representatives.

## 29. What is boundary value analysis?

Test at and immediately around boundaries where behaviour changes: congestion 0.35/0.70, valid hour endpoints, zero preference and domain limits.

## 30. What is regression testing?

Keep a test for a fixed defect so later changes cannot quietly reintroduce it. Examples here are zero comfort, transfer minutes and unclamped negative exposure reduction.

## 31. When did you stop testing?

The recorded suite has 74 passing cases, 93.62% statement and 95.00% branch coverage, with every FR traced and system/benchmark evidence. We stop at explicit coursework gates, without claiming mathematical proof of zero defects.

## 32. What are the main limitations?

Synthetic data, fictional lines, fixed transfer time, departure-only crowd snapshots, no schedules or capacity enforcement, and no real-world validation. High preference can add substantial travel time.

## 33. Can it work with real transit data?

The modular ingestion and feature interfaces could be adapted to validated topology and historical crowd observations. That would require provenance checks, recalibration, new chronological evaluation and possibly arrival-time prediction.

## 34. What results should we quote?

Quote the saved held-out metrics (MAE 0.008378, RMSE 0.012473, R² 0.973181) and full-grid outcomes (4.02% improved, 0.31% worse). Identify the 20.435% demo as a selected scenario.

## Further examiner questions

### What does Random Forest average, and why does that help?
Each regression tree predicts a congestion number. The forest averages tree predictions. Bootstrap samples and random feature subsets diversify the trees, reducing the variance of one tree; they do not make synthetic data representative of reality.

### Why did most benchmark itineraries remain unchanged?
Many station predictions lie below the 0.35 zero-penalty boundary, and alternative routes may cost more time/transfers than their penalty savings. The grid also includes zero preference. Unchanged paths are expected outcomes, not missing calculations.

### What is the difference between black-box and white-box testing?
Black-box tests select input/output cases from the specification without relying on internal code, such as unknown stations and boundary crowd values. White-box tests use knowledge of branches and state transitions, such as stale queue entries or transfer/no-transfer paths.

### What do statement and branch coverage mean?
Statement coverage records executable lines reached; branch coverage records alternatives taken at decisions. Neither guarantees correctness. Here independent NetworkX comparisons and numerical expectations provide evidence beyond execution counts. The denominator excludes UI/build scripts and legacy code.

### What does the Requirements Traceability Matrix prove?
It maps each numbered functional requirement to its acceptance evidence, so omissions can be found and change impact assessed. It does not prove a requirement is correct or exhaustive merely because a test is listed.

### Why can high test R-squared coexist with weak routing improvements?
Prediction estimates this simulator accurately, but the routing benefit depends on available detours, crowd distributions, thresholds and weights. A predictive score does not imply routes will change or that real commuters benefit.
