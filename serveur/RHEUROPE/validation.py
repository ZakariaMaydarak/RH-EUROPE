"""
Contrôles de saisie d'une fiche collaborateur.

`verifier()` renvoie :
  - erreurs : {champ: message} — BLOQUANTES, l'enregistrement est refusé ;
  - alertes : [{type, message, ...}] — informatives (ex. doublon potentiel, qui
    demande une confirmation explicite avant l'enregistrement).

Module sans dépendance au portail (testable seul).
"""

import re
import unicodedata
from datetime import date, timedelta

from . import referentiels as R

CHAMPS = [
    ("nom", "Nom"),
    ("prenom", "Prénom"),
    ("matricule", "Matricule"),
    ("sexe", "Sexe"),
    ("email", "Adresse e-mail Accor"),
    ("date_naissance", "Date de naissance"),
    ("date_debut", "Date de début de contrat"),
    ("date_fin", "Date de fin de contrat"),
    ("type_contrat", "Type de contrat"),
    ("service", "Service"),
    ("etablissement", "Établissement"),
    ("poste", "Poste"),
    ("manager_id", "Manager"),
]
LIBELLES = dict(CHAMPS)
CHAMPS_SAISIS = [c for c, _ in CHAMPS]

MATRICULE_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,19}$")
EMAIL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._'+-]{0,62}[a-z0-9])?@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}$")
# Parties locales d'adresses NON nominatives (boîtes d'hôtel ou de service).
EMAIL_GENERIQUE_RE = re.compile(
    r"^(h[0-9a-z]{4}([._-].*)?|info|contact|reception|accueil|direction|admin|"
    r"no-?reply|rh|hr|compta|booking|reservation|reservations|sales|manager|gm|dm)$")

AGE_MINIMUM = 14
AGE_MAXIMUM = 80
NOM_MAX = 80


def sans_accents(texte):
    return "".join(c for c in unicodedata.normalize("NFD", texte or "") if unicodedata.category(c) != "Mn")


def _prenom(texte):
    """« jean-marie  de la » → « Jean-Marie De La » (harmonisation)."""
    morceaux = re.split(r"([\s'-]+)", texte.strip())
    return "".join(m if re.fullmatch(r"[\s'-]+", m) else m[:1].upper() + m[1:].lower() for m in morceaux)


def normaliser(brut):
    """Valeurs saisies → valeurs enregistrées (espaces, casse, formats)."""
    brut = brut or {}
    c = {}
    for champ in CHAMPS_SAISIS:
        v = brut.get(champ)
        c[champ] = re.sub(r"\s+", " ", str(v)).strip() if v not in (None, "") else ""
    c["nom"] = c["nom"].upper()
    c["prenom"] = _prenom(c["prenom"]) if c["prenom"] else ""
    c["matricule"] = c["matricule"].upper().replace(" ", "")
    c["email"] = c["email"].lower().replace(" ", "")
    for champ in ("sexe", "type_contrat", "service", "etablissement", "poste"):
        c[champ] = c[champ].upper()
    return c


def date_iso(texte):
    try:
        return date.fromisoformat(texte) if texte else None
    except (TypeError, ValueError):
        return None


def cle_doublon(c):
    nom = re.sub(r"[^a-z]", "", sans_accents(c.get("nom", "")).lower())
    prenom = re.sub(r"[^a-z]", "", sans_accents(c.get("prenom", "")).lower())
    if not (nom and prenom and c.get("date_naissance")):
        return None
    return f"{nom}|{prenom}|{c['date_naissance']}"


def domaine_autorise(email, domaines):
    domaine = email.rsplit("@", 1)[-1] if "@" in email else ""
    return any(domaine == d or domaine.endswith("." + d) for d in domaines)


def _age(naissance, a_la_date):
    return a_la_date.year - naissance.year - ((a_la_date.month, a_la_date.day) < (naissance.month, naissance.day))


