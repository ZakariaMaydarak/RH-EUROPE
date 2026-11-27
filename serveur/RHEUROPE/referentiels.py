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

from .i18n import ORDRE as ORDRE_LANGUES, _, langue

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


# Traductions des libellés par défaut : [anglais, allemand, espagnol, italien].
# L'administrateur peut les modifier (champ « traductions » de chaque élément).
TRADUCTIONS_DEFAUT = {
    "sexes": {"F": ["Female", "Weiblich", "Mujer", "Donna"], "H": ["Male", "Männlich", "Hombre", "Uomo"]},
    "pays": {
        "FR": ["France", "Frankreich", "Francia", "Francia"], "DE": ["Germany", "Deutschland", "Alemania", "Germania"],
        "AT": ["Austria", "Österreich", "Austria", "Austria"], "BE": ["Belgium", "Belgien", "Bélgica", "Belgio"],
        "CH": ["Switzerland", "Schweiz", "Suiza", "Svizzera"], "ES": ["Spain", "Spanien", "España", "Spagna"],
        "IT": ["Italy", "Italien", "Italia", "Italia"], "GB": ["United Kingdom", "Vereinigtes Königreich", "Reino Unido", "Regno Unito"],
        "NL": ["Netherlands", "Niederlande", "Países Bajos", "Paesi Bassi"], "PT": ["Portugal", "Portugal", "Portugal", "Portogallo"],
        "HU": ["Hungary", "Ungarn", "Hungría", "Ungheria"], "CZ": ["Czechia", "Tschechien", "Chequia", "Cechia"],
        "DK": ["Denmark", "Dänemark", "Dinamarca", "Danimarca"], "IE": ["Ireland", "Irland", "Irlanda", "Irlanda"],
        "PL": ["Poland", "Polen", "Polonia", "Polonia"], "LU": ["Luxembourg", "Luxemburg", "Luxemburgo", "Lussemburgo"],
    },
    "services": {
        "DIR": ["Management", "Direktion", "Dirección", "Direzione"],
        "REC": ["Front desk", "Rezeption", "Recepción", "Ricevimento"],
        "HEB": ["Housekeeping", "Housekeeping", "Pisos", "Housekeeping"],
        "TEC": ["Maintenance", "Technik / Instandhaltung", "Mantenimiento", "Manutenzione"],
        "PDJ": ["Breakfast / Food & beverage", "Frühstück / Gastronomie", "Desayuno / Restauración", "Colazione / Ristorazione"],
        "COM": ["Sales", "Vertrieb", "Comercial", "Commerciale"],
        "ADM": ["Administration", "Verwaltung", "Administración", "Amministrazione"],
    },
    "postes": {
        "DIR_HOTEL": ["Hotel manager", "Hoteldirektor(in)", "Director(a) de hotel", "Direttore/Direttrice d'albergo"],
        "DIR_ADJ": ["Deputy hotel manager", "Stellvertretende(r) Hoteldirektor(in)", "Subdirector(a)", "Vicedirettore/Vicedirettrice"],
        "CHEF_REC": ["Front office manager", "Empfangschef(in)", "Jefe/a de recepción", "Capo ricevimento"],
        "RECEP": ["Receptionist", "Rezeptionist(in)", "Recepcionista", "Receptionist"],
        "NIGHT": ["Night auditor", "Nachtportier", "Recepcionista de noche", "Portiere di notte"],
        "GOUV": ["Housekeeper", "Hausdame / Hausdiener", "Gobernante/a", "Governante"],
        "VALET": ["Room attendant", "Zimmerreinigung", "Camarero/a de pisos", "Cameriere/a ai piani"],
        "TECH": ["Maintenance technician", "Haustechniker(in)", "Técnico/a de mantenimiento", "Tecnico/a di manutenzione"],
        "EMP_PDJ": ["Breakfast attendant", "Frühstücksmitarbeiter(in)", "Empleado/a de desayunos", "Addetto/a colazioni"],
        "COMMERCIAL": ["Sales representative", "Vertriebsmitarbeiter(in)", "Comercial", "Commerciale"],
        "ASSISTANT": ["Administrative assistant", "Verwaltungsassistent(in)", "Asistente administrativo/a", "Assistente amministrativo/a"],
    },
    "types_contrat": {
        "CDI": ["Permanent contract", "Unbefristeter Vertrag", "Contrato indefinido", "Tempo indeterminato"],
        "CDD": ["Fixed-term contract", "Befristeter Vertrag", "Contrato temporal", "Tempo determinato"],
        "APPRENTI": ["Apprenticeship / Work-study", "Ausbildung / Duales Studium", "Aprendizaje / Formación dual", "Apprendistato / Alternanza"],
        "STAGE": ["Internship", "Praktikum", "Prácticas", "Tirocinio"],
        "INTERIM": ["Temporary agency", "Zeitarbeit", "Trabajo temporal (ETT)", "Lavoro interinale"],
        "SAISON": ["Seasonal", "Saisonarbeit", "Temporada", "Stagionale"],
        "EXTRA": ["Extra / On call", "Aushilfe", "Extra", "Extra / A chiamata"],
    },
    "motifs_sortie": {
        "FIN_CONTRAT": ["End of contract", "Vertragsende", "Fin de contrato", "Fine contratto"],
        "DEMISSION": ["Resignation", "Kündigung durch Mitarbeiter(in)", "Dimisión", "Dimissioni"],
        "LICENCIEMENT": ["Dismissal", "Kündigung durch Arbeitgeber", "Despido", "Licenziamento"],
        "RUPTURE": ["Mutual termination", "Aufhebungsvertrag", "Rescisión de mutuo acuerdo", "Risoluzione consensuale"],
        "RETRAITE": ["Retirement", "Ruhestand", "Jubilación", "Pensionamento"],
        "MUTATION": ["Transfer to another hotel", "Versetzung in ein anderes Hotel", "Traslado a otro establecimiento", "Trasferimento ad altra struttura"],
        "FIN_ESSAI": ["End of probation period", "Ende der Probezeit", "Fin del periodo de prueba", "Fine del periodo di prova"],
        "AUTRE": ["Other", "Sonstiges", "Otro", "Altro"],
    },
}


