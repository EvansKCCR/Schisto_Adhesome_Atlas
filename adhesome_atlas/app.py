"""Stable Streamlit entry point for local and Community Cloud deployments."""

from pathlib import Path
import runpy
import sys


ATLAS_ROOT = Path(__file__).resolve().parent
for directory in (
    ATLAS_ROOT / "main",
    ATLAS_ROOT / "branding",
    ATLAS_ROOT / "maintenance_directories",
):
    location = str(directory)
    if location not in sys.path:
        sys.path.insert(0, location)

# Streamlit reruns this file after widget interactions. run_path executes the
# page definition on each rerun instead of reusing a cached imported module.
runpy.run_path(str(ATLAS_ROOT / "main" / "app.py"), run_name="__main__")
