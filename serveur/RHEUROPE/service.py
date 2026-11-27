"""
Règles métier de HR EUROPE : création, modification, désactivation /
réactivation, effacement RGPD, désactivation automatique, matricules,
référentiels, paramètres. Chaque action est tracée dans l'historique
(qui, quand, quoi).

Module sans dépendance au portail ni à Flask (testable seul) : les routes
lui passent le store, l'identité et la date du jour.
"""

import re
import uuid
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from . import referentiels as R
from . import store as S
from .i18n import _
from .validation import CHAMPS, CHAMPS_SAISIS, LIBELLES, date_iso, generer_matricule, normaliser, verifier

FUSEAU = ZoneInfo("Europe/Paris")
AUTOMATE = {"email": "automatisation", "nom": "Désactivation automatique"}

PARAMETRES_DEFAUT = {
    "domaines_email": ["accor.com"],
    "matricule": {"modele": "EU{N}", "largeur": 6, "depart": 1, "compteurs": {}},
}


class ErreurMetier(Exception):
    def __init__(self, message, code=400, **extra):
        super().__init__(message)
        self.message, self.code, self.extra = message, code, extra


def aujourd_hui():
    return datetime.now(FUSEAU).date()


def maintenant():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# Lectures
# --------------------------------------------------------------------------- #
def collaborateurs(store):
    return store.lire(S.FICHIER_COLLABORATEURS, [])


def refs(store):
    return R.completer(store.lire(S.FICHIER_REFERENTIELS, {}))


def parametres(store):
    p = store.lire(S.FICHIER_PARAMETRES, {})
    res = {**PARAMETRES_DEFAUT, **p}
    res["matricule"] = {**PARAMETRES_DEFAUT["matricule"], **(p.get("matricule") or {})}
    return res


def dans_perimetre(c, perimetre):
    return perimetre is None or c.get("etablissement") in perimetre


# --------------------------------------------------------------------------- #
# Historique
# --------------------------------------------------------------------------- #
def _valeur_lisible(champ, valeur, idx, par_id):
    if not valeur:
        return ""
    type_ = next((t for t, ch in R.CHAMP_COLLABORATEUR.items() if ch == champ), None)
    if type_:
        return R.libelle(idx, type_, valeur, base=True)   # historique : libellé de référence
    if champ == "manager_id":
        m = par_id.get(valeur) or {}
        return f"{m.get('prenom', '')} {m.get('nom', '')}".strip() or valeur
    if champ.startswith("date_"):
        d = date_iso(valeur)
        return d.strftime("%d/%m/%Y") if d else valeur
    if champ == "statut":
        return "Actif" if valeur == "actif" else "Inactif"
    return str(valeur)


LIBELLES_SUIVIS = {**LIBELLES, "statut": "Statut", "date_sortie": "Date de sortie",
                   "motif_sortie": "Motif de sortie", "commentaire_sortie": "Commentaire de sortie"}


def _changements(avant, apres, idx, par_id):
    res = []
    for champ, lib in LIBELLES_SUIVIS.items():
        a, b = (avant or {}).get(champ) or "", (apres or {}).get(champ) or ""
        if a != b:
            res.append({"champ": champ, "libelle": lib,
                        "avant": _valeur_lisible(champ, a, idx, par_id),
                        "apres": _valeur_lisible(champ, b, idx, par_id)})
    return res


def journaliser(store, ident, action, c=None, changements=None, detail=None):
    entree = {"le": maintenant(), "par": ident["email"], "par_nom": ident.get("nom") or ident["email"],
              "action": action}
    if c is not None:
        entree.update({"collaborateur_id": c.get("id"), "matricule": c.get("matricule"),
                       "nom_complet": f"{c.get('prenom', '')} {c.get('nom', '')}".strip(),
                       "etablissement": c.get("etablissement")})
    if changements:
        entree["changements"] = changements
    if detail:
        entree["detail"] = detail
    store.journaliser(entree)
    return entree


