"""A newly deployed page must render with cohorts cached by an older loader."""
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
import data


original_load = data.load


def stale_load():
    cohorts, *rest = original_load()
    stale = {
        name: frame.drop(columns=['audit_classification', 'reviewed_family', 'family_assignment_basis'], errors='ignore')
        for name, frame in cohorts.items()
    }
    return (stale, *rest)


with patch.object(data, 'load', stale_load):
    app = AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=120).run()
    app.sidebar.radio[0].set_value('Components').run()
    for view in ['Summary statistics', 'Summary graphs', 'Family assignment audit']:
        app.sidebar.radio[1].set_value(view).run()
        assert not app.exception, [error.message for error in app.exception]
        print('PASS cached schema:', view, flush=True)
