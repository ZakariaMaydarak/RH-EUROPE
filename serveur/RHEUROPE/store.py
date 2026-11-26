"""
Stockage des données de HR EUROPE : fichiers JSON dans le dossier de données de
l'application (DATA_DIR, /home/data/portail/RHEUROPE en production).

- Lecture avec cache (date de modification du fichier) et nouvelle tentative si la
  lecture tombe pendant un remplacement de fichier.
- Écriture atomique : fichier temporaire puis os.replace.
- Historique (journal d'audit) : un fichier JSON Lines, une ligne par action,
  ajoutée sous verrou (jamais réécrit).
"""

import copy
import io
import json
import os
import threading
import time
import uuid

FICHIER_COLLABORATEURS = "collaborateurs.json"
FICHIER_REFERENTIELS = "referentiels.json"
FICHIER_PARAMETRES = "parametres.json"
FICHIER_AUTOMATISATION = "automatisation.json"
FICHIER_HISTORIQUE = "historique.jsonl"


class FichierIllisible(Exception):
    """Fichier présent mais illisible : on ne doit surtout pas le réécrire."""


class Store:
    def __init__(self, dossier):
        self.dossier = dossier
        os.makedirs(dossier, exist_ok=True)
        # Verrou ré-entrant : une opération « lire → modifier → écrire » le garde
        # du début à la fin.
        self.verrou = threading.RLock()
        self._cache = {}

    def chemin(self, nom):
        return os.path.join(self.dossier, nom)

    # ------------------------------------------------------------------ JSON
    def lire(self, nom, defaut):
        chemin = self.chemin(nom)
        for essai in range(4):
            try:
                mtime = os.stat(chemin).st_mtime_ns
            except FileNotFoundError:
                return copy.deepcopy(defaut)
            en_cache = self._cache.get(nom)
            if en_cache and en_cache[0] == mtime:
                return copy.deepcopy(en_cache[1])
            try:
                with io.open(chemin, encoding="utf-8") as fh:
                    donnees = json.load(fh)
                self._cache[nom] = (mtime, donnees)
                return copy.deepcopy(donnees)
            except FileNotFoundError:
                return copy.deepcopy(defaut)
            except (ValueError, PermissionError, OSError):
                if essai == 3:
                    raise FichierIllisible(nom)
                time.sleep(0.05 * (essai + 1))
        raise FichierIllisible(nom)

    def ecrire(self, nom, donnees):
        chemin = self.chemin(nom)
        tmp = f"{chemin}.{uuid.uuid4().hex[:8]}.tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(donnees, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, chemin)
        self._cache.pop(nom, None)

    # ------------------------------------------------------------ Historique
    def journaliser(self, entree):
        ligne = json.dumps(entree, ensure_ascii=False)
        with self.verrou:
            with io.open(self.chemin(FICHIER_HISTORIQUE), "a", encoding="utf-8") as fh:
                fh.write(ligne + "\n")

    def historique(self):
        """Toutes les entrées, de la plus ancienne à la plus récente."""
        entrees = []
        try:
            with io.open(self.chemin(FICHIER_HISTORIQUE), encoding="utf-8") as fh:
                for ligne in fh:
                    ligne = ligne.strip()
                    if not ligne:
                        continue
                    try:
                        entrees.append(json.loads(ligne))
                    except ValueError:
                        continue   # ligne tronquée (arrêt brutal) : ignorée
        except FileNotFoundError:
            pass
        return entrees

    def reecrire_historique(self, entrees):
        """Réservé à l'effacement RGPD d'un collaborateur (anonymisation)."""
        with self.verrou:
            chemin = self.chemin(FICHIER_HISTORIQUE)
            tmp = f"{chemin}.{uuid.uuid4().hex[:8]}.tmp"
            with io.open(tmp, "w", encoding="utf-8") as fh:
                for e in entrees:
                    fh.write(json.dumps(e, ensure_ascii=False) + "\n")
            os.replace(tmp, chemin)
