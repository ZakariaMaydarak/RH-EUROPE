# ============================================================================
# Lance le PORTAIL en local avec CETTE application (http://localhost:8000/<SLUG>/).
#
# Prerequis (une fois) :
#   - un clone du depot portail-apps (lecture seule suffit), par defaut le dossier
#     frere ..\portail-apps, sinon -Portail <chemin> ou variable PORTAIL_REPO ;
#   - son environnement Python :  cd <portail-apps> ; python -m venv .venv ;
#     .\.venv\Scripts\pip install -r requirements.txt
#
# Le code serveur de l'app est charge DIRECTEMENT depuis serveur\ (PORTAIL_APPS_DEV_DIR) :
# une modification Python recharge le serveur tout seul. Le front est construit dans
# serveur\<SLUG>\static_files\ (ignore par git) ; pour travailler le front a chaud,
# lancer en plus `npm run dev` dans front\ (appels /<SLUG>/api relayes vers le port 8000).
# Donnees locales : .\data\ (ignore par git). Role simule : App.Admin (-Roles pour changer).
# ============================================================================
param(
    [string]$Portail = $env:PORTAIL_REPO,
    [string]$Roles = 'App.Admin',
    [switch]$SansBuild
)
$ErrorActionPreference = 'Stop'
$Racine = Split-Path $PSScriptRoot -Parent
if (-not $Portail) { $Portail = Join-Path (Split-Path $Racine -Parent) 'portail-apps' }
if (-not (Test-Path (Join-Path $Portail 'app.py'))) {
    throw "Clone du portail introuvable : $Portail (git clone https://github.com/ZakariaMaydarak/portail-apps.git, ou -Portail <chemin>)"
}
$dossierServeur = Get-ChildItem (Join-Path $Racine 'serveur') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'routes.py') } | Select-Object -First 1
$Slug = $dossierServeur.Name

if (-not $SansBuild) {
    Push-Location (Join-Path $Racine 'front')
    $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        if (-not (Test-Path 'node_modules')) { npm install 2>&1 | ForEach-Object { "$_" } | Out-Host }
        node 'node_modules\vite\bin\vite.js' build 2>&1 | ForEach-Object { "$_" } | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "vite build a echoue" }
    } finally { $ErrorActionPreference = $eap; Pop-Location }
    $static = Join-Path $dossierServeur.FullName 'static_files'
    if (Test-Path $static) { Remove-Item -Recurse -Force $static }
    Copy-Item -Recurse (Join-Path $Racine 'front\dist') $static
}

$python = Join-Path $Portail '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }
$env:PORTAIL_APPS_DEV_DIR = Join-Path $Racine 'serveur'
$env:PORTAIL_DATA_DIR = Join-Path $Racine 'data'
$env:PORTAIL_APPS_ROOT = Join-Path $Racine 'data\apps-deployees'
$env:PORTAIL_DEV_ROLES = $Roles
Write-Host "Portail local : http://localhost:8000/$Slug/   (Ctrl+C pour arreter)" -ForegroundColor Green
Push-Location $Portail
try { & $python app.py } finally { Pop-Location }
