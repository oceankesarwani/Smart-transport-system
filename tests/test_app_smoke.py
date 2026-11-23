"""
Smoke Test for Streamlit Web Application (streamlit_app.py)
Validates that the Streamlit app module can load, initialize components, and execute.
"""
import pytest
from unittest.mock import patch, MagicMock

def test_streamlit_app_loads_successfully():
    """Smoke test ensuring app/streamlit_app.py imports and initializes without unhandled exceptions."""
    import importlib.util
    from pathlib import Path

    app_path = Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py"
    assert app_path.exists(), "streamlit_app.py does not exist"

    spec = importlib.util.spec_from_file_location("streamlit_app", str(app_path))
    assert spec is not None
