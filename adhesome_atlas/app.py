"""Stable Streamlit entry point for local and Community Cloud deployments."""

from pathlib import Path
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

# Importing the application module executes the Streamlit page definition.
from main.app import *  # noqa: F401,F403,E402
