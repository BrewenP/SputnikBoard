from collections import Counter

import plotly.graph_objects as go
from dash import Dash, Input, Output, ctx, dcc, html

import theme
from donnees import AFRICA, NAME, articles

ISSUES = 'https://github.com/BrewenP/PressBoard/issues/'

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
    return html.Div(className='card kpi', children=[
        html.Div(valeur, className='value' if valeur[0].isdigit() else 'value texte'),
        html.Div(nom, className='name'),
        html.Div(detail, className='detail'),
    ])


def volume(periode):
    n = df.groupby('mois').size()
    x = [libelle(m) for m in n.index]
    fig = go.Figure(go.Bar(
        x=x, y=n.values,
        marker_color=[theme.SERIES[0] if periode[0] <= m <= periode[1] else theme.GRID for m in n.index],
        customdata=[libelle(m, LONGS) for m in n.index],
        hovertemplate='%{customdata}<br><b>%{y}</b> articles<extra></extra>',
    ))
    fig.add_annotation(
        x=libelle('2025-04'), y=n['2025-04'], text='Changement de collecte', showarrow=True, arrowhead=0,
        ax=-16, ay=-24, xanchor='right', arrowcolor=theme.AXIS, font=dict(size=11, color=theme.INK_2),
    )
    fig.update_layout(
        height=150, margin=dict(l=0, r=0, t=8, b=0),
        xaxis=dict(tickmode='array', tickvals=x[::3], showline=False),
        yaxis=dict(nticks=3, showline=False),
    )
    return fig


def carte(titre, question, ticket, large):
    return html.Div(className='card wide' if large else 'card', children=[
        html.H2(titre),
        html.P(question, className='question'),
        html.Div(className='placeholder', children=[
            html.Span('Graphique à venir'),
            html.A(f'Ticket #{ticket}', href=f'{ISSUES}{ticket}', target='_blank'),
        ]),
    ])


app = Dash(__name__, title='PressBoard')

app.layout = html.Div(className='page', children=[
    html.Header(className='header', children=[
        html.Div([
            html.H1('PressBoard'),
            html.P(f"Ce que Sputnik Afrique raconte de la Russie, de la France et de l'Afrique : "
                   f"{nombre(len(df))} articles publiés entre avril 2024 et octobre 2025."),
        ]),
        html.Div(className='source', children=['Source : fr.sputniknews.africa', html.Br(), 'Projet DATA732']),
    ]),
    html.Div(className='card filters', children=[
        html.Div([html.Div('Période', className='label'), html.Div(id='periode-texte', className='periode')]),
        html.Div(className='presets', children=[
            html.Button(texte, id=f'preset-{key}', className='preset') for key, (texte, _) in PRESETS.items()
        ]),
        html.Div(className='slider', children=dcc.RangeSlider(
            id='curseur', min=0, max=len(MOIS) - 1, step=1, value=[0, len(MOIS) - 1], allowCross=False, allow_direct_input=False,
            marks={i: libelle(m) for i, m in enumerate(MOIS) if i % 3 == 0 or i == len(MOIS) - 1},
        )),
    ]),
    dcc.Store(id='periode'),
    html.Div(id='indicateurs', className='overview'),
    dcc.Tabs(id='onglet', value='evolution', className='tabs', mobile_breakpoint=0, children=[
        dcc.Tab(label=label, value=key, className='tab', selected_className='tab--selected', children=[
            html.Div(className='grid', children=[carte(*c) for c in cartes]),
        ])
        for key, (label, cartes) in ONGLETS.items()
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
        kpi(nombre(len(sel)), 'articles', f'{nombre(round(len(sel) / mois))} par mois en moyenne'),
        kpi(nombre(len(personnes)), 'personnes citées', f'la plus citée : {personnes.most_common(1)[0][0]}'),
        kpi(pourcent(afrique), "parlent d'un pays africain", 'au moins un pays africain cité'),
        kpi(NAME[pays], 'pays africain le plus cité', f'dans {pourcent(n_pays / len(sel))} des articles'),
        html.Div(className='card volume', children=[
            html.Div('Articles par mois', className='name'),
            dcc.Graph(figure=volume(periode), config={'displayModeBar': False}),
        ]),
    ]


if __name__ == '__main__':
    app.run(debug=True)
