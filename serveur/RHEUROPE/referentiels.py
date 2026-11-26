"""
Référentiels administrables (listes déroulantes standardisées à l'échelle Europe).

Chaque élément : {"code", "libelle", "actif"} + champs propres :
  - etablissements : "pays" (code du référentiel pays)
  - postes         : "sans_manager" (ex. directeur d'hôtel : manager facultatif)
  - types_contrat  : "date_fin_requise" (CDD… oui ; CDI non)

Un code utilisé par un collaborateur ne peut pas être supprimé : on le désactive
(il reste affiché sur les fiches existantes, mais n'est plus proposé).
"""

import re

TYPES = {
    "sexes": "Sexe",
    "pays": "Pays",
    "etablissements": "Établissements",
    "services": "Services",
    "postes": "Postes",
    "types_contrat": "Types de contrat",
    "motifs_sortie": "Motifs de sortie",
}

# Champ du collaborateur qui utilise chaque référentiel.
CHAMP_COLLABORATEUR = {
    "sexes": "sexe",
    "etablissements": "etablissement",
    "services": "service",
    "postes": "poste",
    "types_contrat": "type_contrat",
    "motifs_sortie": "motif_sortie",
}

CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,19}$")


def _e(code, libelle, **extra):
    return {"code": code, "libelle": libelle, "actif": True, **extra}


DEFAUTS = {
    "sexes": [_e("F", "Femme"), _e("H", "Homme")],
    "pays": [
        _e("FR", "France"), _e("DE", "Allemagne"), _e("AT", "Autriche"), _e("BE", "Belgique"),
        _e("CH", "Suisse"), _e("ES", "Espagne"), _e("IT", "Italie"), _e("GB", "Royaume-Uni"),
        _e("NL", "Pays-Bas"), _e("PT", "Portugal"), _e("HU", "Hongrie"), _e("CZ", "Tchéquie"),
        _e("DK", "Danemark"), _e("IE", "Irlande"), _e("PL", "Pologne"), _e("LU", "Luxembourg"),
    ],
    "etablissements": [],
    "services": [
        _e("DIR", "Direction"), _e("REC", "Réception"), _e("HEB", "Hébergement"),
        _e("TEC", "Technique / Maintenance"), _e("PDJ", "Petit-déjeuner / Restauration"),
        _e("COM", "Commercial"), _e("ADM", "Administration"),
    ],
    "postes": [
        _e("DIR_HOTEL", "Directeur / Directrice d'hôtel", sans_manager=True),
        _e("DIR_ADJ", "Directeur / Directrice adjoint(e)", sans_manager=False),
        _e("CHEF_REC", "Chef de réception", sans_manager=False),
        _e("RECEP", "Réceptionniste", sans_manager=False),
        _e("NIGHT", "Veilleur / Veilleuse de nuit", sans_manager=False),
        _e("GOUV", "Gouvernant(e)", sans_manager=False),
        _e("VALET", "Valet / Femme de chambre", sans_manager=False),
        _e("TECH", "Technicien(ne) de maintenance", sans_manager=False),
        _e("EMP_PDJ", "Employé(e) petit-déjeuner", sans_manager=False),
        _e("COMMERCIAL", "Commercial(e)", sans_manager=False),
        _e("ASSISTANT", "Assistant(e) administratif(ve)", sans_manager=False),
    ],
    "types_contrat": [
        _e("CDI", "CDI", date_fin_requise=False),
        _e("CDD", "CDD", date_fin_requise=True),
        _e("APPRENTI", "Apprentissage / Alternance", date_fin_requise=True),
        _e("STAGE", "Stage", date_fin_requise=True),
        _e("INTERIM", "Intérim", date_fin_requise=True),
        _e("SAISON", "Saisonnier", date_fin_requise=True),
        _e("EXTRA", "Extra", date_fin_requise=True),
    ],
    "motifs_sortie": [
        _e("FIN_CONTRAT", "Fin de contrat"), _e("DEMISSION", "Démission"),
        _e("LICENCIEMENT", "Licenciement"), _e("RUPTURE", "Rupture conventionnelle"),
        _e("RETRAITE", "Départ à la retraite"), _e("MUTATION", "Mutation vers un autre établissement"),
        _e("FIN_ESSAI", "Fin de période d'essai"), _e("AUTRE", "Autre"),
    ],
}


def completer(refs):
    """Référentiels enregistrés complétés des listes absentes (valeurs par défaut)."""
    refs = dict(refs or {})
    for type_, defaut in DEFAUTS.items():
        if type_ not in refs or not isinstance(refs[type_], list):
            refs[type_] = [dict(e) for e in defaut]
    return refs


def index(refs):
    """{type: {code: element}} pour des recherches rapides."""
    return {t: {e["code"]: e for e in refs.get(t, [])} for t in TYPES}


def libelle(refs_index, type_, code):
    e = refs_index.get(type_, {}).get(code)
    if e is None:
        return code or ""
    return e.get("libelle") or code


def _bool(v):
    return v is True or str(v).strip().lower() in ("1", "true", "oui", "vrai", "yes", "x")


def valider_liste(type_, elements, refs, codes_utilises):
    """Contrôle et normalise une liste envoyée par l'administrateur.
    Renvoie (liste_normalisée, erreurs)."""
    erreurs = []
    if type_ not in TYPES:
        return None, ["Référentiel inconnu."]
    if not isinstance(elements, list):
        return None, ["Liste attendue."]
    vus, propre = set(), []
    pays = {p["code"] for p in refs.get("pays", [])}
    for i, brut in enumerate(elements, 1):
        if not isinstance(brut, dict):
            erreurs.append(f"Ligne {i} : format invalide.")
            continue
        code = str(brut.get("code") or "").strip().upper()
        lib = str(brut.get("libelle") or "").strip()
        if not CODE_RE.match(code):
            erreurs.append(f"Ligne {i} : code « {code or '(vide)'} » invalide (lettres, chiffres, - et _, 20 caractères max).")
            continue
        if code in vus:
            erreurs.append(f"Ligne {i} : le code {code} est en double.")
            continue
        if not lib:
            erreurs.append(f"Ligne {i} : libellé obligatoire pour {code}.")
            continue
        vus.add(code)
        e = {"code": code, "libelle": lib[:120], "actif": _bool(brut.get("actif", True))}
        if type_ == "etablissements":
            p = str(brut.get("pays") or "").strip().upper()
            if p not in pays:
                erreurs.append(f"Ligne {i} : pays « {p or '(vide)'} » inconnu pour {code}.")
                continue
            e["pays"] = p
        if type_ == "postes":
            e["sans_manager"] = _bool(brut.get("sans_manager", False))
        if type_ == "types_contrat":
            e["date_fin_requise"] = _bool(brut.get("date_fin_requise", False))
        propre.append(e)
    supprimes = (codes_utilises or set()) - vus
    if supprimes:
        erreurs.append("Codes utilisés par des collaborateurs, impossibles à supprimer (désactivez-les) : "
                       + ", ".join(sorted(supprimes)))
    if type_ == "pays":
        restants = {e["code"] for e in propre}
        orphelins = sorted({e.get("pays") for e in refs.get("etablissements", [])} - restants - {None})
        if orphelins:
            erreurs.append("Pays utilisés par des établissements, impossibles à supprimer : " + ", ".join(orphelins))
    return propre, erreurs
