#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
# Keep Linux dependencies on the Linux filesystem, separate from Windows .venv.
ATLAS_VENV="${ATLAS_VENV:-${HOME}/.venvs/schistoatlas}"
if [[ ! -x "$ATLAS_VENV/bin/python" ]]; then
    echo "Creating Linux environment: $ATLAS_VENV"
    python3 -m venv "$ATLAS_VENV" || {
        echo "Install Python venv support first (Ubuntu/Debian: sudo apt install python3-venv)." >&2
        exit 1
    }
fi
if [[ "${1:-}" == "--setup" ]]; then
    "$ATLAS_VENV/bin/python" -m pip install -r "$PROJECT_DIR/requirements.txt"
    shift
fi
if ! "$ATLAS_VENV/bin/python" -c 'import streamlit, pandas, plotly, openpyxl, networkx' >/dev/null 2>&1; then
    echo "Install atlas dependencies with: bash launch_atlas.sh --setup" >&2
    exit 1
fi
exec "$ATLAS_VENV/bin/python" -m streamlit run "$PROJECT_DIR/app.py" \
    --server.address 127.0.0.1 --server.port "${ATLAS_PORT:-8501}" --server.headless true "$@"
