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
- `notes.py` : notes explicatives des graphiques (comment le lire, comment il est construit), affichées sous chaque graphique et reprises dans la section [Lecture des graphiques](#lecture-des-graphiques)
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

Ensuite

```
uv sync
```

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

## Lecture des graphiques

Le même texte figure sous chaque graphique du dashboard (`notes.py`).

### Articles par mois

**Comment le lire.** Nombre d'articles publiés chaque mois ; la période choisie est en orange. Le saut d'avril 2025 (d'environ 100 à plus de 1 000 articles par mois) vient d'un changement de collecte, pas de l'actualité.

**Comment il est construit.** Simple comptage des articles par mois de publication. Comme le volume, le nombre de mots clés et de personnes par article double aussi en avril 2025 : tous les autres graphiques raisonnent donc en parts d'articles, jamais en nombres bruts.

### Évolution des personnes citées

**Comment le lire.** Chaque courbe donne, mois par mois, la part des articles qui citent une personne : 20 % signifie qu'un article sur cinq la mentionne. Les pointillés repèrent des événements qui expliquent certains pics (pourparlers de Riyad, guerre Israël-Iran, sommet d'Alaska). Poutine domine presque tous les mois, Trump le rejoint en 2025, avec un pic commun au sommet d'Alaska.

**Comment il est construit.** Pour chaque mois, nombre d'articles qui citent la personne divisé par le nombre d'articles du mois. La liste propose les 20 personnes les plus citées du corpus ; un clic sur une personne du réseau l'ajoute. Les mois de 2024 comptent moins de 100 articles : un écart de quelques points y repose sur quelques articles seulement.

### Mots émergents

**Comment le lire.** Une ligne par mot, une colonne par mois. La **couleur** dit si le mot est inhabituellement présent ce mois-là (orange) ou absent (bleu), par rapport à ses autres mois. La **taille** du carré dit combien d'articles du mois le citent. Un gros carré orange est donc un sujet massif et soudain (Iran en juin 2025, Alaska en août 2025) ; un petit carré orange, un pic réel mais qui concerne peu d'articles.

**Comment il est construit.** Pour chaque mot clé, on calcule sa fréquence mensuelle (part des articles du mois qui le contiennent), puis son score z : (fréquence du mois − moyenne du mot) / écart-type du mot. Chaque mot n'est comparé qu'à lui-même, d'où la taille des carrés pour rendre le volume. Sont gardés les mots présents en moyenne dans au moins 0,5 % des articles et dans au moins 5 articles lors de leur pic, puis les 28 aux plus forts pics, triés par mois de pic. Sur n mois, un score ne peut pas dépasser √(n − 1) : environ 4,2 sur toute la période.

### Analyse des correspondances

**Comment le lire.** Les mois (cercles bleus, du clair au foncé dans le temps) sont placés selon leur vocabulaire : deux mois proches parlent des mêmes choses. Un mot (orange) est attiré vers les mois où il est le plus employé. Le titre de chaque axe nomme les mots qui tirent vers chacune de ses extrémités : l'axe 1 oppose par exemple l'Ukraine et les négociations avec Trump à la guerre Israël-Iran. Le pourcentage indique la part des différences entre mois que l'axe résume.

**Comment il est construit.** Analyse factorielle des correspondances (AFC) sur un tableau croisé : pour les 200 mots clés les plus fréquents de la période, le nombre d'articles de chaque mois qui les contiennent. Les mois de moins de 300 articles (ceux de 2024) ont des profils instables : ils sont projetés après coup (cercles vides) sans peser sur les axes. Carte asymétrique : chaque mot est au barycentre des mois, pondérés par son emploi. Seuls les 30 mots qui contribuent le plus aux deux axes sont affichés.

### Pays cités

**Comment le lire.** Plus un pays est orange, plus il est cité. La vue par défaut couvre toute la période ; le curseur et le bouton Lecture font défiler les mois. L'échelle de couleur est recalculée à chaque image : on compare les pays entre eux au sein d'un mois, pas un même pays d'un mois à l'autre (les valeurs exactes sont dans l'infobulle). Le Burkina Faso, le Mali et le Niger arrivent en tête sur l'Afrique. Un clic sur un pays filtre le réseau des personnes.

**Comment il est construit.** Part des articles qui citent au moins une fois le pays, ou l'un de ses lieux reconnus (sa capitale, par exemple Bamako pour le Mali, ou le Kremlin pour la Russie). Les lieux viennent de l'extraction automatique d'entités du corpus, convertis en codes de pays par une table de correspondance.

### Réseau des personnes

**Comment le lire.** Chaque point est une personne, de taille proportionnelle à son nombre d'articles. Un trait relie deux personnes souvent citées ensemble ; plus il est épais, plus l'association est forte. Les couleurs regroupent les personnes plus liées entre elles qu'avec le reste du réseau. La position n'a pas de sens géographique : elle rapproche simplement les personnes reliées. Un clic sur une personne l'ajoute au graphique d'évolution.

**Comment il est construit.** On garde les 35 personnes les plus citées de la période (ou des articles du pays choisi sur la carte). La force d'un lien est l'indice de Jaccard : articles qui citent les deux personnes divisés par articles qui citent l'une ou l'autre. Contrairement au simple nombre d'articles en commun, il ne relie pas tout le monde aux personnes très citées comme Poutine ou Trump. Seules les 75 paires au plus fort indice, avec au moins 3 articles en commun, sont tracées. Les groupes de couleur sont trouvés par maximisation de la modularité.

### Carte des articles

**Comment le lire.** Chaque point est un article, coloré selon son thème. Chaque thème forme un îlot dont l'aire est proportionnelle à son nombre d'articles. À l'intérieur d'un îlot, deux articles proches partagent leur vocabulaire ; la position des îlots les uns par rapport aux autres, en revanche, ne veut rien dire. Les articles hors de la période choisie sont en gris. Faire glisser pour zoomer, double-cliquer pour revenir.

**Comment il est construit.** Les articles sont décrits par leurs mots clés pondérés en TF-IDF (un mot compte d'autant plus qu'il est rare dans le corpus). Une factorisation en matrices non négatives (NMF) en tire 8 thèmes, chacun nommé par ses trois mots les plus lourds ; chaque article est rangé dans le thème qui pèse le plus en lui. Avec plus de thèmes, les sujets se scindent (l'Ukraine en plusieurs) sans devenir plus nets. Dans chaque îlot, les articles sont placés par t-SNE.

### Évolution des thèmes

**Comment le lire.** Chaque bande donne la part des articles du mois rangés dans un thème ; les bandes empilées font 100 %. Une bande qui s'épaissit est un thème qui prend de la place dans la couverture du média, par exemple le thème Iran-Israël en juin 2025.

**Comment il est construit.** Mêmes thèmes et mêmes couleurs que la carte des articles. Pour chaque mois, nombre d'articles de chaque thème divisé par le nombre d'articles du mois. Les mois de 2024, peu fournis, varient davantage.

### Discours comparés

**Comment le lire.** À gauche, les termes caractéristiques des articles sur la France ; à droite, ceux des articles sur la Russie. Plus la barre est longue, plus le terme est propre à ce corpus ; seuls les écarts significatifs (au-delà des pointillés) sont affichés. La France apparaît surtout à travers sa crise intérieure (Bayrou, Lecornu, démission, manifestants) et ses relations avec l'Afrique (Algérie, Niger, franc CFA) ; la Russie, comme une puissance diplomatique (Moscou, Kremlin, négociation, Trump, Ukraine).

**Comment il est construit.** Les deux corpus réunissent les articles qui parlent de la France ou de Macron, et de la Russie ou de Poutine. Les articles présents dans les deux sont retirés des deux côtés, ainsi que les termes qui ont servi à les constituer (France, Macron, Russie, Poutine…). Score : log-odds pondéré avec un a priori de Dirichlet (Monroe, Colaresi et Quinn, 2008), qui compare la fréquence d'un terme dans les deux corpus en tenant compte de sa fréquence dans tout le corpus de la période, puis la divise par son incertitude. On obtient un score z : au-delà de 1,96, l'écart est significatif au seuil de 5 %.

## Dashboard

### Structure

De haut en bas :

1. **En-tête** : titre et présentation du corpus.
2. **Filtre de période** : un curseur sur les mois et trois raccourcis (toute la période, depuis avril 2025, trois derniers mois). Il s'applique à tout ce qui se trouve en dessous.
3. **Indicateurs** : nombre d'articles, personne la plus citée, part des articles parlant d'un pays africain, pays africain le plus cité, et volume d'articles par mois (période sélectionnée en orange).
4. **Onglets** : Évolution, Vocabulaire, Carte, Acteurs, Thèmes, France / Russie. Chaque graphique occupe une carte avec un titre, la question à laquelle il répond et, en dessous, sa note explicative.

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

4. Ajouter sa note explicative dans `NOTES` de `notes.py`, sous le titre de la carte, et la recopier dans la section [Lecture des graphiques](#lecture-des-graphiques) de ce README.

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