def verifier(c, *, collaborateurs, refs, parametres, aujourd_hui, perimetre=None, ancien=None):
    """`c` : fiche normalisée. `collaborateurs` : tous (Europe), pour l'unicité.
    `perimetre` : établissements autorisés (None = tous). `ancien` : fiche avant
    modification (None = création)."""
    erreurs, alertes = {}, []
    idx = R.index(refs)
    mon_id = ancien.get("id") if ancien else None
    autres = [x for x in collaborateurs if x.get("id") != mon_id]

    type_contrat = idx["types_contrat"].get(c.get("type_contrat"))
    poste = idx["postes"].get(c.get("poste"))
    date_fin_requise = bool(type_contrat and type_contrat.get("date_fin_requise"))
    manager_facultatif = bool(poste and poste.get("sans_manager"))

    # 1. Complétude
    for champ, lib in CHAMPS:
        if c.get(champ):
            continue
        if champ == "date_fin" and not date_fin_requise:
            continue
        if champ == "manager_id" and manager_facultatif:
            continue
        if champ == "date_fin":
            erreurs[champ] = f"Date de fin obligatoire pour un contrat « {type_contrat['libelle']} »."
        else:
            erreurs[champ] = "Champ obligatoire."

    # 2. Longueurs / caractères
    for champ in ("nom", "prenom"):
        v = c.get(champ, "")
        if v and len(v) > NOM_MAX:
            erreurs[champ] = f"{LIBELLES[champ]} : {NOM_MAX} caractères maximum."
        elif v and re.search(r"[0-9@#$%*=<>{}\[\]|\\/;:!?]", v):
            erreurs[champ] = f"{LIBELLES[champ]} : caractères non autorisés (chiffres ou symboles)."

    # 3. Listes déroulantes (référentiels)
    for type_, champ in R.CHAMP_COLLABORATEUR.items():
        if champ not in LIBELLES or not c.get(champ) or champ in erreurs:
            continue
        e = idx[type_].get(c[champ])
        if e is None:
            erreurs[champ] = f"{LIBELLES[champ]} : valeur inconnue du référentiel."
        elif not e.get("actif", True) and not (ancien and ancien.get(champ) == c[champ]):
            erreurs[champ] = f"{LIBELLES[champ]} : « {e['libelle']} » est désactivé dans le référentiel."

    # 4. Établissement dans le périmètre de l'utilisateur
    if c.get("etablissement") and "etablissement" not in erreurs and perimetre is not None \
            and c["etablissement"] not in perimetre:
        erreurs["etablissement"] = "Établissement hors de votre périmètre."

    # 5. Matricule : format + unicité Europe
    m = c.get("matricule")
    if m and "matricule" not in erreurs:
        if not MATRICULE_RE.match(m):
            erreurs["matricule"] = "Matricule invalide : 3 à 20 caractères (lettres majuscules, chiffres, - et _)."
        elif any((x.get("matricule") or "").upper() == m for x in autres):
            erreurs["matricule"] = f"Le matricule {m} est déjà attribué à un autre collaborateur (Europe)."

    # 6. E-mail : format, domaine Accor, nominatif, unicité Europe
    em = c.get("email")
    if em and "email" not in erreurs:
        domaines = parametres.get("domaines_email") or []
        local = em.split("@", 1)[0]
        if not EMAIL_RE.match(em):
            erreurs["email"] = "Format d'adresse e-mail invalide."
        elif domaines and not domaine_autorise(em, domaines):
            erreurs["email"] = "Domaine non autorisé : adresse attendue en " + ", ".join("@" + d for d in domaines) + "."
        elif EMAIL_GENERIQUE_RE.match(local):
            erreurs["email"] = "Adresse non nominative (boîte d'hôtel ou de service) : saisir l'adresse personnelle Accor du collaborateur."
        elif any((x.get("email") or "").lower() == em for x in autres):
            erreurs["email"] = "Cette adresse e-mail est déjà utilisée par un autre collaborateur (Europe)."
        else:
            nom_simple = re.sub(r"[^a-z]", "", sans_accents(c.get("nom", "")).lower())
            local_simple = re.sub(r"[^a-z]", "", sans_accents(local))
            if nom_simple and len(nom_simple) >= 3 and nom_simple[:4] not in local_simple:
                alertes.append({"type": "email_nom", "message":
                                "L'adresse e-mail ne semble pas contenir le nom du collaborateur : vérifiez qu'il s'agit bien de la sienne."})

    # 7. Dates : validité et cohérence
    for champ in ("date_naissance", "date_debut", "date_fin"):
        if c.get(champ) and date_iso(c[champ]) is None and champ not in erreurs:
            erreurs[champ] = f"{LIBELLES[champ]} : date invalide."
    naissance, debut, fin = date_iso(c.get("date_naissance")), date_iso(c.get("date_debut")), date_iso(c.get("date_fin"))
    if naissance and "date_naissance" not in erreurs:
        if naissance > aujourd_hui:
            erreurs["date_naissance"] = "La date de naissance ne peut pas être dans le futur."
        elif naissance.year < 1900:
            erreurs["date_naissance"] = "Date de naissance invalide."
    if naissance and debut and "date_naissance" not in erreurs and "date_debut" not in erreurs:
        age = _age(naissance, debut)
        if age < AGE_MINIMUM:
            erreurs["date_debut"] = f"Incohérence : le collaborateur aurait {age} ans au début du contrat (minimum {AGE_MINIMUM} ans)."
        elif age > AGE_MAXIMUM:
            erreurs["date_naissance"] = f"Incohérence : le collaborateur aurait {age} ans au début du contrat."
    if debut and "date_debut" not in erreurs and debut > aujourd_hui + timedelta(days=366):
        erreurs["date_debut"] = "Date de début à plus d'un an : vérifiez la saisie."
    if debut and fin and "date_fin" not in erreurs and fin < debut:
        erreurs["date_fin"] = "La date de fin de contrat doit être postérieure ou égale à la date de début."

    # 8. Manager : collaborateur existant, actif, différent de soi
    mid = c.get("manager_id")
    if mid and "manager_id" not in erreurs:
        manager = next((x for x in collaborateurs if x.get("id") == mid), None)
        if manager is None:
            erreurs["manager_id"] = "Manager introuvable dans la base."
        elif mon_id and mid == mon_id:
            erreurs["manager_id"] = "Un collaborateur ne peut pas être son propre manager."
        elif manager.get("statut") != "actif" and not (ancien and ancien.get("manager_id") == mid):
            erreurs["manager_id"] = "Ce manager est inactif : choisissez un collaborateur actif."
        elif mon_id and _boucle_hierarchique(mon_id, mid, collaborateurs):
            erreurs["manager_id"] = "Boucle hiérarchique : ce manager dépend lui-même de ce collaborateur."

    # 9. Doublon potentiel (nom + prénom + date de naissance) — alerte
    cle = cle_doublon(c)
    if cle:
        doublons = [x for x in autres if cle_doublon(x) == cle]
        if doublons:
            alertes.append({
                "type": "doublon",
                "message": "Doublon potentiel : un collaborateur avec les mêmes nom, prénom et date de naissance existe déjà.",
                "collaborateurs": [{"id": d["id"], "matricule": d.get("matricule"), "nom": d.get("nom"),
                                    "prenom": d.get("prenom"), "etablissement": d.get("etablissement"),
                                    "statut": d.get("statut")} for d in doublons[:5]],
            })
    return erreurs, alertes


