# HR EUROPE (RHEUROPE) — application du Portail Apps Adagio

Ce dépôt contient **une** application du Portail Apps Adagio : son front (SPA React /
Vite) et sa partie serveur (Blueprint Flask). Le portail fournit la connexion
Microsoft, l'accès par rôle et l'hébergement ; l'application se **déploie seule**,
sans toucher au portail ni aux autres applications.

```
front/                    SPA React (Vite) — base '/RHEUROPE/'
serveur/RHEUROPE/           partie serveur (montée sur /RHEUROPE/ par le portail)
    routes.py             Blueprint `bp` + APP_METADATA (nom, rôle d'accès, rôles internes)
    requirements.txt      dépendances Python propres à l'app (souvent vide)
deploiement/construire.ps1   construit le ZIP à déployer (deploiement/sortie/RHEUROPE.zip)
outils/lancer-en-local.ps1   lance le portail en local avec l'app
outils/initialiser.ps1       personnalise le modèle (une seule fois, à la création)
CLAUDE.md                 règles de travail (pour Claude Code et pour vous)
```

## 1. Créer l'application (une fois)

1. **Réserver l'application** auprès de l'administrateur du portail (Zakaria) :
   identifiant (= URL, ex. `PLANNING_MENAGE`), nom, propriétaires (vos e-mails).
   Il la déclare sur la page *Déploiements*, crée le dépôt GitHub de l'app et l'App
   Role `App.<IDENTIFIANT>` dans Azure.
2. Copier ce modèle dans le dossier de votre dépôt, puis :
   ```powershell
   .\outils\initialiser.ps1 -Slug PLANNING_MENAGE -Nom "Planning ménage"
   git add . ; git commit -m "Initialisation depuis le modele" ; git push -u origin main
   git checkout -b dev ; git push -u origin dev
   ```

## 2. Travailler

```
feature/<sujet>  ──PR──►  dev  ──PR──►  main  ──►  ZIP  ──►  page Déploiements
```

- Une branche `feature/…` par évolution, partant de `dev` ; PR vers `dev`, puis
  `dev` → `main`. **Seul ce qui est dans `main` se déploie.**
- Tester en local : `.\outils\lancer-en-local.ps1` puis http://localhost:8000/RHEUROPE/
  (il faut un clone du dépôt `portail-apps` à côté de ce dépôt, voir l'en-tête du script).

## 3. Déployer (vous-même)

```powershell
git checkout main ; git pull
.\deploiement\construire.ps1          # -> deploiement\sortie\RHEUROPE.zip
```

Puis **Portail → Déploiements** (lien en haut de la page d'accueil) → carte de
l'application → *Nouveau ZIP* → **Déployer**. Le portail contrôle le ZIP (chargement
de l'app testé à part), garde les 5 versions précédentes (bouton *Revenir à cette
version*) et se recharge **sans coupure**. Seuls les propriétaires de l'application
(et l'administrateur) peuvent la déployer.

## 4. Droits

- **Accès à l'application** (voir la carte, ouvrir l'app) : App Role `App.RHEUROPE` dans
  Azure, attribué par l'administrateur du portail.
- **Rôles internes** (`APP_METADATA["role_schema"]`, ex. admin / utilisateur) : gérés
  par les propriétaires de l'app dans la console **Administration** du portail.
