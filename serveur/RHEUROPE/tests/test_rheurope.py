"""
Tests de HR EUROPE (sans le portail : `shared` est simulé).

Lancer depuis la racine du dépôt :
    python serveur/RHEUROPE/tests/test_rheurope.py
"""

import io
import os
import shutil
import sys
import tempfile
import types
import unittest
from datetime import date, timedelta

RACINE_SERVEUR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TMP = tempfile.mkdtemp(prefix="rheurope-tests-")

# --- Faux modules du portail ------------------------------------------------
_utilisateurs = {}
shared = types.ModuleType("shared")
role_store = types.ModuleType("shared.role_store")
role_store.DATA_DIR = TMP
role_store.get_user = lambda app, email: _utilisateurs.get(email)
role_store.list_users = lambda app: [{"email": e, **v} for e, v in sorted(_utilisateurs.items())]


def _upsert(app, email, fields):
    _utilisateurs.setdefault(email, {}).update(fields)
    return {"email": email, **_utilisateurs[email]}


role_store.upsert_user = _upsert
role_store.delete_user = lambda app, email: _utilisateurs.pop(email, None) is not None
auth = types.ModuleType("shared.auth")
auth.get_authenticated_user = lambda headers: {
    "name": headers.get("X-Test-Email", "Utilisateur inconnu"),
    "display_name": headers.get("X-Test-Email"),
    "roles": [r for r in (headers.get("X-Test-Roles") or "").split(",") if r]}
shared.role_store, shared.auth = role_store, auth
sys.modules.update({"shared": shared, "shared.role_store": role_store, "shared.auth": auth})
os.environ["RHEUROPE_AUTOMATISATION"] = "0"
sys.path.insert(0, RACINE_SERVEUR)

from flask import Flask  # noqa: E402

import RHEUROPE.routes as routes  # noqa: E402
from RHEUROPE import service as SV  # noqa: E402
from RHEUROPE import validation as V  # noqa: E402
from RHEUROPE import indicateurs as I  # noqa: E402
from RHEUROPE.store import Store  # noqa: E402

AUJ = SV.aujourd_hui()


def fiche(**kw):
    base = {"nom": "Martin", "prenom": "claire", "matricule": "EU000100", "sexe": "F",
            "email": "claire.martin@accor.com", "date_naissance": "1990-05-12", "date_debut": "2024-01-15",
            "date_fin": "", "type_contrat": "CDI", "service": "REC", "etablissement": "H1111",
            "poste": "DIR_HOTEL", "manager_id": ""}
    base.update(kw)
    return base


class Base(unittest.TestCase):
    def setUp(self):
        dossier = tempfile.mkdtemp(dir=TMP)
        routes.store = Store(dossier)
        self.store = routes.store
        _utilisateurs.clear()
        self.admin = {"email": "admin@adagio-city.com", "nom": "Admin"}
        SV.enregistrer_referentiel(self.store, "etablissements", [
            {"code": "H1111", "libelle": "Adagio Paris Test", "pays": "FR"},
            {"code": "H2222", "libelle": "Adagio Berlin Test", "pays": "DE"}], self.admin)
        app = Flask(__name__)
        app.register_blueprint(routes.bp, url_prefix="/RHEUROPE")
        self.client = app.test_client()

    def comme(self, email, roles=""):
        return {"X-Test-Email": email, "X-Test-Roles": roles}


