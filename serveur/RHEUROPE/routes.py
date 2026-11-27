"""
RHEUROPE — HR EUROPE : référentiel unique des collaborateurs des hôtels Adagio
en Europe (Employee Master Data).

Partie SERVEUR : Blueprint Flask monté par le portail sur /RHEUROPE/. Le portail
gère la connexion (Microsoft Entra ID / Easy Auth) et l'accès à l'app (App Role
`App.RHEUROPE`) ; ici : rôles internes, périmètre, métier.

Rôles internes (console Administration du portail ou page Utilisateurs de l'app) :
  - admin : tous les établissements européens, référentiels, paramètres,
            utilisateurs, exports, qualité, historique complet ;
  - gm    : directeur d'hôtel, limité à ses établissements (champ « sites ») ;
  - aucun : pas d'accès aux données.
Règle à la 1re connexion : App.Admin du portail → admin ; adresse hXXXX@… → gm
de l'hôtel HXXXX ; sinon aucun (données personnelles : rien d'ouvert par défaut).

Données : DATA_DIR/RHEUROPE (/home/data/portail/RHEUROPE en production).
"""

import csv
import io
import os
import re
import threading
from datetime import datetime

from flask import Blueprint, Response, abort, jsonify, request, send_from_directory

from shared import role_store
from shared.auth import get_authenticated_user

from . import export as X
from . import i18n
from . import indicateurs as I
from . import referentiels as R
from . import service as SV
from .i18n import _
from .store import FICHIER_AUTOMATISATION, Store

SLUG = "RHEUROPE"

APP_METADATA = {
    "name": "HR EUROPE",
    "description": "Application web de gestion des collaborateurs des hôtels Adagio en Europe",
    "icon": "RH",
    "category": "Outils Adagio",
    "version": "1.1.0",
    "required_role": "App.RHEUROPE",
    "role_schema": {
        "label": "Rôles HR EUROPE",
        "roles": [
            {"value": "admin", "label": "Administrateur (tous les établissements)"},
            {"value": "gm", "label": "Directeur d'hôtel (ses établissements)"},
            {"value": "aucun", "label": "Aucun accès"},
        ],
        "default_role": "aucun",
        "scope": {
            "field": "sites",
            "label": "Établissements",
            "roles": ["gm"],
            "uppercase": True,
            "picker": {
                "options_endpoint": f"/{SLUG}/api/etablissements/options",
                "value_key": "rid",
                "label_key": "name",
            },
        },
    },
}
ROLES = {r["value"]: r["label"] for r in APP_METADATA["role_schema"]["roles"]}

bp = Blueprint(SLUG, __name__, static_folder=None)
BUILD_DIR = os.path.join(os.path.dirname(__file__), "static_files")

DATA_DIR = os.path.join(role_store.DATA_DIR, SLUG)
store = Store(DATA_DIR)


# --------------------------------------------------------------------------- #
# Identité, rôle interne, périmètre
# --------------------------------------------------------------------------- #
def regle_defaut(email, roles_entra):
    if "App.Admin" in (roles_entra or []):
        return {"role": "admin", "sites": []}
    m = re.match(r"^(h[0-9a-z]{4})", email.split("@")[0], re.IGNORECASE)
    if m:
        return {"role": "gm", "sites": [m.group(1).upper()]}
    return {"role": "aucun", "sites": []}


def _identite():
    user = get_authenticated_user(request.headers)
    email = (user.get("name") or "").strip().lower()
    if not email or "@" not in email:
        # Développement local (pas d'Easy Auth) : profil simulé.
        role = os.environ.get("RHEUROPE_DEV_ROLE", "admin")
        sites = [s.strip().upper() for s in os.environ.get("RHEUROPE_DEV_SITES", "").split(",") if s.strip()]
        return {"email": "dev@local", "nom": "Développeur (local)", "role": role, "sites": sites}
    entree = role_store.get_user(SLUG, email)
    if entree is None:
        entree = role_store.upsert_user(SLUG, email, {
            **regle_defaut(email, user.get("roles")),
            "name": user.get("display_name") or email, "source": "auto"})
    role = entree.get("role", "aucun")
    return {"email": email, "nom": user.get("display_name") or entree.get("name") or email,
            "role": role if role in ROLES else "aucun",
            "sites": [str(s).upper() for s in entree.get("sites") or []]}


