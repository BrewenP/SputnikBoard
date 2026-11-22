from dash import Dash, dcc, html

import theme
from donnees import articles

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


def nombre(n):
    return f'{n:,}'.replace(',', ' ')


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
    dcc.Tabs(id='onglet', value='evolution', className='tabs', children=[
        dcc.Tab(label=label, value=key, className='tab', selected_className='tab--selected', children=[
            html.Div(className='grid', children=[carte(*c) for c in cartes]),
        ])
        for key, (label, cartes) in ONGLETS.items()
    ]),
])

if __name__ == '__main__':
    app.run(debug=True)
