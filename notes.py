"""Notes explicatives affichées sous chaque graphique du dashboard, et reprises à l'identique dans le README.

Une entrée par graphique, sous le titre de sa carte : `lecture` (comment le lire) et `construction` (comment il est
construit), en Markdown.
"""

NOTES = {
    'Articles par mois': {
        'lecture': (
            "Nombre d'articles publiés chaque mois ; la période choisie est en orange. Le saut d'avril 2025 "
            "(d'environ 100 à plus de 1 000 articles par mois) vient d'un changement de collecte, pas de l'actualité."
        ),
        'construction': (
            "Simple comptage des articles par mois de publication. Comme le volume, le nombre de mots clés et de "
            "personnes par article double aussi en avril 2025 : tous les autres graphiques raisonnent donc en parts "
            "d'articles, jamais en nombres bruts."
        ),
    },
    'Évolution des personnes citées': {
        'lecture': (
            "Chaque courbe donne, mois par mois, la part des articles qui citent une personne : 20 % signifie qu'un "
            "article sur cinq la mentionne. Les pointillés repèrent des événements qui expliquent certains pics "
            "(pourparlers de Riyad, guerre Israël-Iran, sommet d'Alaska). Poutine domine presque tous les mois, Trump "
            "le rejoint en 2025, avec un pic commun au sommet d'Alaska."
        ),
        'construction': (
            "Pour chaque mois, nombre d'articles qui citent la personne divisé par le nombre d'articles du mois. La "
            "liste propose les 20 personnes les plus citées du corpus ; un clic sur une personne du réseau l'ajoute. "
            "Les mois de 2024 comptent moins de 100 articles : un écart de quelques points y repose sur quelques "
            "articles seulement."
        ),
    },
    'Mots émergents': {
        'lecture': (
            "Une ligne par mot, une colonne par mois. La **couleur** dit si le mot est inhabituellement présent ce "
            "mois-là (orange) ou absent (bleu), par rapport à ses autres mois. La **taille** du carré dit combien "
            "d'articles du mois le citent. Un gros carré orange est donc un sujet massif et soudain (Iran en "
            "juin 2025, Alaska en août 2025) ; un petit carré orange, un pic réel mais qui concerne peu d'articles."
        ),
        'construction': (
            "Pour chaque mot clé, on calcule sa fréquence mensuelle (part des articles du mois qui le contiennent), "
            "puis son score z : (fréquence du mois − moyenne du mot) / écart-type du mot. Chaque mot n'est comparé "
            "qu'à lui-même, d'où la taille des carrés pour rendre le volume. Sont gardés les mots présents en moyenne "
            "dans au moins 0,5 % des articles et dans au moins 5 articles lors de leur pic, puis les 28 aux plus forts "
            "pics, triés par mois de pic. Sur n mois, un score ne peut pas dépasser √(n − 1) : environ 4,2 sur toute "
            "la période."
        ),
    },
    'Analyse des correspondances': {
        'lecture': (
            "Les mois (cercles bleus, du clair au foncé dans le temps) sont placés selon leur vocabulaire : deux mois "
            "proches parlent des mêmes choses. Un mot (orange) est attiré vers les mois où il est le plus employé. "
            "Le titre de chaque axe nomme les mots qui tirent vers chacune de ses extrémités : l'axe 1 oppose par "
            "exemple l'Ukraine et les négociations avec Trump à la guerre Israël-Iran. Le pourcentage indique la part "
            "des différences entre mois que l'axe résume."
        ),
        'construction': (
            "Analyse factorielle des correspondances (AFC) sur un tableau croisé : pour les 200 mots clés les plus "
            "fréquents de la période, le nombre d'articles de chaque mois qui les contiennent. Les mois de moins de "
            "300 articles (ceux de 2024) ont des profils instables : ils sont projetés après coup (cercles vides) sans "
            "peser sur les axes. Carte asymétrique : chaque mot est au barycentre des mois, pondérés par son emploi. "
            "Seuls les 30 mots qui contribuent le plus aux deux axes sont affichés."
        ),
    },
    'Pays cités': {
        'lecture': (
            "Plus un pays est orange, plus il est cité. La vue par défaut couvre toute la période ; le curseur et le "
            "bouton Lecture font défiler les mois. L'échelle de couleur est recalculée à chaque image : on compare "
            "les pays entre eux au sein d'un mois, pas un même pays d'un mois à l'autre (les valeurs exactes sont "
            "dans l'infobulle). Le Burkina Faso, le Mali et le Niger arrivent en tête sur l'Afrique. Un clic sur un "
            "pays filtre le réseau des personnes."
        ),
        'construction': (
            "Part des articles qui citent au moins une fois le pays, ou l'un de ses lieux reconnus (sa capitale, par "
            "exemple Bamako pour le Mali, ou le Kremlin pour la Russie). Les lieux viennent de l'extraction "
            "automatique d'entités du corpus, convertis en codes de pays par une table de correspondance."
        ),
    },
    'Réseau des personnes': {
        'lecture': (
            "Chaque point est une personne, de taille proportionnelle à son nombre d'articles. Un trait relie deux "
            "personnes souvent citées ensemble ; plus il est épais, plus l'association est forte. Les couleurs "
            "regroupent les personnes plus liées entre elles qu'avec le reste du réseau. La position n'a pas de sens "
            "géographique : elle rapproche simplement les personnes reliées. Un clic sur une personne l'ajoute au "
            "graphique d'évolution."
        ),
        'construction': (
            "On garde les 35 personnes les plus citées de la période (ou des articles du pays choisi sur la carte). "
            "La force d'un lien est l'indice de Jaccard : articles qui citent les deux personnes divisés par articles "
            "qui citent l'une ou l'autre. Contrairement au simple nombre d'articles en commun, il ne relie pas tout le "
            "monde aux personnes très citées comme Poutine ou Trump. Seules les 75 paires au plus fort indice, avec "
            "au moins 3 articles en commun, sont tracées. Les groupes de couleur sont trouvés par maximisation de la "
            "modularité."
        ),
    },
    'Carte des articles': {
        'lecture': (
            "Chaque point est un article, coloré selon son thème. Chaque thème forme un îlot dont l'aire est "
            "proportionnelle à son nombre d'articles. À l'intérieur d'un îlot, deux articles proches partagent leur "
            "vocabulaire ; la position des îlots les uns par rapport aux autres, en revanche, ne veut rien dire. Les "
            "articles hors de la période choisie sont en gris. Faire glisser pour zoomer, double-cliquer pour revenir."
        ),
        'construction': (
            "Les articles sont décrits par leurs mots clés pondérés en TF-IDF (un mot compte d'autant plus qu'il est "
            "rare dans le corpus). Une factorisation en matrices non négatives (NMF) en tire 8 thèmes, chacun nommé "
            "par ses trois mots les plus lourds ; chaque article est rangé dans le thème qui pèse le plus en lui. Avec "
            "plus de thèmes, les sujets se scindent (l'Ukraine en plusieurs) sans devenir plus nets. Dans chaque îlot, "
            "les articles sont placés par t-SNE."
        ),
    },
    'Évolution des thèmes': {
        'lecture': (
            "Chaque bande donne la part des articles du mois rangés dans un thème ; les bandes empilées font 100 %. "
            "Une bande qui s'épaissit est un thème qui prend de la place dans la couverture du média, par exemple le "
            "thème Iran-Israël en juin 2025."
        ),
        'construction': (
            "Mêmes thèmes et mêmes couleurs que la carte des articles. Pour chaque mois, nombre d'articles de chaque "
            "thème divisé par le nombre d'articles du mois. Les mois de 2024, peu fournis, varient davantage."
        ),
    },
    'Discours comparés': {
        'lecture': (
            "À gauche, les termes caractéristiques des articles sur la France ; à droite, ceux des articles sur la "
            "Russie. Plus la barre est longue, plus le terme est propre à ce corpus ; seuls les écarts significatifs "
            "(au-delà des pointillés) sont affichés. La France apparaît surtout à travers sa crise intérieure "
            "(Bayrou, Lecornu, démission, manifestants) et ses relations avec l'Afrique (Algérie, Niger, franc CFA) ; "
            "la Russie, comme une puissance diplomatique (Moscou, Kremlin, négociation, Trump, Ukraine)."
        ),
        'construction': (
            "Les deux corpus réunissent les articles qui parlent de la France ou de Macron, et de la Russie ou de "
            "Poutine. Les articles présents dans les deux sont retirés des deux côtés, ainsi que les termes qui ont "
            "servi à les constituer (France, Macron, Russie, Poutine…). Score : log-odds pondéré avec un a priori de "
            "Dirichlet (Monroe, Colaresi et Quinn, 2008), qui compare la fréquence d'un terme dans les deux corpus en "
            "tenant compte de sa fréquence dans tout le corpus de la période, puis la divise par son incertitude. "
            "On obtient un score z : au-delà de 1,96, l'écart est significatif au seuil de 5 %."
        ),
    },
}
