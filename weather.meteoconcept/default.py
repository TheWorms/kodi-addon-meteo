# -*- coding: utf-8 -*-
"""
default.py — Fournisseur météo Kodi basé sur l'API Météo Concept.

Kodi appelle ce script de deux façons :
  - sys.argv[1] == "Location1"  -> recherche/choix de la commune (réglages)
  - sys.argv[1] == "1"           -> récupération de la météo pour la commune 1
"""

import os
import sys
import datetime

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))

# Rendre nos modules importables
sys.path.insert(0, os.path.join(ADDON_PATH, "resources", "lib"))
import meteoconcept                      # noqa: E402
import meteo_concept_mapping as wmap     # noqa: E402

WEATHER_WINDOW = xbmcgui.Window(12600)
JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
COMPASS_FR = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]


# --------------------------------------------------------------------------- #
# Helpers Kodi
# --------------------------------------------------------------------------- #
def log(msg):
    xbmc.log("[%s] %s" % (ADDON_ID, msg), xbmc.LOGINFO)


def set_prop(name, value=""):
    WEATHER_WINDOW.setProperty(name, u"%s" % value)


def clear_prop(name):
    WEATHER_WINDOW.clearProperty(name)


def notify(message):
    xbmcgui.Dialog().notification(ADDON.getAddonInfo("name"), message,
                                  ADDON.getAddonInfo("icon"), 5000)


