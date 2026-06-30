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


def infer_subscription(headers):
    """Déduit le palier d'abonnement à partir des en-têtes HTTP de quota.

    Météo Concept propose les mêmes routes/fonctions sur toutes les formules ;
    seul le VOLUME d'appels diffère (Basique = 500/jour, Standard/Premium = plus).
    On lit donc une éventuelle limite quotidienne dans les en-têtes.

    Retourne (label, detail) :
      - ("Basique", "500 appels/jour")          si limite <= 500
      - ("Standard ou Premium", "N appels/jour") si limite > 500
      - (None, None)                              si l'API n'expose aucun quota
    """
    limit = None
    for key, value in headers.items():
        k = key.lower()
        if ("limit" in k or "quota" in k) and "remaining" not in k and "reset" not in k:
            digits = "".join(ch for ch in str(value) if ch.isdigit())
            if digits:
                limit = int(digits)
                break
    if limit is None:
        return None, None
    if limit <= 500:
        return "Basique", "%d appels/jour (formule gratuite)" % limit
    return "Standard ou Premium", "%d appels/jour (formule payante)" % limit


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