# --------------------------------------------------------------------------- #
# Fiches
# --------------------------------------------------------------------------- #
def verifier_fiche(store, brut, perimetre, id_=None):
    tous = collaborateurs(store)
    ancien = next((x for x in tous if x["id"] == id_), None) if id_ else None
    c = normaliser(brut)
    return verifier(c, collaborateurs=tous, refs=refs(store), parametres=parametres(store),
                    aujourd_hui=aujourd_hui(), perimetre=perimetre, ancien=ancien)


def _controler(c, tous, store, perimetre, ancien, confirmer_doublon):
    erreurs, alertes = verifier(c, collaborateurs=tous, refs=refs(store), parametres=parametres(store),
                                aujourd_hui=aujourd_hui(), perimetre=perimetre, ancien=ancien)
    if erreurs:
        raise ErreurMetier(_("La fiche contient des erreurs : corrigez-les avant d'enregistrer."), 400,
                           erreurs=erreurs, alertes=alertes)
    if any(a["type"] == "doublon" for a in alertes) and not confirmer_doublon:
        raise ErreurMetier(_("Doublon potentiel détecté : confirmez qu'il s'agit bien d'une autre personne."), 409,
                           erreurs={}, alertes=alertes)
    return alertes


def creer(store, brut, ident, perimetre, confirmer_doublon=False):
    with store.verrou:
        tous = collaborateurs(store)
        c = normaliser(brut)
        _controler(c, tous, store, perimetre, None, confirmer_doublon)
        fiche = {"id": uuid.uuid4().hex, **{k: c[k] for k in CHAMPS_SAISIS},
                 "statut": "actif", "date_sortie": "", "motif_sortie": "", "commentaire_sortie": "",
                 "cree_le": maintenant(), "cree_par": ident["email"],
                 "modifie_le": maintenant(), "modifie_par": ident["email"]}
        fin = date_iso(fiche["date_fin"])
        if fin and fin < aujourd_hui():   # contrat déjà terminé : saisi pour l'historique
            fiche.update(statut="inactif", date_sortie=fiche["date_fin"], motif_sortie="FIN_CONTRAT")
        tous.append(fiche)
        store.ecrire(S.FICHIER_COLLABORATEURS, tous)
        idx, par_id = R.index(refs(store)), {x["id"]: x for x in tous}
        journaliser(store, ident, "creation", fiche, _changements({}, fiche, idx, par_id))
        return fiche


def _trouver(tous, id_, perimetre):
    c = next((x for x in tous if x["id"] == id_), None)
    if c is None or not dans_perimetre(c, perimetre):
        raise ErreurMetier(_("Collaborateur introuvable ou hors de votre périmètre."), 404)
    return c


def modifier(store, id_, brut, ident, perimetre, confirmer_doublon=False):
    with store.verrou:
        tous = collaborateurs(store)
        ancien = _trouver(tous, id_, perimetre)
        c = normaliser(brut)
        _controler(c, tous, store, perimetre, ancien, confirmer_doublon)
        nouveau = {**ancien, **{k: c[k] for k in CHAMPS_SAISIS}}
        fin = date_iso(nouveau.get("date_fin"))
        if nouveau.get("statut") == "actif" and fin and fin < aujourd_hui():
            nouveau.update(statut="inactif", date_sortie=fin.isoformat(),
                           motif_sortie=nouveau.get("motif_sortie") or "FIN_CONTRAT")
        idx, par_id = R.index(refs(store)), {x["id"]: x for x in tous}
        diff = _changements(ancien, nouveau, idx, par_id)
        if not diff:
            return ancien, []
        nouveau.update(modifie_le=maintenant(), modifie_par=ident["email"])
        tous[tous.index(ancien)] = nouveau
        store.ecrire(S.FICHIER_COLLABORATEURS, tous)
        journaliser(store, ident, "modification", nouveau, diff)
        return nouveau, diff


