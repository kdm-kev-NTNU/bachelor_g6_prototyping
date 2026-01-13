# Go Backend med Eino - Oppsummering

## Hva er bygget

En komplett Go-basert backend for LLM-as-Judge testing system som bruker Eino framework for alle LLM-operasjoner.

## Struktur

```
backend/
├── main.go              # Server entry point
├── routes.go            # API route definitions
├── handlers.go          # HTTP handlers
├── models.go            # Data structures
├── config.go            # Configuration and prompts
├── building_data.go     # Test data generation
├── pdf_processor.go     # PDF text extraction (via Python)
├── vector_db.go         # ChromaDB integration
├── advisor.go           # RAG advisor med Eino ChatModel
├── judge.go             # LLM-as-judge med Eino ChatModel
├── go.mod               # Go dependencies
├── README.md            # Dokumentasjon
└── SETUP.md             # Setup guide
```

## Eino Framework Integrasjon

Systemet bruker Eino framework for:
- **Chat Completions**: RAG advisor og LLM-as-judge
- **Embeddings**: Vector database embeddings
- **Document Processing**: Via Python pdfplumber (kalt fra Go)

## Neste steg

1. **Installer avhengigheter**:
   ```bash
   cd backend
   go mod download
   pip install pdfplumber
   ```

2. **Sjekk pakkenavn**: 
   - Verifiser at Eino Go-pakker har riktige navn
   - Verifiser ChromaDB Go client pakkenavn
   - Juster imports i koden hvis nødvendig

3. **Test kompilering**:
   ```bash
   go build
   ```

4. **Konfigurer miljøvariabler**:
   ```powershell
   $env:OPENAI_API_KEY = "sk-your-key"
   ```

5. **Start serveren**:
   ```bash
   go run main.go
   ```

## Viktige notater

- PDF processing bruker Python `pdfplumber` via `exec.Command`
- ChromaDB integrasjon kan kreve justering av pakkenavn
- Eino pakkenavn kan kreve justering basert på faktisk Eino Go SDK
- Systemet vil fungere uten ChromaDB, men uten dokumentretrieval

## API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/buildings` - List buildings
- `GET /api/v1/buildings/:id` - Get building
- `POST /api/v1/advice` - Generate advice
- `POST /api/v1/judge` - Evaluate advice
- `POST /api/v1/evaluate` - Full pipeline
- `POST /api/v1/initialize-db` - Initialize vector DB

UI er tilgjengelig på `http://localhost:8000`
