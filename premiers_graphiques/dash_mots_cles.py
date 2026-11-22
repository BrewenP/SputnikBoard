import json
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

file_name = Path(__file__).parent.parent / 'data' /'fr.sputniknews.africa-2025' / 'data' / 'fr.sputniknews.africa-all.json'

with open(file_name, 'r', encoding='utf-8') as f:
    years = json.load(f)['metadata']['year']

app = Dash(__name__)

app.layout = html.Div([
    html.H4('Les 10 mots clés les plus fréquents par année'),
    dcc.Dropdown(id='year', options=sorted(years), value=max(years), clearable=False),
    dcc.Graph(id='graph'),
])


@app.callback(Output('graph', 'figure'), Input('year', 'value'))
def update_bar_chart(year):
    top_kws = sorted(years[year]['kws'].items(), key=lambda kv: kv[1], reverse=True)[:10]
    df = pd.DataFrame(top_kws, columns=['mot clé', 'occurrences'])
    return px.bar(df, x='mot clé', y='occurrences', title=f'Top 10 des mots clés en {year}')


if __name__ == '__main__':
    app.run(debug=True)