class TestValidation(Base):
    def test_creation_et_normalisation(self):
        c = SV.creer(self.store, fiche(nom=" martin ", prenom="jean-marie"), self.admin, None)
        self.assertEqual((c["nom"], c["prenom"], c["statut"]), ("MARTIN", "Jean-Marie", "actif"))
        self.assertEqual(self.store.historique()[-1]["action"], "creation")

    def test_champs_obligatoires(self):
        e, _ = SV.verifier_fiche(self.store, {}, None)
        for champ in ("nom", "prenom", "matricule", "sexe", "email", "date_naissance", "date_debut",
                      "type_contrat", "service", "etablissement", "poste", "manager_id"):
            self.assertIn(champ, e)
        self.assertNotIn("date_fin", e)   # pas de type de contrat : date de fin non exigée

    def test_date_fin_obligatoire_pour_cdd(self):
        e, _ = SV.verifier_fiche(self.store, fiche(type_contrat="CDD"), None)
        self.assertIn("date_fin", e)
        e, _ = SV.verifier_fiche(self.store, fiche(type_contrat="CDD", date_fin="2026-12-31"), None)
        self.assertNotIn("date_fin", e)

    def test_manager_obligatoire_sauf_poste_de_direction(self):
        e, _ = SV.verifier_fiche(self.store, fiche(poste="RECEP"), None)
        self.assertIn("manager_id", e)
        e, _ = SV.verifier_fiche(self.store, fiche(poste="DIR_HOTEL"), None)
        self.assertNotIn("manager_id", e)

    def test_unicite_matricule_et_email(self):
        SV.creer(self.store, fiche(), self.admin, None)
        e, _ = SV.verifier_fiche(self.store, fiche(nom="Durand", prenom="Paul", email="paul.durand@accor.com"), None)
        self.assertIn("matricule", e)
        e, _ = SV.verifier_fiche(self.store, fiche(matricule="EU000200", nom="Durand", prenom="Paul",
                                                   email="CLAIRE.MARTIN@accor.com"), None)
        self.assertIn("email", e)

    def test_format_et_domaine_email(self):
        for mauvais in ("claire.martin", "claire@gmail.com", "h1111@accor.com", "reception@accor.com"):
            e, _ = SV.verifier_fiche(self.store, fiche(email=mauvais), None)
            self.assertIn("email", e, mauvais)
        e, _ = SV.verifier_fiche(self.store, fiche(email="claire.martin@fr.accor.com"), None)
        self.assertNotIn("email", e)

    def test_coherence_des_dates(self):
        e, _ = SV.verifier_fiche(self.store, fiche(type_contrat="CDD", date_debut="2025-01-10", date_fin="2025-01-01"), None)
        self.assertIn("date_fin", e)
        e, _ = SV.verifier_fiche(self.store, fiche(date_naissance="2015-01-01"), None)
        self.assertIn("date_debut", e)
        futur = (AUJ + timedelta(days=3)).isoformat()
        e, _ = SV.verifier_fiche(self.store, fiche(date_naissance=futur), None)
        self.assertIn("date_naissance", e)
        e, _ = SV.verifier_fiche(self.store, fiche(date_naissance="1990-02-30"), None)
        self.assertIn("date_naissance", e)

    def test_doublon_bloque_sans_confirmation(self):
        SV.creer(self.store, fiche(), self.admin, None)
        autre = fiche(matricule="EU000999", email="claire.martin2@accor.com")
        with self.assertRaises(SV.ErreurMetier) as ctx:
            SV.creer(self.store, autre, self.admin, None)
        self.assertEqual(ctx.exception.code, 409)
        SV.creer(self.store, autre, self.admin, None, confirmer_doublon=True)
        self.assertEqual(len(SV.collaborateurs(self.store)), 2)

    def test_perimetre_gm(self):
        e, _ = SV.verifier_fiche(self.store, fiche(etablissement="H2222"), {"H1111"})
        self.assertIn("etablissement", e)

    def test_manager_actif_et_pas_soi_meme(self):
        chef = SV.creer(self.store, fiche(), self.admin, None)
        e, _ = SV.verifier_fiche(self.store, fiche(matricule="EU1", poste="RECEP", manager_id=chef["id"]), None)
        self.assertNotIn("manager_id", e)
        e, _ = SV.verifier_fiche(self.store, fiche(poste="RECEP", manager_id=chef["id"]), None, chef["id"])
        self.assertIn("manager_id", e)
        SV.desactiver(self.store, chef["id"], self.admin, None, AUJ.isoformat(), "DEMISSION")
        e, _ = SV.verifier_fiche(self.store, fiche(matricule="EU2", poste="RECEP", manager_id=chef["id"]), None)
        self.assertIn("manager_id", e)


