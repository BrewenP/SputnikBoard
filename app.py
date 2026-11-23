import math
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, ctx, dcc, html

import theme
from donnees import AFRICA, COUNTRIES, NAME, articles, proportion, surrepresentation
from themes import themes

ISSUES = 'https://github.com/BrewenP/SputnikBoard/issues/'

ONGLETS = {
    'evolution': ('Évolution', [
        ('Évolution de termes dans le temps', "Quels sujets et quels acteurs dominent l'actualité, semaine après semaine ?", 3, True),
    ]),
    'vocabulaire': ('Vocabulaire', [
        ('Mots émergents', 'Quels mots surgissent puis disparaissent ?', 4, False),
        ('Analyse des correspondances', 'Comment le vocabulaire distingue-t-il les périodes ?', 7, False),
    ]),
    'carte': ('Carte', [
        ('Pays cités', 'Quelles régions le média couvre-t-il, et à quel moment ?', 5, True),
    ]),
    'acteurs': ('Acteurs', [
        ('Réseau des personnes', 'Qui est cité avec qui ?', 6, True),
    ]),
    'themes': ('Thèmes', [
        ('Carte des articles', 'Quels grands thèmes structurent le corpus ?', 8, True),
        ('Évolution des thèmes', 'Quelle place prend chaque thème au fil des mois ?', 8, True),
    ]),
    'france-russie': ('France / Russie', [
        ('Discours comparés', 'Avec quels mots parle-t-on de la France et de la Russie ?', 9, True),
    ]),
}

THEMES = themes('fr')
df = articles('fr').assign(theme=THEMES['theme'])
macron, poutine = articles('macron'), articles('poutine')
MOIS = sorted(df['mois'].unique())
COURTS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
LONGS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre',
         'novembre', 'décembre']
PRESETS = {
    'tout': ('Toute la période', 0),
    'collecte': ('Depuis avril 2025', MOIS.index('2025-04')),
    'recent': ('3 derniers mois', len(MOIS) - 3),
}


def nombre(n):
    return f'{n:,}'.replace(',', ' ')


def pourcent(x):
    return f'{x:.0%}'.replace('%', ' %')


def libelle(mois, noms=COURTS):
    annee, m = mois.split('-')
    return f'{noms[int(m) - 1]} {annee if noms is LONGS else annee[2:]}'


def filtrer(periode):
    return df[df['mois'].between(*periode)]


def kpi(valeur, nom, detail):
    return html.Div(className='kpi', children=[
        html.Div(valeur, className='value' if valeur[0].isdigit() else 'value texte'),
        html.Div(nom, className='name'),
        html.Div(detail, className='detail'),
    ])


def volume(periode):
    n = df.groupby('mois').size()
    x = [libelle(m) for m in n.index]
    fig = go.Figure(go.Bar(
        x=x, y=n.values,
        marker_color=[theme.ACCENT if periode[0] <= m <= periode[1] else theme.GRID for m in n.index],
        customdata=[libelle(m, LONGS) for m in n.index],
        hovertemplate='%{customdata}<br><b>%{y}</b> articles<extra></extra>',
    ))
    fig.add_annotation(
        x=libelle('2025-04'), y=n['2025-04'], text='Changement de collecte', showarrow=True, arrowhead=0,
        ax=-16, ay=-24, xanchor='right', arrowcolor=theme.AXIS, font=dict(size=11, color=theme.INK_2),
    )
    fig.update_layout(
        height=196, margin=dict(l=0, r=0, t=8, b=0),
        xaxis=dict(tickmode='array', tickvals=x[::3], showline=False),
        yaxis=dict(nticks=3, showline=False),
    )
    return fig


# mode -> (libellé du bouton, colonne de `articles`, fréquence cumulée minimale, unité des fréquences)
MODES = {
    'mots': ('Mots clés', 'mots', 20, 'occurrences'),
    'personnes': ('Personnes', 'personnes', 8, 'articles'),
}
FRANCE = ('France / Macron', theme.DIVERGING[1])
RUSSIE = ('Russie / Poutine', theme.DIVERGING[5])
TOP = 15


def decimal(x, signe=False):
    return f'{x:+.2f}'.replace('.', ',') if signe else f'{x:.2f}'.replace('.', ',')


