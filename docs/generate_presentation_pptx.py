"""Compatibility wrapper for reproducible submission documents."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
if __name__=='__main__':
    from scripts.build_documents import build_documents
    build_documents()
