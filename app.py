from collections import Counter
from itertools import combinations

import networkx as nx
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


def reseau_personnes(periode):
    sel = filtrer(periode)
    articles_personnes = Counter(p for personnes in sel['personnes'] for p in personnes)
    principaux = [nom for nom, _ in articles_personnes.most_common(35)]
    principaux_set = set(principaux)

    cooccurrences = Counter()
    for personnes in sel['personnes']:
        presentes = sorted(principaux_set & personnes)
        cooccurrences.update(combinations(presentes, 2))

    liens = []
    seuil = 1
    for seuil_candidat in (2, 3, 4, 5, 6, 8):
        candidats = [(a, b, poids) for (a, b), poids in cooccurrences.items() if poids >= seuil_candidat]
        if len(candidats) <= 75:
            seuil = seuil_candidat
            liens = candidats
            break
    if not liens:
        seuil = 1
        liens = [(a, b, poids) for (a, b), poids in cooccurrences.items() if poids >= seuil]

    graphe = nx.Graph()
    graphe.add_nodes_from(principaux)
    graphe.add_weighted_edges_from(liens)

    couleurs = [
        '#2a78d6', '#ff6a13', '#36a269', '#9854cc', '#d94f70',
        '#8a6b4f', '#168c92', '#d1a21f', '#627ac0', '#c45b2d',
    ]
    communautes = list(nx.community.greedy_modularity_communities(graphe, weight='weight', resolution=1))
    couleur_par_personne = {}
    for numero, groupe in enumerate(communautes):
        for personne in groupe:
            couleur_par_personne[personne] = couleurs[numero % len(couleurs)]

    position = nx.spring_layout(graphe, k=0.58, iterations=80, seed=42, weight='weight')
    max_articles = max((articles_personnes[nom] for nom in principaux), default=1)
    min_articles = min((articles_personnes[nom] for nom in principaux), default=1)
    max_poids = max((poids for _, _, poids in liens), default=1)

    fig = go.Figure()
    for a, b, poids in liens:
        x0, y0 = position[a]
        x1, y1 = position[b]
        intensite = poids / max_poids
        fig.add_trace(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=0.6 + 3.4 * intensite, color=f'rgba(128,132,140,{0.25 + 0.55 * intensite:.2f})'),
            hoverinfo='skip',
            showlegend=False,
        ))

    tailles = []
    for nom in principaux:
        if max_articles == min_articles:
            tailles.append(20)
        else:
            ratio = (articles_personnes[nom] - min_articles) / (max_articles - min_articles)
            tailles.append(12 + 24 * ratio)

    textes = []
    survol = []
    for nom in principaux:
        voisins = sorted(
            ((graphe[nom][voisin].get('weight', 0), voisin) for voisin in graphe.neighbors(nom)),
            reverse=True,
        )
        voisins_texte = '<br>'.join(f'{voisin} ({poids})' for poids, voisin in voisins[:5])
        textes.append(nom)
        survol.append(
            f'<b>{nom}</b><br>{nombre(articles_personnes[nom])} articles'
            + (f'<br><br>Principaux voisins :<br>{voisins_texte}' if voisins_texte else '')
        )

    fig.add_trace(go.Scatter(
        x=[position[nom][0] for nom in principaux],
        y=[position[nom][1] for nom in principaux],
        mode='markers+text',
        text=textes,
        textposition='top center',
        textfont=dict(size=11, color=theme.INK),
        marker=dict(
            size=tailles,
            color=[couleur_par_personne[nom] for nom in principaux],
            line=dict(width=1, color='rgba(255,255,255,0.9)'),
        ),
        customdata=survol,
        hovertemplate='%{customdata}<extra></extra>',
    ))

    fig.update_layout(
        height=620,
        margin=dict(l=12, r=12, t=12, b=12),
        hovermode='closest',
        dragmode='pan',
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[dict(
            text=f'Seuil de co-occurrence : {seuil} article{"s" if seuil > 1 else ""}',
            x=0,
            y=1,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='bottom',
            showarrow=False,
            font=dict(size=12, color=theme.MUTED),
        )],
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

    if not selection:
        fig.update_layout(
            height=440,
            margin=dict(l=8, r=8, t=62, b=8),
            xaxis=dict(
                tickmode='array',
                tickvals=[libelle(m) for m in mois_selectionnes[::3]],
                title=None,
            ),
            yaxis=dict(
                tickformat='.0%',
                range=[0, 1],
                dtick=0.05,
                title='Part des articles',
            ),
            annotations=[dict(
                text='Sélectionnez au moins un terme',
                xref='paper',
                yref='paper',
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color=theme.MUTED),
                bgcolor='rgba(255,255,255,0.92)',
            )],
        )
        return fig

    for valeur in selection or []:
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
                html.Div(className='termes-selection', children=[
                    dcc.Dropdown(
                        id='termes-evolution',
                        options=EVOLUTION_TERME_OPTIONS,
                        value=EVOLUTION_TERME_DEFAUT,
                        multi=True,
                        clearable=False,
                        placeholder='Sélectionner des termes',
                    ),
                    html.Button('Tout désélectionner', id='tout-deselectionner', className='termes-clear', n_clicks=0),
                ]),
            ]),
            dcc.Graph(id='evolution-graphique', config={'displayModeBar': False}),
        ])
    if ticket == 6:
        return html.Div(className='panel wide', children=[
            html.H2(titre),
            html.P(question, className='question'),
            dcc.Graph(
                id='reseau-personnes',
                config={
                    'scrollZoom': True,
                    'doubleClick': 'reset',
                    'displayModeBar': True,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                    'toImageButtonOptions': {'format': 'png', 'filename': 'reseau-personnes', 'scale': 2},
                },
            ),
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


@app.callback(
    Output('reseau-personnes', 'figure'),
    Input('periode', 'data'),
)
def mettre_a_jour_reseau(periode):
    return reseau_personnes(periode)


@app.callback(
    Output('termes-evolution', 'value'),
    Input('tout-deselectionner', 'n_clicks'),
    prevent_initial_call=True,
)
def deselectionner_tous_les_termes(_):
    return []


if __name__ == '__main__':
    app.run(debug=True)
