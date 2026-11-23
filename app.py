from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import prince
from dash import Dash, Input, Output, ctx, dcc, html

import theme
from donnees import AFRICA, NAME, articles

ISSUES = 'https://github.com/BrewenP/SputnikBoard/issues/'

ONGLETS = {
    'evolution': ('Évolution', [
        ('Évolution de termes dans le temps', "Quels sujets et quels acteurs dominent l'actualité, semaine après semaine ?", 3, True),
    ]),
    'vocabulaire': ('Vocabulaire', [
        ('Mots émergents', 'Quels mots surgissent puis disparaissent ?', 4, False),
        ('Analyse des correspondances', 'Comment le vocabulaire distingue-t-il les périodes ?', 7, True, 'afc-graphique'),
    ]),
    'carte': ('Carte', [
        ('Pays cités', 'Quelles régions le média couvre-t-il, et à quel moment ?', 5, True),
    ]),
    'acteurs': ('Acteurs', [
        ('Réseau des personnes', 'Qui est cité avec qui ?', 6, True),
    ]),
    'themes': ('Thèmes', [
        ('Carte des articles', 'Quels grands thèmes structurent le corpus ?', 8, False),
        ('Évolution des thèmes', 'Quelle place prend chaque thème au fil des mois ?', 8, False),
    ]),
    'france-russie': ('France / Russie', [
        ('Discours comparés', 'Avec quels mots parle-t-on de la France et de la Russie ?', 9, True),
    ]),
}

df = articles('fr')
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


AFC_FREQUENTS = 200  # mots clés les plus fréquents de la période, gardés pour le tableau de contingence
AFC_AFFICHES = 30  # mots qui contribuent le plus aux deux axes, affichés sur le graphique


@app.callback(Output('afc-graphique', 'figure'), Input('periode', 'data'))
def afc(periode):
    sel = filtrer(periode)
    fig = go.Figure()
    fig.update_layout(height=600)
    if sel['mois'].nunique() < 3:
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), annotations=[dict(
            text="Choisir au moins 3 mois pour l'analyse des correspondances.", showarrow=False,
            xref='paper', yref='paper', x=0.5, y=0.5, font=dict(color=theme.MUTED))])
        return fig

    # Tableau de contingence : nombre d'articles de chaque mois qui contiennent chaque mot clé fréquent.
    paires = pd.DataFrame([(m, w) for m, mots in zip(sel['mois'], sel['mots']) for w in mots], columns=['mois', 'mot'])
    frequents = paires['mot'].value_counts().index[:AFC_FREQUENTS]
    paires = paires[paires['mot'].isin(frequents)]
    tableau = pd.crosstab(paires['mot'], paires['mois'])

    ca = prince.CA(n_components=2, random_state=0).fit(tableau)
    mots, mois = ca.row_coordinates(tableau), ca.column_coordinates(tableau)
    # Carte asymétrique : les mois en coordonnées standard (divisées par la racine de la valeur propre)
    # s'écartent du centre, et chaque mot se place au barycentre des mois où il apparaît le plus.
    mois = mois / ca.eigenvalues_ ** 0.5
    inertie = ca.percentage_of_variance_
    # Mots les plus variables dans le temps : ceux qui contribuent le plus à la construction des deux axes.
    contribution = ca.row_contributions_[0] * inertie[0] + ca.row_contributions_[1] * inertie[1]
    mots = mots.loc[contribution.nlargest(AFC_AFFICHES).index]
    # Les mots trop proches du centre se chevauchent : ils gardent leur point, avec le nom au survol seulement.
    distance = (mots[0] ** 2 + mots[1] ** 2) ** 0.5
    etiquettes = [m if d >= distance.quantile(0.35) else '' for m, d in zip(mots.index, distance)]

    fig.add_trace(go.Scatter(
        x=mots[0], y=mots[1], mode='markers+text', name='Mots clés', text=etiquettes, textposition='top center',
        marker=dict(color=theme.SERIES[1], size=6), textfont=dict(color=theme.SERIES[1], size=12),
        customdata=list(zip(mots.index, tableau.loc[mots.index].sum(axis=1))),
        hovertemplate='<b>%{customdata[0]}</b><br>dans %{customdata[1]} articles<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=mois[0], y=mois[1], mode='lines+markers+text', name='Mois (dans l’ordre)',
        text=[libelle(m) for m in mois.index], textposition='bottom center',
        line=dict(color=theme.SERIES[0], width=1.5), marker=dict(color=theme.SERIES[0], size=8),
        textfont=dict(color=theme.SERIES[0], size=11), customdata=[libelle(m, LONGS) for m in mois.index],
        hovertemplate='<b>%{customdata}</b><extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(title=f'Axe 1 ({pourcent(inertie[0] / 100)} de l’inertie)', zeroline=True, zerolinecolor=theme.AXIS),
        yaxis=dict(title=f'Axe 2 ({pourcent(inertie[1] / 100)} de l’inertie)', zeroline=True, zerolinecolor=theme.AXIS),
    )
    return fig


if __name__ == '__main__':
    app.run(debug=True)