def _exiger(*roles):
    ident = _identite()
    if ident["role"] not in roles:
        abort(403, description=_("Action non autorisée pour votre profil."))
    return ident


def _perimetre(ident):
    """None = tous les établissements (admin) ; sinon l'ensemble des codes."""
    return None if ident["role"] == "admin" else set(ident["sites"])


def _corps():
    return request.get_json(silent=True) or {}


# --------------------------------------------------------------------------- #
# Langue : en-tête X-Langue envoyé par le front (choix de l'utilisateur), sinon
# préférence enregistrée, sinon français. Les messages d'erreur suivent.
# --------------------------------------------------------------------------- #
FICHIER_PREFERENCES = "preferences.json"


def _langue_preferee(email):
    return (store.lire(FICHIER_PREFERENCES, {}).get(email) or {}).get("langue")


@bp.before_request
def _choisir_langue():
    demandee = (request.headers.get("X-Langue") or request.args.get("langue") or "").lower()
    if demandee not in i18n.LANGUES:
        user = get_authenticated_user(request.headers)
        email = (user.get("name") or "").strip().lower()
        demandee = _langue_preferee(email if "@" in email else "dev@local") or "fr"
    i18n.definir(demandee)


@bp.errorhandler(400)
@bp.errorhandler(403)
@bp.errorhandler(404)
@bp.errorhandler(409)
@bp.errorhandler(413)
def _erreur_json(err):
    if request.path.startswith(f"/{SLUG}/api/"):
        return jsonify({"error": getattr(err, "description", str(err))}), err.code
    return err


@bp.errorhandler(SV.ErreurMetier)
def _erreur_metier(err):
    return jsonify({"error": err.message, **err.extra}), err.code


# --------------------------------------------------------------------------- #
# Identité et référentiels
# --------------------------------------------------------------------------- #
@bp.route("/api/me")
def api_me():
    ident = _identite()
    return jsonify({**ident, "role_libelle": _(ROLES.get(ident["role"], ident["role"])),
                    "aujourd_hui": SV.aujourd_hui().isoformat(),
                    "langue": _langue_preferee(ident["email"]), "langues": i18n.LANGUES})


@bp.route("/api/me/langue", methods=["PUT"])
def api_me_langue():
    """Langue d'affichage choisie par l'utilisateur (tous profils), mémorisée côté
    serveur pour la retrouver sur un autre poste."""
    ident = _identite()
    langue = str(_corps().get("langue") or "").lower()
    if langue not in i18n.LANGUES:
        abort(400, description=_("Langue non prise en charge."))
    with store.verrou:
        prefs = store.lire(FICHIER_PREFERENCES, {})
        prefs.setdefault(ident["email"], {})["langue"] = langue
        store.ecrire(FICHIER_PREFERENCES, prefs)
    i18n.definir(langue)
    return jsonify({"ok": True, "langue": langue})


@bp.route("/api/etablissements/options")
def api_etablissements_options():
    """Liste des établissements pour le sélecteur de périmètre de la console
    Administration du portail (aucune donnée personnelle)."""
    return jsonify([{"rid": e["code"], "name": f"{e['code']} — {e['libelle']}"}
                    for e in SV.refs(store)["etablissements"]])


@bp.route("/api/referentiels")
def api_referentiels():
    _exiger("admin", "gm")
    return jsonify({"types": R.TYPES, "referentiels": SV.refs(store)})


