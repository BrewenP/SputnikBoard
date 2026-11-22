import json
from pathlib import Path

import pandas as pd
import plotly.express as px

root = Path(__file__).parent.parent
file_name = root / 'data' / 'fr.sputniknews.africa-2025' / 'data' / 'fr.sputniknews.africa-all.json'

with open(file_name, 'r', encoding='utf-8') as f:
    metadata = json.load(f)['metadata']

# nombre d'articles par mois
months = [(int(y), int(m), v['num']) for y, ms in metadata['month'].items() for m, v in ms.items()]
df_months = pd.DataFrame(months, columns=['année', 'mois', 'articles']).sort_values(['année', 'mois'])
df_months['date'] = df_months['année'].astype(str) + '-' + df_months['mois'].astype(str).str.zfill(2)

fig = px.bar(df_months, x='date', y='articles', title="Nombre d'articles par mois")
fig.write_html(root / 'sorties' / 'articles_par_mois.html')
fig.show()

# 10 mots clés les plus fréquents
top_kws = sorted(metadata['all']['kws'].items(), key=lambda kv: kv[1], reverse=True)[:10]
df_kws = pd.DataFrame(top_kws, columns=['mot clé', 'occurrences'])

fig = px.bar(df_kws, x='mot clé', y='occurrences', title='Les 10 mots clés les plus fréquents')
fig.show()