def desactiver(store, id_, ident, perimetre, date_sortie=None, motif=None, commentaire=""):
    """Sortie du collaborateur. Date passée ou du jour → inactif tout de suite ;
    date future → date de fin positionnée, désactivation automatique ce jour-là."""
    with store.verrou:
        tous = collaborateurs(store)
        ancien = _trouver(tous, id_, perimetre)
        if ancien.get("statut") != "actif":
            raise ErreurMetier(_("Ce collaborateur est déjà inactif."))
        idx = R.index(refs(store))
        motif = (motif or "").strip().upper()
        if motif not in idx["motifs_sortie"]:
            raise ErreurMetier(_("Motif de sortie obligatoire."), erreurs={"motif_sortie": _("Choisissez un motif.")})
        jour = date_iso(date_sortie) if date_sortie else aujourd_hui()
        if jour is None:
            raise ErreurMetier(_("Date de sortie invalide."), erreurs={"date_sortie": _("Date invalide.")})
        debut = date_iso(ancien.get("date_debut"))
        if debut and jour < debut:
            raise ErreurMetier(_("La date de sortie précède la date de début de contrat."),
                               erreurs={"date_sortie": _("Antérieure au début du contrat.")})
        nouveau = dict(ancien)
        fin = date_iso(ancien.get("date_fin"))
        if fin is None or fin > jour:
            nouveau["date_fin"] = jour.isoformat()
        programme = jour > aujourd_hui()
        nouveau["motif_sortie"] = motif
        nouveau["commentaire_sortie"] = (commentaire or "").strip()[:300]
        if not programme:
            nouveau.update(statut="inactif", date_sortie=jour.isoformat())
        nouveau.update(modifie_le=maintenant(), modifie_par=ident["email"])
        tous[tous.index(ancien)] = nouveau
        store.ecrire(S.FICHIER_COLLABORATEURS, tous)
        par_id = {x["id"]: x for x in tous}
        journaliser(store, ident, "sortie_programmee" if programme else "desactivation", nouveau,
                    _changements(ancien, nouveau, idx, par_id))
        return nouveau, programme


def reactiver(store, id_, ident, perimetre, brut=None):
    """Prolongation de contrat ou retour : nouvelle date de fin (ou aucune pour
    un CDI), éventuellement nouveau type de contrat / date de début."""
    brut = brut or {}
    with store.verrou:
        tous = collaborateurs(store)
        ancien = _trouver(tous, id_, perimetre)
        if ancien.get("statut") == "actif":
            raise ErreurMetier(_("Ce collaborateur est déjà actif."))
        proposition = {k: ancien.get(k, "") for k in CHAMPS_SAISIS}
        for cle in ("type_contrat", "date_debut", "date_fin"):
            if cle in brut:
                proposition[cle] = brut.get(cle) or ""
        c = normaliser(proposition)
        erreurs, _alertes = verifier(c, collaborateurs=tous, refs=refs(store), parametres=parametres(store),
                              aujourd_hui=aujourd_hui(), perimetre=perimetre, ancien=ancien)
        fin = date_iso(c.get("date_fin"))
        if fin and fin < aujourd_hui() and "date_fin" not in erreurs:
            erreurs["date_fin"] = _("Indiquez une nouvelle date de fin (aujourd'hui ou plus tard), ou laissez vide pour un contrat sans fin.")
        # Un manager devenu inactif entre-temps n'empêche pas la réactivation
        # (il sera signalé dans la qualité des données).
        if ancien.get("manager_id") == c.get("manager_id"):
            erreurs.pop("manager_id", None)
        if erreurs:
            raise ErreurMetier(_("Réactivation impossible : corrigez les informations indiquées."), 400, erreurs=erreurs)
        nouveau = {**ancien, **{k: c[k] for k in CHAMPS_SAISIS},
                   "statut": "actif", "date_sortie": "", "motif_sortie": "", "commentaire_sortie": "",
                   "modifie_le": maintenant(), "modifie_par": ident["email"]}
        tous[tous.index(ancien)] = nouveau
        store.ecrire(S.FICHIER_COLLABORATEURS, tous)
        idx, par_id = R.index(refs(store)), {x["id"]: x for x in tous}
        journaliser(store, ident, "reactivation", nouveau, _changements(ancien, nouveau, idx, par_id))
        return nouveau