@bp.route("/api/referentiels/<type_>", methods=["PUT"])
def api_referentiel_enregistrer(type_):
    ident = _exiger("admin")
    if type_ not in R.TYPES:
        abort(404, description=_("Référentiel inconnu."))
    return jsonify({"ok": True, "elements": SV.enregistrer_referentiel(store, type_, _corps().get("elements"), ident)})


@bp.route("/api/referentiels/etablissements/import", methods=["POST"])
def api_import_etablissements():
    """Import Excel / CSV : colonnes code (ou rid), nom (ou libellé), pays.
    Les établissements existants sont mis à jour, les nouveaux ajoutés."""
    ident = _exiger("admin")
    fichier = request.files.get("fichier")
    if not fichier or not fichier.filename:
        abort(400, description=_("Fichier manquant."))
    contenu = fichier.read(5 * 1024 * 1024 + 1)
    if len(contenu) > 5 * 1024 * 1024:
        abort(413, description=_("Fichier trop volumineux (5 Mo maximum)."))
    try:
        lignes = _lire_tableau(fichier.filename, contenu)
    except Exception:  # noqa: BLE001
        abort(400, description=_("Fichier illisible : utilisez un Excel (.xlsx) ou un CSV."))
    if not lignes:
        abort(400, description=_("Fichier vide."))
    entete = [_normal(h) for h in lignes[0]]

    def colonne(*noms):
        return next((i for i, h in enumerate(entete) if h in noms), None)

    i_code = colonne("code", "rid", "codehotel", "codeetablissement", "etablissement")
    i_nom = colonne("nom", "libelle", "name", "nometablissement", "hotel")
    i_pays = colonne("pays", "codepays", "country", "paysiso")
    if None in (i_code, i_nom, i_pays):
        abort(400, description=_("Colonnes attendues : code, nom, pays (code ISO à 2 lettres ou nom du pays)."))
    refs = SV.refs(store)
    pays_par_nom = {_normal(p["libelle"]): p["code"] for p in refs["pays"]}
    actuels = {e["code"]: dict(e) for e in refs["etablissements"]}
    ajoutes, maj = 0, 0
    for ligne in lignes[1:]:
        def val(i):
            return str(ligne[i]).strip() if i < len(ligne) and ligne[i] is not None else ""
        code, nom, pays = val(i_code).upper(), val(i_nom), val(i_pays)
        if not code:
            continue
        pays = pays.upper() if len(pays) == 2 else pays_par_nom.get(_normal(pays), pays.upper())
        if code in actuels:
            actuels[code].update(libelle=nom or actuels[code]["libelle"], pays=pays)
            maj += 1
        else:
            actuels[code] = {"code": code, "libelle": nom, "pays": pays, "actif": True}
            ajoutes += 1
    elements = SV.enregistrer_referentiel(store, "etablissements", list(actuels.values()), ident)
    return jsonify({"ok": True, "ajoutes": ajoutes, "mis_a_jour": maj, "elements": elements})


def _normal(texte):
    from .validation import sans_accents
    return re.sub(r"[^a-z0-9]", "", sans_accents(str(texte or "")).lower())


def _lire_tableau(nom, contenu):
    if nom.lower().endswith((".xlsx", ".xlsm")):
        from openpyxl import load_workbook
        ws = load_workbook(io.BytesIO(contenu), read_only=True, data_only=True).active
        ws.reset_dimensions()
        return [list(r) for r in ws.iter_rows(values_only=True) if any(v not in (None, "") for v in r)]
    texte = contenu.decode("utf-8-sig", errors="replace")
    sep = ";" if texte.count(";") >= texte.count(",") else ","
    return [r for r in csv.reader(io.StringIO(texte), delimiter=sep) if any(x.strip() for x in r)]


# --------------------------------------------------------------------------- #
# Tableau de bord
# --------------------------------------------------------------------------- #
@bp.route("/api/tableau-de-bord")
def api_tableau_de_bord():
    ident = _exiger("admin", "gm")
    perimetre = _perimetre(ident)
    collabs = [c for c in SV.collaborateurs(store) if SV.dans_perimetre(c, perimetre)]
    etab = (request.args.get("etablissement") or "").upper()
    if etab:
        collabs = [c for c in collabs if c.get("etablissement") == etab]
    return jsonify(I.tableau_de_bord(collabs, SV.refs(store), SV.aujourd_hui()))


