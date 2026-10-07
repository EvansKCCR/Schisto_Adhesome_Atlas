"""Consistent browser-side figure exports without a server rendering dependency."""
import math
import re
import unicodedata

import streamlit as st

FORMAT_KEY = 'atlas_figure_download_format'
FORMATS = ['High-resolution PNG', 'Vector SVG']
PNG_SCALE = 3
MAX_RASTER_SIDE = 16000
MAX_RASTER_PIXELS = 64000000


def export_filename(fig, filename=None):
    title = filename or fig.layout.title.text or 'schisto_adhesome_figure'
    title = re.sub(r'<[^>]+>', '', str(title)).replace('α', 'alpha').replace('β', 'beta')
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-zA-Z0-9_-]+', '_', title).strip('_')[:120] or 'schisto_adhesome_figure'


def image_export_config(fig, *, image_format='png', filename=None, config=None):
    """Retain tall figures and bound PNG dimensions to browser canvas limits."""
    if image_format not in {'png', 'svg'}:
        raise ValueError('Figure download format must be PNG or SVG')
    width = max(1600, int(fig.layout.width or 1600))
    height = max(600, int(fig.layout.height or 900))
    scale = 1
    if image_format == 'png':
        scale = min(PNG_SCALE, MAX_RASTER_SIDE / width, MAX_RASTER_SIDE / height,
                    math.sqrt(MAX_RASTER_PIXELS / (width * height)))
    settings = {'displaylogo': False, **(config or {})}
    settings['toImageButtonOptions'] = {'format': image_format,
        'filename': export_filename(fig, filename), 'width': width, 'height': height,
        'scale': scale}
    return settings


def selected_export_config(fig, *, filename=None, config=None):
    image_format = 'svg' if st.session_state.get(FORMAT_KEY) == FORMATS[1] else 'png'
    return image_export_config(fig, image_format=image_format, filename=filename, config=config)


def plotly_chart(fig, *, filename=None, config=None, **kwargs):
    return st.plotly_chart(fig, config=selected_export_config(fig, filename=filename, config=config), **kwargs)


def figure_download_settings():
    with st.expander('Figure downloads'):
        st.selectbox('Download format', FORMATS, key=FORMAT_KEY)
        st.caption('Use each chart’s camera icon. PNG exports use up to 3× resolution '
                   '(typically 4,800 × 2,700 pixels); SVG scales without losing sharpness. '
                   'Network SVG buttons preserve your current layout. Very tall PNGs are '
                   'bounded to browser canvas limits; SVG keeps the full scalable figure.')