def supprimer(store, id_, ident):
    """Effacement définitif (RGPD, administrateur) : la fiche est supprimée et
    l'historique du collaborateur anonymisé ; la trace de l'effacement reste."""
    with store.verrou:
        tous = collaborateurs(store)
        c = _trouver(tous, id_, None)
        geres = [x for x in tous if x.get("manager_id") == id_ and x.get("statut") == "actif"]
        if geres:
            raise ErreurMetier(_("Impossible : ce collaborateur est le manager de {n} collaborateur(s) actif(s). "
                                 "Changez d'abord leur manager.", n=len(geres)))
        tous.remove(c)
        for x in tous:
            if x.get("manager_id") == id_:
                x["manager_id"] = ""
        store.ecrire(S.FICHIER_COLLABORATEURS, tous)
        historique = store.historique()
        for e in historique:
            if e.get("collaborateur_id") == id_:
                e["nom_complet"] = "[données effacées]"
                e["matricule"] = "[effacé]"
                e.pop("changements", None)
        store.reecrire_historique(historique)
        journaliser(store, ident, "effacement", {"id": id_, "matricule": "[effacé]", "prenom": "",
                                                 "nom": "[données effacées]", "etablissement": c.get("etablissement")},
                    detail="Effacement définitif des données (RGPD)")


def desactivation_automatique(store, jour=None):
    """Désactive les collaborateurs actifs dont la date de fin est dépassée."""
    jour = jour or aujourd_hui()
    traites = []
    with store.verrou:
        tous = collaborateurs(store)
        idx = R.index(refs(store))
        par_id = {x["id"]: x for x in tous}
        for i, c in enumerate(tous):
            fin = date_iso(c.get("date_fin"))
            if c.get("statut") == "actif" and fin and fin < jour:
                nouveau = {**c, "statut": "inactif", "date_sortie": fin.isoformat(),
                           "motif_sortie": c.get("motif_sortie") or "FIN_CONTRAT",
                           "modifie_le": maintenant(), "modifie_par": AUTOMATE["email"]}
                tous[i] = nouveau
                traites.append((c, nouveau))
        if traites:
            store.ecrire(S.FICHIER_COLLABORATEURS, tous)
            for avant, apres in traites:
                journaliser(store, AUTOMATE, "desactivation_auto", apres, _changements(avant, apres, idx, par_id),
                            detail="Date de fin de contrat atteinte")
        etat = store.lire(S.FICHIER_AUTOMATISATION, {})
        passages = [{"le": maintenant(), "jour": jour.isoformat(), "desactives": len(traites)}] + (etat.get("passages") or [])
        store.ecrire(S.FICHIER_AUTOMATISATION, {"dernier_passage": passages[0], "passages": passages[:30]})
    return [apres for _, apres in traites]


def generer(store, ident, etablissement):
    with store.verrou:
        p = parametres(store)
        idx = R.index(refs(store))
        etab = idx["etablissements"].get((etablissement or "").upper()) or {}
        modele = (p["matricule"].get("modele") or "").upper()
        if ("{PAYS}" in modele or "{ETAB}" in modele) and not etab:
            raise ErreurMetier(_("Choisissez d'abord l'établissement : il entre dans la composition du matricule."))
        utilises = [x.get("matricule") for x in collaborateurs(store)]
        matricule, prefixe, n = generer_matricule(p, utilises, pays=etab.get("pays", ""),
                                                  etablissement=etab.get("code", ""), annee=aujourd_hui().year)
        brut = store.lire(S.FICHIER_PARAMETRES, {})
        regle = {**PARAMETRES_DEFAUT["matricule"], **(brut.get("matricule") or {})}
        regle["compteurs"] = {**(regle.get("compteurs") or {}), prefixe: n}   # numéro réservé
        brut["matricule"] = regle
        store.ecrire(S.FICHIER_PARAMETRES, brut)
        return matricule