# --------------------------------------------------------------------------- #
# Collaborateurs
# --------------------------------------------------------------------------- #
CHAMPS_LISTE = ("id", "matricule", "nom", "prenom", "sexe", "email", "date_naissance", "date_debut", "date_fin",
                "type_contrat", "service", "etablissement", "poste", "manager_id", "statut", "date_sortie",
                "motif_sortie", "modifie_le")


@bp.route("/api/collaborateurs")
def api_collaborateurs():
    ident = _exiger("admin", "gm")
    perimetre = _perimetre(ident)
    tous = SV.collaborateurs(store)
    par_id = {c["id"]: c for c in tous}
    res = []
    for c in tous:
        if not SV.dans_perimetre(c, perimetre):
            continue
        m = par_id.get(c.get("manager_id")) or {}
        res.append({**{k: c.get(k, "") for k in CHAMPS_LISTE},
                    "manager_nom": f"{m.get('prenom', '')} {m.get('nom', '')}".strip()})
    return jsonify(res)


def _resume_manager(m):
    if not m:
        return None
    return {"id": m["id"], "matricule": m.get("matricule"), "nom": m.get("nom"), "prenom": m.get("prenom"),
            "etablissement": m.get("etablissement"), "statut": m.get("statut")}


@bp.route("/api/collaborateurs/<id_>")
def api_collaborateur(id_):
    ident = _exiger("admin", "gm")
    tous = SV.collaborateurs(store)
    c = next((x for x in tous if x["id"] == id_), None)
    if c is None or not SV.dans_perimetre(c, _perimetre(ident)):
        abort(404, description=_("Collaborateur introuvable ou hors de votre périmètre."))
    manager = next((x for x in tous if x["id"] == c.get("manager_id")), None)
    equipe = [_resume_manager(x) for x in tous if x.get("manager_id") == id_ and x.get("statut") == "actif"]
    historique = [e for e in reversed(store.historique()) if e.get("collaborateur_id") == id_][:100]
    return jsonify({"collaborateur": c, "manager": _resume_manager(manager), "equipe": equipe,
                    "historique": historique})


@bp.route("/api/collaborateurs/verifier", methods=["POST"])
def api_verifier():
    ident = _exiger("admin", "gm")
    corps = _corps()
    erreurs, alertes = SV.verifier_fiche(store, corps.get("collaborateur"), _perimetre(ident), corps.get("id"))
    return jsonify({"erreurs": erreurs, "alertes": alertes})


@bp.route("/api/collaborateurs", methods=["POST"])
def api_creer():
    ident = _exiger("admin", "gm")
    corps = _corps()
    fiche = SV.creer(store, corps.get("collaborateur"), ident, _perimetre(ident),
                     bool(corps.get("confirmer_doublon")))
    return jsonify({"ok": True, "collaborateur": fiche}), 201


@bp.route("/api/collaborateurs/<id_>", methods=["PUT"])
def api_modifier(id_):
    ident = _exiger("admin", "gm")
    corps = _corps()
    fiche, diff = SV.modifier(store, id_, corps.get("collaborateur"), ident, _perimetre(ident),
                              bool(corps.get("confirmer_doublon")))
    return jsonify({"ok": True, "collaborateur": fiche, "changements": len(diff)})


@bp.route("/api/collaborateurs/<id_>/desactiver", methods=["POST"])
def api_desactiver(id_):
    ident = _exiger("admin", "gm")
    corps = _corps()
    fiche, programme = SV.desactiver(store, id_, ident, _perimetre(ident), corps.get("date_sortie"),
                                     corps.get("motif_sortie"), corps.get("commentaire") or "")
    return jsonify({"ok": True, "collaborateur": fiche, "programme": programme})


