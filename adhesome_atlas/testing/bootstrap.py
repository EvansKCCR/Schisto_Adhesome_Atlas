"""Make the organized Atlas modules importable by direct test scripts."""

from pathlib import Path
import sys


ATLAS_ROOT = Path(__file__).resolve().parents[1]
for directory in (
    ATLAS_ROOT / "main",
    ATLAS_ROOT / "branding",
    ATLAS_ROOT / "maintenance_directories",
    ATLAS_ROOT / "testing",
):
    location = str(directory)
    if location not in sys.path:
        sys.path.insert(0, location)
