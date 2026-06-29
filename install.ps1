# Ultimate Compression Installer for Windows (PowerShell)

$InstallDir = "$env:USERPROFILE\.ultimate-compression"
Write-Host "Installing Ultimate Compression to: $InstallDir" -ForegroundColor Cyan

# 1. Check Python
$PythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonInstalled) {
    Write-Error "Error: Python is required but not installed. Please install Python from python.org or MS Store."
    exit 1
}

# 2. Create Directory
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
}

# Download codebase if files aren't present (e.g., remote PowerShell installation)
if (-not (Test-Path "$InstallDir\uc")) {
    Write-Host "Downloading codebase from GitHub (LucasGazula/ultimate-compression)..." -ForegroundColor Yellow
    $ZipPath = "$InstallDir\archive.zip"
    Invoke-WebRequest -Uri "https://github.com/LucasGazula/ultimate-compression/zipball/main" -OutFile $ZipPath
    
    Write-Host "Extracting archive..." -ForegroundColor Yellow
    $TempExtractDir = "$InstallDir\temp_extract"
    Expand-Archive -Path $ZipPath -DestinationPath $TempExtractDir -Force
    
    # GitHub zipball has a top-level folder like 'LucasGazula-ultimate-compression-hash'
    $SubFolder = Get-ChildItem -Path $TempExtractDir -Directory | Select-Object -First 1
    if ($SubFolder) {
        Get-ChildItem -Path $SubFolder.FullName | Move-Item -Destination $InstallDir -Force
    }
    
    Remove-Item $ZipPath -Force
    Remove-Item $TempExtractDir -Recurse -Force
}

# 3. Setup Virtual Environment
Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow
Start-Process python -ArgumentList "-m venv $InstallDir\.venv" -Wait
Start-Process "$InstallDir\.venv\Scripts\pip.exe" -ArgumentList "install --upgrade pip" -Wait
Start-Process "$InstallDir\.venv\Scripts\pip.exe" -ArgumentList "install fastapi uvicorn requests" -Wait

# 4. Add to User Path Environment Variable
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$InstallDir;$UserPath", "User")
    Write-Host "Added $InstallDir to User PATH environment variable." -ForegroundColor Green
}

# 5. Create wrapper batch file in the installation directory to run Python CLI
$WrapperContent = @"
@echo off
python "%InstallDir%\uc" %*
"@
Set-Content -Path "$InstallDir\uc.cmd" -Value $WrapperContent

Write-Host "--------------------------------------------------------" -ForegroundColor Green
Write-Host "✅ Ultimate Compression successfully installed!" -ForegroundColor Green
Write-Host "--------------------------------------------------------" -ForegroundColor Green
Write-Host "Please restart your PowerShell terminal to apply PATH changes."
Write-Host "To start the local server, run:"
Write-Host "  uc start"
Write-Host ""
Write-Host "To configure your session for token compression, run:"
Write-Host "  uc env | iex"
Write-Host "--------------------------------------------------------" -ForegroundColor Green
