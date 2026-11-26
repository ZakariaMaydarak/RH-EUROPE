"""
Export standardisé des collaborateurs (Excel et CSV) pour l'alimentation des
systèmes internes : colonnes fixes, codes ET libellés des référentiels, dates
ISO (AAAA-MM-JJ) en CSV et vraies dates en Excel, encodage UTF-8.
"""

import csv
import io
from datetime import datetime

from . import referentiels as R
from .validation import date_iso

COLONNES = [
    ("Matricule", "matricule"),
    ("Nom", "nom"),
    ("Prenom", "prenom"),
    ("SexeCode", "sexe"),
    ("Sexe", "@sexes:sexe"),
    ("Email", "email"),
    ("DateNaissance", "#date_naissance"),
    ("DateDebutContrat", "#date_debut"),
    ("DateFinContrat", "#date_fin"),
    ("TypeContratCode", "type_contrat"),
    ("TypeContrat", "@types_contrat:type_contrat"),
    ("ServiceCode", "service"),
    ("Service", "@services:service"),
    ("PosteCode", "poste"),
    ("Poste", "@postes:poste"),
    ("EtablissementCode", "etablissement"),
    ("Etablissement", "@etablissements:etablissement"),
    ("PaysCode", "=pays_code"),
    ("Pays", "=pays"),
    ("ManagerMatricule", "=manager_matricule"),
    ("ManagerNom", "=manager_nom"),
    ("Statut", "=statut"),
    ("DateSortie", "#date_sortie"),
    ("MotifSortieCode", "motif_sortie"),
    ("MotifSortie", "@motifs_sortie:motif_sortie"),
    ("CreeLe", "=cree_le"),
    ("ModifieLe", "=modifie_le"),
]


def filtrer(collaborateurs, refs, filtres):
    """filtres : {pays, etablissement, service, type_contrat, statut} (listes ou chaînes)."""
    idx = R.index(refs)

    def valeurs(cle):
        v = filtres.get(cle)
        if not v:
            return None
        if isinstance(v, str):
            v = [x for x in v.split(",") if x]
        return {x.strip().upper() if cle != "statut" else x.strip().lower() for x in v} or None

    pays, etab, serv, tc, statut = (valeurs(k) for k in ("pays", "etablissement", "service", "type_contrat", "statut"))
    res = []
    for c in collaborateurs:
        if pays and (idx["etablissements"].get(c.get("etablissement")) or {}).get("pays") not in pays:
            continue
        if etab and c.get("etablissement") not in etab:
            continue
        if serv and c.get("service") not in serv:
            continue
        if tc and c.get("type_contrat") not in tc:
            continue
        if statut and c.get("statut") not in statut:
            continue
        res.append(c)
    return sorted(res, key=lambda c: (c.get("etablissement") or "", c.get("nom") or "", c.get("prenom") or ""))


def lignes(collaborateurs, refs, tous):
    """Une liste de dicts (ordre COLONNES). `tous` : base complète (managers)."""
    idx = R.index(refs)
    par_id = {c["id"]: c for c in tous}
    for c in collaborateurs:
        etab = idx["etablissements"].get(c.get("etablissement")) or {}
        manager = par_id.get(c.get("manager_id")) or {}
        calc = {
            "pays_code": etab.get("pays", ""),
            "pays": R.libelle(idx, "pays", etab.get("pays")) if etab.get("pays") else "",
            "manager_matricule": manager.get("matricule", ""),
            "manager_nom": f"{manager.get('nom', '')} {manager.get('prenom', '')}".strip(),
            "statut": "Actif" if c.get("statut") == "actif" else "Inactif",
            "cree_le": (c.get("cree_le") or "")[:19],
            "modifie_le": (c.get("modifie_le") or "")[:19],
        }
        ligne = {}
        for titre, source in COLONNES:
            if source.startswith("="):
                ligne[titre] = calc[source[1:]]
            elif source.startswith("@"):
                type_, champ = source[1:].split(":")
                ligne[titre] = R.libelle(idx, type_, c.get(champ)) if c.get(champ) else ""
            elif source.startswith("#"):
                ligne[titre] = c.get(source[1:]) or ""
            else:
                ligne[titre] = c.get(source) or ""
        yield ligne


def csv_octets(lignes_):
    tampon = io.StringIO()
    ecrivain = csv.writer(tampon, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    ecrivain.writerow([t for t, _ in COLONNES])
    for l in lignes_:
        ecrivain.writerow([l[t] for t, _ in COLONNES])
    return ("﻿" + tampon.getvalue()).encode("utf-8")   # BOM : accents lus par Excel


def excel_octets(lignes_, filtres_texte):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Collaborateurs"
    ws.append([t for t, _ in COLONNES])
    entete = PatternFill("solid", fgColor="FF0050")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = entete
        cell.alignment = Alignment(vertical="center")
    dates = {i for i, (_, s) in enumerate(COLONNES) if s.startswith("#")}
    nb = 0
    for l in lignes_:
        valeurs = []
        for i, (t, _) in enumerate(COLONNES):
            v = l[t]
            if i in dates and v:
                v = date_iso(v) or v
            valeurs.append(v)
        ws.append(valeurs)
        nb += 1
    for i in dates:
        lettre = get_column_letter(i + 1)
        for cell in ws[lettre][1:]:
            cell.number_format = "DD/MM/YYYY"
    for i, (t, _) in enumerate(COLONNES, 1):
        ws.column_dimensions[get_column_letter(i)].width = max(12, min(len(t) + 4, 34))
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLONNES))}{nb + 1}"

    info = wb.create_sheet("Export")
    info.append(["Application", "HR EUROPE — Employee Master Data"])
    info.append(["Exporté le", datetime.now().strftime("%d/%m/%Y %H:%M")])
    info.append(["Filtres", filtres_texte or "Aucun (tous les collaborateurs)"])
    info.append(["Nombre de collaborateurs", nb])
    info.append(["Données personnelles", "Usage interne Adagio uniquement (RGPD) — ne pas diffuser."])
    info.column_dimensions["A"].width = 26
    info.column_dimensions["B"].width = 70
    tampon = io.BytesIO()
    wb.save(tampon)
    return tampon.getvalue()
