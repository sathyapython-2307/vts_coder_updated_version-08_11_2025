<#
PowerShell helper to create or recreate the project's virtual environment
and install Python dependencies from requirements.txt.

Usage (from project root):
  # Recreate venv and install
  .\scripts\setup_venv.ps1 -Recreate

  # Create venv only if missing and install
  .\scripts\setup_venv.ps1

This script uses the system `python` command to create the venv. If you
have multiple Python installs, run the script with the python you want in
PATH (for example: C:\Python311\python.exe .\scripts\setup_venv.ps1 -Recreate)
#>

param(
    [switch]$Recreate
)

Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Resolve-Path (Join-Path $scriptDir '..')
$venvPath = Join-Path $projectRoot 'venv'

Write-Host "Project root: $projectRoot"
Write-Host "Virtualenv path: $venvPath"

if (Test-Path $venvPath) {
    if ($Recreate) {
        Write-Host 'Removing existing virtualenv...'
        Remove-Item -LiteralPath $venvPath -Recurse -Force -ErrorAction Stop
    } else {
        Write-Host 'Virtualenv already exists. Will reuse it.'
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Host 'Creating virtual environment...'
    & python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Failed to create virtualenv. Ensure `python` on PATH is the desired interpreter.'
        exit 1
    }
}

$venvPython = Join-Path $venvPath 'Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    Write-Error "Expected Python executable not found in virtualenv: $venvPython"
    exit 1
}

Write-Host 'Upgrading pip, setuptools and wheel in the venv...'
& $venvPython -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Failed to upgrade pip in venv.'
    exit 1
}

$requirements = Join-Path $projectRoot 'requirements.txt'
if (Test-Path $requirements) {
    Write-Host 'Installing requirements from requirements.txt...'
    & $venvPython -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'pip install reported errors. Inspect the output above.'
        exit 1
    }
} else {
    Write-Warning 'requirements.txt not found in project root; skipping pip install.'
}

Write-Host "Setup complete. To activate the venv in PowerShell run:"
Write-Host "  .\\venv\\Scripts\\Activate.ps1"
Write-Host "Then run:"
Write-Host "  python manage.py migrate"
Write-Host "  python manage.py runserver"
