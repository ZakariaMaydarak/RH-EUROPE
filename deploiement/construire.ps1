# ============================================================================
# Construit le ZIP de deploiement de l'application (Portail Apps Adagio).
#
#   1. verifie que le depot est sur main, propre et a jour avec origin/main
#      (on ne deploie que ce qui est fusionne dans main ; -Force pour passer outre)
#   2. build du front (front\ -> dist\, base Vite = /<SLUG>/)
#   3. assemble serveur\<SLUG>\ + front\dist\ (-> static_files\) + deploiement.json
#   4. ecrit deploiement\sortie\<SLUG>.zip
#
# Ensuite : portail -> Deploiements -> carte de l'app -> Nouveau ZIP -> Deployer.
# ============================================================================
param([switch]$Force)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$Racine = Split-Path $PSScriptRoot -Parent
$dossierServeur = Get-ChildItem (Join-Path $Racine 'serveur') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'routes.py') } | Select-Object -First 1
if (-not $dossierServeur) { throw "serveur\<SLUG>\routes.py introuvable" }
$Slug = $dossierServeur.Name
Write-Host "=== ZIP de deploiement de $Slug ===" -ForegroundColor Cyan

function Invoke-Natif([scriptblock]$Bloc) {
    # Commandes git / node : sorties a l'ecran, stderr non bloquant, code retour verifie.
    $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { & $Bloc 2>&1 | ForEach-Object { "$_" } | Out-Host } finally { $ErrorActionPreference = $eap }
    return $LASTEXITCODE
}

# --- 1. Etat du depot --------------------------------------------------------
Invoke-Natif { git -C $Racine fetch origin --quiet } | Out-Null
$branche = (git -C $Racine rev-parse --abbrev-ref HEAD)
$problemes = @()
if ($branche -ne 'main') { $problemes += "branche courante = $branche (attendu : main)" }
if (git -C $Racine status --porcelain --untracked-files=no) { $problemes += "modifications non commitees" }
$eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
$distant = (git -C $Racine rev-parse --verify --quiet origin/main 2>$null)   # absent = depot sans origin
$ErrorActionPreference = $eap
if ($distant -and (git -C $Racine rev-parse HEAD) -ne $distant) { $problemes += "main local different de origin/main" }
if ($problemes.Count) {
    $msg = $problemes -join ' ; '
    if ($Force) { Write-Warning "$msg -> poursuite forcee (-Force)" }
    else { throw "$msg. On ne deploie que ce qui est fusionne dans main (ou relancer avec -Force)." }
}

# --- 2. Build du front --------------------------------------------------------
$front = Join-Path $Racine 'front'
$config = Get-ChildItem $front -Filter 'vite.config.*' -File | Select-Object -First 1
if ((Get-Content $config.FullName -Raw) -notmatch "base:\s*['""]/$Slug/['""]") {
    throw "$($config.Name) doit contenir base: '/$Slug/'"
}
Push-Location $front
try {
    if (-not (Test-Path 'node_modules')) {
        if ((Invoke-Natif { npm install }) -ne 0) { throw "npm install a echoue" }
    }
    # node direct (et non npm run build) : les chemins OneDrive contiennent ' & '.
    if ((Invoke-Natif { node 'node_modules\vite\bin\vite.js' build }) -ne 0) { throw "vite build a echoue" }
} finally { Pop-Location }

# --- 3. Assemblage ---------------------------------------------------------------
$travail = Join-Path ([System.IO.Path]::GetTempPath()) ("paquet-$Slug-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
$exclus = @('__pycache__', 'static_files', '_vendor', 'tests', '.pytest_cache')
function Copy-Arbre([string]$Source, [string]$Cible, [string[]]$Exclure) {
    New-Item -ItemType Directory -Force -Path $Cible | Out-Null
    Get-ChildItem -Path $Source -Force | Where-Object { $Exclure -notcontains $_.Name } | ForEach-Object {
        if ($_.PSIsContainer) { Copy-Arbre $_.FullName (Join-Path $Cible $_.Name) @('__pycache__') }
        else { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Cible $_.Name) -Force }
    }
}
try {
    Copy-Arbre $dossierServeur.FullName $travail $exclus
    Copy-Arbre (Join-Path $front 'dist') (Join-Path $travail 'static_files') @()
    $version = $null
    $m = Select-String -Path (Join-Path $dossierServeur.FullName 'routes.py') -Pattern '"version"\s*:\s*"([^"]+)"' | Select-Object -First 1
    if ($m) { $version = $m.Matches[0].Groups[1].Value }
    $manifeste = [ordered]@{
        slug = $Slug; version = $version
        commit = (git -C $Racine rev-parse --short HEAD); branche = $branche
        construit_le = (Get-Date).ToString('s'); construit_par = (git config user.email)
    }
    [System.IO.File]::WriteAllText((Join-Path $travail 'deploiement.json'), ($manifeste | ConvertTo-Json), (New-Object System.Text.UTF8Encoding($false)))

    # --- 4. ZIP (chemins en '/') ----------------------------------------------
    $sortie = Join-Path $PSScriptRoot 'sortie'
    New-Item -ItemType Directory -Force -Path $sortie | Out-Null
    $zip = Join-Path $sortie "$Slug.zip"
    if (Test-Path $zip) { Remove-Item -LiteralPath $zip -Force }
    $racineTravail = (Resolve-Path $travail).Path.TrimEnd('\') + '\'
    $flux = [System.IO.File]::Open($zip, [System.IO.FileMode]::CreateNew)
    try {
        $archive = New-Object System.IO.Compression.ZipArchive($flux, [System.IO.Compression.ZipArchiveMode]::Create)
        try {
            Get-ChildItem $travail -Recurse -File -Force | ForEach-Object {
                $nom = $_.FullName.Substring($racineTravail.Length).Replace('\', '/')
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $_.FullName, $nom) | Out-Null
            }
        } finally { $archive.Dispose() }
    } finally { $flux.Dispose() }
} finally {
    Remove-Item -Recurse -Force -LiteralPath $travail -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "TERMINE : $zip ($([math]::Round((Get-Item $zip).Length / 1KB, 1)) Ko)" -ForegroundColor Green
Write-Host "Mise en production : https://app-portail-apps-prod-bfahfjhzdcdgevg5.francecentral-01.azurewebsites.net/deploiements/" -ForegroundColor Yellow
Write-Host "  carte '$Slug' -> Nouveau ZIP -> Deployer -> attendre 'Termine' -> tester /$Slug/" -ForegroundColor Yellow

exit 0
