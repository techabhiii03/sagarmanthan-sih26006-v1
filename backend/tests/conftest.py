"""Ensure app package is importable when running pytest from backend/."""
import sys
from pathlib import Path

# backend/ is on sys.path via pytest.ini pythonpath=.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
