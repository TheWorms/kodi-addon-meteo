# -*- coding: utf-8 -*-
"""
meteoconcept.py
---------------
Client minimal pour l'API Météo Concept (https://api.meteo-concept.com).
Sans dépendance externe (urllib uniquement) + cache fichier pour rester
sous le quota gratuit de 500 requêtes/jour.
"""

import os
import json
import time
import hashlib
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "https://api.meteo-concept.com/api"

STATUS_MESSAGES = {
    400: "Paramètre manquant, valeur incorrecte ou quota dépassé",
    401: "Authentification échouée : token absent ou invalide",
    403: "Action non autorisée pour cet abonnement",
    404: "URL inconnue",
    500: "Erreur interne du serveur Météo Concept",
    503: "API momentanément indisponible",
}


class MeteoConceptError(Exception):
    pass


def _read_daily_limit(headers):
    """Cherche une limite d'appels quotidienne dans les en-têtes HTTP.
    Retourne un entier ou None si rien n'est exposé."""
    for key, value in headers.items():
        k = key.lower()
        if ("limit" in k or "quota" in k) and "remaining" not in k and "reset" not in k:
            digits = "".join(ch for ch in str(value) if ch.isdigit())
            if digits:
                return int(digits)
    return None


def infer_subscription(headers, is_premium):
    """Déduit le palier d'abonnement Météo Concept.

    Les fonctions diffèrent ainsi (cf. page tarifs) :
      - Basique & Standard : mêmes routes ; seul le volume d'appels change
        (Basique = 500/jour gratuit, Standard = plus, payant).
      - Premium : seul à débloquer indice UV, archives/stats, prévisions
        horaires/tri-horaires sur 14 j et cartes.

    Méthode :
      - Premium est détecté en amont en testant une route exclusive
        (indice UV) : `is_premium` vaut True/False/None.
      - Si non Premium, on départage Basique/Standard via le quota.

    Retourne (label, detail).
    """
    if is_premium is True:
        return "Premium", u"indice UV, archives et cartes accessibles"

    limit = _read_daily_limit(headers)
    if is_premium is False:
        # Route UV refusée (403) -> forcément Basique ou Standard
        if limit is not None and limit > 500:
            return "Standard", u"%d appels/jour (formule payante)" % limit
        if limit is not None:
            return "Basique", u"%d appels/jour (formule gratuite)" % limit
        return "Basique ou Standard", u"indice UV non accessible ; quota non communiqué"

    # is_premium indéterminé (erreur réseau sur le test UV) : on se rabat sur le quota
    if limit is not None and limit <= 500:
        return "Basique", u"%d appels/jour" % limit
    if limit is not None:
        return "Standard ou Premium", u"%d appels/jour" % limit
    return None, None


class MeteoConcept(object):
    def __init__(self, token, cache_dir=None, cache_minutes=30):
        self.token = (token or "").strip()
        self.cache_dir = cache_dir
        self.cache_minutes = max(0, int(cache_minutes))
        if self.cache_dir and not os.path.isdir(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
            except OSError:
                self.cache_dir = None

    # ------------------------------------------------------------------ #
    # Cache
    # ------------------------------------------------------------------ #
    def _cache_path(self, url):
        if not self.cache_dir:
            return None
        key = hashlib.md5(url.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, "mc_%s.json" % key)

    def _read_cache(self, path):
        if not path or not os.path.isfile(path):
            return None
        if self.cache_minutes <= 0:
            return None
        age = time.time() - os.path.getmtime(path)
        if age > self.cache_minutes * 60:
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, OSError):
            return None

    def _write_cache(self, path, data):
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except OSError:
            pass

    # ------------------------------------------------------------------ #
    # Requête générique
    # ------------------------------------------------------------------ #
    def _request(self, path, params):
        if not self.token:
            raise MeteoConceptError("Token Météo Concept manquant (à renseigner dans les réglages).")

        params = dict(params)
        params["token"] = self.token
        url = "%s%s?%s" % (BASE_URL, path, urllib.parse.urlencode(params))

        cache_path = self._cache_path(url)
        cached = self._read_cache(cache_path)
        if cached is not None:
            return cached

        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "kodi-addon-meteo/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
        except urllib.error.HTTPError as e:
            msg = STATUS_MESSAGES.get(e.code, "Erreur HTTP %s" % e.code)
            raise MeteoConceptError(msg)
        except urllib.error.URLError as e:
            raise MeteoConceptError("Connexion impossible : %s" % e.reason)
        except ValueError:
            raise MeteoConceptError("Réponse illisible de l'API.")

        self._write_cache(cache_path, data)
        return data

    # ------------------------------------------------------------------ #
    # Routes utilisées par l'addon
    # ------------------------------------------------------------------ #
    def probe_premium(self, insee="35238"):
        """Teste la route exclusivement Premium « indice UV »
        (/forecast/uv/daily/0). Sur Basique/Standard l'API renvoie 403.

        Retourne :
          - True  si Premium (route autorisée : 200, ou 400 = atteinte mais
                   paramètre rejeté après autorisation)
          - False si 403 (route refusée pour l'abonnement)
          - None  si indéterminé (token absent, panne réseau, 401/500…)
        """
        if not self.token:
            return None
        params = {"insee": insee, "token": self.token}
        url = "%s/forecast/uv/daily/0?%s" % (BASE_URL, urllib.parse.urlencode(params))
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json",
                     "User-Agent": "kodi-addon-meteo/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
            return True
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return False
            if e.code == 400:
                return True   # route atteinte/autorisée, simple souci de paramètre
            return None       # 401/404/500/503 : non concluant
        except urllib.error.URLError:
            return None

    def validate(self, insee="35238"):
        """Valide le token via une route légère SANS cache, et renvoie un dict
        {'data', 'headers'} pour pouvoir lire d'éventuels en-têtes de quota.
        Lève MeteoConceptError si le token est invalide / la requête échoue."""
        if not self.token:
            raise MeteoConceptError("Token Météo Concept manquant.")
        params = {"insee": insee, "token": self.token}
        url = "%s/location/city?%s" % (BASE_URL, urllib.parse.urlencode(params))
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json",
                     "User-Agent": "kodi-addon-meteo/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                headers = {k.lower(): v for k, v in resp.headers.items()}
            data = json.loads(raw)
        except urllib.error.HTTPError as e:
            msg = STATUS_MESSAGES.get(e.code, "Erreur HTTP %s" % e.code)
            raise MeteoConceptError(msg)
        except urllib.error.URLError as e:
            raise MeteoConceptError("Connexion impossible : %s" % e.reason)
        except ValueError:
            raise MeteoConceptError("Réponse illisible de l'API.")
        return {"data": data, "headers": headers}

    def location_city(self, insee="35238"):
        """Route légère (commune par INSEE) — sert à valider le token."""
        return self._request("/location/city", {"insee": insee})

    def search_cities(self, text):
        """Recherche de communes par nom ou code postal."""
        data = self._request("/location/cities", {"search": text})
        return data.get("cities", [])

    def daily(self, insee):
        """Prévisions journalières sur 14 jours."""
        return self._request("/forecast/daily", {"insee": insee})

    def next_hours(self, insee):
        """Prévisions heure par heure sur les 12 prochaines heures."""
        return self._request("/forecast/nextHours", {"insee": insee, "hourly": "true"})

    def ephemeride(self, insee, day=0):
        """Lever / coucher du soleil pour déterminer jour/nuit."""
        return self._request("/ephemeride/%d" % day, {"insee": insee})
