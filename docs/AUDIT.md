# Initial audit

Baseline commit: 27afae7 (latest main at clone). Original remote retained. One existing commit; no other remote development branches. Branch push succeeded, verifying write access. GitHub CLI unavailable.

Before edits: Python 3.11.0; compileall succeeded; pytest initially unavailable while dependencies were being installed. Importing src.pipeline.data_loader failed with ModuleNotFoundError: SRC. README used uppercase SRC paths, claimed Pareto routing, sensor data, invented fallback metrics and unrecorded fault seeding.

Two pipelines inspected: A src/transport used categorical classification and a separate STOP_ network, random splits, prediction inside search and inconsistent baseline evaluation; B src/model + pipeline + routing used continuous congestion, CSV station/parallel-line network, expanded routing states and richer map UI. B is selected as authoritative because it matches the core station-exposure objective. Preserve A source and tests as explicitly legacy regression material; no legitimate contributor work removed. Public entrypoints, CI and build scripts will use B.

Verified defects in B: uppercase imports and artifact paths; validation absent for negative/NaN costs; zero comfort clamped to 0.1; baseline transfer weight differed; transfer minutes multiplied twice and omitted from duration; negative exposure reduction clamped; identity route crowd forced to zero; model selected on test data; stored is_peak could differ from prediction-time derivation; malformed congestion clipped silently.

Existing config contributor records retained. Fictional lines and all historical samples are simulation, not verified transit services or sensors.

Pristine baseline extracted from Git commit 27afae7 and collected after dependency installation: 27 tests collected, 2 import errors (uppercase SRC in data loader and integration imports). See results/baseline_collection.txt. First corrected-suite run: 71 passed and one test assertion failed because it expected nine Streamlit metric widgets while the UI deliberately has five and reports remaining values as text. Assertion corrected to match required displayed metrics.
