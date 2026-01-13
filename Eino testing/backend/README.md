# Energy Advice Backend - Go + Eino

Komplett Go-basert backend for LLM-as-Judge testing system med Eino framework.

## 🚀 Quick Start

```bash
cd "Eino testing/backend"

# Installer avhengigheter
go mod download
go mod tidy
pip install pdfplumber chromadb

# Sett miljøvariabler
$env:OPENAI_API_KEY = "sk-your-openai-api-key"

# Start serveren
go run .
# eller
go run *.go
```

Serveren starter på `http://localhost:8000`

## 📁 Prosjektstruktur

```
backend/
├── main.go              # Server entry point
├── routes.go            # API route definitions
├── handlers.go          # HTTP handlers
├── models.go            # Data structures
├── config.go            # Configuration and prompts
├── building_data.go     # Test data generation
├── pdf_processor.go     # PDF text extraction (via Python)
├── vector_db.go         # ChromaDB integration (embedded mode)
├── vector_db.py         # Python wrapper for ChromaDB
├── advisor.go           # RAG advisor med Eino ChatModel
├── judge.go             # LLM-as-judge med Eino ChatModel
├── go.mod               # Go dependencies
├── requirements.txt     # Python dependencies
└── README.md            # Denne filen
```

## 🏗️ Arkitektur

```
PDF Documents → Python pdfplumber → Text Chunks → ChromaDB (embedded)
                                                          ↓
Building Data → Hybrid Retrieval → RAG Advisor (Eino) → Advice
                                                          ↓
Fixed Rubric → LLM-as-Judge (Eino) → Evaluation Scores
```

## ⚙️ Installasjon

### 1. Go Dependencies
```bash
go mod download
go mod tidy
```

### 2. Python Dependencies
```bash
pip install pdfplumber chromadb
```

### 3. Miljøvariabler

Opprett `.env` fil eller sett i PowerShell:
```powershell
$env:OPENAI_API_KEY = "sk-your-openai-api-key"
$env:PORT = "8000"  # Valgfritt, default er 8000
```

## 🔧 Konfigurasjon

### ChromaDB (Embedded Mode)

**Ingen server nødvendig!** Backend bruker ChromaDB i embedded mode via Python:
- Bruker eksisterende `chroma_db/` mappe direkte
- Ingen ekstra prosesser eller Docker
- Eksisterende data er umiddelbart tilgjengelig

### Eksisterende Mapper

Backend bruker eksisterende mapper fra prosjektet:
- ✅ `chroma_db/` - Vector database (brukes direkte)
- ✅ `pdf/` - PDF-filer for dokumentprocessing
- ✅ `ui/` - Frontend UI (allerede oppdatert)

## 📡 API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/buildings` - List all buildings
- `GET /api/v1/buildings/:id` - Get specific building
- `POST /api/v1/advice` - Generate advice for building
- `POST /api/v1/judge` - Evaluate advice quality
- `POST /api/v1/evaluate` - Full pipeline (advice + judge)
- `POST /api/v1/initialize-db` - Process PDFs and store in vector DB

## 🧪 Testing

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

## 🔍 Eino Framework

Alle LLM-kall bruker Eino framework:
- **ChatModel**: `github.com/cloudwego/eino-ext/components/model/openai`
  - Brukes i `advisor.go` og `judge.go`
  - Konfigurert med OpenAI API key
- **EmbeddingModel**: `github.com/cloudwego/eino-ext/components/model/openai`
  - Brukes i `vector_db.go` for embeddings
  - Bruker `text-embedding-3-small` modell

## 🐛 Feilsøking

### "missing go.sum entry"
```bash
go mod tidy
```

### "ChromaDB not available"
- Sjekk at `chromadb` er installert: `pip install chromadb`
- Verifiser at Python er tilgjengelig: `python --version`
- Sjekk at `vector_db.py` finnes i `backend/` mappen
- Verifiser at `chroma_db/` mappen eksisterer og er lesbar

### "python script failed"
- Test Python: `python --version`
- Test ChromaDB: `python -c "import chromadb; print('OK')"`
- Hvis `python` ikke fungerer, prøv `python3`
- Eller endre `exec.Command("python", ...)` til `exec.Command("python3", ...)` i `vector_db.go`

### PDF processing feiler
- Sjekk at Python er installert og `pdfplumber` er installert
- Test manuelt: `python -c "import pdfplumber; print('OK')"`

### OpenAI API feil
- Sjekk at `OPENAI_API_KEY` er satt korrekt
- Verifiser at API key har tilgang til `gpt-4o` og `text-embedding-3-small`

## 📝 Eksisterende Data

Hvis du allerede har prosessert PDF-filer og lagret dem i ChromaDB:
- ✅ Eksisterende data i `chroma_db/` vil automatisk være tilgjengelig
- ✅ Du trenger ikke å kalle `/api/v1/initialize-db` på nytt
- ✅ Ingen server trenger å kjøre - backend bruker databasen direkte

Hvis du vil prosessere PDF-filer på nytt eller legge til nye:
- Kall `POST /api/v1/initialize-db` for å prosessere alle PDF-filer i `pdf/` mappen

## 🎯 Neste Steg

1. Test systemet med forskjellige bygninger
2. Evaluer rådkvalitet med judge-systemet
3. Juster prompts i `config.go` basert på resultater
4. Optimaliser chunking-strategi i `pdf_processor.go`
