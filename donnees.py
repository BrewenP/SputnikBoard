import json
import math
import re
from collections import Counter
from functools import cache
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / 'data' / 'fr.sputniknews.africa-2025' / 'data'
CORPUS = {
    'fr': DATA / 'fr.sputniknews.africa-all.json',
    'macron': DATA / 'fr.sputniknews.africa-france-macron.json',
    'poutine': DATA / 'fr.sputniknews.africa-russie-poutine.json',
}

STOP = {
    'sputnik', 'déclarer', 'pays', 'président', 'ministre', 'année', 'faire', 'selon', 'indiquer', 'affirmer',
    'souligner', 'dire', 'an', 'jour', 'pouvoir', 'devoir', 'premier', 'nouveau', 'cours', 'fin', 'partie',
    'cadre', 'lors', 'rappeler', 'ajouter', 'noter', 'estimer', 'expliquer', 'agence', 'source', 'information',
    'heure', 'temps', 'fois', 'point', 'place', 'mois', 'semaine', 'dernier', 'grand', 'plus', 'autre', 'afin',
    'propos', 'aussi', 'déjà', 'notamment', 'ainsi', 'également', 'question', 'situation', 'niveau', 'nombre',
    'personne', 'monde', 'général', 'actuel', 'important', 'déclaration', 'déclaré', 'précisé', 'précédemment',
    'mettre', 'prendre', 'donner', 'venir', 'aller', 'voir', 'savoir', 'vouloir', 'falloir', 'tenir', 'permettre',
    'chef', 'rapport', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre',
    'décembre', 'janvier', 'février', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
    'image', 'viral', 'vidéo', 'événement', 'annoncer', 'rapporter', 'lieu', 'principal', 'viser', 'vladimir',
    'affaire', 'étranger', 'devenir', 'passer', 'mener', 'créer', 'prévoir', 'utiliser', 'appeler', 'lancer',
    'générer', 'ia', 'face', 'clé', 'local', 'spécial', 'renforcer', 'soutenir', 'service', 'site', 'centre',
}
NOT_PERSON = {
    'washington', 'victoire', 'burkinab', 'sputnik', 'sputnikradio', 'afrique', 'kremlin', 'moscou', 'kiev',
    'guin', 'fran', 'faso', 'ivoire', 'premier', 'ministre', 'castbox', 'bloomberg', 'rosatom', 'sergue', 'gate',
    'interrog', 'axio', 'jazeera', 'iskander',
}
ALIASES = {
    'Traor': 'Traoré', 'Jinping': 'Xi Jinping', 'Leyen': 'von der Leyen', 'Gaulle': 'de Gaulle',
    'Jong': 'Kim Jong-un', 'Itno': 'Déby', 'Silva': 'Lula', 'Medinski': 'Medinsky',
}

COUNTRIES = {
    'DZA': 'Algérie|Alger', 'AGO': 'Angola|Luanda', 'BEN': 'Bénin|Cotonou', 'BWA': 'Botswana',
    'BFA': 'Burkina Faso|Burkina|Ouagadougou', 'BDI': 'Burundi', 'CMR': 'Cameroun|Yaoundé',
    'CAF': 'Centrafrique|République centrafricaine|Bangui', 'TCD': "Tchad|N'Djamena",
    'COD': 'RDC|République démocratique du Congo|Kinshasa', 'COG': 'Congo|Brazzaville',
    'CIV': "Côte d'Ivoire|Abidjan", 'DJI': 'Djibouti', 'EGY': 'Égypte|Caire|Le Caire', 'ERI': 'Érythrée',
    'ETH': 'Éthiopie|Addis Abeba', 'GAB': 'Gabon|Libreville', 'GMB': 'Gambie', 'GHA': 'Ghana|Accra',
    'GIN': 'Guinée|Conakry', 'GNB': 'Guinée-Bissau', 'GNQ': 'Guinée équatoriale', 'KEN': 'Kenya|Nairobi',
    'LBR': 'Liberia', 'LBY': 'Libye|Tripoli', 'MDG': 'Madagascar|Antananarivo', 'MWI': 'Malawi',
    'MLI': 'Mali|Bamako', 'MAR': 'Maroc|Rabat', 'MRT': 'Mauritanie|Nouakchott', 'MOZ': 'Mozambique|Maputo',
    'NAM': 'Namibie|Windhoek', 'NER': 'Niger|Niamey', 'NGA': 'Nigeria|Abuja|Lagos', 'UGA': 'Ouganda|Kampala',
    'RWA': 'Rwanda|Kigali', 'SEN': 'Sénégal|Dakar', 'SLE': 'Sierra Leone', 'SOM': 'Somalie|Mogadiscio',
    'SDN': 'Soudan|Khartoum', 'SSD': 'Soudan du Sud', 'ZAF': 'Afrique du Sud|Pretoria|Johannesburg|Le Cap',
    'TZA': 'Tanzanie|Dodoma|Dar es Salaam', 'TGO': 'Togo|Lomé', 'TUN': 'Tunisie|Tunis', 'ZMB': 'Zambie|Lusaka',
    'ZWE': 'Zimbabwe|Harare',
    'RUS': 'Russie|Moscou|Kremlin|Saint-Pétersbourg', 'UKR': 'Ukraine|Kiev', 'FRA': 'France|Paris|Élysée',
    'USA': 'États-Unis|Uni|US|USA|Washington|Maison Blanche', 'CHN': 'Chine|Pékin', 'IRN': 'Iran|Téhéran',
    'ISR': 'Israël|Isra|Tel Aviv', 'PSE': 'Palestine|Gaza|Cisjordanie', 'TUR': 'Turquie|Ankara|Istanbul',
    'IND': 'Inde|New Delhi', 'DEU': 'Allemagne|Berlin', 'GBR': 'Royaume-Uni|Londres', 'BRA': 'Brésil|Brasilia',
    'SYR': 'Syrie|Damas', 'LBN': 'Liban|Beyrouth', 'IRQ': 'Irak|Bagdad', 'QAT': 'Qatar|Doha',
    'SAU': 'Arabie saoudite|Riyad', 'PAK': 'Pakistan', 'JPN': 'Japon|Tokyo', 'POL': 'Pologne|Varsovie',
    'MDA': 'Moldavie|Chisinau', 'BLR': 'Biélorussie|Minsk', 'ITA': 'Italie|Rome', 'CUB': 'Cuba',
    'VEN': 'Venezuela|Caracas', 'PRK': 'Corée du Nord|Pyongyang',
}
AFRICA = set(list(COUNTRIES)[:list(COUNTRIES).index('RUS')])
NAME = {iso: names.split('|')[0] for iso, names in COUNTRIES.items()}