@bp.route("/api/collaborateurs/<id_>/reactiver", methods=["POST"])
def api_reactiver(id_):
    ident = _exiger("admin", "gm")
    return jsonify({"ok": True, "collaborateur": SV.reactiver(store, id_, ident, _perimetre(ident), _corps())})


@bp.route("/api/collaborateurs/<id_>", methods=["DELETE"])
def api_supprimer(id_):
    ident = _exiger("admin")
    if _corps().get("confirmation") != "EFFACER":
        abort(400, description=_("Confirmation manquante : saisir EFFACER."))
    SV.supprimer(store, id_, ident)
    return jsonify({"ok": True})


@bp.route("/api/managers")
def api_managers():
    """Recherche d'un manager parmi les collaborateurs ACTIFS de toute l'Europe
    (informations minimales : identité, poste, établissement)."""
    _exiger("admin", "gm")
    from .validation import sans_accents
    q = sans_accents(request.args.get("q") or "").lower().strip()
    exclure = request.args.get("exclure") or ""
    etab = (request.args.get("etablissement") or "").upper()
    idx = R.index(SV.refs(store))
    res = []
    for c in SV.collaborateurs(store):
        if c.get("statut") != "actif" or c["id"] == exclure:
            continue
        texte = sans_accents(f"{c.get('prenom')} {c.get('nom')} {c.get('nom')} {c.get('prenom')} {c.get('matricule')}").lower()
        if q and q not in texte:
            continue
        if not q and etab and c.get("etablissement") != etab:
            continue
        res.append({**_resume_manager(c), "poste": R.libelle(idx, "postes", c.get("poste"))})
    res.sort(key=lambda x: (x["etablissement"] != etab, x["nom"] or "", x["prenom"] or ""))
    return jsonify(res[:25])


@bp.route("/api/matricule/generer", methods=["POST"])
def api_generer_matricule():
    ident = _exiger("admin", "gm")
    return jsonify({"matricule": SV.generer(store, ident, _corps().get("etablissement"))})


# --------------------------------------------------------------------------- #
# Historique, qualité, export (administrateur ; historique filtré pour un GM)
# --------------------------------------------------------------------------- #
ACTIONS = {
    "creation": "Création", "modification": "Modification", "desactivation": "Désactivation",
    "sortie_programmee": "Sortie programmée", "desactivation_auto": "Désactivation automatique",
    "reactivation": "Réactivation", "effacement": "Effacement RGPD", "referentiel": "Référentiel",
    "parametres": "Paramètres", "utilisateur": "Utilisateur", "export": "Export",
}


@bp.route("/api/historique")
def api_historique():
    ident = _exiger("admin", "gm")
    perimetre = _perimetre(ident)
    action = request.args.get("action") or ""
    q = (request.args.get("q") or "").lower().strip()
    limite = min(int(request.args.get("limite") or 300), 2000)
    res = []
    for e in reversed(store.historique()):
        if perimetre is not None and (not e.get("collaborateur_id") or e.get("etablissement") not in perimetre):
            continue
        if action and e.get("action") != action:
            continue
        if q and q not in " ".join(str(e.get(k) or "") for k in ("nom_complet", "matricule", "par", "par_nom",
                                                                  "etablissement", "detail")).lower():
            continue
        res.append(e)
        if len(res) >= limite:
            break
    return jsonify({"actions": ACTIONS, "entrees": res})


@bp.route("/api/qualite")
def api_qualite():
    _exiger("admin")
    return jsonify(I.qualite(SV.collaborateurs(store), SV.refs(store), SV.parametres(store), SV.aujourd_hui()))