# --------------------------------------------------------------------------- #
# Utilitaires de données
# --------------------------------------------------------------------------- #
def parse_dt(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
    except (ValueError, TypeError):
        try:
            return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
        except (ValueError, TypeError):
            return None


def wind_dir_fr(deg):
    try:
        ix = int((float(deg) + 22.5) // 45) % 8
        return COMPASS_FR[ix]
    except (ValueError, TypeError):
        return ""


def hhmm_to_minutes(s):
    try:
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return None


def is_daytime(dt, sunrise, sunset):
    """dt: datetime ; sunrise/sunset: 'HH:MM'. True si en plein jour."""
    if dt is None:
        return True
    sr = hhmm_to_minutes(sunrise)
    ss = hhmm_to_minutes(sunset)
    if sr is None or ss is None:
        return 7 <= dt.hour < 21
    minutes = dt.hour * 60 + dt.minute
    return sr <= minutes <= ss


def test_token(location_index="1"):
    current = (ADDON.getSetting("token") or "").strip()
    keyboard = xbmc.Keyboard(current, "Collez votre token Météo Concept")
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return
    token = keyboard.getText().strip()
    if not token:
        notify("Token vide : rien n'a été enregistré.")
        return

    ADDON.setSetting("token", token)
    log("Token enregistré (%d caractères), test en cours…" % len(token))

    # Pas de cache : on force un vrai appel réseau pour valider
    api = meteoconcept.MeteoConcept(token)
    try:
        api.location_city("35238")
    except meteoconcept.MeteoConceptError as e:
        log("Token invalide : %s" % e)
        xbmcgui.Dialog().ok(
            ADDON.getAddonInfo("name"),
            "Token enregistré, mais le test a échoué :\n\n%s" % e)
        return

    log("Token valide.")
    xbmcgui.Dialog().ok(
        ADDON.getAddonInfo("name"),
        "Token enregistré et valide. \u2713\n\n"
        "Vous pouvez maintenant rechercher votre commune.")


# --------------------------------------------------------------------------- #
# Recherche de localisation (réglages)
# --------------------------------------------------------------------------- #
def location_search(location_index):
    token = (ADDON.getSetting("token") or "").strip()
    log("Recherche de commune ; token %s" % ("présent" if token else "VIDE"))

    if not token:
        xbmcgui.Dialog().ok(
            ADDON.getAddonInfo("name"),
            "Le token est lu vide.\n\n"
            "Saisissez le token, fermez les réglages par OK pour l'enregistrer, "
            "puis rouvrez la configuration avant de relancer la recherche.")
        return

    api = meteoconcept.MeteoConcept(token)

    keyboard = xbmc.Keyboard("", "Ville ou code postal")
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return
    text = keyboard.getText().strip()
    if not text:
        return

    try:
        cities = api.search_cities(text)
    except meteoconcept.MeteoConceptError as e:
        notify(str(e))
        return

    if not cities:
        notify("Aucune commune trouvée.")
        return

    labels = [u"%s (%s)" % (c.get("name", "?"), c.get("cp", "")) for c in cities]
    choice = xbmcgui.Dialog().select("Choisissez une commune", labels)
    if choice == -1:
        return

    city = cities[choice]
    ADDON.setSetting("Location%s" % location_index, city.get("name", ""))
    ADDON.setSetting("Location%sid" % location_index, str(city.get("insee", "")))
    notify(u"Commune enregistrée : %s" % city.get("name", ""))


# --------------------------------------------------------------------------- #
# Récupération et publication de la météo
# --------------------------------------------------------------------------- #
MAX_DAYS = 6     # Day0..Day6
MAX_DAILY = 7    # Daily.1..7 / Weekend.1..7
MAX_HOURLY = 24  # Hourly.1..24


def clear():
    """Vide toutes les catégories pour ne pas conserver les valeurs d'un
    fournisseur précédent (ex. Gismeteo) que cet addon ne réécrirait pas."""
    for p in ("Location", "Condition", "Temperature", "Wind", "WindDirection",
              "Humidity", "FeelsLike", "DewPoint", "OutlookIcon", "FanartCode",
              "ConditionIcon", "Pressure", "Precipitation"):
        clear_prop("Current.%s" % p)
    for p in ("Sunrise", "Sunset"):
        clear_prop("Today.%s" % p)
    for p in ("City", "Country", "State", "Latitude", "Longitude", "Updated"):
        clear_prop("Forecast.%s" % p)

    day = ("Title", "HighTemp", "LowTemp", "Outlook", "OutlookIcon", "FanartCode")
    for i in range(0, MAX_DAYS + 1):
        for p in day:
            clear_prop("Day%d.%s" % (i, p))

    daily = ("Title", "LongDay", "ShortDay", "LongDate", "ShortDate", "Outlook",
             "OutlookIcon", "FanartCode", "WindSpeed", "WindDirection",
             "HighTemperature", "LowTemperature", "Precipitation")
    for i in range(1, MAX_DAILY + 1):
        for p in daily:
            clear_prop("Daily.%d.%s" % (i, p))
            clear_prop("Weekend.%d.%s" % (i, p))

    hourly = ("Time", "Temperature", "Outlook", "OutlookIcon", "FanartCode",
              "WindSpeed", "WindDirection", "Precipitation", "Humidity")
    for i in range(1, MAX_HOURLY + 1):
        for p in hourly:
            clear_prop("Hourly.%d.%s" % (i, p))


def refresh_locations(city_name):
    """Publie la localisation comme PROPRIÉTÉ DE FENÊTRE (lue par le widget
    d'accueil et l'infolabel Weather.Location), pas seulement comme réglage."""
    set_prop("Location1", city_name)
    set_prop("Locations", "1")


def publish_current(entry, city_name, sunrise, sunset):
    code = entry.get("weather", 4)
    dt = parse_dt(entry.get("datetime"))
    day = is_daytime(dt, sunrise, sunset)

    label = wmap.get_label(code)
    kodi_code = wmap.get_kodi_code(code, day)

    set_prop("Current.Location", city_name)
    set_prop("Current.Condition", label)
    set_prop("Current.Temperature", entry.get("temp2m", ""))
    set_prop("Current.Wind", entry.get("wind10m", ""))
    set_prop("Current.WindDirection", wind_dir_fr(entry.get("dirwind10m")))
    set_prop("Current.Humidity", entry.get("rh2m", ""))
    set_prop("Current.OutlookIcon", "%s.png" % kodi_code)
    set_prop("Current.FanartCode", "%s" % kodi_code)
    set_prop("Current.ConditionIcon", "%s.png" % kodi_code)


def publish_daily(forecast, sunrise, sunset):
    today = datetime.date.today()
    for i, day_data in enumerate(forecast[:7]):
        n = i + 1
        code = day_data.get("weather", 4)
        kodi_code = wmap.get_kodi_code(code, True)  # icône de jour pour le résumé
        label = wmap.get_label(code)

        dt = parse_dt(day_data.get("datetime"))
        date = dt.date() if dt else (today + datetime.timedelta(days=i))
        title = JOURS_FR[date.weekday()]

        # Propriétés étendues (Arctic Zephyr & co.)
        set_prop("Daily.%d.Title" % n, title)
        set_prop("Daily.%d.LongDay" % n, title)
        set_prop("Daily.%d.ShortDay" % n, title[:3])
        set_prop("Daily.%d.LongDate" % n, u"%s %s" % (title, date.strftime("%d/%m")))
        set_prop("Daily.%d.ShortDate" % n, date.strftime("%d/%m"))
        set_prop("Daily.%d.HighTemperature" % n, day_data.get("tmax", ""))
        set_prop("Daily.%d.LowTemperature" % n, day_data.get("tmin", ""))
        set_prop("Daily.%d.Outlook" % n, label)
        set_prop("Daily.%d.OutlookIcon" % n, "%s.png" % kodi_code)
        set_prop("Daily.%d.FanartCode" % n, "%s" % kodi_code)
        set_prop("Daily.%d.WindSpeed" % n, day_data.get("wind10m", ""))
        set_prop("Daily.%d.WindDirection" % n, wind_dir_fr(day_data.get("dirwind10m")))
        set_prop("Daily.%d.Precipitation" % n, "%s%%" % day_data.get("probarain", 0))

        # Propriétés héritées (DayN.*) pour compatibilité large
        set_prop("Day%d.Title" % i, title)
        set_prop("Day%d.HighTemp" % i, day_data.get("tmax", ""))
        set_prop("Day%d.LowTemp" % i, day_data.get("tmin", ""))
        set_prop("Day%d.Outlook" % i, label)
        set_prop("Day%d.OutlookIcon" % i, "%s.png" % kodi_code)
        set_prop("Day%d.FanartCode" % i, "%s" % kodi_code)


def publish_hourly(forecast, sunrise, sunset):
    for i, hour in enumerate(forecast[:24]):
        n = i + 1
        code = hour.get("weather", 4)
        dt = parse_dt(hour.get("datetime"))
        day = is_daytime(dt, sunrise, sunset)
        kodi_code = wmap.get_kodi_code(code, day)
        label = wmap.get_label(code)

        set_prop("Hourly.%d.Time" % n, dt.strftime("%H:%M") if dt else "")
        set_prop("Hourly.%d.Temperature" % n, hour.get("temp2m", ""))
        set_prop("Hourly.%d.Outlook" % n, label)
        set_prop("Hourly.%d.OutlookIcon" % n, "%s.png" % kodi_code)
        set_prop("Hourly.%d.FanartCode" % n, "%s" % kodi_code)
        set_prop("Hourly.%d.WindSpeed" % n, hour.get("wind10m", ""))
        set_prop("Hourly.%d.WindDirection" % n, wind_dir_fr(hour.get("dirwind10m")))
        set_prop("Hourly.%d.Precipitation" % n, "%s%%" % hour.get("probarain", 0))


def fetch_weather(location_index):
    token = ADDON.getSetting("token")
    insee = ADDON.getSetting("Location%sid" % location_index)
    city_name = ADDON.getSetting("Location%s" % location_index) or u"Localisation"
    log("Récupération météo : token %s, INSEE %r, ville %r" % (
        "présent" if (token or "").strip() else "VIDE", insee, city_name))

    set_prop("WeatherProvider", "Météo Concept")
    set_prop("WeatherProviderLogo",
             os.path.join(ADDON_PATH, "resources", "icons", "logo.png"))
    # Toujours réécrire la localisation (efface l'ancienne valeur d'un autre fournisseur)
    refresh_locations(city_name)

    if not token or not insee:
        notify("Renseignez le token et la commune dans les réglages.")
        clear()
        set_prop("Current.Location", city_name)
        set_prop("Weather.IsFetched", "true")
        return

    cache_minutes = 30
    try:
        cache_minutes = int(ADDON.getSetting("cache_minutes") or 30)
    except ValueError:
        pass

    api = meteoconcept.MeteoConcept(token, cache_dir=PROFILE, cache_minutes=cache_minutes)

    try:
        # Éphéméride (jour/nuit) — best effort, ne bloque pas si indisponible
        sunrise = sunset = None
        try:
            eph = api.ephemeride(insee, 0).get("ephemeride", {})
            sunrise, sunset = eph.get("sunrise"), eph.get("sunset")
        except meteoconcept.MeteoConceptError:
            pass

        hourly = api.next_hours(insee).get("forecast", [])
        daily = api.daily(insee).get("forecast", [])
    except meteoconcept.MeteoConceptError as e:
        log("Erreur API : %s" % e)
        notify(str(e))
        set_prop("Weather.IsFetched", "true")
        return

    clear()

    if hourly:
        publish_current(hourly[0], city_name, sunrise, sunset)
        publish_hourly(hourly, sunrise, sunset)
    if daily:
        publish_daily(daily, sunrise, sunset)

    # Métadonnées de localisation et éphéméride
    set_prop("Forecast.City", city_name)
    set_prop("Forecast.Updated", datetime.datetime.now().strftime("%d/%m %H:%M"))
    if sunrise and sunset:
        set_prop("Today.Sunrise", sunrise)
        set_prop("Today.Sunset", sunset)

    # Drapeaux "données prêtes"
    for flag in ("Current.IsFetched", "Today.IsFetched",
                 "Daily.IsFetched", "Hourly.IsFetched", "Weather.IsFetched"):
        set_prop(flag, "true")

    log("Météo publiée pour %s (INSEE %s)" % (city_name, insee))


# --------------------------------------------------------------------------- #
# Entrée
# --------------------------------------------------------------------------- #
def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    log("Appel de l'addon avec argument : %r" % arg)
    if arg.startswith("Location"):
        location_search(arg.replace("Location", "") or "1")
    elif arg == "TestToken":
        test_token()
    else:
        fetch_weather(arg)


if __name__ == "__main__":
    main()
