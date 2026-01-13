# Setup Guide - Go Backend med Eino

## Forutsetninger

1. **Go 1.21+** installert
2. **Python 3.8+** med `pdfplumber` installert
3. **ChromaDB** kjørende (valgfritt, men anbefalt)
4. **OpenAI API key**

## Steg-for-steg oppsett

### 1. Installer Python avhengigheter
```bash
pip install pdfplumber
```

### 2. Installer Go avhengigheter
```bash
cd backend
go mod download
```

### 3. Konfigurer miljøvariabler

Opprett `.env` fil i `backend/` mappen:
```
OPENAI_API_KEY=sk-your-openai-api-key
CHROMA_PATH=../chroma_db
PORT=8000
```

Eller sett i PowerShell:
```powershell
$env:OPENAI_API_KEY = "sk-your-openai-api-key"
$env:PORT = "8000"
```

### 4. Start ChromaDB (valgfritt)

Hvis du vil bruke vector database:
```bash
# Installer ChromaDB (se ChromaDB dokumentasjon)
# Start ChromaDB server på localhost:8000
```

Hvis ChromaDB ikke er tilgjengelig, vil systemet fortsatt fungere, men uten dokumentretrieval.

### 5. Initialiser vector database (valgfritt)

Kjør serveren og kall:
```bash
POST http://localhost:8000/api/v1/initialize-db
```

Dette vil prosessere PDF-filene i `../pdf/` mappen og lagre dem i ChromaDB.

### 6. Start serveren

```bash
cd backend
go run main.go
```

Serveren starter på `http://localhost:8000`

### 7. Test systemet

Åpne `http://localhost:8000` i nettleseren for å bruke UI, eller test API direkte:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# List buildings
curl http://localhost:8000/api/v1/buildings

# Generate advice
curl -X POST http://localhost:8000/api/v1/advice \
  -H "Content-Type: application/json" \
  -d '{"building_id": "building_1"}'
```

## Eino Framework Bruk

Systemet bruker Eino framework for alle LLM-operasjoner:

- **ChatModel**: `github.com/cloudwego/eino-ext/components/model/openai`
  - Brukes i `advisor.go` og `judge.go`
  - Konfigurert med OpenAI API key

- **EmbeddingModel**: `github.com/cloudwego/eino-ext/components/model/openai`
  - Brukes i `vector_db.go` for å generere embeddings
  - Bruker `text-embedding-3-small` modell

## PDF Processing

PDF-behandling bruker Python `pdfplumber` biblioteket, kalt fra Go via `exec.Command`. Dette gir mer stabil PDF-tekstekstraksjon enn native Go-biblioteker.

## Feilsøking

### ChromaDB ikke tilgjengelig
- Systemet vil fortsette å fungere, men returnere tomme resultater for retrieval
- Sjekk at ChromaDB kjører på `localhost:8000`

### PDF processing feiler
- Sjekk at Python er installert og `pdfplumber` er installert
- Test manuelt: `python -c "import pdfplumber; print('OK')"`

### OpenAI API feil
- Sjekk at `OPENAI_API_KEY` er satt korrekt
- Verifiser at API key har tilgang til `gpt-4o` og `text-embedding-3-small`

## Neste steg

1. Test systemet med forskjellige bygninger
2. Evaluer rådkvalitet med judge-systemet
3. Juster prompts i `config.go` basert på resultater
4. Optimaliser chunking-strategi i `pdf_processor.go`
