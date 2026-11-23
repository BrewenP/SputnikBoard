"""Thèmes des articles (ticket #8), extraits par factorisation en matrices non négatives (NMF).

Les articles sont décrits par leurs mots clés pondérés en TF-IDF. La NMF décompose ce tableau en K thèmes : chaque
thème est une liste de mots pondérés, chaque article un mélange de thèmes. Un article est rangé dans le thème qui
pèse le plus dans son mélange, et un thème est nommé par ses trois mots de plus fort poids.
K vaut 8, une couleur distincte par thème. Avec 10, 12 ou 15 thèmes, les sujets ne deviennent pas plus nets : ils se
scindent (l'Ukraine en conflit, sommets et négociations d'Istanbul), alors que les 8 thèmes restent bien séparés.

Pour la carte, chaque thème forme un îlot : ses articles sont placés par t-SNE (proches s'ils partagent leur
vocabulaire), et l'aire de l'îlot est proportionnelle à son nombre d'articles. La position des îlots les uns par
rapport aux autres ne veut rien dire, seule compte la disposition à l'intérieur d'un îlot.
Le calcul prend moins d'une minute : il est fait une seule fois puis enregistré dans data/cache/.
"""
import pickle
from pathlib import Path

import numpy as np
from sklearn.decomposition import NMF, TruncatedSVD
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.manifold import TSNE
from sklearn.preprocessing import normalize

from donnees import CORPUS, DATA, articles

K = 8  # autant que de couleurs dans theme.SERIES
MIN_ARTICLES = 5  # un mot clé présent dans moins de 5 articles est ignoré
DIMENSIONS = 50  # réduction avant t-SNE
GRAINE = 0
CACHE = DATA.parent.parent / 'cache'  # data/cache/, non versionné comme tout data/
VERSION = 4  # à augmenter si on change le calcul, pour forcer un nouveau cache
SOURCES = [Path(__file__).with_name('donnees.py'), Path(__file__)]  # le cache est refait si le nettoyage change


def ilot(vecteurs):
    """Coordonnées t-SNE d'un groupe d'articles, centrées et ramenées dans le disque unité."""
    if len(vecteurs) < 5:
        xy = np.zeros((len(vecteurs), 2))
    else:
        xy = TSNE(2, init='pca', perplexity=min(30, len(vecteurs) // 4), random_state=GRAINE).fit_transform(vecteurs)
    xy -= xy.mean(axis=0)
    return xy / max(np.linalg.norm(xy, axis=1).max(), 1e-9)


def calculer(df):
    vect = DictVectorizer()
    comptes = vect.fit_transform(df['mots'])
    garder = np.asarray((comptes > 0).sum(axis=0)).ravel() >= MIN_ARTICLES
    comptes, vocabulaire = comptes[:, garder], vect.get_feature_names_out()[garder]
    tfidf = TfidfTransformer(sublinear_tf=True).fit_transform(comptes)

    nmf = NMF(K, init='nndsvda', max_iter=500, random_state=GRAINE)
    melange = nmf.fit_transform(tfidf)
    groupes = melange.argmax(axis=1)
    # Thèmes numérotés du plus gros au plus petit, pour garder les mêmes couleurs d'un calcul à l'autre.
    ordre = np.argsort(-np.bincount(groupes, minlength=K))
    groupes = np.argsort(ordre)[groupes]
    poids = nmf.components_[ordre]
    noms = [', '.join(vocabulaire[p.argsort()[::-1][:3]]) for p in poids]
    part = melange[np.arange(len(df)), ordre[groupes]] / np.maximum(melange.sum(axis=1), 1e-12)

    # Îlots d'aire proportionnelle au nombre d'articles : le plus gros à gauche, les autres sur deux rangées à droite.
    reduit = normalize(TruncatedSVD(DIMENSIONS, random_state=GRAINE).fit_transform(tfidf))
    tailles = np.bincount(groupes, minlength=K)
    rayons = np.sqrt(tailles / tailles.max())
    centres, curseurs = [(0.0, 0.0)], [1.25, 1.25]
    for t in range(1, K):
        rang = int(np.argmin(curseurs))
        centres.append((curseurs[rang] + rayons[t], 0.55 if rang == 0 else -0.55))
        curseurs[rang] += 2 * rayons[t] + 0.6
    x, y = np.zeros(len(df)), np.zeros(len(df))
    for t in range(K):
        choix = groupes == t
        xy = ilot(reduit[choix]) * rayons[t]
        x[choix], y[choix] = xy[:, 0] + centres[t][0], xy[:, 1] + centres[t][1]
    return {'version': VERSION, 'n': len(df), 'k': K, 'noms': noms, 'theme': groupes, 'part': part,
            'x': x, 'y': y, 'centres': centres, 'rayons': rayons}


def themes(nom='fr'):
    """Renvoie un dictionnaire : nombre de thèmes `k`, `noms` des thèmes, `centres` et `rayons` des îlots,
    et pour chaque article (même ordre que articles(nom)) son `theme`, la `part` de ce thème dans l'article
    et ses coordonnées `x`, `y` sur la carte."""
    df = articles(nom)
    cache = CACHE / f'themes-{nom}.pkl'
    if cache.exists() and cache.stat().st_mtime > max(f.stat().st_mtime for f in [CORPUS[nom], *SOURCES]):
        with open(cache, 'rb') as f:
            res = pickle.load(f)
        if res.get('version') == VERSION and res['n'] == len(df):
            return res
    res = calculer(df)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, 'wb') as f:
        pickle.dump(res, f)
    return res
