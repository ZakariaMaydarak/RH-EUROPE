# ============================================================================
# Personnalise le modele pour une NOUVELLE application (a lancer une seule fois).
#   -Slug       identifiant = URL dans le portail (/SLUG/) et nom de l'App Role
#               (App.SLUG). Lettres, chiffres et _, commence par une lettre.
#               Convention : MAJUSCULES, ex. PLANNING_MENAGE.
#   -Nom        nom affiche sur la carte du portail
#   -Icone      1 a 3 lettres (defaut : 2 premieres lettres du slug)
#   -Categorie  categorie EXISTANTE de l'accueil du portail (defaut : Outils Adagio)
# Le slug doit etre reserve aupres de l'administrateur du portail (page Deploiements).
# ============================================================================
param(
    [Parameter(Mandatory = $true)] [string]$Slug,
    [Parameter(Mandatory = $true)] [string]$Nom,
    [string]$Icone = '',
    [string]$Categorie = 'Outils Adagio',
    [string]$Description = ''
)
$ErrorActionPreference = 'Stop'
if ($Slug -notmatch '^[A-Za-z][A-Za-z0-9_]{1,40}$') { throw "Slug invalide : lettres, chiffres et _, commence par une lettre." }
if (@('admin', 'deploiements', 'static', 'health', 'me', 'preview', 'auth', 'api') -contains $Slug.ToLower()) { throw "Slug reserve par le portail." }
if (-not $Icone) { $Icone = $Slug.Substring(0, [Math]::Min(2, $Slug.Length)).ToUpper() }
if (-not $Description) { $Description = "Application $Nom du Portail Adagio." }
$Racine = Split-Path $PSScriptRoot -Parent
$ancien = Join-Path $Racine 'serveur\MONAPP'
if (-not (Test-Path $ancien)) { throw "Modele deja initialise (serveur\MONAPP absent)." }

# Liste de paires (et non une table : les cles d'une table PowerShell ignorent la
# casse, or MONAPP et monapp sont deux remplacements distincts).
$remplacements = @(
    , @('Courte description affichée sur la carte du portail.', $Description)
    , @('"Outils Adagio"', ('"' + $Categorie + '"'))
    , @('"MA"', ('"' + $Icone + '"'))
    , @('Mon application', $Nom)
    , @('MONAPP', $Slug)
    , @('monapp', $Slug.ToLower())
)
$utf8 = New-Object System.Text.UTF8Encoding($false)
$fichiers = Get-ChildItem $Racine -Recurse -File -Include *.py, *.js, *.jsx, *.json, *.html, *.md, *.ps1, *.yml, *.css |
    Where-Object { $_.FullName -notmatch '\\node_modules\\|\\\.git\\' -and $_.Name -ne 'initialiser.ps1' }
foreach ($f in $fichiers) {
    $texte = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
    $nouveau = $texte
    foreach ($paire in $remplacements) { $nouveau = $nouveau.Replace($paire[0], $paire[1]) }
    if ($nouveau -ne $texte) {
        $bom = $f.Extension -eq '.ps1'
        [System.IO.File]::WriteAllText($f.FullName, $nouveau, (New-Object System.Text.UTF8Encoding($bom)))
        Write-Host "  modifie : $($f.FullName.Substring($Racine.Length + 1))"
    }
}
Rename-Item $ancien $Slug
Write-Host "OK : application $Slug ($Nom) initialisee. Etapes suivantes dans README.md." -ForegroundColor Green
