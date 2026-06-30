# -*- coding: utf-8 -*-
"""
meteo_concept_mapping.py
------------------------
Table de correspondance pour l'API Météo Concept (https://api.meteo-concept.com).

Le champ `weather` renvoyé par l'API est un entier "Temps sensible" (codes 0 à 235).
Ce module le traduit en :
    - un libellé français (pour l'affichage)
    - un code condition Kodi 0-47 (= le nom de l'icône du skin : 0.png ... 47.png)

Les skins Kodi (dont Arctic Zephyr) embarquent un jeu d'icônes nommé selon ce
standard 0-47. En renvoyant ce code, ton addon laisse le skin afficher SES
propres icônes, cohérentes avec l'habillage.

Rappel des codes condition Kodi (legacy Weather.com), pour mémoire :
    20 brouillard | 26 couvert | 27/28 très nuageux nuit/jour
    29/30 partiellement nuageux nuit/jour | 31 ciel clair (nuit) | 32 ensoleillé
    33/34 beau temps nuit/jour | 9 bruine | 10 pluie verglaçante | 11/12 averses
    14 neige faible | 16 neige | 42 neige forte | 5 pluie et neige mêlées
    4 orages | 3 orages violents | 37/38 orages isolés/épars | 17 grêle
"""

# ---------------------------------------------------------------------------
# 1) Libellés français officiels (table "Temps sensible" de Météo Concept)
# ---------------------------------------------------------------------------
WEATHER_LABELS = {
    0:  "Soleil",
    1:  "Peu nuageux",
    2:  "Ciel voilé",
    3:  "Nuageux",
    4:  "Très nuageux",
    5:  "Couvert",
    6:  "Brouillard",
    7:  "Brouillard givrant",
    10: "Pluie faible",
    11: "Pluie modérée",
    12: "Pluie forte",
    13: "Pluie faible verglaçante",
    14: "Pluie modérée verglaçante",
    15: "Pluie forte verglaçante",
    16: "Bruine",
    20: "Neige faible",
    21: "Neige modérée",
    22: "Neige forte",
    30: "Pluie et neige mêlées faibles",
    31: "Pluie et neige mêlées modérées",
    32: "Pluie et neige mêlées fortes",
    40: "Averses de pluie locales et faibles",
    41: "Averses de pluie locales",
    42: "Averses locales et fortes",
    43: "Averses de pluie faibles",
    44: "Averses de pluie",
    45: "Averses de pluie fortes",
    46: "Averses de pluie faibles et fréquentes",
    47: "Averses de pluie fréquentes",
    48: "Averses de pluie fortes et fréquentes",
    60: "Averses de neige localisées et faibles",
    61: "Averses de neige localisées",
    62: "Averses de neige localisées et fortes",
    63: "Averses de neige faibles",
    64: "Averses de neige",
    65: "Averses de neige fortes",
    66: "Averses de neige faibles et fréquentes",
    67: "Averses de neige fréquentes",
    68: "Averses de neige fortes et fréquentes",
    70: "Averses de pluie et neige mêlées localisées et faibles",
    71: "Averses de pluie et neige mêlées localisées",
    72: "Averses de pluie et neige mêlées localisées et fortes",
    73: "Averses de pluie et neige mêlées faibles",
    74: "Averses de pluie et neige mêlées",
    75: "Averses de pluie et neige mêlées fortes",
    76: "Averses de pluie et neige mêlées faibles et nombreuses",
    77: "Averses de pluie et neige mêlées fréquentes",
    78: "Averses de pluie et neige mêlées fortes et fréquentes",
    100: "Orages faibles et locaux",
    101: "Orages locaux",
    102: "Orages forts et locaux",
    103: "Orages faibles",
    104: "Orages",
    105: "Orages forts",
    106: "Orages faibles et fréquents",
    107: "Orages fréquents",
    108: "Orages forts et fréquents",
    120: "Orages faibles et locaux de neige ou grésil",
    121: "Orages locaux de neige ou grésil",
    122: "Orages locaux de neige ou grésil",
    123: "Orages faibles de neige ou grésil",
    124: "Orages de neige ou grésil",
    125: "Orages de neige ou grésil",
    126: "Orages faibles et fréquents de neige ou grésil",
    127: "Orages fréquents de neige ou grésil",
    128: "Orages fréquents de neige ou grésil",
    130: "Orages faibles et locaux de pluie et neige mêlées ou grésil",
    131: "Orages locaux de pluie et neige mêlées ou grésil",
    132: "Orages forts et locaux de pluie et neige mêlées ou grésil",
    133: "Orages faibles de pluie et neige mêlées ou grésil",
    134: "Orages de pluie et neige mêlées ou grésil",
    135: "Orages forts de pluie et neige mêlées ou grésil",
    136: "Orages faibles et fréquents de pluie et neige mêlées ou grésil",
    137: "Orages fréquents de pluie et neige mêlées ou grésil",
    138: "Orages forts et fréquents de pluie et neige mêlées ou grésil",
    140: "Pluies orageuses",
    141: "Pluie et neige mêlées à caractère orageux",
    142: "Neige à caractère orageux",
    210: "Pluie faible intermittente",
    211: "Pluie modérée intermittente",
    212: "Pluie forte intermittente",
    220: "Neige faible intermittente",
    221: "Neige modérée intermittente",
    222: "Neige forte intermittente",
    230: "Pluie et neige mêlées",
    231: "Pluie et neige mêlées",
    232: "Pluie et neige mêlées",
    235: "Averses de grêle",
}