def discours(periode, mode):
    _, colonne, minimum, unite = MODES[mode]
    fr, ru = (d[d['mois'].between(*periode)] for d in (macron, poutine))
    s = surrepresentation(ru, fr, colonne, minimum)  # score > 0 : côté Russie, score < 0 : côté France
    cotes = {
        FRANCE: s[s['score'] < 0].tail(TOP).iloc[::-1],
        RUSSIE: s[s['score'] > 0].head(TOP),
    }
    fig = go.Figure()
    for (nom, couleur), d in cotes.items():
        fig.add_bar(
            x=d['score'], y=list(range(len(d))), orientation='h', name=nom, marker_color=couleur,
            text=d['terme'], textposition='outside', cliponaxis=False,
            customdata=[(t, decimal(abs(sc)), f'{math.exp(abs(sc)):.1f}'.replace('.', ','), nombre(a), nombre(b))
                        for t, sc, a, b in zip(d['terme'], d['score'], d['freq_b'], d['freq_a'])],
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                'Score : %{customdata[1]} (cote ×%{customdata[2]} par rapport à l\'autre corpus)<br>'
                f'{FRANCE[0]} : %{{customdata[3]}} {unite}<br>'
                f'{RUSSIE[0]} : %{{customdata[4]}} {unite}<extra></extra>'
            ),
        )
    if s.empty:
        fig.add_annotation(text='Pas assez de données sur cette période', showarrow=False, font=dict(color=theme.MUTED))
    bord = max(s['score'].abs().max() if not s.empty else 1, 1)
    graduations = list(range(-math.ceil(bord), math.ceil(bord) + 1))
    fig.add_vline(x=0, line_color=theme.AXIS)
    fig.update_layout(
        barmode='overlay', height=max(TOP, *(len(d) for d in cotes.values())) * 30 + 130,
        xaxis=dict(
            range=[-bord * 1.35, bord * 1.35], tickvals=graduations, ticktext=[str(abs(g)) for g in graduations],
            showgrid=True, title='Score de surreprésentation (logarithme du rapport de cotes)',
        ),
        yaxis=dict(autorange='reversed', showticklabels=False, showgrid=False, showline=False),
    )
    return fig


VUES = {'afrique': 'Afrique', 'monde': 'Monde'}


def part(x):
    return f'{x * 100:.1f}'.replace('.', ',') + ' %'


