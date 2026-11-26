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
