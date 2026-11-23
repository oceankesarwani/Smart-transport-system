"""
Pipeline Orchestrator: Data -> Train -> Evaluate -> Build Report Assets & Slides
Executes complete research lifecycle with fixed seeds and empirical verification.
"""
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.transport.data_gen import generate_ridership_dataset
from src.transport.model import CrowdModelManager
from src.transport.evaluate import run_evaluation_suite
from src.transport.utils import load_config, get_project_root
import pandas as pd

def run_entire_pipeline():
    print("=" * 75)
    print(" Smart Public Transport System: Full End-to-End Execution Pipeline ")
    print("=" * 75)

    config = load_config()

    # 1. Generate Synthetic Dataset
    print("\n--- STEP 1: Synthetic Dataset Generation (~60,000 records) ---")
    raw_csv = get_project_root() / config["data"]["raw_path"]
    if not raw_csv.exists():
        df = generate_ridership_dataset(config)
    else:
        print(f"[*] Found existing dataset at: {raw_csv}")
        df = pd.read_csv(raw_csv)

    # 2. Train and Benchmark Models
    print("\n--- STEP 2: ML Model Training (GridSearchCV Random Forest vs Baselines) ---")
    model_mgr = CrowdModelManager(config)
    model_mgr.train_and_benchmark(df)
    model_mgr.save()

    # 3. Comprehensive Evaluation
    print("\n--- STEP 3: Evaluation Suite (500 OD-Pairs, Figures, LaTeX Tables) ---")
    metrics = run_evaluation_suite()

    # 4. Build Report Assets
    print("\n--- STEP 4: Copying Assets into Paper Directory ---")
    from scripts.build_report_assets import sync_report_assets
    sync_report_assets()

    # 5. Build Slides
    print("\n--- STEP 5: Generating 5-Slide Presentation (PPT.pptx & PPT.pdf) ---")
    from scripts.build_slides import generate_presentation_deck
    generate_presentation_deck()

    print("\n" + "=" * 75)
    print(" [✓] PIPELINE EXECUTION SUCCESSFUL: ALL ARTIFACTS PRODUCED & SYNCHRONIZED! ")
    print("=" * 75)

if __name__ == "__main__":
    run_entire_pipeline()
