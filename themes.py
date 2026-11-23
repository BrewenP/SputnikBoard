"""Regroupement thématique des articles (ticket #8).

Les articles sont décrits par leurs mots clés pondérés en TF-IDF, réduits à 100 dimensions (SVD),
regroupés par k-means puis projetés en deux dimensions avec t-SNE pour la carte.
Le calcul prend environ une minute : il est fait une seule fois puis enregistré dans data/cache/.
"""
import pickle

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

from donnees import CORPUS, DATA, articles

K_POSSIBLES = range(4, 9)  # au plus 8 thèmes : autant que de couleurs dans theme.SERIES
MIN_ARTICLES = 5  # un mot clé présent dans moins de 5 articles est ignoré
DIMENSIONS = 100
GRAINE = 0
CACHE = DATA.parent.parent / 'cache'  # data/cache/, non versionné comme tout data/
VERSION = 2  # à augmenter si on change le calcul, pour forcer un nouveau cache


def calculer(df):
    vect = DictVectorizer()
    comptes = vect.fit_transform(df['mots'])
    garder = np.asarray((comptes > 0).sum(axis=0)).ravel() >= MIN_ARTICLES
    comptes, vocabulaire = comptes[:, garder], vect.get_feature_names_out()[garder]

    tfidf = TfidfTransformer(sublinear_tf=True).fit_transform(comptes)
    reduit = normalize(TruncatedSVD(DIMENSIONS, random_state=GRAINE).fit_transform(tfidf))

    silhouettes, modeles = {}, {}
    for k in K_POSSIBLES:
        modeles[k] = KMeans(k, n_init=10, random_state=GRAINE).fit(reduit)
        silhouettes[k] = silhouette_score(reduit, modeles[k].labels_, sample_size=4000, random_state=GRAINE)
    k = max(silhouettes, key=silhouettes.get)
    groupes = modeles[k].labels_

    # Thèmes numérotés du plus gros au plus petit, pour garder les mêmes couleurs d'un calcul à l'autre.
    ordre = np.argsort(-np.bincount(groupes, minlength=k))
    groupes = np.argsort(ordre)[groupes]
    # Nom d'un thème : ses 3 mots les plus représentatifs, c'est-à-dire ceux dont le poids TF-IDF moyen
    # dans le thème dépasse le plus leur poids moyen dans tout le corpus.
    moyenne = np.asarray(tfidf.mean(axis=0)).ravel()
    noms = []
    for t in range(k):
        poids = np.asarray(tfidf[groupes == t].mean(axis=0)).ravel() - moyenne
        noms.append(', '.join(vocabulaire[poids.argsort()[::-1][:3]]))

    xy = TSNE(2, init='pca', random_state=GRAINE).fit_transform(reduit)
    return {'version': VERSION, 'n': len(df), 'k': k, 'silhouettes': silhouettes, 'noms': noms,
            'theme': groupes, 'x': xy[:, 0], 'y': xy[:, 1]}


def themes(nom='fr'):
    """Renvoie un dictionnaire : nombre de thèmes `k`, scores `silhouettes`, `noms` des thèmes,
    et pour chaque article (même ordre que articles(nom)) son `theme` et ses coordonnées `x`, `y`."""
    df = articles(nom)
    cache = CACHE / f'themes-{nom}.pkl'
    if cache.exists() and cache.stat().st_mtime > CORPUS[nom].stat().st_mtime:
        with open(cache, 'rb') as f:
            res = pickle.load(f)
        if res.get('version') == VERSION and res['n'] == len(df):
            return res
    res = calculer(df)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, 'wb') as f:
        pickle.dump(res, f)
    return res