def _boucle_hierarchique(mon_id, manager_id, collaborateurs):
    par_id = {x.get("id"): x for x in collaborateurs}
    courant, vus = manager_id, set()
    while courant and courant not in vus:
        if courant == mon_id:
            return True
        vus.add(courant)
        courant = (par_id.get(courant) or {}).get("manager_id")
    return False


# --------------------------------------------------------------------------- #
# Génération de matricule
# --------------------------------------------------------------------------- #
def appliquer_modele(modele, *, pays="", etablissement="", annee=None):
    """Remplace {PAYS}, {ETAB}, {AAAA}, {AA} ; {N} est laissé pour la séquence."""
    annee = annee or date.today().year
    return (modele.replace("{PAYS}", pays or "").replace("{ETAB}", etablissement or "")
            .replace("{AAAA}", f"{annee:04d}").replace("{AA}", f"{annee % 100:02d}")).upper()


def generer_matricule(parametres, utilises, *, pays="", etablissement="", annee=None):
    """Renvoie (matricule, prefixe, prochain_numero). Le compteur est propre à
    chaque préfixe résolu (ex. EUFR, EUDE…)."""
    regle = parametres.get("matricule") or {}
    modele = (regle.get("modele") or "EU{N}").upper()
    if "{N}" not in modele:
        modele += "{N}"
    largeur = max(3, min(int(regle.get("largeur") or 6), 12))
    gabarit = appliquer_modele(modele, pays=pays, etablissement=etablissement, annee=annee)
    prefixe = gabarit.replace("{N}", "")
    compteurs = regle.get("compteurs") or {}
    n = max(int(compteurs.get(prefixe) or 0) + 1, int(regle.get("depart") or 1))
    utilises = {u.upper() for u in utilises if u}
    while True:
        candidat = gabarit.replace("{N}", str(n).zfill(largeur))
        if candidat not in utilises:
            return candidat, prefixe, n
        n += 1