def completer(refs):
    """Référentiels enregistrés complétés des listes absentes (valeurs par défaut)
    et des traductions par défaut manquantes."""
    refs = dict(refs or {})
    for type_, defaut in DEFAUTS.items():
        if type_ not in refs or not isinstance(refs[type_], list):
            refs[type_] = [dict(e) for e in defaut]
        trads = TRADUCTIONS_DEFAUT.get(type_, {})
        for e in refs[type_]:
            if "traductions" not in e and e.get("code") in trads:
                e["traductions"] = dict(zip(ORDRE_LANGUES, trads[e["code"]]))
    return refs


def index(refs):
    """{type: {code: element}} pour des recherches rapides."""
    return {t: {e["code"]: e for e in refs.get(t, [])} for t in TYPES}


def libelle(refs_index, type_, code, base=False):
    """Libellé dans la langue de la requête (`base=True` : libellé français de
    référence, pour l'historique et les exports)."""
    e = refs_index.get(type_, {}).get(code)
    if e is None:
        return code or ""
    if not base:
        lang = langue()
        if lang != "fr":
            trad = (e.get("traductions") or {}).get(lang)
            if trad:
                return trad
    return e.get("libelle") or code


def _bool(v):
    return v is True or str(v).strip().lower() in ("1", "true", "oui", "vrai", "yes", "x")


def valider_liste(type_, elements, refs, codes_utilises):
    """Contrôle et normalise une liste envoyée par l'administrateur.
    Renvoie (liste_normalisée, erreurs)."""
    erreurs = []
    if type_ not in TYPES:
        return None, [_("Référentiel inconnu.")]
    if not isinstance(elements, list):
        return None, [_("Liste attendue.")]
    vus, propre = set(), []
    pays = {p["code"] for p in refs.get("pays", [])}
    for i, brut in enumerate(elements, 1):
        if not isinstance(brut, dict):
            erreurs.append(_("Ligne {i} : format invalide.", i=i))
            continue
        code = str(brut.get("code") or "").strip().upper()
        lib = str(brut.get("libelle") or "").strip()
        if not CODE_RE.match(code):
            erreurs.append(_("Ligne {i} : code « {code} » invalide (lettres, chiffres, - et _, 20 caractères max).",
                             i=i, code=code or _("(vide)")))
            continue
        if code in vus:
            erreurs.append(_("Ligne {i} : le code {code} est en double.", i=i, code=code))
            continue
        if not lib:
            erreurs.append(_("Ligne {i} : libellé obligatoire pour {code}.", i=i, code=code))
            continue
        vus.add(code)
        e = {"code": code, "libelle": lib[:120], "actif": _bool(brut.get("actif", True))}
        trads = brut.get("traductions") if isinstance(brut.get("traductions"), dict) else {}
        propres = {k: str(v).strip()[:120] for k, v in trads.items() if k in ORDRE_LANGUES and str(v or "").strip()}
        e["traductions"] = propres   # {} = traductions volontairement vides
        if type_ == "etablissements":
            p = str(brut.get("pays") or "").strip().upper()
            if p not in pays:
                erreurs.append(_("Ligne {i} : pays « {pays} » inconnu pour {code}.", i=i, pays=p or _("(vide)"), code=code))
                continue
            e["pays"] = p
        if type_ == "postes":
            e["sans_manager"] = _bool(brut.get("sans_manager", False))
        if type_ == "types_contrat":
            e["date_fin_requise"] = _bool(brut.get("date_fin_requise", False))
        propre.append(e)
    supprimes = (codes_utilises or set()) - vus
    if supprimes:
        erreurs.append(_("Codes utilisés par des collaborateurs, impossibles à supprimer (désactivez-les) : {codes}",
                         codes=", ".join(sorted(supprimes))))
    if type_ == "pays":
        restants = {e["code"] for e in propre}
        orphelins = sorted({e.get("pays") for e in refs.get("etablissements", [])} - restants - {None})
        if orphelins:
            erreurs.append(_("Pays utilisés par des établissements, impossibles à supprimer : {codes}",
                             codes=", ".join(orphelins)))
    return propre, erreurs
