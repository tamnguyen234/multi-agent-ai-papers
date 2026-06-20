# PowerShell environment setup script for AI Paper Multi-Agent System

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Starting environment setup for AI Paper Multi-Agent System..." -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. Copy .env files
Write-Host "`n[1/3] Copying environment configurations..." -ForegroundColor Yellow

$envFiles = @(
    @{ Source = ".env.example"; Dest = ".env" },
    @{ Source = "backend/.env.example"; Dest = "backend/.env" },
    @{ Source = "agents/summarizer_agent/.env.example"; Dest = "agents/summarizer_agent/.env" },
    @{ Source = "agents/trend_agent/.env.example"; Dest = "agents/trend_agent/.env" },
    @{ Source = "agents/qa_agent/.env.example"; Dest = "agents/qa_agent/.env" },
    @{ Source = "agents/tts_agent/.env.example"; Dest = "agents/tts_agent/.env" },
    @{ Source = "frontend/.env.example"; Dest = "frontend/.env" }
)

foreach ($file in $envFiles) {
    if (-not (Test-Path $file.Dest)) {
        Write-Host "Creating $($file.Dest) from $($file.Source)..."
        Copy-Item $file.Source $file.Dest
    } else {
        Write-Host "$($file.Dest) already exists. Skipping."
    }
}

# 2. Setup Backend venv
Write-Host "`n[2/3] Setting up Backend virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "backend/.venv")) {
    Write-Host "Creating virtual environment in backend/.venv..."
    python -m venv backend/.venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment for Backend."
        exit 1
    }
} else {
    Write-Host "backend/.venv already exists. Skipping creation."
}

Write-Host "Upgrading pip and installing Backend dependencies..."
& backend/.venv/Scripts/python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to upgrade pip for Backend."; exit 1 }

& backend/.venv/Scripts/pip.exe install -r backend/requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to install Backend dependencies."; exit 1 }

# 3. Setup Agent venvs
Write-Host "`n[3/3] Setting up virtual environments for AI Agents (Health-check mode)..." -ForegroundColor Yellow

$agents = @("summarizer_agent", "trend_agent", "qa_agent", "tts_agent")
foreach ($agent in $agents) {
    Write-Host "`nConfiguring agents/$agent..." -ForegroundColor Cyan
    $venvPath = "agents/$agent/.venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment in $venvPath..."
        python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment for agents/$agent."
            exit 1
        }
    } else {
        Write-Host "$venvPath already exists. Skipping creation."
    }

    Write-Host "Upgrading pip for agents/$agent..."
    & $venvPath/Scripts/python.exe -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to upgrade pip for agents/$agent."; exit 1 }

    Write-Host "Installing health dependencies for agents/$agent..."
    & $venvPath/Scripts/pip.exe install -r agents/$agent/requirements-health.txt
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to install dependencies for agents/$agent."; exit 1 }
}

Write-Host "`n=======================================================" -ForegroundColor Green
Write-Host "SUCCESS: Environment setup completed successfully!" -ForegroundColor Green
Write-Host "To start the services, run: scripts\run_all.bat" -ForegroundColor Green
Write-Host "To verify their health check: scripts\check_health.bat" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
