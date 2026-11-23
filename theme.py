import plotly.graph_objects as go
import plotly.io as pio

FONT = '"Schibsted Grotesk", system-ui, sans-serif'

SURFACE = '#ffffff'
PAGE = '#f2f2f0'
INK = '#1d1e21'
INK_2 = '#505257'
MUTED = '#6f7178'
GRID = '#e3e3e0'
AXIS = '#c4c4c0'
ACCENT = '#ff6a13'

SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
SEQUENTIAL = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
DIVERGING = ['#184f95', '#3987e5', '#9ec5f4', '#f0efec', '#f2a7a6', '#e34948', '#a82b2b']
DIVERGING_SIGNAL = [
    [0, '#184f95'], [0.12, '#3987e5'], [0.3, '#9ec5f4'], [0.5, '#ecebe7'],
    [0.66, '#ffd2b5'], [0.82, '#ff965a'], [0.92, ACCENT], [1, '#c94a06'],
]

axis = dict(
    showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
    showline=True, linecolor=AXIS, ticks='', tickfont=dict(color=MUTED, size=12),
    title=dict(font=dict(color=INK_2, size=13)), automargin=True,
)

pio.templates['sputnikboard'] = go.layout.Template(layout=dict(
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
    geo=dict(
        bgcolor=SURFACE, showframe=False, showcoastlines=True, coastlinecolor=AXIS, coastlinewidth=0.5,
        showland=True, landcolor='#f4f4f2', showcountries=True, countrycolor=AXIS, countrywidth=0.5,
        showocean=False, showlakes=False,
    ),
))
pio.templates.default = 'sputnikboard'