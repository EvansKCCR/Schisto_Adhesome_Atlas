"""Verify the deployed entry point executes the page on every rerun."""

from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "app.py"


def main():
    calls = []

    def record(path, run_name=None):
        calls.append((Path(path).resolve(), run_name))
        return {}

    source = compile(ENTRYPOINT.read_text(encoding="utf-8"), str(ENTRYPOINT), "exec")
    with patch("runpy.run_path", side_effect=record):
        exec(source, {"__file__": str(ENTRYPOINT), "__name__": "__main__"})
        exec(source, {"__file__": str(ENTRYPOINT), "__name__": "__main__"})
    assert calls == [((ROOT / "main/app.py").resolve(), "__main__")] * 2
    print("PASS root entry point executes main/app.py on every rerun")


if __name__ == "__main__":
    main()
