from collections import Counter

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, ctx, dcc, html

import theme
from donnees import AFRICA, NAME, articles
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
        ('Carte des articles', 'Quels grands thèmes structurent le corpus ?', 8, True, 'themes-carte'),
        ('Évolution des thèmes', 'Quelle place prend chaque thème au fil des mois ?', 8, True, 'themes-evolution'),
    ]),
    'france-russie': ('France / Russie', [
        ('Discours comparés', 'Avec quels mots parle-t-on de la France et de la Russie ?', 9, True),
    ]),
}

df = articles('fr')
THEMES = themes('fr')
df['theme'] = THEMES['theme']
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


def carte(titre, question, ticket, large, graphe=None):
    contenu = dcc.Graph(id=graphe, config={'displayModeBar': False}) if graphe else html.Div(
        className='placeholder', children=[
            html.Span('Graphique à venir'),
            html.A(f'Ticket #{ticket}', href=f'{ISSUES}{ticket}', target='_blank'),
        ])
    return html.Div(className='panel wide' if large else 'panel', children=[
        html.H2(titre),
        html.P(question, className='question'),
        contenu,
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


def nom_theme(t):
    return THEMES['noms'][t].capitalize()


def note_themes():
    return (f"{THEMES['k']} thèmes, nombre choisi par le meilleur score de silhouette entre "
            f"{min(THEMES['silhouettes'])} et {max(THEMES['silhouettes'])}")


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
                      yaxis=dict(tickformat='.0%', range=[0, 1]), hovermode='x unified')
    return fig


if __name__ == '__main__':
    app.run(debug=True)
