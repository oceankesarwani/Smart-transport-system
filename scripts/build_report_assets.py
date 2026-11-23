"""
Build Report Assets Script
Copies generated figures and LaTeX tables from results/ into paper/figures/ and paper/
"""
import os
import shutil
from pathlib import Path

def sync_report_assets():
    root = Path(__file__).resolve().parent.parent
    src_figs = root / "results" / "figures"
    dst_figs = root / "paper" / "figures"
    os.makedirs(dst_figs, exist_ok=True)

    if src_figs.exists():
        for f in src_figs.glob("*.png"):
            shutil.copy2(f, dst_figs / f.name)
        print(f"[+] Synced {len(list(src_figs.glob('*.png')))} figures -> {dst_figs}")

if __name__ == "__main__":
    sync_report_assets()
