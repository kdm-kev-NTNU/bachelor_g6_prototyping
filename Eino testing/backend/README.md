# Energy Advice Backend - Go + Eino

Komplett Go-basert backend for LLM-as-Judge testing system med Eino framework.

## ⚠️ Viktig: Eksisterende mapper

Den nye Go-backenden **beholder og bruker** alle eksisterende mapper:
- ✅ `chroma_db/` - Eksisterende vector database brukes (via ChromaDB-server)
- ✅ `pdf/` - PDF-filer brukes for dokumentprocessing
- ✅ `ui/` - Frontend UI brukes (allerede oppdatert)

Se `MIGRATION.md` for detaljer om migrasjon fra Python til Go backend.

## Arkitektur

```
PDF Documents → Python pdfplumber → Text Chunks → Chroma Vector DB
                                                          ↓
Building Data → Hybrid Retrieval → RAG Advisor (Eino) → Advice
                                                          ↓
Fixed Rubric → LLM-as-Judge (Eino) → Evaluation Scores
```

## Komponenter

- **PDF Processing**: Python pdfplumber (kalt fra Go) for PDF parsing
- **Vector Database**: ChromaDB integrasjon via Go client (bruker eksisterende `chroma_db/` mappe)
- **Retrieval**: Hybrid retrieval (semantic + keyword)
- **RAG Advisor**: Eino ChatModel for rådgenerering
- **LLM-as-Judge**: Eino ChatModel for evaluering
- **REST API**: Gin framework for HTTP endpoints

## Installasjon

### 1. Installer Go dependencies
```bash
cd backend
go mod download
```

### 2. Installer Python pdfplumber (for PDF processing)
```bash
pip install pdfplumber
```

### 3. Start ChromaDB (hvis ikke allerede kjørende)
```bash
# ChromaDB må kjøre på localhost:8000
# Viktig: ChromaDB må være konfigurert til å bruke den eksisterende chroma_db/ mappen
# Se ChromaDB dokumentasjon for installasjon

# Eksempel med Docker:
docker run -p 8000:8000 -v "$(pwd)/chroma_db:/chroma/chroma" chromadb/chroma
```

## Konfigurasjon

Opprett `.env` fil:
```
OPENAI_API_KEY=sk-your-openai-key
CHROMA_PATH=../chroma_db
PORT=8000
```

## Kjøring

```bash
# Sett OpenAI API key
$env:OPENAI_API_KEY = "sk-your-openai-key"

# Kjør serveren
go run main.go
```

Server starter på `http://localhost:8000`

## API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/buildings` - List all buildings
- `GET /api/v1/buildings/:id` - Get specific building
- `POST /api/v1/advice` - Generate advice for building
- `POST /api/v1/judge` - Evaluate advice quality
- `POST /api/v1/evaluate` - Full pipeline (advice + judge)
- `POST /api/v1/initialize-db` - Process PDFs and store in vector DB

## Eino Framework

Alle LLM-kall bruker Eino framework:
- **ChatModel**: Eino ChatModel med OpenAI provider
- **EmbeddingModel**: Eino EmbeddingModel med OpenAI provider
- **Document Processing**: Eino document loaders (via Python for PDF)

## Testing

Åpne `http://localhost:8000` i nettleseren for å bruke UI, eller bruk API direkte.

## Eksisterende Data

Hvis du allerede har prosessert PDF-filer og lagret dem i ChromaDB:
- ✅ Eksisterende data i `chroma_db/` vil automatisk være tilgjengelig
- ✅ Du trenger ikke å kalle `/api/v1/initialize-db` på nytt
- ✅ Bare start ChromaDB-serveren og den nye backend vil bruke eksisterende data

Hvis du vil prosessere PDF-filer på nytt eller legge til nye:
- Kall `POST /api/v1/initialize-db` for å prosessere alle PDF-filer i `pdf/` mappen
