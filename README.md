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

## Traitement des données

Tout passe par `donnees.py`. Aucun graphique ne lit les fichiers JSON directement.

### Corpus

| Nom | Contenu | Articles |
|---|---|---|
| `fr` | tous les articles de Sputnik Afrique en français, avril 2024 à octobre 2025 | 9 954 |
| `macron` | articles qui parlent de la France ou de Macron | 527 |
| `poutine` | articles qui parlent de la Russie ou de Poutine | 3 123 |

`macron` et `poutine` sont des sous-ensembles de `fr`, et 176 articles appartiennent aux deux.

### Tableau d'articles

`articles('fr')` renvoie un DataFrame pandas, une ligne par article :

| Colonne | Type | Exemple |
|---|---|---|
| `titre` | texte | `"Un avion de l'Onu effectue un atterrissage d'urgence en Somalie"` |
| `date` | date | `2025-04-01` |
| `mois` | texte | `"2025-04"` |
| `semaine` | date (lundi de la semaine) | `2025-03-31` |
| `mots` | dictionnaire mot clé vers nombre d'occurrences | `{'aéroport': 1, 'technique': 1}` |
| `personnes` | ensemble de noms de famille | `{'Poutine', 'Trump'}` |
| `pays` | ensemble de codes ISO à trois lettres | `{'RUS', 'UKR'}` |

Le résultat est mis en cache : appeler `articles()` plusieurs fois ne recharge pas le fichier.

### Nettoyage appliqué

- **Mots clés** : déjà lemmatisés dans les données (masculin singulier, verbes à l'infinitif). Les mots vides propres au corpus (`sputnik`, `déclarer`, `pays`, verbes et adjectifs génériques…) sont retirés via la liste `STOP`.
- **Personnes** : réduites au nom de famille pour fusionner les variantes (`Vladimir Poutine` et `Poutine`). Les fragments sans sens sont écartés (`NOT_PERSON`) et les noms tronqués corrigés (`ALIASES`, par exemple `Traor` vers `Traoré`).
- **Pays** : les lieux sont convertis en codes ISO grâce à la table `COUNTRIES`, qui inclut les capitales (`Bamako` compte pour le Mali, `Moscou` et `Kremlin` pour la Russie). `NAME` donne le nom français d'un code et `AFRICA` l'ensemble des pays africains.

Pour corriger un mot, une personne ou un pays, il suffit de modifier ces listes en haut de `donnees.py`.

### Points importants

- **Accents perdus.** L'extraction des entités a supprimé les lettres accentuées (`S n gal` pour Sénégal, `gypte` pour Égypte) et parfois le `s` final (`Pari` pour Paris). La fonction `norm()` applique la même transformation aux noms de `COUNTRIES` pour que la correspondance fonctionne. Les mots clés, eux, ont gardé leurs accents.
- **Rupture de collecte en avril 2025.** Le corpus passe d'environ 100 articles par mois à plus de 1 000. C'est un effet de la collecte, pas de l'actualité. Tout graphique dans le temps doit utiliser des proportions et non des nombres bruts :

  ```python
  from donnees import articles, proportion

  df = articles('fr')
  proportion(df, 'personnes', ['Poutine', 'Trump'])
  proportion(df, 'pays', ['MLI', 'BFA'], par='semaine')
  ```

  Le résultat a une ligne par mois (ou par semaine), une colonne par terme, et contient la part des articles qui mentionnent ce terme (entre 0 et 1).
- **Entités imparfaites.** L'extraction automatique laisse du bruit (prénoms seuls, quelques mots anglais issus de tweets cités). Il reste négligeable dès qu'on se limite aux entités les plus fréquentes.
