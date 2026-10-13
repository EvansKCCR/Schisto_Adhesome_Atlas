"""Consistent browser-side figure exports without a server rendering dependency."""
import math
import re
import unicodedata
import colorsys

import streamlit as st

FORMAT_KEY = 'atlas_figure_download_format'
FORMATS = ['High-resolution PNG', 'Vector SVG']
PNG_SCALE = 3
MAX_RASTER_SIDE = 16000
MAX_RASTER_PIXELS = 64000000
TEXT_COLOR = '#000000'
FONT_FAMILY = 'Arial, sans-serif'


def light_label_background(color):
    """Retain a fill's hue while giving black inside-labels a light background."""
    if not isinstance(color, str):
        return color
    if re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        rgb = tuple(int(color[index:index + 2], 16) / 255 for index in (1, 3, 5))
    elif re.fullmatch(r'#[0-9a-fA-F]{3}', color):
        rgb = tuple(int(character * 2, 16) / 255 for character in color[1:])
    elif color.startswith('rgb('):
        rgb = tuple(float(value) / 255 for value in color[4:-1].split(','))
    else:
        return color
    hue, lightness, saturation = colorsys.rgb_to_hls(*rgb)
    values = colorsys.hls_to_rgb(hue, max(lightness, .78), saturation)
    return '#'+''.join(f'{round(value * 255):02x}' for value in values)


def legible_figure(fig):
    """Apply black text to the displayed figure and its HTML/PNG/SVG exports."""
    import plotly.express as px
    layout_names = set(fig.layout.to_plotly_json())
    if any('xaxis' in trace or 'yaxis' in trace for trace in fig.data):
        layout_names.update(['xaxis', 'yaxis'])

    def font(value, minimum):
        # Preserve deliberately large text, e.g. tall phylogenetic trees.
        size = value.size if isinstance(value.size, (int, float)) else minimum
        value.update(color=TEXT_COLOR, family=FONT_FAMILY, size=max(minimum, size))

    font(fig.layout.font, 16)
    font(fig.layout.title.font, 22)
    font(fig.layout.legend.font, 14)
    font(fig.layout.legend.title.font, 16)
    fig.update_layout(paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
                      hoverlabel=dict(bgcolor='#ffffff', bordercolor='#000000', font=dict(color=TEXT_COLOR, family=FONT_FAMILY, size=15)),
                      uniformtext=dict(minsize=14, mode='hide'))
    for name in layout_names:
        if re.fullmatch(r'[xy]axis\d*', name):
            axis = fig.layout[name]
            axis.update(color=TEXT_COLOR, automargin=True)
            font(axis.tickfont, 14)
            font(axis.title.font, 17)
    for annotation in fig.layout.annotations:
        font(annotation.font, 14)
        annotation.update(bgcolor='#ffffff', opacity=1)
    for shape in fig.layout.shapes:
        if 'label' in shape:
            font(shape.label.font, 14)
    for collection in [fig.layout.updatemenus, fig.layout.sliders]:
        for item in collection:
            if 'font' in item:
                font(item.font, 14)
            if 'currentvalue' in item:
                font(item.currentvalue.font, 14)
    inside_fills = False
    default_scale = [(0., '#ffffdf'), (.5, '#c9e5cc'), (1., '#8ccb9d')]
    for trace in fig.data:
        if 'textfont' in trace:
            font(trace.textfont, 14)
            if 'shadow' in trace.textfont:
                trace.textfont.shadow = '0px 0px 2px #ffffff, 0px 0px 2px #ffffff'
        for field in ['insidetextfont', 'outsidetextfont']:
            if field in trace:
                font(trace[field], 14)
        if 'hoverlabel' in trace:
            trace.hoverlabel.update(bgcolor='#ffffff', font=dict(color=TEXT_COLOR, family=FONT_FAMILY, size=15))
        if trace.type == 'bar' and (trace.text is not None or trace.texttemplate):
            trace.update(textposition='outside', cliponaxis=False)
        labels_on_fill = trace.type in {'pie', 'treemap', 'sunburst', 'icicle', 'funnelarea'} or (trace.type == 'heatmap' and bool(trace.texttemplate))
        if labels_on_fill:
            inside_fills = True
            if 'marker' in trace and 'colors' in trace.marker:
                if trace.marker.colors is not None:
                    trace.marker.colors = [light_label_background(color) for color in trace.marker.colors]
            if 'colorscale' in trace and not trace.coloraxis:
                trace.colorscale = [(position, light_label_background(color)) for position, color in (trace.colorscale or default_scale)]
        if 'colorbar' in trace:
            font(trace.colorbar.tickfont, 14)
            font(trace.colorbar.title.font, 16)
        if 'marker' in trace and 'colorbar' in trace.marker and (trace.marker.showscale or trace.marker.colorbar.to_plotly_json()):
            font(trace.marker.colorbar.tickfont, 14)
            font(trace.marker.colorbar.title.font, 16)
    if inside_fills:
        fig.layout.colorway = [light_label_background(color) for color in (fig.layout.colorway or px.colors.qualitative.Plotly)]
    for name in layout_names:
        if re.fullmatch(r'coloraxis\d*', name):
            axis = fig.layout[name]
            font(axis.colorbar.tickfont, 14)
            font(axis.colorbar.title.font, 16)
            if inside_fills:
                axis.colorscale = [(position, light_label_background(color)) for position, color in (axis.colorscale or default_scale)]
    return fig


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
    legible_figure(fig)
    kwargs.setdefault('theme', None)
    return st.plotly_chart(fig, config=selected_export_config(fig, filename=filename, config=config), **kwargs)


def figure_download_settings():
    with st.expander('Figure downloads'):
        st.selectbox('Download format', FORMATS, key=FORMAT_KEY)
        st.caption('Use each chart’s camera icon. PNG exports use up to 3× resolution '
                   '(typically 4,800 × 2,700 pixels); SVG scales without losing sharpness. '
                   'Network SVG buttons preserve your current layout. Very tall PNGs are '
                   'bounded to browser canvas limits; SVG keeps the full scalable figure.')
