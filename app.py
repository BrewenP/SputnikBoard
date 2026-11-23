from collections import Counter

import plotly.graph_objects as go
from dash import Dash, Input, Output, ctx, dcc, html

import theme
from donnees import AFRICA, NAME, articles, proportion

ISSUES = 'https://github.com/BrewenP/SputnikBoard/issues/'

ONGLETS = {
    'evolution': ('Évolution', [
        ('Évolution de termes dans le temps', "Quels sujets et quels acteurs dominent l'actualité, mois après mois ?", 3, True),
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


EVOLUTION_TERME_OPTIONS = [
    {'label': 'Poutine (personne)', 'value': 'personnes|Poutine'},
    {'label': 'Trump (personne)', 'value': 'personnes|Trump'},
    {'label': 'Zelensky (personne)', 'value': 'personnes|Zelensky'},
    {'label': 'Macron (personne)', 'value': 'personnes|Macron'},
    {'label': 'Lavrov (personne)', 'value': 'personnes|Lavrov'},
    {'label': 'Russie (mot-clé)', 'value': 'mots|russie'},
    {'label': 'Ukraine (mot-clé)', 'value': 'mots|ukraine'},
    {'label': 'Afrique (mot-clé)', 'value': 'mots|afrique'},
    {'label': 'Trump (mot-clé)', 'value': 'mots|trump'},
    {'label': 'Poutine (mot-clé)', 'value': 'mots|poutine'},
    {'label': 'militaire (mot-clé)', 'value': 'mots|militaire'},
    {'label': 'gaza (mot-clé)', 'value': 'mots|gaza'},
]

EVOLUTION_TERME_DEFAUT = [
    'personnes|Poutine',
    'personnes|Trump',
    'mots|russie',
    'mots|ukraine',
]

EVENEMENTS = [
    ('2025-02', 'Début des pourparlers Russie-États-Unis à Riyad'),
    ('2025-06', 'Guerre Israël-Iran'),
    ('2025-08', 'Sommet Trump-Poutine en Alaska'),
]


def evolution_termes(periode, selection):
    sel = filtrer(periode)
    mois_selectionnes = [m for m in MOIS if periode[0] <= m <= periode[1]]
    fig = go.Figure()

    for valeur in selection or EVOLUTION_TERME_DEFAUT:
        colonne, terme = valeur.split('|', 1)
        serie = proportion(sel, colonne, [terme], par='mois').reindex(mois_selectionnes)
        label = next(
            (o['label'].replace(' (personne)', '').replace(' (mot-clé)', '')
             for o in EVOLUTION_TERME_OPTIONS if o['value'] == valeur),
            terme,
        )
        y = serie[terme].fillna(0).values
        fig.add_trace(go.Scatter(
            x=[libelle(m) for m in mois_selectionnes],
            y=y,
            mode='lines+markers',
            name=label,
            customdata=[libelle(m, LONGS) for m in mois_selectionnes],
            text=[label] * len(mois_selectionnes),
            hovertemplate='<b>%{customdata}</b><br>Terme : %{text}<br>Part : %{y:.1%}<extra></extra>',
        ))

    for mois, texte in EVENEMENTS:
        if periode[0] <= mois <= periode[1]:
            fig.add_vline(
                x=libelle(mois),
                line_width=1,
                line_dash='dot',
                line_color=theme.AXIS,
            )
            fig.add_annotation(
                x=libelle(mois),
                y=1.04,
                yref='paper',
                text=texte,
                showarrow=False,
                yanchor='bottom',
                bgcolor='rgba(255,255,255,0.92)',
                bordercolor=theme.GRID,
                font=dict(size=11, color=theme.INK_2),
            )

    fig.update_layout(
        height=440,
        margin=dict(l=8, r=8, t=62, b=8),
        hovermode='x unified',
        yaxis=dict(tickformat='.0%', rangemode='tozero', title='Part des articles'),
        xaxis=dict(tickmode='array', tickvals=[libelle(m) for m in mois_selectionnes[::3]], title=None),
        legend=dict(orientation='h', y=1.12, yanchor='bottom', x=0),
    )
    return fig


def carte(titre, question, ticket, large):
    if ticket == 3:
        return html.Div(className='panel wide evolution-panel', children=[
            html.H2(titre),
            html.P(question, className='question'),
            html.Div(className='termes-controles', children=[
                html.Div('Termes affichés', className='label'),
                dcc.Dropdown(
                    id='termes-evolution',
                    options=EVOLUTION_TERME_OPTIONS,
                    value=EVOLUTION_TERME_DEFAUT,
                    multi=True,
                    clearable=False,
                    placeholder='Sélectionner des termes',
                ),
            ]),
            dcc.Graph(id='evolution-graphique', config={'displayModeBar': False}),
        ])
    return html.Div(className='panel wide' if large else 'panel', children=[
        html.H2(titre),
        html.P(question, className='question'),
        html.Div(className='placeholder', children=[
            html.Span('Graphique à venir'),
            html.A(f'Ticket #{ticket}', href=f'{ISSUES}{ticket}', target='_blank'),
        ]),
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


@app.callback(
    Output('evolution-graphique', 'figure'),
    Input('periode', 'data'),
    Input('termes-evolution', 'value'),
)
def mettre_a_jour_evolution(periode, selection):
    return evolution_termes(periode, selection)


if __name__ == '__main__':
    app.run(debug=True)
