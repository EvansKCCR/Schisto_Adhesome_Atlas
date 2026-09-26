"""Check the contact page and its client-side email draft."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


app = AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=120).run()
pages = list(app.sidebar.radio[0].options)
assert pages.index('Comments & feedback') < pages.index('Source Library') == pages.index('Citations') - 1
app.sidebar.radio[0].set_value('Comments & feedback').run()
assert not app.exception
assert any('mailto:evansasamoahadu@gmail.com' in item.value for item in app.markdown)
app.text_area[0].set_value('Please review Smp_126140 and its orthogroup.')
app.button[0].click().run()
assert not app.exception
assert any('mailto:evansasamoahadu@gmail.com?subject=' in item.value and 'Smp_126140' in item.value for item in app.markdown)
print('PASS comments, feedback, direct contact and email draft')
