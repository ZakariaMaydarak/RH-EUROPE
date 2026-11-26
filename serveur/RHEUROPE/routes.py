"""
RHEUROPE — HR EUROPE  (modèle d'application du Portail Apps Adagio)

Partie SERVEUR de l'app : un Blueprint Flask monté par le portail sur /RHEUROPE/.
Le portail s'occupe de l'authentification (Microsoft Entra ID / Easy Auth) et
de l'accès à l'app (App Role `App.RHEUROPE`) : ici on ne gère que le métier.

Règles (voir CLAUDE.md du dépôt) :
  - tout le code de l'app vit dans ce dossier (jamais dans le portail) ;
  - données persistantes : dans DATA_DIR ci-dessous (disque /home du serveur),
    JAMAIS dans ce dossier (il est remplacé à chaque déploiement) ;
  - le front (SPA Vite) est copié dans static_files/ par deploiement/construire.ps1.
"""

import io
import json
import os
import threading

from flask import Blueprint, abort, jsonify, request, send_from_directory

from shared import role_store
from shared.auth import get_authenticated_user

SLUG = "RHEUROPE"

APP_METADATA = {
    "name": "HR EUROPE",
    "description": "Application web de gestion des collaborateurs des hôtels Adagio en Europe",
    "icon": "RH",                       # 1 à 3 lettres, ou un emoji
    "category": "Outils Adagio",        # catégorie EXISTANTE de l'accueil du portail
    "version": "0.1.0",
    "required_role": "App.RHEUROPE",      # App Role Entra (créé par l'admin du portail)
    # Rôles INTERNES (optionnel) : gérés par les propriétaires de l'app dans la
    # console /admin du portail. Supprimer ce bloc si l'app n'en a pas besoin.
    "role_schema": {
        "label": "Rôles HR EUROPE",
        "roles": [
            {"value": "admin", "label": "Administrateur"},
            {"value": "utilisateur", "label": "Utilisateur"},
            {"value": "aucun", "label": "Aucun accès"},
        ],
        "default_role": "utilisateur",
    },
}

bp = Blueprint(SLUG, __name__, static_folder=None)
BUILD_DIR = os.path.join(os.path.dirname(__file__), "static_files")

# Données persistantes de l'app : /home/data/portail/RHEUROPE en production
# (survit aux déploiements), ./data/RHEUROPE en local.
DATA_DIR = os.path.join(role_store.DATA_DIR, SLUG)
os.makedirs(DATA_DIR, exist_ok=True)
_verrou = threading.Lock()


# --------------------------------------------------------------------------- #
# Identité et rôle interne
# --------------------------------------------------------------------------- #
def _identite():
    user = get_authenticated_user(request.headers)
    email = (user.get("name") or "").strip().lower()
    if not email or "@" not in email:
        return {"email": "dev@local", "nom": "Développeur (local)", "role": "admin"}   # dev local
    entree = role_store.get_user(SLUG, email)
    if entree is None:   # 1re visite : rôle par défaut, ajustable dans la console /admin
        entree = role_store.upsert_user(SLUG, email, {
            "role": APP_METADATA["role_schema"]["default_role"],
            "name": user.get("display_name") or email, "source": "auto"})
    return {"email": email, "nom": user.get("display_name") or email, "role": entree.get("role", "aucun")}


def _exiger(*roles):
    ident = _identite()
    if ident["role"] not in roles:
        abort(403, description="Action non autorisée pour votre rôle.")
    return ident


@bp.errorhandler(400)
@bp.errorhandler(403)
@bp.errorhandler(404)
def _erreur_json(err):
    if request.path.startswith(f"/{SLUG}/api/"):
        return jsonify({"error": getattr(err, "description", str(err))}), err.code
    return err


# --------------------------------------------------------------------------- #
# API (exemples)
# --------------------------------------------------------------------------- #
@bp.route("/api/me")
def api_me():
    return jsonify(_identite())


@bp.route("/api/notes", methods=["GET"])
def api_notes():
    _exiger("admin", "utilisateur")
    return jsonify(_lire("notes.json", []))


@bp.route("/api/notes", methods=["POST"])
def api_ajouter_note():
    ident = _exiger("admin", "utilisateur")
    texte = str((request.get_json(silent=True) or {}).get("texte") or "").strip()
    if not texte:
        abort(400, description="Texte obligatoire.")
    with _verrou:
        notes = _lire("notes.json", [])
        notes.insert(0, {"texte": texte[:500], "par": ident["email"]})
        _ecrire("notes.json", notes[:200])
    return jsonify({"ok": True})


def _lire(nom, defaut):
    try:
        with io.open(os.path.join(DATA_DIR, nom), encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return defaut


def _ecrire(nom, donnees):
    chemin = os.path.join(DATA_DIR, nom)
    with io.open(chemin + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(donnees, fh, ensure_ascii=False, indent=1)
    os.replace(chemin + ".tmp", chemin)   # écriture atomique


# --------------------------------------------------------------------------- #
# Déploiement : le portail demande s'il peut recharger (facultatif).
# Renvoyer un message si une tâche ne doit pas être interrompue, sinon None.
# --------------------------------------------------------------------------- #
def deploiement_occupe():
    return None


# Tâches planifiées éventuelles : ne PAS les démarrer pendant le contrôle d'un
# déploiement (le portail importe l'app une fois à blanc pour la vérifier).
if os.environ.get("PORTAIL_VALIDATION_DEPLOIEMENT") != "1":
    pass  # ex. démarrer ici un APScheduler (un seul processus gunicorn)


# --------------------------------------------------------------------------- #
# SPA (front Vite buildé dans static_files/)
# --------------------------------------------------------------------------- #
@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def servir(path):
    if path.startswith("api/"):
        abort(404, description="Endpoint inconnu.")
    if not os.path.isdir(BUILD_DIR):
        abort(503, description="Front non construit : lancer deploiement/construire.ps1 (ou outils/lancer-en-local.ps1).")
    demande = os.path.normpath(os.path.join(BUILD_DIR, path))
    if not demande.startswith(os.path.abspath(BUILD_DIR)):
        abort(403)
    if path and os.path.isfile(demande) and not path.endswith("index.html"):
        resp = send_from_directory(BUILD_DIR, path)
        if path.startswith("assets/"):          # noms hachés par Vite : immuables
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp
    resp = send_from_directory(BUILD_DIR, "index.html", max_age=0)   # jamais en cache
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp
