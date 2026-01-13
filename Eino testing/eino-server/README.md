# Eino LLM Proxy Server

HTTP proxy server som eksponerer OpenAI-kompatible API endpoints. Fungerer som en gateway mellom Python-koden og OpenAI API.

## Installasjon

1. Installer Go: https://go.dev/dl/
2. Kompiler serveren:
   ```bash
   go build -o eino-server.exe server.go
   ```

## Konfigurasjon

Sett OpenAI API key:
```powershell
$env:OPENAI_API_KEY = "sk-your-openai-api-key"
```

## Kjøring

### Metode 1: Bruk PowerShell script
```powershell
# Sett OpenAI API key først
$env:OPENAI_API_KEY = "sk-your-openai-api-key"

# Kjør scriptet
.\start-server.ps1
```

### Metode 2: Kjør direkte
```powershell
# Sett OpenAI API key
$env:OPENAI_API_KEY = "sk-your-openai-api-key"

# Legg Go til PATH hvis nødvendig
$env:PATH += ";C:\Program Files\Go\bin"

# Kjør serveren
go run server.go

# Eller bruk executable
.\eino-server.exe
```

Serveren starter på port 8080 (eller PORT miljøvariabel hvis satt).

## Endpoints

### POST /v1/chat/completions
OpenAI-kompatibel chat completion endpoint.

### POST /v1/embeddings
OpenAI-kompatibel embeddings endpoint.

## Bruk med Python-koden

I `Eino testing` mappen, sett:

```powershell
$env:EINO_API_KEY = "any-key"
$env:EINO_BASE_URL = "http://localhost:8080"
```

Deretter vil Python-koden automatisk bruke Eino serveren i stedet for OpenAI direkte.