# --------------------------------------------------------------------------- #
# Administration
# --------------------------------------------------------------------------- #
def enregistrer_referentiel(store, type_, elements, ident):
    with store.verrou:
        tous_refs = refs(store)
        champ = R.CHAMP_COLLABORATEUR.get(type_)
        utilises = {c.get(champ) for c in collaborateurs(store) if champ and c.get(champ)}
        propre, erreurs = R.valider_liste(type_, elements, tous_refs, utilises)
        if erreurs:
            raise ErreurMetier(_("Référentiel non enregistré."), 400, details=erreurs)
        avant = {e["code"]: e for e in tous_refs.get(type_, [])}
        apres = {e["code"]: e for e in propre}
        resume = []
        ajoutes = sorted(set(apres) - set(avant))
        retires = sorted(set(avant) - set(apres))
        modifies = sorted(c for c in set(apres) & set(avant) if apres[c] != avant[c])
        if ajoutes:
            resume.append("Ajout : " + ", ".join(ajoutes))
        if modifies:
            resume.append("Modification : " + ", ".join(modifies))
        if retires:
            resume.append("Suppression : " + ", ".join(retires))
        tous_refs[type_] = propre
        store.ecrire(S.FICHIER_REFERENTIELS, tous_refs)
        if resume:
            journaliser(store, ident, "referentiel", detail=f"{R.TYPES[type_]} — " + " ; ".join(resume))
        return propre


def enregistrer_parametres(store, brut, ident):
    erreurs = {}
    domaines = []
    for d in brut.get("domaines_email") or []:
        d = str(d).strip().lower().lstrip("@")
        if d and not re.match(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$", d):
            erreurs["domaines_email"] = _("Domaine invalide : {d}", d=d)
        elif d and d not in domaines:
            domaines.append(d)
    if not domaines and "domaines_email" not in erreurs:
        erreurs["domaines_email"] = _("Au moins un domaine autorisé est requis.")
    m = brut.get("matricule") or {}
    modele = str(m.get("modele") or "").strip().upper()
    if not modele or "{N}" not in modele or not re.match(r"^([A-Z0-9_-]|\{PAYS\}|\{ETAB\}|\{AAAA\}|\{AA\}|\{N\})+$", modele) \
            or modele.count("{N}") != 1:
        erreurs["modele"] = _("Modèle invalide : lettres, chiffres, - et _ et les repères {PAYS}, {ETAB}, {AAAA}, {AA}, avec un seul {N}.")
    try:
        largeur = int(m.get("largeur"))
        assert 3 <= largeur <= 12
    except (TypeError, ValueError, AssertionError):
        erreurs["largeur"] = _("Nombre de chiffres entre 3 et 12.")
        largeur = 6
    try:
        depart = int(m.get("depart") or 1)
        assert depart >= 1
    except (TypeError, ValueError, AssertionError):
        erreurs["depart"] = _("Numéro de départ : entier positif.")
        depart = 1
    if erreurs:
        raise ErreurMetier(_("Paramètres non enregistrés."), 400, erreurs=erreurs)
    with store.verrou:
        actuel = store.lire(S.FICHIER_PARAMETRES, {})
        regle = {**PARAMETRES_DEFAUT["matricule"], **(actuel.get("matricule") or {})}
        regle.update(modele=modele, largeur=largeur, depart=depart)
        nouveau = {**actuel, "domaines_email": domaines, "matricule": regle}
        store.ecrire(S.FICHIER_PARAMETRES, nouveau)
        journaliser(store, ident, "parametres",
                    detail=f"Domaines : {', '.join(domaines)} ; matricule : {modele} ({largeur} chiffres, départ {depart})")
    return parametres(store)
