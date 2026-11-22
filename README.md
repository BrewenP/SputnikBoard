# PressBoard

Projet DATA732 : visualisation avec Plotly d'un corpus d'articles de presse en ligne (Sputnik Afrique).

## Organisation

- `data/` : les corpus JSON (non versionnés, trop volumineux pour GitHub)
- `donnees.py` : chargement et nettoyage des corpus, commun à tous les graphiques
  - `articles(nom)` : tableau des articles (titre, date, mois, semaine, mots clés, personnes, pays), mis en cache
  - `proportion(df, colonne, termes, par)` : part des articles mentionnant chaque terme, par mois ou par semaine
- `premiers_graphiques/` : premiers graphiques du sujet
  - `premiers_graphiques.py` : articles par mois (export HTML) et top 10 des mots clés
  - `dash_mots_cles.py` : application Dash, top 10 des mots clés par année
- `sorties/` : graphiques exportés en HTML

## Installation

Placer les données dans `data/` (le dossier `fr.sputniknews.africa-2025/data/` est celui utilisé par le projet), puis :

```
uv sync
```

## Lancement

```
uv run premiers_graphiques/premiers_graphiques.py
uv run premiers_graphiques/dash_mots_cles.py
```

L'application Dash est accessible sur http://127.0.0.1:8050/.
