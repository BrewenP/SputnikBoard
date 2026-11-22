import json
import re
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
    'DZA': ('Algérie', 'Algeria'), 'AGO': ('Angola', 'Angola'), 'BEN': ('Bénin', 'Benin'),
    'BWA': ('Botswana', 'Botswana'), 'BFA': ('Burkina Faso|Burkina', 'Burkina Faso'), 'BDI': ('Burundi', 'Burundi'),
    'CMR': ('Cameroun', 'Cameroon'), 'CAF': ('Centrafrique|République centrafricaine', 'Central African Republic|CAR'),
    'TCD': ('Tchad', 'Chad'), 'COD': ('RDC|République démocratique du Congo', 'DRC|Democratic Republic of the Congo'),
    'COG': ('Congo', 'Congo'), 'CIV': ("Côte d'Ivoire", "Ivory Coast|Côte d'Ivoire|Cote d'Ivoire"),
    'DJI': ('Djibouti', 'Djibouti'), 'EGY': ('Égypte', 'Egypt'), 'ERI': ('Érythrée', 'Eritrea'),
    'ETH': ('Éthiopie', 'Ethiopia'), 'GAB': ('Gabon', 'Gabon'), 'GMB': ('Gambie', 'Gambia'), 'GHA': ('Ghana', 'Ghana'),
    'GIN': ('Guinée', 'Guinea'), 'GNB': ('Guinée-Bissau', 'Guinea-Bissau'), 'GNQ': ('Guinée équatoriale', 'Equatorial Guinea'),
    'KEN': ('Kenya', 'Kenya'), 'LBR': ('Liberia', 'Liberia'), 'LBY': ('Libye', 'Libya'), 'MDG': ('Madagascar', 'Madagascar'),
    'MWI': ('Malawi', 'Malawi'), 'MLI': ('Mali', 'Mali'), 'MAR': ('Maroc', 'Morocco'), 'MRT': ('Mauritanie', 'Mauritania'),
    'MOZ': ('Mozambique', 'Mozambique'), 'NAM': ('Namibie', 'Namibia'), 'NER': ('Niger', 'Niger'),
    'NGA': ('Nigeria', 'Nigeria'), 'UGA': ('Ouganda', 'Uganda'), 'RWA': ('Rwanda', 'Rwanda'),
    'SEN': ('Sénégal', 'Senegal'), 'SLE': ('Sierra Leone', 'Sierra Leone'), 'SOM': ('Somalie', 'Somalia'),
    'SDN': ('Soudan', 'Sudan'), 'SSD': ('Soudan du Sud', 'South Sudan'), 'ZAF': ('Afrique du Sud', 'South Africa'),
    'TZA': ('Tanzanie', 'Tanzania'), 'TGO': ('Togo', 'Togo'), 'TUN': ('Tunisie', 'Tunisia'), 'ZMB': ('Zambie', 'Zambia'),
    'ZWE': ('Zimbabwe', 'Zimbabwe'), 'RUS': ('Russie', 'Russia'), 'UKR': ('Ukraine', 'Ukraine'), 'FRA': ('France', 'France'),
    'USA': ('États-Unis|Uni|US', 'US|United States|United State|USA'), 'CHN': ('Chine', 'China'), 'IRN': ('Iran', 'Iran'),
    'ISR': ('Israël|Isra', 'Israel'), 'TUR': ('Turquie', 'Turkey'), 'IND': ('Inde', 'India'), 'DEU': ('Allemagne', 'Germany'),
    'GBR': ('Royaume-Uni', 'United Kingdom|UK|Britain'), 'BRA': ('Brésil', 'Brazil'), 'SYR': ('Syrie', 'Syria'),
    'SAU': ('Arabie saoudite', 'Saudi Arabia'), 'JPN': ('Japon', 'Japan'), 'POL': ('Pologne', 'Poland'),
    'MDA': ('Moldavie', 'Moldova'), 'BLR': ('Biélorussie', 'Belarus'), 'ITA': ('Italie', 'Italy'), 'CUB': ('Cuba', 'Cuba'),
    'VEN': ('Venezuela', 'Venezuela'), 'PRK': ('Corée du Nord', 'North Korea'),
}
AFRICA = set(list(COUNTRIES)[:list(COUNTRIES).index('RUS')])
NAME = {iso: fr.split('|')[0] for iso, (fr, en) in COUNTRIES.items()}


def norm(s):
    s = re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()
    return s[:-1] if s.endswith('s') else s


ISO = {
    lang: {norm(alias): iso for iso, names in COUNTRIES.items() for alias in names[i].split('|')}
    for i, lang in enumerate(['fr', 'en'])
}


def load(name):
    with open(CORPUS[name], 'r', encoding='utf-8') as f:
        return json.load(f)


def countries(entities, lang='fr'):
    return {ISO[lang][norm(e)] for e in entities if norm(e) in ISO[lang]}


def person(name):
    last = name.split()[-1] if name.split() else ''
    ok = len(last) >= 4 and last.isalpha() and last.istitle() and last.lower() not in NOT_PERSON
    return ALIASES.get(last, last) if ok else None


@cache
def articles(name='fr'):
    rows = [a for y in load(name)['data'].values() for m in y.values() for d in m.values() for a in d]
    df = pd.DataFrame(rows)[['title', 'timestamp', 'date', 'kws', 'loc', 'org', 'per']]
    df['date'] = pd.to_datetime(df['date'])
    df['mois'] = df['date'].dt.strftime('%Y-%m')
    df['kws'] = df['kws'].map(lambda k: {w: n for w, n in k.items() if w not in STOP and len(w) > 2})
    df['per'] = df['per'].map(lambda p: {person(n) for n in p} - {None})
    df['pays'] = df['loc'].map(countries)
    return df