@bp.route("/api/export")
def api_export():
    ident = _exiger("admin")
    fmt = (request.args.get("format") or "xlsx").lower()
    if fmt not in ("xlsx", "csv"):
        abort(400, description=_("Format attendu : xlsx ou csv."))
    filtres = {k: request.args.get(k) for k in ("pays", "etablissement", "service", "type_contrat", "statut")}
    tous, refs = SV.collaborateurs(store), SV.refs(store)
    choisis = X.filtrer(tous, refs, filtres)
    texte = " ; ".join(f"{k} = {v}" for k, v in filtres.items() if v)
    lignes = X.lignes(choisis, refs, tous)
    horodatage = datetime.now(SV.FUSEAU).strftime("%Y%m%d_%H%M")
    SV.journaliser(store, ident, "export",
                   detail=f"Export {fmt.upper()} de {len(choisis)} collaborateur(s)" + (f" ({texte})" if texte else ""))
    if fmt == "csv":
        return Response(X.csv_octets(lignes), mimetype="text/csv; charset=utf-8", headers={
            "Content-Disposition": f'attachment; filename="HR_EUROPE_collaborateurs_{horodatage}.csv"'})
    return Response(X.excel_octets(lignes, texte),
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="HR_EUROPE_collaborateurs_{horodatage}.xlsx"'})


@bp.route("/api/export/apercu")
def api_export_apercu():
    _exiger("admin")
    filtres = {k: request.args.get(k) for k in ("pays", "etablissement", "service", "type_contrat", "statut")}
    return jsonify({"nb": len(X.filtrer(SV.collaborateurs(store), SV.refs(store), filtres)),
                    "colonnes": [t for t, _ in X.COLONNES]})


# --------------------------------------------------------------------------- #
# Paramètres, utilisateurs, automatisation (administrateur)
# --------------------------------------------------------------------------- #
@bp.route("/api/parametres", methods=["GET", "PUT"])
def api_parametres():
    ident = _exiger("admin")
    if request.method == "PUT":
        return jsonify({"ok": True, "parametres": SV.enregistrer_parametres(store, _corps(), ident)})
    return jsonify(SV.parametres(store))


@bp.route("/api/utilisateurs", methods=["GET"])
def api_utilisateurs():
    _exiger("admin")
    return jsonify({"roles": {k: _(v) for k, v in ROLES.items()}, "utilisateurs": role_store.list_users(SLUG)})


@bp.route("/api/utilisateurs", methods=["PUT"])
def api_utilisateur_enregistrer():
    ident = _exiger("admin")
    corps = _corps()
    email = str(corps.get("email") or "").strip().lower()
    role = corps.get("role")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", email):
        abort(400, description=_("Adresse e-mail invalide."))
    if role not in ROLES:
        abort(400, description=_("Rôle inconnu."))
    connus = {e["code"] for e in SV.refs(store)["etablissements"]}
    sites = sorted({str(s).strip().upper() for s in corps.get("sites") or [] if str(s).strip()})
    inconnus = [s for s in sites if s not in connus]
    if inconnus:
        abort(400, description=_("Établissements inconnus : {codes}", codes=", ".join(inconnus)))
    if role == "gm" and not sites:
        abort(400, description=_("Un directeur d'hôtel doit avoir au moins un établissement."))
    if email == ident["email"] and role != "admin":
        abort(400, description=_("Vous ne pouvez pas retirer votre propre rôle d'administrateur."))
    champs = {"role": role, "sites": sites if role == "gm" else [], "source": "manual"}
    if corps.get("name"):
        champs["name"] = str(corps["name"]).strip()[:120]
    entree = role_store.upsert_user(SLUG, email, champs)
    SV.journaliser(store, ident, "utilisateur",
                   detail=f"{email} : {ROLES[role]}" + (f" ({', '.join(sites)})" if role == "gm" else ""))
    return jsonify({"ok": True, "utilisateur": entree})


@bp.route("/api/utilisateurs/<path:email>", methods=["DELETE"])
def api_utilisateur_supprimer(email):
    ident = _exiger("admin")
    email = email.strip().lower()
    if email == ident["email"]:
        abort(400, description=_("Vous ne pouvez pas supprimer votre propre accès."))
    if not role_store.delete_user(SLUG, email):
        abort(404, description=_("Utilisateur inconnu."))
    SV.journaliser(store, ident, "utilisateur", detail=f"{email} : accès retiré")
    return jsonify({"ok": True})


@bp.route("/api/automatisation", methods=["GET"])
def api_automatisation():
    _exiger("admin")
    etat = store.lire(FICHIER_AUTOMATISATION, {})
    return jsonify({**etat, "heure": f"{HEURE_AUTOMATISATION:02d}:{MINUTE_AUTOMATISATION:02d}",
                    "active": _planificateur is not None})


@bp.route("/api/automatisation/lancer", methods=["POST"])
def api_automatisation_lancer():
    _exiger("admin")
    desactives = SV.desactivation_automatique(store)
    return jsonify({"ok": True, "desactives": len(desactives)})


# --------------------------------------------------------------------------- #
# Désactivation automatique quotidienne (fin de contrat atteinte)
# --------------------------------------------------------------------------- #
HEURE_AUTOMATISATION = int(os.environ.get("RHEUROPE_AUTOMATISATION_HEURE", "1"))
MINUTE_AUTOMATISATION = int(os.environ.get("RHEUROPE_AUTOMATISATION_MINUTE", "5"))
_planificateur = None
_planif_verrou = threading.Lock()


def _tache_quotidienne():
    try:
        SV.desactivation_automatique(store)
    except Exception as exc:  # noqa: BLE001 — une erreur ne doit pas arrêter le planificateur
        print(f"[RHEUROPE] désactivation automatique en échec : {exc!r}", flush=True)


def _demarrer_planificateur():
    global _planificateur
    with _planif_verrou:
        if _planificateur is not None:
            return
        from datetime import timedelta
        from apscheduler.schedulers.background import BackgroundScheduler
        sched = BackgroundScheduler(timezone="Europe/Paris", daemon=True)
        sched.add_job(_tache_quotidienne, "cron", hour=HEURE_AUTOMATISATION, minute=MINUTE_AUTOMATISATION,
                      id="rheurope-desactivation", replace_existing=True, misfire_grace_time=6 * 3600,
                      coalesce=True)
        # Rattrapage au démarrage (serveur arrêté pendant la nuit, déploiement…).
        sched.add_job(_tache_quotidienne, "date", run_date=datetime.now(SV.FUSEAU) + timedelta(seconds=45),
                      id="rheurope-rattrapage")
        sched.start()
        _planificateur = sched


def deploiement_occupe():
    """Le portail demande s'il peut recharger : rien de long à protéger ici
    (la désactivation automatique dure quelques millisecondes)."""
    return None


if os.environ.get("PORTAIL_VALIDATION_DEPLOIEMENT") != "1" and os.environ.get("RHEUROPE_AUTOMATISATION", "1") != "0":
    try:
        _demarrer_planificateur()
    except Exception as exc:  # noqa: BLE001 — l'app reste utilisable sans planificateur
        print(f"[RHEUROPE] planificateur non démarré : {exc!r}", flush=True)


# --------------------------------------------------------------------------- #
# SPA (front Vite construit dans static_files/)
# --------------------------------------------------------------------------- #
@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def servir(path):
    if path.startswith("api/"):
        abort(404, description=_("Endpoint inconnu."))
    if not os.path.isdir(BUILD_DIR):
        abort(503, description=_("Front non construit : lancer deploiement/construire.ps1 (ou outils/lancer-en-local.ps1)."))
    demande = os.path.normpath(os.path.join(BUILD_DIR, path))
    if not demande.startswith(os.path.abspath(BUILD_DIR)):
        abort(403)
    if path and os.path.isfile(demande) and not path.endswith("index.html"):
        resp = send_from_directory(BUILD_DIR, path)
        if path.startswith("assets/"):
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp
    resp = send_from_directory(BUILD_DIR, "index.html", max_age=0)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp
