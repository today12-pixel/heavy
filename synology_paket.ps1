# Baut den Ordner dist\heavy-synology, der nach /volume1/docker/heavy auf die Synology kopiert wird.
#   powershell -ExecutionPolicy Bypass -File .\synology_paket.ps1               Erstinstallation: Programm + alle Profile
#   powershell -ExecutionPolicy Bypass -File .\synology_paket.ps1 -NurCode      Programm-Update, Daten auf dem NAS bleiben
#   powershell -ExecutionPolicy Bypass -File .\synology_paket.ps1 -Profil anna  nur die neue Person (landet in daten\anna)
param([switch]$NurCode, [string]$Profil)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $root "dist\heavy-synology"
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory -Force $out | Out-Null

function Copy-ProfileData([string]$src, [string]$token, [string]$dst) {
    New-Item -ItemType Directory -Force (Join-Path $dst "data"), (Join-Path $dst "report"), (Join-Path $dst ".garminconnect-heavy") | Out-Null
    Copy-Item (Join-Path $src "config.json") $dst
    foreach ($f in "data\heavy.db", "report\dashboard.html") {
        $p = Join-Path $src $f
        if (Test-Path $p) { Copy-Item $p (Join-Path $dst $f) }
    }
    if (Test-Path $token) { Copy-Item $token (Join-Path $dst ".garminconnect-heavy") }
    else { Write-Warning "Kein Garmin-Token fuer $src - vorher anmelden (login)." }
}

if (-not $Profil) {
    # Programm
    Copy-Item (Join-Path $root "heavy") (Join-Path $out "heavy") -Recurse
    Get-ChildItem $out -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Copy-Item (Join-Path $root "requirements.txt") $out
    foreach ($f in "Dockerfile", "docker-compose.yml", "ANLEITUNG.md") { Copy-Item (Join-Path $root "synology\$f") $out }
    # Name des Hauptprofils aus der lokalen config.json übernehmen (Standard: haupt)
    $cfgFile = Join-Path $root "config.json"
    if (Test-Path $cfgFile) {
        $hp = (Get-Content $cfgFile -Raw -Encoding utf8 | ConvertFrom-Json).hauptprofil
        if ($hp -and $hp -match '^[a-z0-9][a-z0-9_-]{0,30}$') {
            $c = Join-Path $out "docker-compose.yml"
            $txt = [IO.File]::ReadAllText($c) -replace 'HAUPTPROFIL=haupt\b', "HAUPTPROFIL=$hp"
            [IO.File]::WriteAllText($c, $txt, (New-Object Text.UTF8Encoding $false))
        }
    }
    $sh = [IO.File]::ReadAllText((Join-Path $root "synology\entrypoint.sh")) -replace "`r`n", "`n"
    [IO.File]::WriteAllText((Join-Path $out "entrypoint.sh"), $sh, (New-Object Text.UTF8Encoding $false))
}

if ($Profil) {
    $src = Join-Path $root "profile\$Profil"
    if (-not (Test-Path (Join-Path $src "config.json"))) { throw "Profil '$Profil' gibt es nicht (heavy.cmd profile)." }
    Copy-ProfileData $src (Join-Path $src ".garminconnect-heavy\garmin_tokens.json") (Join-Path $out "daten\$Profil")
} elseif (-not $NurCode) {
    $d = Join-Path $out "daten"
    Copy-ProfileData $root (Join-Path $env:USERPROFILE ".garminconnect-heavy\garmin_tokens.json") $d
    $pdir = Join-Path $root "profile"
    if (Test-Path $pdir) {
        Get-ChildItem $pdir -Directory | Where-Object { Test-Path (Join-Path $_.FullName "config.json") } | ForEach-Object {
            Copy-ProfileData $_.FullName (Join-Path $_.FullName ".garminconnect-heavy\garmin_tokens.json") (Join-Path $d $_.Name)
        }
    }
}

Write-Host "Fertig: $out"
if (-not $NurCode) { Write-Host "ACHTUNG: daten enthaelt Garmin-Zugaenge. Nach dem Kopieren dist\ loeschen." }
