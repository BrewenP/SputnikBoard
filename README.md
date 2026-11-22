# PressBoard

Projet DATA732 : visualisation avec Plotly d'un corpus d'articles de presse en ligne (Sputnik Afrique).

## Organisation

- `data/` : les corpus JSON (non versionnés, trop volumineux pour GitHub)
- `premiers_graphiques/` : premiers graphiques du sujet
  - `premiers_graphiques.py` : articles par mois (export HTML) et top 10 des mots clés
  - `dash_mots_cles.py` : application Dash, top 10 des mots clés par année
- `sorties/` : graphiques exportés en HTML

## Installation

Placer les données dans `data/`, puis :

```
uv sync
```

## Lancement

```
uv run premiers_graphiques/premiers_graphiques.py
uv run premiers_graphiques/dash_mots_cles.py
```

L'application Dash est accessible sur http://127.0.0.1:8050/.