class TestCycleDeVie(Base):
    def test_desactivation_reactivation(self):
        c = SV.creer(self.store, fiche(), self.admin, None)
        hier = (AUJ - timedelta(days=1)).isoformat()
        c, programme = SV.desactiver(self.store, c["id"], self.admin, None, hier, "DEMISSION")
        self.assertFalse(programme)
        self.assertEqual((c["statut"], c["date_fin"], c["motif_sortie"]), ("inactif", hier, "DEMISSION"))
        with self.assertRaises(SV.ErreurMetier):   # date de fin passée sans nouvelle date
            SV.reactiver(self.store, c["id"], self.admin, None, {"type_contrat": "CDD"})
        c = SV.reactiver(self.store, c["id"], self.admin, None,
                         {"type_contrat": "CDD", "date_fin": (AUJ + timedelta(days=90)).isoformat()})
        self.assertEqual(c["statut"], "actif")
        actions = [e["action"] for e in self.store.historique()]
        self.assertEqual(actions[-3:], ["creation", "desactivation", "reactivation"])

    def test_sortie_programmee_puis_automatique(self):
        c = SV.creer(self.store, fiche(), self.admin, None)
        demain = AUJ + timedelta(days=1)
        c, programme = SV.desactiver(self.store, c["id"], self.admin, None, demain.isoformat(), "MUTATION")
        self.assertTrue(programme)
        self.assertEqual(c["statut"], "actif")
        self.assertEqual(SV.desactivation_automatique(self.store, demain), [])          # dernier jour : actif
        faits = SV.desactivation_automatique(self.store, demain + timedelta(days=1))
        self.assertEqual(len(faits), 1)
        c = SV.collaborateurs(self.store)[0]
        self.assertEqual((c["statut"], c["motif_sortie"], c["date_sortie"]), ("inactif", "MUTATION", demain.isoformat()))
        self.assertEqual(self.store.historique()[-1]["par"], "automatisation")

    def test_modification_tracee(self):
        c = SV.creer(self.store, fiche(), self.admin, None)
        _, diff = SV.modifier(self.store, c["id"], fiche(service="HEB"), self.admin, None)
        self.assertEqual([d["champ"] for d in diff], ["service"])
        self.assertEqual(diff[0]["apres"], "Hébergement")

    def test_effacement_rgpd(self):
        c = SV.creer(self.store, fiche(), self.admin, None)
        SV.supprimer(self.store, c["id"], self.admin)
        self.assertEqual(SV.collaborateurs(self.store), [])
        texte = str(self.store.historique())
        self.assertNotIn("MARTIN", texte)
        self.assertNotIn("claire.martin", texte)


class TestMatricule(Base):
    def test_generation_unique_et_configurable(self):
        m1 = SV.generer(self.store, self.admin, "H1111")
        m2 = SV.generer(self.store, self.admin, "H1111")
        self.assertEqual((m1, m2), ("EU000001", "EU000002"))
        SV.enregistrer_parametres(self.store, {"domaines_email": ["accor.com"],
                                               "matricule": {"modele": "{PAYS}{AA}{N}", "largeur": 4, "depart": 1}},
                                  self.admin)
        self.assertEqual(SV.generer(self.store, self.admin, "H2222"), f"DE{AUJ.year % 100:02d}0001")
        SV.creer(self.store, fiche(matricule=f"FR{AUJ.year % 100:02d}0001"), self.admin, None)
        self.assertEqual(SV.generer(self.store, self.admin, "H1111"), f"FR{AUJ.year % 100:02d}0002")