def norm(s):
    s = re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()
    return s[:-1] if s.endswith('s') else s


ISO = {norm(alias): iso for iso, names in COUNTRIES.items() for alias in names.split('|')}


def load(name):
    with open(CORPUS[name], 'r', encoding='utf-8') as f:
        return json.load(f)


def countries(entities):
    return {ISO[norm(e)] for e in entities if norm(e) in ISO}


def person(name):
    last = name.split()[-1] if name.split() else ''
    ok = len(last) >= 4 and last.isalpha() and last.istitle() and last.lower() not in NOT_PERSON
    return ALIASES.get(last, last) if ok else None


@cache
def articles(name='fr'):
    rows = [a for y in load(name)['data'].values() for m in y.values() for d in m.values() for a in d]
    raw = pd.DataFrame(rows)
    df = pd.DataFrame({'titre': raw['title'], 'date': pd.to_datetime(raw['date'])})
    df['mois'] = df['date'].dt.strftime('%Y-%m')
    df['semaine'] = df['date'].dt.to_period('W').dt.start_time
    df['mots'] = raw['kws'].map(lambda k: {w: n for w, n in k.items() if w not in STOP and len(w) > 2})
    df['personnes'] = raw['per'].map(lambda p: {person(n) for n in p} - {None})
    df['pays'] = raw['loc'].map(countries)
    return df.sort_values('date', ignore_index=True)


def proportion(df, colonne, termes, par='mois'):
    presence = pd.DataFrame({t: df[colonne].map(lambda s: t in s) for t in termes})
    return presence.groupby(df[par]).mean()


def compter(serie):
    """Fréquence de chaque terme d'une colonne : occurrences pour `mots`, nombre d'articles pour `personnes`."""
    total = Counter()
    for termes in serie:
        total.update(termes if isinstance(termes, dict) else dict.fromkeys(termes, 1))
    return total


def surrepresentation(a, b, colonne, minimum=20, lissage=0.5):
    """Surreprésentation relative de chaque terme de `a` par rapport à `b` (logarithme du rapport de cotes).

    Pour un terme, la cote dans un corpus est sa fréquence divisée par la fréquence de tous les autres termes.
    Le score est le logarithme népérien du rapport des cotes : positif si le terme est plus caractéristique
    de `a`, négatif s'il l'est de `b`, proche de 0 s'il est utilisé de la même façon des deux côtés.
    Le lissage (`lissage` ajouté à chaque fréquence) évite de diviser par zéro quand un terme est absent d'un corpus.
    Les termes dont la fréquence cumulée est inférieure à `minimum` sont écartés.

    Renvoie un tableau trié par score décroissant, avec les colonnes `terme`, `freq_a`, `freq_b` et `score`.
    """
    ca, cb = compter(a[colonne]), compter(b[colonne])
    ta, tb = sum(ca.values()), sum(cb.values())
    lignes = []
    for terme in ca.keys() | cb.keys():
        fa, fb = ca[terme], cb[terme]
        if fa + fb < minimum:
            continue
        cote_a = (fa + lissage) / (ta - fa + lissage)
        cote_b = (fb + lissage) / (tb - fb + lissage)
        lignes.append((terme, fa, fb, math.log(cote_a / cote_b)))
    return pd.DataFrame(lignes, columns=['terme', 'freq_a', 'freq_b', 'score']).sort_values(
        ['score', 'terme'], ascending=[False, True], ignore_index=True)