import plotly.graph_objects as go
import plotly.io as pio

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

SURFACE = '#fcfcfb'
PAGE = '#f9f9f7'
INK = '#0b0b0b'
INK_2 = '#52514e'
MUTED = '#898781'
GRID = '#e1e0d9'
AXIS = '#c3c2b7'

SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
SEQUENTIAL = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
DIVERGING = ['#184f95', '#3987e5', '#9ec5f4', '#f0efec', '#f2a7a6', '#e34948', '#a82b2b']

axis = dict(
    showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
    showline=True, linecolor=AXIS, ticks='', tickfont=dict(color=MUTED, size=12),
    title=dict(font=dict(color=INK_2, size=13)), automargin=True,
)

pio.templates['pressboard'] = go.layout.Template(layout=dict(
    font=dict(family=FONT, color=INK, size=13),
    separators=', ',
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    colorway=SERIES,
    colorscale=dict(sequential=SEQUENTIAL, diverging=DIVERGING),
    title=dict(font=dict(size=16, color=INK), x=0, xanchor='left', pad=dict(l=4)),
    xaxis=dict(axis, showgrid=False),
    yaxis=axis,
    legend=dict(orientation='h', y=1.02, yanchor='bottom', x=0, title=None, font=dict(color=INK_2)),
    hoverlabel=dict(bgcolor='white', bordercolor=GRID, font=dict(family=FONT, color=INK, size=13)),
    margin=dict(l=8, r=8, t=48, b=8),
    bargap=0.25, barcornerradius=4,
))
pio.templates.default = 'pressboard'
