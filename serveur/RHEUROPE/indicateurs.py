"""
Indicateurs du tableau de bord et contrôles de qualité des données.
Module sans dépendance au portail (testable seul).
"""

from collections import Counter
from datetime import timedelta

from . import referentiels as R
from .validation import CHAMPS, cle_doublon, date_iso, domaine_autorise

JOURS_ARRIVEES = 30
JOURS_DEPARTS = 60
JOURS_ECHEANCES = 30
LISTE_MAX = 10


def _resume(c, idx, date_cle=None):
    return {
        "id": c["id"], "matricule": c.get("matricule"), "nom": c.get("nom"), "prenom": c.get("prenom"),
        "poste": R.libelle(idx, "postes", c.get("poste")),
        "etablissement": c.get("etablissement"),
        "type_contrat": R.libelle(idx, "types_contrat", c.get("type_contrat")),
        "date": c.get(date_cle) if date_cle else None,
    }


def _repartition(actifs, idx, type_, champ):
    compte = Counter(c.get(champ) or "" for c in actifs)
    return sorted(({"code": code, "libelle": R.libelle(idx, type_, code) if code else "Non renseigné", "nb": nb}
                   for code, nb in compte.items()), key=lambda x: (-x["nb"], x["libelle"]))


def tableau_de_bord(collaborateurs, refs, aujourd_hui):
    idx = R.index(refs)
    actifs = [c for c in collaborateurs if c.get("statut") == "actif"]
    inactifs = [c for c in collaborateurs if c.get("statut") != "actif"]

    arrivees, a_venir, departs, echeances = [], [], [], []
    for c in actifs:
        debut, fin = date_iso(c.get("date_debut")), date_iso(c.get("date_fin"))
        if debut and aujourd_hui - timedelta(days=JOURS_ARRIVEES) <= debut <= aujourd_hui:
            arrivees.append(c)
        elif debut and debut > aujourd_hui:
            a_venir.append(c)
        if fin and aujourd_hui <= fin <= aujourd_hui + timedelta(days=JOURS_DEPARTS):
            departs.append(c)
            tc = idx["types_contrat"].get(c.get("type_contrat")) or {}
            if tc.get("date_fin_requise") and fin <= aujourd_hui + timedelta(days=JOURS_ECHEANCES):
                echeances.append(c)

    def trie(liste, cle, inverse=False):
        return sorted(liste, key=lambda c: c.get(cle) or "", reverse=inverse)

    par_etab = Counter(c.get("etablissement") for c in actifs)
    return {
        "aujourd_hui": aujourd_hui.isoformat(),
        "fenetres": {"arrivees": JOURS_ARRIVEES, "departs": JOURS_DEPARTS, "echeances": JOURS_ECHEANCES},
        "compteurs": {
            "total": len(collaborateurs), "actifs": len(actifs), "inactifs": len(inactifs),
            "arrivees": len(arrivees), "arrivees_a_venir": len(a_venir),
            "departs": len(departs), "echeances": len(echeances),
        },
        "listes": {
            "arrivees": [_resume(c, idx, "date_debut") for c in trie(arrivees + a_venir, "date_debut", True)[:LISTE_MAX]],
            "departs": [_resume(c, idx, "date_fin") for c in trie(departs, "date_fin")[:LISTE_MAX]],
            "echeances": [_resume(c, idx, "date_fin") for c in trie(echeances, "date_fin")[:LISTE_MAX]],
        },
        "repartition": {
            "service": _repartition(actifs, idx, "services", "service"),
            "sexe": _repartition(actifs, idx, "sexes", "sexe"),
            "type_contrat": _repartition(actifs, idx, "types_contrat", "type_contrat"),
        },
        "par_etablissement": sorted(
            ({"code": code, "libelle": R.libelle(idx, "etablissements", code), "nb": nb} for code, nb in par_etab.items()),
            key=lambda x: (-x["nb"], x["libelle"])),
    }


# --------------------------------------------------------------------------- #
# Qualité des données (administrateur)
# --------------------------------------------------------------------------- #
CONTROLES = {
    "doublons": "Doublons potentiels (nom, prénom, date de naissance)",
    "incomplets": "Fiches incomplètes",
    "echus_actifs": "Actifs dont le contrat est terminé",
    "manager_inactif": "Actifs rattachés à un manager inactif ou absent",
    "referentiel": "Valeurs inconnues ou désactivées dans les référentiels",
    "email_domaine": "Adresses e-mail hors des domaines autorisés",
}


def qualite(collaborateurs, refs, parametres, aujourd_hui):
    idx = R.index(refs)
    par_id = {c["id"]: c for c in collaborateurs}
    res = {k: [] for k in CONTROLES}

    def item(c, detail):
        return {"id": c["id"], "matricule": c.get("matricule"), "nom": c.get("nom"), "prenom": c.get("prenom"),
                "etablissement": c.get("etablissement"), "statut": c.get("statut"), "detail": detail}

    groupes = {}
    for c in collaborateurs:
        cle = cle_doublon(c)
        if cle:
            groupes.setdefault(cle, []).append(c)
    for membres in groupes.values():
        if len(membres) > 1:
            for c in membres:
                autres = ", ".join(x.get("matricule") or "?" for x in membres if x is not c)
                res["doublons"].append(item(c, f"Mêmes informations que : {autres}"))

    domaines = parametres.get("domaines_email") or []
    for c in collaborateurs:
        tc = idx["types_contrat"].get(c.get("type_contrat")) or {}
        poste = idx["postes"].get(c.get("poste")) or {}
        manquants = []
        for champ, lib in CHAMPS:
            if c.get(champ):
                continue
            if champ == "date_fin" and not tc.get("date_fin_requise"):
                continue
            if champ == "manager_id" and poste.get("sans_manager"):
                continue
            manquants.append(lib)
        if manquants:
            res["incomplets"].append(item(c, "Manquant : " + ", ".join(manquants)))

        if c.get("statut") == "actif":
            fin = date_iso(c.get("date_fin"))
            if fin and fin < aujourd_hui:
                res["echus_actifs"].append(item(c, f"Fin de contrat le {fin.strftime('%d/%m/%Y')}"))
            mid = c.get("manager_id")
            if mid:
                m = par_id.get(mid)
                if m is None:
                    res["manager_inactif"].append(item(c, "Manager supprimé de la base"))
                elif m.get("statut") != "actif":
                    res["manager_inactif"].append(item(c, f"Manager inactif : {m.get('prenom')} {m.get('nom')}"))

        problemes = []
        for type_, champ in R.CHAMP_COLLABORATEUR.items():
            code = c.get(champ)
            if not code:
                continue
            e = idx[type_].get(code)
            if e is None:
                problemes.append(f"{R.TYPES[type_]} « {code} » inconnu")
            elif not e.get("actif", True) and c.get("statut") == "actif":
                problemes.append(f"{R.TYPES[type_]} « {e['libelle']} » désactivé")
        if problemes:
            res["referentiel"].append(item(c, " ; ".join(problemes)))

        if domaines and c.get("email") and not domaine_autorise(c["email"], domaines):
            res["email_domaine"].append(item(c, c["email"]))

    return {
        "controles": [{"code": k, "libelle": lib, "nb": len(res[k]), "elements": res[k][:300]}
                      for k, lib in CONTROLES.items()],
        "total_collaborateurs": len(collaborateurs),
        "fiches_conformes": len(collaborateurs) - len({x["id"] for v in res.values() for x in v}),
    }
