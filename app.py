import math
from collections import Counter
from itertools import combinations

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
import prince
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

import theme
from donnees import AFRICA, COUNTRIES, NAME, articles, compter, emergence, proportion, surrepresentation
from themes import themes

ISSUES = 'https://github.com/BrewenP/SputnikBoard/issues/'

ONGLETS = {
    'evolution': ('Évolution', [
        ('Évolution des personnes citées', "Quels acteurs dominent l'actualité, mois après mois ?", 3, True),
    ]),
    'vocabulaire': ('Vocabulaire', [
        ('Mots émergents', 'Quels mots surgissent puis disparaissent ?', 4, True),
        ('Analyse des correspondances', 'Comment le vocabulaire distingue-t-il les périodes ?', 7, True),
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


RESEAU_PERSONNES = 35  # personnes les plus citées de la période
RESEAU_LIENS = 75  # nombre maximal de liens affichés


def reseau_personnes(periode, pays=None):
    sel = filtrer(periode)
    if pays:
        sel = sel[sel['pays'].map(lambda s: pays in s)]
    citations = Counter(p for personnes in sel['personnes'] for p in personnes)
    principaux = {nom for nom, _ in citations.most_common(RESEAU_PERSONNES)}
    cooccurrences = Counter()
    for personnes in sel['personnes']:
        cooccurrences.update(combinations(sorted(principaux & personnes), 2))

    # Plus petit seuil (au moins 2 articles en commun) qui garde au plus RESEAU_LIENS liens.
    seuil = next((s for s in range(2, max(cooccurrences.values(), default=1) + 1)
                  if sum(n >= s for n in cooccurrences.values()) <= RESEAU_LIENS), 1)
    graphe = nx.Graph()
    graphe.add_weighted_edges_from((a, b, n) for (a, b), n in cooccurrences.items() if n >= seuil)

    fig = go.Figure()
    fig.update_layout(height=640, xaxis=dict(visible=False), yaxis=dict(visible=False), hovermode='closest')
    if graphe.number_of_edges() == 0:
        precision = f'dans les articles sur {NAME[pays]}' if pays else 'sur cette période'
        fig.add_annotation(text=f'Pas assez de personnes citées ensemble {precision}', showarrow=False,
                           font=dict(color=theme.MUTED))
        return fig

    position = placer(graphe)
    poids_max = max(n for _, _, n in graphe.edges(data='weight'))
    for a, b, n in sorted(graphe.edges(data='weight'), key=lambda e: e[2]):
        force = n / poids_max
        fig.add_trace(go.Scatter(
            x=[position[a][0], position[b][0]], y=[position[a][1], position[b][1]], mode='lines',
            line=dict(width=0.8 + 5 * force, color=f'rgba(80, 82, 87, {0.12 + 0.5 * force:.2f})'),
            hoverinfo='skip', showlegend=False,
        ))

    # Communautés par modularité, de la plus grande à la plus petite, nommées d'après leur personne la plus citée.
    communautes = sorted(nx.community.greedy_modularity_communities(graphe, weight='weight', resolution=1.5),
                         key=lambda c: (-len(c), min(c)))
    citations_max = max(citations[nom] for nom in graphe)
    autres = []
    for i, groupe in enumerate(communautes):
        if len(groupe) < 2 or i >= len(theme.SERIES):
            autres += groupe
            continue
        ajouter_noeuds(fig, graphe, position, citations, citations_max, sorted(groupe),
                       f'Autour de {max(groupe, key=citations.get)}', theme.SERIES[i])
    if autres:
        ajouter_noeuds(fig, graphe, position, citations, citations_max, sorted(autres), 'Autres', theme.AXIS)

    masques = len(principaux) - graphe.number_of_nodes()
    note = f'Liens : au moins {seuil} article{"s" if seuil > 1 else ""} en commun'
    if masques:
        note += f'. {masques} des {len(principaux)} personnes les plus citées, sans lien à ce seuil, ne sont pas affichées'
    fig.add_annotation(text=note, xref='paper', yref='paper', x=0, y=0, showarrow=False, xanchor='left',
                       yanchor='top', yshift=-4, font=dict(size=11, color=theme.MUTED))
    fig.update_layout(margin=dict(l=8, r=8, t=48, b=28), legend=dict(itemsizing='constant'))
    return fig


def placer(graphe):
    # Le plus grand groupe connecté occupe le centre, les petits groupes isolés sont rangés sur la droite.
    composantes = sorted(nx.connected_components(graphe), key=lambda c: (-len(c), min(c)))
    position = nx.kamada_kawai_layout(graphe.subgraph(composantes[0]), weight=None)
    for i, c in enumerate(composantes[1:]):
        centre = (1.35 + 0.4 * (i // 6), 0.85 - 0.34 * (i % 6))
        position.update(nx.spring_layout(graphe.subgraph(c), seed=0, scale=0.12, center=centre))
    return position


def ajouter_noeuds(fig, graphe, position, citations, citations_max, noms, nom_groupe, couleur):
    survols = []
    for nom in noms:
        voisins = sorted(graphe[nom].items(), key=lambda v: -v[1]['weight'])[:5]
        survols.append(f'<b>{nom}</b><br>{nombre(citations[nom])} articles<br><br>Le plus souvent avec :<br>'
                       + '<br>'.join(f'{v} ({nombre(d["weight"])} articles)' for v, d in voisins))
    fig.add_trace(go.Scatter(
        x=[position[n][0] for n in noms], y=[position[n][1] for n in noms], mode='markers+text', name=nom_groupe,
        text=noms, textposition='top center', textfont=dict(size=12, color=theme.INK),
        marker=dict(size=[10 + 32 * (citations[n] / citations_max) ** 0.5 for n in noms], color=couleur,
                    line=dict(color=theme.SURFACE, width=1.5)),
        customdata=survols, hovertemplate='%{customdata}<extra></extra>',
    ))


EVOLUTION_PERSONNES = 20  # personnes les plus citées du corpus, proposées dans la liste
EVOLUTION_TERME_OPTIONS = [
    {'label': nom, 'value': f'personnes|{nom}'}
    for nom, _ in Counter(p for s in df['personnes'] for p in s).most_common(EVOLUTION_PERSONNES)
]

EVOLUTION_TERME_DEFAUT = ['personnes|Poutine', 'personnes|Trump', 'personnes|Zelensky', 'personnes|Macron']

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
                text='Sélectionnez au moins une personne',
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
            (o['label']
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
            hovertemplate='<b>%{customdata}</b><br>%{text} : cité dans %{y:.1%} des articles<extra></extra>',
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


# mode -> (libellé du bouton, colonne de `articles`, fréquence cumulée minimale, unité des fréquences)
MODES = {
    'mots': ('Mots clés', 'mots', 20, 'occurrences'),
    'personnes': ('Personnes', 'personnes', 8, 'articles'),
}
# Termes qui ont servi à constituer les deux corpus : forcément surreprésentés, ils n'apprennent rien.
DEFINITOIRES = {
    'mots': {'france', 'français', 'macron', 'emmanuel', 'russie', 'russe', 'poutine', 'vladimir'},
    'personnes': {'Macron', 'Poutine'},
}
FRANCE = ('France / Macron', theme.DIVERGING[1])
RUSSIE = ('Russie / Poutine', theme.DIVERGING[5])
TOP = 15
SEUIL_Z = 1.96


def decimal(x, signe=False):
    return f'{x:+.2f}'.replace('.', ',') if signe else f'{x:.2f}'.replace('.', ',')


def discours(periode, mode):
    _, colonne, minimum, unite = MODES[mode]
    fr, ru = (d[d['mois'].between(*periode)] for d in (macron, poutine))
    communs = set(fr['titre']) & set(ru['titre'])  # articles présents dans les deux corpus, retirés des deux côtés
    fr, ru = fr[~fr['titre'].isin(communs)], ru[~ru['titre'].isin(communs)]
    s = surrepresentation(ru, fr, colonne, filtrer(periode), minimum, exclus=DEFINITOIRES[mode])
    totaux = {FRANCE: sum(compter(fr[colonne]).values()) or 1, RUSSIE: sum(compter(ru[colonne]).values()) or 1}
    cotes = {  # seuls les écarts significatifs au seuil de 5 % sont affichés
        FRANCE: s[s['score'] < -SEUIL_Z].tail(TOP).iloc[::-1],
        RUSSIE: s[s['score'] > SEUIL_Z].head(TOP),
    }
    fig = go.Figure()
    for (nom, couleur), d in cotes.items():
        fig.add_bar(
            x=d['score'], y=list(range(len(d))), orientation='h', name=nom, marker_color=couleur,
            text=d['terme'], textposition='outside', cliponaxis=False,
            customdata=[(t, decimal(abs(sc)), nombre(a), decimal(1000 * a / totaux[FRANCE]),
                         nombre(b), decimal(1000 * b / totaux[RUSSIE]))
                        for t, sc, a, b in zip(d['terme'], d['score'], d['freq_b'], d['freq_a'])],
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                'Score z : %{customdata[1]}<br>'
                f'{FRANCE[0]} : %{{customdata[2]}} {unite} (%{{customdata[3]}} pour 1 000)<br>'
                f'{RUSSIE[0]} : %{{customdata[4]}} {unite} (%{{customdata[5]}} pour 1 000)<extra></extra>'
            ),
        )
    bord = max(s['score'].abs().max() if not s.empty else 2, 2)
    pas = 1 if bord < 6 else 2
    graduations = list(range(-math.ceil(bord) // pas * pas, math.ceil(bord) + 1, pas))
    fig.add_vline(x=0, line_color=theme.AXIS)
    for x in (-SEUIL_Z, SEUIL_Z):
        fig.add_vline(x=x, line_color=theme.MUTED, line_dash='dot', line_width=1)
    fig.update_layout(
        barmode='overlay', height=max(TOP, *(len(d) for d in cotes.values())) * 30 + 150,
        xaxis=dict(
            range=[-bord * 1.35, bord * 1.35], tickvals=graduations, ticktext=[str(abs(g)) for g in graduations],
            showgrid=True, title='Score de surreprésentation (score z, en pointillés le seuil de significativité de 5 %)',
        ),
        yaxis=dict(autorange='reversed', showticklabels=False, showgrid=False, showline=False),
        annotations=[dict(
            text=f'{nombre(len(communs))} articles communs aux deux corpus retirés. '
                 f'Termes qui définissent les corpus exclus : {", ".join(sorted(DEFINITOIRES[mode]))}.',
            xref='paper', yref='paper', x=0, y=0, yshift=-58, yanchor='top', showarrow=False,
            font=dict(size=11, color=theme.MUTED))],
        margin=dict(b=70),
    )
    if all(d.empty for d in cotes.values()):
        fig.add_annotation(text='Aucun écart significatif sur cette période', showarrow=False, font=dict(color=theme.MUTED))
    return fig


VUES = {'afrique': 'Afrique', 'monde': 'Monde'}


def part(x):
    return f'{x * 100:.1f}'.replace('.', ',') + ' %'


AES = {'MLI', 'BFA', 'NER'}  # Alliance des États du Sahel
TOUTE_PERIODE = 'periode'


def carte_pays(periode, vue):
    sel = filtrer(periode)
    codes = sorted(AFRICA if vue == 'afrique' else COUNTRIES)
    presence = pd.DataFrame({c: sel['pays'].map(lambda s: c in s) for c in codes})
    parts = presence.groupby(sel['mois']).mean()
    parts.loc[TOUTE_PERIODE] = presence.mean()
    effectifs = sel.groupby('mois').size()
    effectifs[TOUTE_PERIODE] = len(sel)
    images = [TOUTE_PERIODE, *sel['mois'].drop_duplicates().sort_values()]
    contour = dict(color=[theme.INK if c in AES else theme.AXIS for c in codes],
                   width=[1.6 if c in AES else 0.5 for c in codes])

    def trace(m):
        z = parts.loc[m]
        quand = 'de la période' if m == TOUTE_PERIODE else 'du mois'
        return go.Choropleth(
            # Échelle propre à chaque image : un mois très concentré n'écrase plus les autres.
            locations=codes, z=z.values, locationmode='ISO-3', zmin=0, zmax=max(float(z.max()), 0.01),
            colorscale=theme.SEQUENTIAL_SIGNAL, marker_line=contour,
            colorbar=dict(title='Part des articles', tickformat='.0%', thickness=12, len=0.7, outlinewidth=0),
            customdata=[(NAME[c], part(v), nombre(round(v * effectifs[m]))) for c, v in z.items()],
            hovertemplate=f'<b>%{{customdata[0]}}</b><br>%{{customdata[1]}} des articles {quand} '
                          '(%{customdata[2]} articles)<extra></extra>',
        )

    def nom_image(m):
        return 'Toute la période' if m == TOUTE_PERIODE else libelle(m, LONGS)

    cadre = dict(duration=700, redraw=True)
    fig = go.Figure(
        data=trace(TOUTE_PERIODE),
        frames=[go.Frame(data=[trace(m)], name=m) for m in images],
    )
    fig.update_geos(scope='africa' if vue == 'afrique' else 'world', projection_type='natural earth')
    if vue == 'monde':  # cadrage explicite : sinon la carte garde le décalage de la vue Afrique
        fig.update_geos(lonaxis_range=[-180, 180], lataxis_range=[-58, 85], projection_rotation_lon=0)
    fig.update_layout(
        height=580, margin=dict(l=0, r=0, t=8, b=0), dragmode=False, uirevision=vue,
        annotations=[dict(
            text='Contour noir : Mali, Burkina Faso et Niger, membres de l\'Alliance des États du Sahel (AES)',
            xref='paper', yref='paper', x=0, y=1, xanchor='left', yanchor='top', showarrow=False,
            font=dict(size=12, color=theme.INK_2))],
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
            currentvalue=dict(prefix='Vue : ', font=dict(size=13, color=theme.INK_2)),
            font=dict(size=10, color=theme.MUTED),
            steps=[dict(label='Période' if m == TOUTE_PERIODE else libelle(m), value=nom_image(m), method='animate',
                        args=[[m], dict(mode='immediate', frame=dict(duration=0, redraw=True),
                                        transition=dict(duration=0))]) for m in images],
        )],
    )
    return fig


EMERGENTS = 28  # mots affichés sur la heatmap des mots émergents
EMERGENTS_FREQUENCE_MIN = 0.005  # un mot doit être dans au moins 0,5 % des articles en moyenne par mois
EMERGENTS_ARTICLES_MIN = 5  # et dans au moins 5 articles lors de son mois de pic
EMERGENTS_SCORE_MAX = 5  # au-delà, la couleur ne change plus (sinon un seul pic écrase tout le reste)
EMERGENTS_HAUTEUR = 700


def mots_emergents(periode):
    mois = [m for m in MOIS if periode[0] <= m <= periode[1]]
    fig = go.Figure()
    fig.update_layout(height=EMERGENTS_HAUTEUR)
    if len(mois) < 3:
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), annotations=[dict(
            text='Choisir au moins 3 mois pour repérer les mots émergents.', showarrow=False,
            xref='paper', yref='paper', x=0.5, y=0.5, font=dict(color=theme.MUTED))])
        return fig

    score, freq, comptes = emergence(filtrer(periode), mois, EMERGENTS, EMERGENTS_FREQUENCE_MIN, EMERGENTS_ARTICLES_MIN)
    mots, z = list(score.index), score.to_numpy()
    borne = min(EMERGENTS_SCORE_MAX, float(z.max()))  # sur n mois, un score ne dépasse pas racine(n - 1)
    teintes = sample_colorscale(theme.DIVERGING_SIGNAL, ((z.clip(-borne, borne) + borne) / (2 * borne)).ravel())

    # Cases arrondies façon calendrier : un rectangle par case, en unités d'axe. Plotly ne connaît pas la taille
    # en pixels du graphique, on l'estime pour obtenir des écarts et des arrondis d'environ 3 pixels.
    largeur, hauteur = 1100 / len(mois), (EMERGENTS_HAUTEUR - 90) / len(mots)
    gx, gy, rx, ry = 1.5 / largeur, 1.5 / hauteur, 4 / largeur, 4 / hauteur
    cases = []
    for k, teinte in enumerate(teintes):
        i, j = divmod(k, len(mois))
        x0, x1, y0, y1 = j - 0.5 + gx, j + 0.5 - gx, i - 0.5 + gy, i + 0.5 - gy
        cases.append(dict(
            type='path', layer='below', fillcolor=teinte, line_width=0,
            path=f'M{x0 + rx},{y0} L{x1 - rx},{y0} Q{x1},{y0} {x1},{y0 + ry} L{x1},{y1 - ry} Q{x1},{y1} {x1 - rx},{y1} '
                 f'L{x0 + rx},{y1} Q{x0},{y1} {x0},{y1 - ry} L{x0},{y0 + ry} Q{x0},{y0} {x0 + rx},{y0} Z',
        ))

    # Heatmap transparente posée sur les cases : elle porte l'infobulle et la légende des couleurs.
    fig.add_trace(go.Heatmap(
        z=z, zmin=-borne, zmax=borne, zmid=0, colorscale=theme.DIVERGING_SIGNAL, opacity=0,
        colorbar=dict(title='Score (z)', thickness=10, len=0.6, outlinewidth=0),
        customdata=[[(w, libelle(m, LONGS), part(freq.loc[w, m]), nombre(comptes.loc[w, m])) for m in mois] for w in mots],
        hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Score : <b>%{z:+.1f}</b><br>'
                      'Fréquence : %{customdata[2]} des articles (%{customdata[3]} articles)<extra></extra>',
    ))
    graduations = list(range(len(mois)))[::3 if len(mois) > 12 else 1]
    fig.update_layout(
        height=EMERGENTS_HAUTEUR, shapes=cases,
        xaxis=dict(tickmode='array', tickvals=graduations, ticktext=[libelle(mois[j]) for j in graduations],
                   range=[-0.5, len(mois) - 0.5], side='top', showgrid=False, showline=False, zeroline=False),
        yaxis=dict(tickmode='array', tickvals=list(range(len(mots))), ticktext=mots, range=[len(mots) - 0.5, -0.5],
                   showgrid=False, showline=False, zeroline=False),
        annotations=[dict(
            text="Score = écart de la fréquence du mois à la moyenne du mot, en écarts-types. Mots triés par mois de pic.",
            xref='paper', yref='paper', x=0, y=0, yshift=-6, yanchor='top', showarrow=False,
            font=dict(size=11, color=theme.MUTED))],
    )
    return fig


def bandeau(nom, actions):
    """Bandeau masqué par défaut : un texte et des boutons, d'identifiants `nom`-texte et `nom`-<action>."""
    return html.Div(id=nom, className='filtre', hidden=True, children=[
        html.Span(id=f'{nom}-texte'),
        *[html.Button(texte, id=f'{nom}-{action}', className='filtre-bouton', n_clicks=0) for action, texte in actions],
    ])


CONTENUS = {
    3: [
        html.Div(className='termes-controles', children=[
            html.Div('Personnes affichées', className='label'),
            html.Div(className='termes-selection', children=[
                dcc.Dropdown(
                    id='termes-evolution', options=EVOLUTION_TERME_OPTIONS, value=EVOLUTION_TERME_DEFAUT,
                    multi=True, clearable=False, placeholder='Sélectionner des personnes',
                ),
                html.Button('Tout désélectionner', id='tout-deselectionner', className='termes-clear', n_clicks=0),
            ]),
        ]),
        dcc.Graph(id='evolution-graphique', config={'displayModeBar': False}),
    ],
    4: [dcc.Graph(id='emergents-graphique', config={'displayModeBar': False})],
    5: [
        dcc.RadioItems(
            id='carte-vue', value='afrique', inline=True, className='bascule',
            options=[{'label': nom, 'value': vue} for vue, nom in VUES.items()],
        ),
        html.P('Cliquer sur un pays pour filtrer le réseau des personnes.', className='astuce'),
        bandeau('carte-filtre', [('voir', 'Voir le réseau'), ('retirer', 'Retirer')]),
        dcc.Graph(id='carte-graphique', config={'displayModeBar': False}),
    ],
    6: [
        html.P('Cliquer sur une personne pour suivre son évolution, sur un pays de la carte pour filtrer le réseau.',
               className='astuce'),
        bandeau('reseau-filtre', [('retirer', 'Retirer le filtre')]),
        bandeau('reseau-ajout', [('voir', "Voir l'évolution")]),
        dcc.Graph(id='reseau-personnes', config={'displayModeBar': False}),
    ],
    7: [dcc.Graph(id='afc-graphique', config={'displayModeBar': False})],
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
        dcc.Store(id='filtre-pays'),
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
    Input('filtre-pays', 'data'),
)
def mettre_a_jour_reseau(periode, pays):
    return reseau_personnes(periode, pays)


@app.callback(
    Output('filtre-pays', 'data'),
    Output('carte-graphique', 'clickData'),
    Input('carte-graphique', 'clickData'),
    Input('carte-filtre-retirer', 'n_clicks'),
    Input('reseau-filtre-retirer', 'n_clicks'),
    prevent_initial_call=True,
)
def choisir_pays(clic, *_):
    if ctx.triggered_id == 'carte-graphique':
        return (clic['points'][0]['location'], no_update) if clic else (no_update, no_update)
    return None, None  # clickData remis à zéro pour qu'un nouveau clic sur le même pays soit pris en compte


@app.callback(
    Output('carte-filtre', 'hidden'), Output('carte-filtre-texte', 'children'),
    Output('reseau-filtre', 'hidden'), Output('reseau-filtre-texte', 'children'),
    Input('filtre-pays', 'data'),
)
def afficher_filtre(pays):
    if not pays:
        return True, '', True, ''
    return False, ['Réseau filtré sur : ', html.B(NAME[pays])], False, ['Filtré sur : ', html.B(NAME[pays])]


@app.callback(
    Output('termes-evolution', 'value'),
    Output('termes-evolution', 'options'),
    Output('reseau-ajout', 'hidden'),
    Output('reseau-ajout-texte', 'children'),
    Output('reseau-personnes', 'clickData'),
    Input('tout-deselectionner', 'n_clicks'),
    Input('reseau-personnes', 'clickData'),
    State('termes-evolution', 'value'),
    State('termes-evolution', 'options'),
    prevent_initial_call=True,
)
def choisir_termes(_, clic, valeur, options):
    if ctx.triggered_id == 'tout-deselectionner':
        return [], no_update, True, '', no_update
    nom = clic and clic['points'][0].get('text')
    if not nom:
        return no_update, no_update, no_update, no_update, no_update
    terme = f'personnes|{nom}'
    if terme not in [o['value'] for o in options]:
        options = options + [{'label': nom, 'value': terme}]
    if terme not in valeur:
        valeur = valeur + [terme]
    return valeur, options, False, [html.B(nom), " ajouté au graphique d'évolution"], None


@app.callback(
    Output('onglet', 'value'),
    Input('carte-filtre-voir', 'n_clicks'),
    Input('reseau-ajout-voir', 'n_clicks'),
    prevent_initial_call=True,
)
def changer_onglet(*_):
    return 'acteurs' if ctx.triggered_id == 'carte-filtre-voir' else 'evolution'


AFC_FREQUENTS = 200  # mots clés les plus fréquents de la période, gardés pour le tableau de contingence
AFC_AFFICHES = 30  # mots qui contribuent le plus aux deux axes, affichés sur le graphique
AFC_MIN_ARTICLES = 300  # en dessous, un mois est projeté en élément supplémentaire


def sans_chevauchement(points, ecart=(0.08, 0.05)):
    xs, ys = [x for x, _ in points], [y for _, y in points]
    lx, ly = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
    places, visibles = [], []
    for x, y in points:
        libre = all(abs(x - a) / lx > ecart[0] or abs(y - b) / ly > ecart[1] for a, b in places)
        visibles.append(libre)
        if libre:
            places.append((x, y))
    return visibles


@app.callback(Output('emergents-graphique', 'figure'), Input('periode', 'data'))
def mettre_a_jour_emergents(periode):
    return mots_emergents(periode)


def pole(contributions, coordonnees, signe, n=3):
    """Mots qui tirent le plus l'axe d'un côté (signe -1 ou 1) : plus fortes contributions de ce côté."""
    return ', '.join(contributions[coordonnees * signe > 0].nlargest(n).index)


@app.callback(Output('afc-graphique', 'figure'), Input('periode', 'data'))
def afc(periode):
    sel = filtrer(periode)
    fig = go.Figure()
    fig.update_layout(height=680)
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

    # Les mois peu fournis (avant la rupture de collecte) ont des profils instables : ils sont projetés sur la carte
    # en éléments supplémentaires, sans participer au calcul des axes.
    effectifs = sel['mois'].value_counts()
    actifs = [m for m in tableau.columns if effectifs[m] >= AFC_MIN_ARTICLES]
    if len(actifs) < 3:
        actifs = list(tableau.columns)
    ca = prince.CA(n_components=2, random_state=0).fit(tableau[actifs])
    inertie = ca.percentage_of_variance_
    # Carte asymétrique : les mois en coordonnées standard (divisées par la racine de la valeur propre) forment le
    # cadre, et chaque mot se place au barycentre des mois où il apparaît : un mot proche d'un mois y est surreprésenté.
    mots, mois = ca.row_coordinates(tableau[actifs]), ca.column_coordinates(tableau) / ca.eigenvalues_ ** 0.5
    contributions = ca.row_contributions_
    mots_tous = mots
    # Mots les plus variables dans le temps : ceux qui contribuent le plus à la construction des deux axes.
    mots = mots.loc[(contributions[0] * inertie[0] + contributions[1] * inertie[1]).nlargest(AFC_AFFICHES).index]

    ordre_mois = list((mois[0] ** 2 + mois[1] ** 2).sort_values(ascending=False).index)
    points = [(mois.loc[m, 0], mois.loc[m, 1]) for m in ordre_mois] + list(zip(mots[0], mots[1]))
    visibles = sans_chevauchement(points, ecart=(0.06, 0.035))
    mois_visibles = {m for m, v in zip(ordre_mois, visibles) if v}
    etiquettes = [m if v else '' for m, v in zip(mots.index, visibles[len(ordre_mois):])]

    fig.add_trace(go.Scatter(
        x=mots[0], y=mots[1], mode='markers+text', name='Mots clés', text=etiquettes, textposition='top center',
        marker=dict(color=theme.ACCENT, size=6, opacity=0.8), textfont=dict(color=theme.ORANGE_TEXTE, size=12),
        customdata=list(zip(mots.index, tableau.loc[mots.index].sum(axis=1))),
        hovertemplate='<b>%{customdata[0]}</b><br>dans %{customdata[1]} articles<extra></extra>',
    ))
    for nom, liste, plein in (('Mois', actifs, True), ('Mois peu fournis, projetés sans peser sur les axes',
                                                    [m for m in mois.index if m not in actifs], False)):
        if not liste:
            continue
        rang = [list(mois.index).index(m) for m in liste]
        fig.add_trace(go.Scatter(
            x=mois.loc[liste, 0], y=mois.loc[liste, 1], mode='markers+text', name=nom,
            text=[libelle(m) if m in mois_visibles else '' for m in liste], textposition='bottom center',
            marker=dict(size=13, symbol='circle' if plein else 'circle-open', line=dict(width=1.5 if plein else 2),
                        color=[theme.SEQUENTIAL[1 + round(r * (len(theme.SEQUENTIAL) - 2) / max(len(mois) - 1, 1))]
                               for r in rang]),
            textfont=dict(color=theme.SEQUENTIAL[-2], size=12),
            customdata=[(libelle(m, LONGS), nombre(effectifs[m])) for m in liste],
            hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]} articles<extra></extra>',
        ))

    def titre(axe):
        return (f'◀ {pole(contributions[axe], mots_tous[axe], -1)}'
                f'      Axe {axe + 1} · {pourcent(inertie[axe] / 100)} de l’inertie      '
                f'{pole(contributions[axe], mots_tous[axe], 1)} ▶')

    fig.update_layout(
        legend=dict(itemsizing='constant'),
        xaxis=dict(title=titre(0), zeroline=True, zerolinecolor=theme.AXIS, showgrid=False, showticklabels=False),
        yaxis=dict(title=titre(1), zeroline=True, zerolinecolor=theme.AXIS, showgrid=False, showticklabels=False),
    )
    return fig


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