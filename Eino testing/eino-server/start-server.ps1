# PowerShell script for å starte Eino server

# Sjekk om OpenAI API key er satt
if (-not $env:OPENAI_API_KEY) {
    Write-Host "FEIL: OPENAI_API_KEY må være satt!" -ForegroundColor Red
    Write-Host "Sett den med: `$env:OPENAI_API_KEY = 'sk-your-key'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starter Eino server..." -ForegroundColor Green
Write-Host "OpenAI API key: $($env:OPENAI_API_KEY.Substring(0, [Math]::Min(10, $env:OPENAI_API_KEY.Length)))..." -ForegroundColor Gray

# Legg Go til PATH hvis ikke allerede der
if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    $env:PATH += ";C:\Program Files\Go\bin"
}

# Kjør serveren
go run server.go
