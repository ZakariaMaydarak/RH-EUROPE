# Application RHEUROPE — Portail Apps Adagio

Ce dépôt = **une seule application** du Portail Apps Adagio (portail Flask sur Azure
App Service, connexion Microsoft Entra ID par Easy Auth). Lire aussi `README.md`.

## Architecture (à respecter)

- `front/` : SPA React + Vite. `vite.config.js` garde **`base: '/RHEUROPE/'`** ; les appels
  API se construisent avec `import.meta.env.BASE_URL + 'api/…'` (jamais d'URL en dur).
- `serveur/RHEUROPE/` : partie serveur, **tout** le code serveur de l'app est ici.
  - `routes.py` expose `bp` (Blueprint Flask) et `APP_METADATA` (`name`, `description`,
    `icon`, `category` existante, `version`, `required_role` = `App.RHEUROPE`,
    `role_schema` optionnel). Le portail le monte sur `/RHEUROPE/`.
  - Les routes d'API sont sous `/RHEUROPE/api/…` et répondent en JSON.
  - Modules internes : `from . import mon_module` (imports relatifs).
  - Du portail, on n'utilise QUE : `shared.auth.get_authenticated_user`,
    `shared.role_store` (rôles internes + `DATA_DIR`). Rien d'autre du portail,
    jamais le code d'une autre application.
  - **Données persistantes** : sous `os.path.join(role_store.DATA_DIR, "RHEUROPE")`
    (= /home/data/portail/RHEUROPE en prod). JAMAIS dans `serveur/RHEUROPE/` : ce dossier
    est remplacé à chaque déploiement. Écritures atomiques (fichier .tmp puis os.replace).
  - Dépendances Python absentes du portail : `serveur/RHEUROPE/requirements.txt`
    (installées à part au déploiement). Pas de bibliothèque déjà fournie par le portail.
  - Tâches de fond / planifiées : jamais au chargement si
    `PORTAIL_VALIDATION_DEPLOIEMENT=1` (contrôle à blanc d'un déploiement) ; si une
    tâche ne doit pas être coupée, `deploiement_occupe()` renvoie un message.
  - Secrets (clés d'API, mots de passe) : JAMAIS dans Git ni dans le front. Ils se
    demandent à l'administrateur du portail (paramètres de l'App Service) et se
    lisent par `os.environ`.
- Interface en **français**, couleurs de la charte Adagio (magenta `#FF0050`).

## HR EUROPE — fonctionnement (v1.0.0, nov. 2026)

Référentiel unique des collaborateurs des hôtels Adagio en Europe (Employee Master Data).

- **Rôles internes** (`role_schema`, champ de périmètre `sites`) : `admin` (Europe entière,
  référentiels, paramètres, utilisateurs, exports, qualité), `gm` (ses établissements),
  `aucun`. 1re connexion (`routes.regle_defaut`) : App.Admin → admin ; `hXXXX@…` → gm sur
  HXXXX ; sinon aucun. Gérés aussi dans l'app (page Utilisateurs, via `shared.role_store`).
  Dev local : `RHEUROPE_DEV_ROLE` / `RHEUROPE_DEV_SITES` simulent un profil.
- **Modules** (`serveur/RHEUROPE/`) : `store.py` (JSON atomiques + historique JSON Lines),
  `referentiels.py` (listes par défaut, contrôle des listes), `validation.py` (contrôles
  bloquants + alertes, génération de matricule), `service.py` (règles métier, historique),
  `indicateurs.py` (tableau de bord, qualité), `export.py` (Excel / CSV standardisés),
  `routes.py` (API, droits, planificateur). `validation`, `service`, `indicateurs`,
  `export` ne dépendent ni de Flask ni du portail.
- **Données** (DATA_DIR/RHEUROPE) : `collaborateurs.json`, `referentiels.json`,
  `parametres.json`, `automatisation.json`, `historique.jsonl` (audit : qui, quand, quoi,
  avant → après).
- **Contrôles bloquants** : complétude (date de fin seulement si le type de contrat
  l'exige ; manager facultatif pour un poste `sans_manager`), unicité Europe du matricule
  et de l'e-mail, format + domaine (`parametres.domaines_email`, sous-domaines acceptés)
  + adresse nominative, valeurs des référentiels actives, périmètre du GM, cohérence des
  dates (âge 14-80 ans au début, fin ≥ début, naissance non future), manager actif sans
  boucle. **Doublon potentiel** (nom + prénom + date de naissance, sans accents) : 409 tant
  que `confirmer_doublon` n'est pas envoyé.
- **Statut** : désactivation manuelle (date de sortie + motif ; date future = sortie
  programmée, date de fin positionnée), réactivation (nouvelle date de fin ≥ aujourd'hui
  ou aucune), désactivation automatique quotidienne (APScheduler, 01:05 Europe/Paris,
  `RHEUROPE_AUTOMATISATION_HEURE/MINUTE`, `RHEUROPE_AUTOMATISATION=0` pour couper,
  rattrapage 45 s après le démarrage) quand date de fin < aujourd'hui. Effacement RGPD
  (admin, saisie « EFFACER ») : fiche supprimée, historique anonymisé.
- **Matricule** : modèle configurable (`{PAYS}`, `{ETAB}`, `{AAAA}`, `{AA}`, `{N}`),
  compteur par préfixe réservé à chaque génération, matricules existants sautés.
- **Exports** (admin) : `GET /api/export?format=xlsx|csv&pays=&etablissement=&service=&type_contrat=&statut=`
  (listes séparées par des virgules), 27 colonnes fixes (`export.COLONNES`), tracés.
- Tests : `python serveur/RHEUROPE/tests/test_rheurope.py` (portail simulé, aussi en CI).

## Ce qu'on ne fait JAMAIS depuis ce dépôt

- Modifier le dépôt `portail-apps` (le portail), ses fichiers `shared/`, ses
  templates ou une autre application. Un besoin côté portail (nouvelle fonction
  partagée, rôle, paramètre Azure) se **demande** à l'administrateur du portail.
- Déployer par Kudu / ZipDeploy (réservé au portail lui-même).
- Pousser directement sur `main`.

## Flux Git

`feature/<sujet>` (depuis `dev`) → PR vers `dev` → PR `dev` → `main`. Messages de
commit en français. Seul `main` se déploie.

## Tester

- Local : `.\outils\lancer-en-local.ps1` (portail local + cette app, rôle App.Admin simulé ;
  `-Roles App.RHEUROPE` pour tester comme un utilisateur). Front à chaud : `npm run dev`
  dans `front/` en plus.
- Vérifier le parcours dans le navigateur avant toute PR.

## Déployer

1. `main` à jour et propre : `git checkout main ; git pull`.
2. `.\deploiement\construire.ps1` → `deploiement\sortie\RHEUROPE.zip`.
3. Portail → **Déploiements** → carte RHEUROPE → Nouveau ZIP → Déployer → attendre
   « Terminé » → tester `/RHEUROPE/`. En cas de problème : *Revenir à cette version*.