class TestIndicateurs(Base):
    def test_tableau_de_bord(self):
        chef = SV.creer(self.store, fiche(), self.admin, None)
        SV.creer(self.store, fiche(nom="Dupont", prenom="Luc", matricule="EU2", email="luc.dupont@accor.com",
                                   sexe="H", poste="RECEP", manager_id=chef["id"], type_contrat="CDD",
                                   date_debut=(AUJ - timedelta(days=5)).isoformat(),
                                   date_fin=(AUJ + timedelta(days=10)).isoformat()), self.admin, None)
        t = I.tableau_de_bord(SV.collaborateurs(self.store), SV.refs(self.store), AUJ)
        self.assertEqual(t["compteurs"]["actifs"], 2)
        self.assertEqual(t["compteurs"]["arrivees"], 1)
        self.assertEqual(t["compteurs"]["echeances"], 1)
        self.assertEqual(t["compteurs"]["departs"], 1)
        self.assertEqual({r["code"]: r["nb"] for r in t["repartition"]["sexe"]}, {"F": 1, "H": 1})


class TestApi(Base):
    def test_droits_et_perimetre(self):
        a = self.client.post("/RHEUROPE/api/collaborateurs", json={"collaborateur": fiche()},
                             headers=self.comme("admin@adagio-city.com", "App.Admin"))
        self.assertEqual(a.status_code, 201, a.get_json())
        self.client.post("/RHEUROPE/api/collaborateurs",
                         json={"collaborateur": fiche(matricule="EU5", email="b.b@accor.com", nom="Bb",
                                                      prenom="Bob", etablissement="H2222")},
                         headers=self.comme("admin@adagio-city.com", "App.Admin"))
        # Directeur H1111 (règle hXXXX@) : ne voit que son hôtel
        r = self.client.get("/RHEUROPE/api/collaborateurs", headers=self.comme("h1111-gm@accor.com"))
        self.assertEqual([c["etablissement"] for c in r.get_json()], ["H1111"])
        self.assertEqual(self.client.get("/RHEUROPE/api/export", headers=self.comme("h1111-gm@accor.com")).status_code, 403)
        # Sans rôle : rien
        self.assertEqual(self.client.get("/RHEUROPE/api/collaborateurs",
                                         headers=self.comme("x.y@adagio-city.com")).status_code, 403)

    def test_erreurs_bloquantes_renvoyees_par_champ(self):
        r = self.client.post("/RHEUROPE/api/collaborateurs", json={"collaborateur": fiche(email="faux")},
                             headers=self.comme("admin@adagio-city.com", "App.Admin"))
        self.assertEqual(r.status_code, 400)
        self.assertIn("email", r.get_json()["erreurs"])

    def test_exports(self):
        SV.creer(self.store, fiche(), self.admin, None)
        h = self.comme("admin@adagio-city.com", "App.Admin")
        r = self.client.get("/RHEUROPE/api/export?format=csv&pays=FR", headers=h)
        texte = r.data.decode("utf-8-sig")
        self.assertTrue(texte.startswith("Matricule;Nom;Prenom"))
        self.assertIn("EU000100;MARTIN;Claire", texte)
        r = self.client.get("/RHEUROPE/api/export?format=csv&pays=DE", headers=h)
        self.assertEqual(len(r.data.decode("utf-8-sig").strip().splitlines()), 1)
        r = self.client.get("/RHEUROPE/api/export?format=xlsx", headers=h)
        from openpyxl import load_workbook
        ws = load_workbook(io.BytesIO(r.data)).active
        self.assertEqual(ws["A2"].value, "EU000100")
        self.assertEqual(self.store.historique()[-1]["action"], "export")

    def test_import_etablissements(self):
        contenu = "Code;Nom;Pays\nH3333;Adagio Wien;Autriche\nH1111;Adagio Paris Renommé;FR\n".encode("utf-8")
        r = self.client.post("/RHEUROPE/api/referentiels/etablissements/import",
                             data={"fichier": (io.BytesIO(contenu), "etab.csv")},
                             headers=self.comme("admin@adagio-city.com", "App.Admin"))
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual((r.get_json()["ajoutes"], r.get_json()["mis_a_jour"]), (1, 1))
        codes = {e["code"]: e for e in SV.refs(self.store)["etablissements"]}
        self.assertEqual(codes["H3333"]["pays"], "AT")

    def test_referentiel_code_utilise_non_supprimable(self):
        SV.creer(self.store, fiche(), self.admin, None)
        r = self.client.put("/RHEUROPE/api/referentiels/services",
                            json={"elements": [{"code": "HEB", "libelle": "Hébergement"}]},
                            headers=self.comme("admin@adagio-city.com", "App.Admin"))
        self.assertEqual(r.status_code, 400)
        self.assertIn("REC", " ".join(r.get_json()["details"]))


