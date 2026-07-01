**Français** · [English](readme.en.md)

# Météo Concept — `weather.meteoconcept`

<!-- version:auto -->
**Version : 1.0.5**
<!-- /version:auto -->

**Fournisseur météo Kodi pour la France**, basé sur l'API
[Météo Concept](https://api.meteo-concept.com) (données Météo-France).
Une localisation, libellés en **français**, et icônes affichées par votre
skin (Arctic Zephyr, Estuary…).

> Identifiant de l'addon : `weather.meteoconcept` · Type :
> `xbmc.python.weather` · Kodi ≥ 19 (Matrix), Python 3.

---

## Installation

**Recommandé — dépôt TheWorms** (mises à jour automatiques).

Télécharge le dépôt en cliquant **[ICI](https://raw.githubusercontent.com/TheWorms/kodi-repo/main/zips/repository.theworms/repository.theworms.zip)**, puis dans Kodi :

1. **Add-ons** → **Installer depuis un fichier zip** → sélectionne le zip téléchargé
   *(si Kodi bloque, active **Sources inconnues** dans Système → Add-ons)*
2. **Installer depuis un dépôt** → **TheWorms Repository** → choisis l'addon
3. Les mises à jour seront ensuite automatiques

**Installation manuelle (alternative) :** télécharge le zip de l'addon depuis la page [Releases](../../releases), puis **Add-ons** → **Installer depuis un fichier zip**.

---

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Configuration](#configuration)
- [Comment ça marche](#comment-ça-marche)
- [Quota et cache](#quota-et-cache)
- [Codes météo et icônes](#codes-météo-et-icônes)
- [Dépannage](#dépannage)
- [Développement](#développement)
- [Structure du projet](#structure-du-projet)
- [Contribuer](#contribuer)
- [Licence et crédits](#licence-et-crédits)

---

## Fonctionnalités

- **Conditions actuelles** : température, vent (vitesse + direction en
  français), humidité, condition.
- **Prévisions journalières** sur 7 jours (min/max, condition, probabilité de
  pluie, vent).
- **Prévisions horaires** sur les 12 prochaines heures.
- **Libellés en français** issus de la table « temps sensible » de Météo Concept.
- **Icônes du skin** : l'addon publie le code condition Kodi (0–47) ; votre
  skin affiche ses propres pictogrammes, cohérents avec son habillage.
- **Gestion jour / nuit** automatique (icône lune après le coucher du soleil),
  via l'éphéméride de la commune.
- **Recherche de commune** par nom ou code postal, directement dans Kodi.
- **Bouton « Enregistrer et tester le token »** qui valide la clé par un appel
  réel à l'API.
- **Cache fichier paramétrable** pour rester très loin du quota gratuit.

## Prérequis

- **Kodi 19 (Matrix) ou supérieur** (testé jusqu'à Omega), Python 3.
- Un **token gratuit Météo Concept** : créez un compte sur
  <https://api.meteo-concept.com>, formule *Basique* (500 requêtes/jour).
- Une commune en **France métropolitaine** (Belgique, Luxembourg et Andorre
  sont aussi couverts par l'API via coordonnées).

## Configuration

1. **Réglages → Modules → Mes modules → Services → Météo Concept → Configurer**.
2. Collez votre **token** dans le champ prévu.
3. Cliquez sur **« Enregistrer et tester le token »** : saisissez/collez le
   token dans la fenêtre, validez. L'addon l'enregistre puis le teste, et
   confirme « valide ✓ » ou affiche l'erreur renvoyée par l'API.
4. Cliquez sur **« Rechercher une commune… »**, tapez le nom ou le code postal,
   sélectionnez la commune (le code INSEE est enregistré automatiquement).
5. Activez l'addon comme fournisseur : **Réglages → Météo → Service
   d'informations météo → Météo Concept**.

> Certains skins (dont Arctic Zephyr) ont **leur propre** réglage de
> fournisseur météo : vérifiez aussi côté skin si le widget d'accueil ne se met
> pas à jour.

## Comment ça marche

Kodi appelle l'addon de plusieurs façons :

- `RunScript(weather.meteoconcept,Location1)` → recherche/choix de la commune.
- `RunScript(weather.meteoconcept,TestToken)` → enregistrement + test du token.
- avec un index numérique (`1`) → récupération de la météo.

À chaque récupération, l'addon interroge trois routes Météo Concept
(`/forecast/nextHours`, `/forecast/daily`, `/ephemeride/0`), puis écrit des
**propriétés de fenêtre** sur la fenêtre météo de Kodi (`Window(12600)`), que
le skin lit pour l'affichage :

- `Current.*` (conditions actuelles),
- `Daily.N.*` et `Day0..6.*` (prévisions journalières, format étendu + hérité),
- `Hourly.N.*` (prévisions horaires),
- `Location1` + `Locations`, `Forecast.City`, `Today.Sunrise`/`Sunset`.

> ⚠️ La propriété de fenêtre `Location1` est **essentielle** : c'est elle que
> lisent le widget d'accueil et l'infolabel `Weather.Location`. Sans elle, le
> widget conserverait la localisation laissée par un fournisseur précédent.

L'addon **vide toutes les catégories** avant d'écrire, pour ne jamais laisser
de valeurs résiduelles d'un autre fournisseur.

## Quota et cache

La formule *Basique* est limitée à **500 requêtes/jour**. Chaque
rafraîchissement consomme **3 appels** (horaire + journalier + éphéméride).
Avec le **cache** (30 min par défaut, réglable de 10 à 120 min) et un intervalle
de rafraîchissement Kodi raisonnable, l'usage reste de l'ordre de la centaine
d'appels par jour — très en deçà du plafond. Le cache est stocké dans le profil
de l'addon (`~/.kodi/userdata/addon_data/weather.meteoconcept/`).

## Codes météo et icônes

Le champ `weather` de l'API est un entier « temps sensible » (codes 0 à 235).
Le module `resources/lib/meteo_concept_mapping.py` le traduit en :

- un **libellé français** (table officielle Météo Concept),
- un **code condition Kodi 0–47** = le nom de l'icône du skin (`28.png`…).

Pour utiliser un jeu d'icônes embarqué plutôt que celui du skin, la fonction
`get_icon_path(code, is_day, icons_dir=…)` renvoie un chemin complet. Un set
libre et complet : [Weather Icons d'Erik Flowers](https://erikflowers.github.io/weather-icons/)
(licence SIL OFL).

## Dépannage

**Le widget d'accueil garde l'ancien fournisseur (localisation figée).**
Les propriétés de fenêtre persistent en mémoire jusqu'à réécriture. Après
changement de fournisseur, **redémarrez Kodi** (ou désactivez/réactivez
l'addon) pour forcer la réécriture propre.

**« Token manquant » alors que je viens de le saisir.**
Kodi ne sauvegarde la valeur d'un champ qu'à la **fermeture** des réglages.
Utilisez le bouton **« Enregistrer et tester le token »** (qui enregistre
immédiatement), ou saisissez le token puis fermez par **OK** avant de lancer
une autre action.

**Vérifier ce que l'addon lit / écrit.**
Activez le débogage (Réglages → Système → Journalisation → Activer la
journalisation de débogage), puis :

```bash
tail -f ~/.kodi/temp/kodi.log | grep meteoconcept
```

**Vérifier que le token est bien enregistré :**

```bash
cat ~/.kodi/userdata/addon_data/weather.meteoconcept/settings.xml
```

## Développement

Construire le zip installable (nommé d'après la version d'`addon.xml`) :

```bash
./build.sh          # -> dist/weather.meteoconcept-x.y.z.zip
```

Les modules `resources/lib/` sont indépendants de Kodi et peuvent être testés
hors de Kodi (le mapping et le client API n'importent pas `xbmc*`) :

```bash
python3 weather.meteoconcept/resources/lib/meteo_concept_mapping.py
```

Pour modifier l'**identifiant** de l'addon, répercutez-le sur trois éléments
cohérents : le dossier `weather.meteoconcept/`, l'attribut `id` d'`addon.xml`,
et les actions `RunScript(...)` de `settings.xml`.

## Structure du projet

```
kodi-addon-meteo/
├── README.md / readme.fr.md
├── LICENSE                         # GPL-2.0
├── .gitignore
├── build.sh                        # produit dist/weather.meteoconcept-x.y.z.zip
└── weather.meteoconcept/           # l'addon (id : weather.meteoconcept)
    ├── addon.xml
    ├── default.py                  # point d'entrée Kodi
    ├── icon.png
    ├── LICENSE.txt
    ├── changelog.txt
    └── resources/
        ├── settings.xml
        ├── icons/logo.png
        ├── language/resource.language.fr_fr/strings.po
        └── lib/
            ├── meteoconcept.py            # client API + cache
            └── meteo_concept_mapping.py   # codes météo -> libellé FR + icône
```

## Contribuer

Les contributions sont bienvenues : ouvrez une *issue* ou une *pull/merge
request*. Merci de garder les modules `resources/lib/` testables hors Kodi et
de mettre à jour `changelog.txt` ainsi que la version dans `addon.xml`.

## Licence et crédits

- Code sous **GPL-2.0-only** — voir [`LICENSE`](LICENSE).
- Données météo © **Météo Concept** (<https://api.meteo-concept.com>), basées
  sur des données **Météo-France**. L'usage des données est soumis aux
  conditions de Météo Concept. Ce projet n'est ni affilié ni approuvé par
  Météo Concept ou Météo-France.
- Modèle de fournisseur météo Kodi inspiré de l'addon open source
  [`weather.gismeteo`](https://github.com/vlmaksime/weather.gismeteo) (GPL).
