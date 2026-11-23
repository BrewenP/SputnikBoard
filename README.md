# SputnikBoard

Projet DATA732 : visualisation avec Plotly d'un corpus d'articles de presse en ligne (Sputnik Afrique).

## Organisation

- `data/` : les corpus JSON (non versionnés, trop volumineux pour GitHub)
- `app.py` : le dashboard Dash
- `theme.py` : palette de couleurs et thème Plotly commun à tous les graphiques
- `assets/style.css` : mise en page et style du dashboard (chargé automatiquement par Dash)
- `donnees.py` : chargement et nettoyage des corpus, commun à tous les graphiques
  - `articles(nom)` : tableau des articles (titre, date, mois, semaine, mots clés, personnes, pays), mis en cache
  - `proportion(df, colonne, termes, par)` : part des articles mentionnant chaque terme, par mois ou par semaine
- `themes.py` : regroupement des articles par thème (TF-IDF, NMF, t-SNE) pour l'onglet Thèmes
  - `themes(nom)` : thème et position sur la carte de chaque article, noms des thèmes, centre et rayon de chaque îlot. Le calcul (moins d'une minute) est fait au premier lancement puis enregistré dans `data/cache/`
- `premiers_graphiques/` : premiers graphiques du sujet
  - `premiers_graphiques.py` : articles par mois (export HTML) et top 10 des mots clés
  - `dash_mots_cles.py` : application Dash, top 10 des mots clés par année
- `sorties/` : graphiques exportés en HTML

## Installation

Placer les données qui sont données sur Moodle dans `data/` (le dossier `fr.sputniknews.africa-2025/data/` est celui utilisé par le projet) en vérifiant d'avoir bien tout dézippé.

Vous donc êtes censé avoir 4 dossiers : 
- `data-2`
- `fr.sputniknews.africa-2025`
- `fr.sputniknews.africa--20220630--20230630`
- `fr.sputniknews.africa--20221101--20221231`

Ensuite tout simplement :

```
uv sync
```

Et le projet est lancé

## Lancement

```
uv run app.py
```

Le dashboard est accessible sur http://127.0.0.1:8050/. Il se recharge tout seul à chaque modification du code.

Les premiers graphiques du sujet restent disponibles :

```
uv run premiers_graphiques/premiers_graphiques.py
uv run premiers_graphiques/dash_mots_cles.py
```

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

## Dashboard

### Structure

De haut en bas :

1. **En-tête** : titre et présentation du corpus.
2. **Filtre de période** : un curseur sur les mois et trois raccourcis (toute la période, depuis avril 2025, trois derniers mois). Il s'applique à tout ce qui se trouve en dessous.
3. **Indicateurs** : nombre d'articles, personnes citées, part des articles parlant d'un pays africain, pays africain le plus cité, et volume d'articles par mois (période sélectionnée en bleu).
4. **Onglets** : Évolution, Vocabulaire, Carte, Acteurs, Thèmes, France / Russie. Chaque graphique occupe une carte avec un titre et la question à laquelle il répond.

Les onglets et leurs cartes sont décrits dans le dictionnaire `ONGLETS` de `app.py`. Une carte encore vide affiche un lien vers son ticket.

### Filtrage croisé

Certains graphiques réagissent aux clics sur d'autres, toujours en plus du filtre de période :

- **Clic sur un pays de la carte** : le réseau des personnes est recalculé sur les seuls articles qui citent ce pays. Le pays choisi est gardé dans le `dcc.Store` `filtre-pays`.
- **Clic sur une personne du réseau** : elle est ajoutée aux termes suivis du graphique d'évolution.

Chaque filtre actif est signalé par un bandeau (fonction `bandeau()`) avec un bouton pour le retirer ou pour aller voir le graphique concerné. Un même composant ne peut être modifié que par un seul callback : pour réagir à un nouveau clic, ajouter une entrée au callback existant (`choisir_pays`, `choisir_termes`) plutôt qu'un nouveau callback sur la même sortie.

### Ajouter un graphique

1. Écrire une fonction qui prend la période et renvoie une figure Plotly, en partant de `filtrer(periode)` qui donne les articles de la période.
2. Ajouter dans le dictionnaire `CONTENUS` de `app.py`, sous le numéro du ticket, le contenu de la carte : un `dcc.Graph` avec un identifiant, précédé si besoin de contrôles (boutons, liste déroulante). La carte vide est alors remplacée automatiquement. Si un ticket a plusieurs cartes, utiliser le titre de la carte comme clé. Ne pas modifier `carte()` au cas par cas.
3. Relier les deux par un callback qui écoute la période :

```python
@app.callback(Output('evolution-graphique', 'figure'), Input('periode', 'data'))
def evolution(periode):
    sel = filtrer(periode)
    ...
```

`periode` vaut par exemple `['2025-04', '2025-10']` (premier et dernier mois inclus).

Avant d'ouvrir une pull request, fusionner `main` dans sa branche et vérifier que tous les onglets fonctionnent encore : `app.py` est partagé par tous les tickets, et le remplacer par une version ancienne efface le travail des autres.

### Règles de style

- **Ne pas définir de couleurs, polices ou marges dans les graphiques.** Le thème `sputnikboard` de `theme.py` est appliqué automatiquement à toutes les figures dès que `theme` est importé.
- **Couleurs** : utiliser les constantes de `theme.py`.
  - `SERIES` pour des catégories, dans l'ordre et sans sauter de couleur. Une même entité garde toujours la même couleur, quel que soit le filtre.
  - `SEQUENTIAL` (bleu, du clair au foncé) pour une intensité, par exemple sur une carte.
  - `SEQUENTIAL_SIGNAL` (gris vers orange Sputnik) pour une intensité qu'on veut mettre en avant, par exemple la carte des pays.
  - `DIVERGING` (bleu, gris, rouge) pour une opposition autour d'un point neutre, par exemple France contre Russie.
  - `DIVERGING_SIGNAL` (bleu, gris, orange Sputnik) pour un écart à la normale où seul le côté positif compte, par exemple les mots émergents.
- **Pas de double axe vertical.** Deux mesures d'échelles différentes vont dans deux graphiques.
- **Textes en français**, y compris les infobulles (`hovertemplate`), avec des noms de mois via `libelle()`.
- **Graphiques dans le temps en proportions** (voir la rupture de collecte plus haut), avec `proportion()` de `donnees.py`.
- **Barre d'outils Plotly masquée** : `config={'displayModeBar': False}` sur chaque `dcc.Graph`.