# ---------------------------------------------------------------------------
# 2) Code Météo Concept -> code condition Kodi (icône du skin)
#    Pour les codes "jour/nuit" différents, on stocke un tuple (jour, nuit).
#    Pour les autres (pluie, neige, orage...), une seule valeur suffit.
# ---------------------------------------------------------------------------
WEATHER_TO_KODI = {
    # Ciel ------------------------------------------------------------------
    0:  (32, 31),   # Soleil -> ensoleillé (jour) / ciel clair (nuit)
    1:  (34, 33),   # Peu nuageux -> beau temps
    2:  (30, 29),   # Ciel voilé -> partiellement nuageux
    3:  (28, 27),   # Nuageux -> très nuageux
    4:  26,         # Très nuageux -> couvert
    5:  26,         # Couvert
    6:  20,         # Brouillard
    7:  20,         # Brouillard givrant -> brouillard
    # Pluie -----------------------------------------------------------------
    10: 11,         # Pluie faible -> averses
    11: 12,         # Pluie modérée
    12: 40,         # Pluie forte -> forte pluie
    13: 10,         # Pluie faible verglaçante -> pluie verglaçante
    14: 10,
    15: 10,
    16: 9,          # Bruine -> bruine
    210: 11,        # Pluie faible intermittente
    211: 12,
    212: 40,
    # Neige -----------------------------------------------------------------
    20: 14,         # Neige faible
    21: 16,         # Neige modérée -> neige
    22: 42,         # Neige forte
    220: 14,
    221: 16,
    222: 42,
    # Pluie et neige mêlées -------------------------------------------------
    30: 5, 31: 5, 32: 5,
    230: 5, 231: 5, 232: 5,
    # Averses de pluie ------------------------------------------------------
    40: 11, 41: 11, 42: 12, 43: 11, 44: 11, 45: 12,
    46: 11, 47: 11, 48: 12,
    # Averses de neige ------------------------------------------------------
    60: 14, 61: 14, 62: 16, 63: 14, 64: 16, 65: 42,
    66: 14, 67: 16, 68: 42,
    # Averses pluie + neige mêlées -----------------------------------------
    70: 5, 71: 5, 72: 5, 73: 5, 74: 5, 75: 5, 76: 5, 77: 5, 78: 5,
    # Orages ----------------------------------------------------------------
    100: 37, 101: 38, 102: 3, 103: 4, 104: 4, 105: 3,
    106: 4, 107: 4, 108: 3,
    120: 4, 121: 4, 122: 4, 123: 4, 124: 4, 125: 4, 126: 4, 127: 4, 128: 4,
    130: 4, 131: 4, 132: 4, 133: 4, 134: 4, 135: 4, 136: 4, 137: 4, 138: 4,
    140: 4, 141: 4, 142: 4,
    # Grêle -----------------------------------------------------------------
    235: 17,        # Averses de grêle
}

# Valeurs de repli si un code inconnu apparaît un jour
DEFAULT_LABEL = "Conditions inconnues"
DEFAULT_KODI_CODE = 26  # couvert (icône neutre)


# ---------------------------------------------------------------------------
# 3) Helpers
# ---------------------------------------------------------------------------
def get_label(code):
    """Retourne le libellé français pour un code Météo Concept."""
    return WEATHER_LABELS.get(code, DEFAULT_LABEL)


def get_kodi_code(code, is_day=True):
    """
    Retourne le code condition Kodi 0-47 (= nom de l'icône du skin).
    `is_day` choisit la variante jour/nuit quand elle existe.
    """
    value = WEATHER_TO_KODI.get(code, DEFAULT_KODI_CODE)
    if isinstance(value, tuple):
        return value[0] if is_day else value[1]
    return value


def get_icon_path(code, is_day=True, icons_dir=None):
    """
    Retourne le chemin/nom d'icône.
    - Sans `icons_dir` : renvoie 'NN.png' (à laisser résoudre par le skin Kodi).
    - Avec `icons_dir` : renvoie le chemin complet vers un jeu d'icônes embarqué
      (ex: icons_dir='special://home/addons/weather.monaddon/resources/icons').
    """
    kodi_code = get_kodi_code(code, is_day)
    filename = "{}.png".format(kodi_code)
    if icons_dir:
        sep = "" if icons_dir.endswith(("/", "\\")) else "/"
        return "{}{}{}".format(icons_dir, sep, filename)
    return filename


def describe(code, is_day=True):
    """
    Renvoie un dict prêt à l'emploi pour alimenter les propriétés Kodi.
    """
    return {
        "code_source": code,
        "label": get_label(code),
        "kodi_code": get_kodi_code(code, is_day),
        "icon": get_icon_path(code, is_day),
    }


# ---------------------------------------------------------------------------
# 4) Démo en ligne de commande
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Quelques codes vus dans les exemples de la doc Météo Concept
    for c in (0, 3, 4, 10, 11, 40, 41, 104, 211, 235):
        d_day = describe(c, is_day=True)
        d_night = describe(c, is_day=False)
        print("MC {:>3} | {:<32} | jour -> {}  | nuit -> {}".format(
            c, d_day["label"], d_day["icon"], d_night["icon"]))
