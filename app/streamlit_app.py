"""Compatibility startup entrypoint. The authoritative UI is src/ui/app.py."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[1] / 'src' / 'ui' / 'app.py'),run_name='__main__')