class TestLangue(Base):
    def setUp(self):
        super().setUp()
        self.h = {**self.comme("admin@adagio-city.com", "App.Admin")}

    def test_messages_traduits_selon_l_entete(self):
        SV.creer(self.store, fiche(), self.admin, None)
        corps = {"collaborateur": fiche(nom="Durand", prenom="Paul", email="paul.durand@accor.com")}
        r = self.client.post("/RHEUROPE/api/collaborateurs/verifier", json=corps, headers={**self.h, "X-Langue": "de"})
        self.assertIn("Personalnummer EU000100", r.get_json()["erreurs"]["matricule"])
        r = self.client.post("/RHEUROPE/api/collaborateurs/verifier", json=corps, headers={**self.h, "X-Langue": "en"})
        self.assertIn("already assigned", r.get_json()["erreurs"]["matricule"])
        r = self.client.post("/RHEUROPE/api/collaborateurs/verifier", json=corps, headers=self.h)
        self.assertIn("déjà attribué", r.get_json()["erreurs"]["matricule"])

    def test_preference_memorisee(self):
        self.assertEqual(self.client.put("/RHEUROPE/api/me/langue", json={"langue": "xx"}, headers=self.h).status_code, 400)
        self.client.put("/RHEUROPE/api/me/langue", json={"langue": "it"}, headers=self.h)
        me = self.client.get("/RHEUROPE/api/me", headers=self.h).get_json()
        self.assertEqual(me["langue"], "it")
        self.assertIn("Italiano", me["langues"].values())
        r = self.client.post("/RHEUROPE/api/collaborateurs/verifier", json={"collaborateur": {}}, headers=self.h)
        self.assertEqual(r.get_json()["erreurs"]["nom"], "Campo obbligatorio.")   # préférence sans en-tête

    def test_referentiels_traduits_mais_historique_et_export_en_francais(self):
        c = SV.creer(self.store, fiche(), self.admin, None)
        refs = self.client.get("/RHEUROPE/api/referentiels", headers=self.h).get_json()["referentiels"]
        cdi = next(e for e in refs["types_contrat"] if e["code"] == "CDI")
        self.assertEqual(cdi["traductions"]["de"], "Unbefristeter Vertrag")
        t = self.client.get("/RHEUROPE/api/tableau-de-bord", headers={**self.h, "X-Langue": "es"}).get_json()
        self.assertEqual(t["repartition"]["type_contrat"][0]["libelle"], "Contrato indefinido")
        self.client.put(f"/RHEUROPE/api/collaborateurs/{c['id']}", json={"collaborateur": fiche(service="HEB")},
                        headers={**self.h, "X-Langue": "en"})
        self.assertEqual(self.store.historique()[-1]["changements"][0]["apres"], "Hébergement")
        texte = self.client.get("/RHEUROPE/api/export?format=csv", headers={**self.h, "X-Langue": "de"}).data.decode("utf-8-sig")
        self.assertIn(";CDI;CDI;", texte)
        self.assertIn("Hébergement", texte)

    def test_traductions_saisies_par_l_admin(self):
        r = self.client.put("/RHEUROPE/api/referentiels/services", headers=self.h, json={"elements": [
            {"code": "REC", "libelle": "Réception", "traductions": {"en": "Reception", "xx": "?"}},
            {"code": "HEB", "libelle": "Hébergement", "traductions": {}}]})
        self.assertEqual(r.status_code, 200, r.get_json())
        services = {e["code"]: e for e in SV.refs(self.store)["services"]}
        self.assertEqual(services["REC"]["traductions"], {"en": "Reception"})
        self.assertEqual(services["HEB"]["traductions"], {})   # vidées volontairement : pas de retour des valeurs par défaut


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