def carte_pays(periode, vue):
    sel = filtrer(periode)
    codes = sorted(AFRICA if vue == 'afrique' else COUNTRIES)
    parts = proportion(sel, 'pays', codes)
    n_articles = sel.groupby('mois').size()
    mois = list(parts.index)
    zmax = max(float(parts.to_numpy().max()), 0.01)  # même échelle pour toutes les images

    def trace(m):
        z = parts.loc[m]
        return go.Choropleth(
            locations=codes, z=z.values, locationmode='ISO-3', zmin=0, zmax=zmax,
            colorscale=theme.SEQUENTIAL, marker_line_width=0.5, marker_line_color=theme.AXIS,
            colorbar=dict(title='Part des articles', tickformat='.0%', thickness=12, len=0.7, outlinewidth=0),
            customdata=[(NAME[c], part(v), nombre(round(v * n_articles[m]))) for c, v in z.items()],
            hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]} des articles du mois '
                          '(%{customdata[2]} articles)<extra></extra>',
        )

    cadre = dict(duration=700, redraw=True)
    fig = go.Figure(
        data=trace(mois[0]),
        frames=[go.Frame(data=[trace(m)], name=m) for m in mois],
    )
    fig.update_geos(scope='africa' if vue == 'afrique' else 'world', projection_type='natural earth')
    if vue == 'monde':  # cadrage explicite : sinon la carte garde le décalage de la vue Afrique
        fig.update_geos(lonaxis_range=[-180, 180], lataxis_range=[-58, 85], projection_rotation_lon=0)
    fig.update_layout(
        height=560, margin=dict(l=0, r=0, t=8, b=0), dragmode=False, uirevision=vue,
        updatemenus=[dict(
            type='buttons', direction='left', x=0, y=0, xanchor='left', yanchor='top', pad=dict(t=30, l=4),
            buttons=[
                dict(label='▶ Lecture', method='animate',
                     args=[None, dict(frame=cadre, transition=dict(duration=0), fromcurrent=True)]),
                dict(label='❚❚ Pause', method='animate',
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate',
                                        transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            x=0.2, y=0, len=0.8, xanchor='left', yanchor='top', pad=dict(t=30, b=0),
            currentvalue=dict(prefix='Mois : ', font=dict(size=13, color=theme.INK_2)),
            font=dict(size=10, color=theme.MUTED),
            steps=[dict(label=libelle(m), method='animate',
                        args=[[m], dict(mode='immediate', frame=dict(duration=0, redraw=True),
                                        transition=dict(duration=0))]) for m in mois],
        )],
    )
    return fig


CONTENUS = {
    5: [
        dcc.RadioItems(
            id='carte-vue', value='afrique', inline=True, className='bascule',
            options=[{'label': nom, 'value': vue} for vue, nom in VUES.items()],
        ),
        dcc.Graph(id='carte-graphique', config={'displayModeBar': False}),
    ],
    9: [
        dcc.RadioItems(
            id='discours-mode', value='mots', inline=True, className='bascule',
            options=[{'label': libelle_, 'value': mode} for mode, (libelle_, *_) in MODES.items()],
        ),
        dcc.Graph(id='discours-graphique', config={'displayModeBar': False}),
    ],
    'Carte des articles': [dcc.Graph(id='themes-carte', config={'displayModeBar': False})],
    'Évolution des thèmes': [dcc.Graph(id='themes-evolution', config={'displayModeBar': False})],
}


def carte(titre, question, ticket, large):
    return html.Div(className='panel wide' if large else 'panel', children=[
        html.H2(titre),
        html.P(question, className='question'),
        *CONTENUS.get(titre, CONTENUS.get(ticket, [html.Div(className='placeholder', children=[
            html.Span('Graphique à venir'),
            html.A(f'Ticket #{ticket}', href=f'{ISSUES}{ticket}', target='_blank'),
        ])])),
    ])


app = Dash(__name__, title='SputnikBoard', external_stylesheets=[
    'https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400..800&display=swap',
])

app.layout = html.Div([
    html.Header(className='bande', children=html.Div(className='bande-contenu', children=[
        html.Div(className='entete', children=[
            html.Div(className='marque', children=[
                html.Span(className='planete'), html.Span(className='orbite'), html.Span(className='satellite'),
            ]),
            html.Div([
                html.H1('SputnikBoard'),
                html.P(f"Ce que Sputnik Afrique raconte de la Russie, de la France et de l'Afrique : "
                       f"{nombre(len(df))} articles publiés entre avril 2024 et octobre 2025."),
            ]),
            html.Div(className='source', children=['Source : fr.sputniknews.africa', html.Br(), 'Projet DATA732']),
        ]),
        html.Div(className='filters', children=[
            html.Div([html.Div('Période', className='label'), html.Div(id='periode-texte', className='periode')]),
            html.Div(className='presets', children=[
                html.Button(texte, id=f'preset-{key}', className='preset') for key, (texte, _) in PRESETS.items()
            ]),
            html.Div(className='slider', children=dcc.RangeSlider(
                id='curseur', min=0, max=len(MOIS) - 1, step=1, value=[0, len(MOIS) - 1], allowCross=False, allow_direct_input=False,
                marks={i: libelle(m) for i, m in enumerate(MOIS) if i % 3 == 0 or i == len(MOIS) - 1},
            )),
        ]),
    ])),
    html.Main(className='page', children=[
        dcc.Store(id='periode'),
        html.Div(id='indicateurs', className='overview'),
        dcc.Tabs(id='onglet', value='evolution', className='tabs', mobile_breakpoint=0, children=[
            dcc.Tab(label=label, value=key, className='tab', selected_className='tab--selected', children=[
                html.Div(className='grid', children=[carte(*c) for c in cartes]),
            ])
            for key, (label, cartes) in ONGLETS.items()
        ]),
    ]),
])

@app.callback(
    Output('curseur', 'value'),
    [Input(f'preset-{key}', 'n_clicks') for key in PRESETS],
    prevent_initial_call=True,
)
def appliquer_preset(*_):
    return [PRESETS[ctx.triggered_id.removeprefix('preset-')][1], len(MOIS) - 1]


@app.callback(Output('periode', 'data'), Output('periode-texte', 'children'), Input('curseur', 'value'))
def choisir_periode(valeur):
    debut, fin = MOIS[valeur[0]], MOIS[valeur[1]]
    return [debut, fin], f'{libelle(debut, LONGS)} – {libelle(fin, LONGS)}'


@app.callback(Output('indicateurs', 'children'), Input('periode', 'data'))
def indicateurs(periode):
    sel = filtrer(periode)
    personnes = Counter(p for s in sel['personnes'] for p in s)
    pays, n_pays = Counter(p for s in sel['pays'] for p in s & AFRICA).most_common(1)[0]
    afrique = sel['pays'].map(lambda s: bool(s & AFRICA)).mean()
    mois = sel['mois'].nunique()
    return [
        html.Div(className='panel chiffres', key='-'.join(periode), children=[
            kpi(nombre(len(sel)), 'articles', f'{nombre(round(len(sel) / mois))} par mois en moyenne'),
            kpi(nombre(len(personnes)), 'personnes citées', f'la plus citée : {personnes.most_common(1)[0][0]}'),
            kpi(pourcent(afrique), "parlent d'un pays africain", 'au moins un pays africain cité'),
            kpi(NAME[pays], 'pays africain le plus cité', f'dans {pourcent(n_pays / len(sel))} des articles'),
        ]),
        html.Div(className='panel volume', children=[
            html.Div('Articles par mois', className='name'),
            dcc.Graph(figure=volume(periode), config={'displayModeBar': False}),
        ]),
    ]


@app.callback(Output('discours-graphique', 'figure'), Input('periode', 'data'), Input('discours-mode', 'value'))
def comparer_discours(periode, mode):
    return discours(periode, mode)


@app.callback(Output('carte-graphique', 'figure'), Input('periode', 'data'), Input('carte-vue', 'value'))
def cartographier(periode, vue):
    return carte_pays(periode, vue)


def nom_theme(t):
    return THEMES['noms'][t].capitalize()


def note_themes():
    s, k = THEMES['silhouettes'], THEMES['k']
    if k == max(s):
        raison = f'la silhouette croît avec le nombre de thèmes, plafonné à {k} pour garder des couleurs distinctes'
    else:
        raison = f'meilleure silhouette entre {min(s)} et {max(s)} thèmes'
    return f"{k} thèmes : {raison} (silhouette {s[k]:.2f})".replace('.', ',')


@app.callback(Output('themes-carte', 'figure'), Input('periode', 'data'))
def carte_themes(periode):
    dans = df['mois'].between(*periode).to_numpy()
    fig = go.Figure(go.Scattergl(
        x=THEMES['x'][~dans], y=THEMES['y'][~dans], mode='markers', name='Hors période',
        marker=dict(color=theme.GRID, size=4), hoverinfo='skip', showlegend=False,
    ))
    for t in range(THEMES['k']):
        choix = dans & (df['theme'] == t).to_numpy()
        sel = df[choix]
        fig.add_trace(go.Scattergl(
            x=THEMES['x'][choix], y=THEMES['y'][choix], mode='markers', name=nom_theme(t),
            marker=dict(color=theme.SERIES[t], size=4, opacity=0.7),
            customdata=list(zip(sel['titre'], sel['date'].dt.strftime('%d/%m/%Y'))),
            hovertemplate=f'<b>%{{customdata[0]}}</b><br>%{{customdata[1]}}<br>Thème : {nom_theme(t)}<extra></extra>',
        ))
    fig.update_layout(
        height=560, legend=dict(orientation='v', x=1.02, y=1, yanchor='top', traceorder='normal', itemsizing='constant'),
        xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor='x'),
        annotations=[dict(text=note_themes(), xref='paper', yref='paper', x=0, y=0, showarrow=False,
                          xanchor='left', yanchor='bottom', font=dict(size=11, color=theme.MUTED))],
    )
    return fig


@app.callback(Output('themes-evolution', 'figure'), Input('periode', 'data'))
def evolution_themes(periode):
    sel = filtrer(periode)
    parts = pd.crosstab(sel['mois'], sel['theme'], normalize='index').reindex(columns=range(THEMES['k']), fill_value=0)
    x = [libelle(m) for m in parts.index]
    fig = go.Figure()
    for t in parts.columns:
        fig.add_trace(go.Scatter(
            x=x, y=parts[t], name=nom_theme(t), stackgroup='un', mode='lines',
            line=dict(width=0.5, color=theme.SERIES[t]),
            hovertemplate=f'{nom_theme(t)} : <b>%{{y:.0%}}</b><extra></extra>',
        ))
    fig.update_layout(height=420, legend=dict(orientation='v', x=1.02, y=1, yanchor='top', traceorder='reversed', itemsizing='constant'),
                      xaxis=dict(tickmode='array', tickvals=x[::3], tickangle=0),
                      yaxis=dict(tickformat='.0%', range=[0, 1]), hovermode='x unified')
    return fig


if __name__ == '__main__':
    app.run(debug=True)