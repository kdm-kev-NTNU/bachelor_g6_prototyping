# Migrasjon fra Python til Go Backend

## Eksisterende mapper og deres status

### 📁 `chroma_db/` - Eksisterende Vector Database

**Status**: ✅ **Beholdes og brukes**

Den eksisterende ChromaDB-databasen i `chroma_db/` mappen vil **ikke** bli overskrevet eller endret av den nye Go-backenden.

**Hvordan det fungerer:**
- Den nye Go-backenden bruker ChromaDB via **HTTP client** (ikke direkte filtilgang)
- ChromaDB-serveren må kjøre på `localhost:8000` og peke til den eksisterende `chroma_db/` mappen
- Hvis ChromaDB-serveren allerede kjører og bruker denne mappen, vil all eksisterende data være tilgjengelig
- Den nye backend vil bruke collection `energy_advice_docs` - hvis denne allerede eksisterer, vil den brukes; hvis ikke, opprettes den

**Konfigurasjon:**
```bash
# Start ChromaDB-serveren med eksisterende database
# ChromaDB må være konfigurert til å bruke ../chroma_db som data-mappe
```

**Viktig**: Hvis du har eksisterende data i ChromaDB, vil den nye backend kunne lese fra den umiddelbart. Du trenger ikke å re-prosessere PDF-filene med mindre du vil oppdatere dem.

---

### 📁 `pdf/` - PDF Dokumenter

**Status**: ✅ **Beholdes og brukes**

PDF-mappen brukes fortsatt av den nye Go-backenden.

**Hvordan det fungerer:**
- `pdf_processor.go` leser fra `../pdf/` mappen (relativt til `backend/` mappen)
- PDF-filene prosesseres når du kaller `/api/v1/initialize-db` endpoint
- Eksisterende PDF-filer vil bli prosessert på nytt hvis du kaller initialize-db

**Anbefaling:**
- Hvis du allerede har prosessert PDF-filene og lagret dem i ChromaDB, trenger du ikke å kalle `initialize-db` på nytt
- Hvis du legger til nye PDF-filer, kan du kalle `initialize-db` for å prosessere dem

---

### 📁 `ui/` - Frontend UI

**Status**: ✅ **Beholdes og brukes**

UI-mappen brukes fortsatt av den nye Go-backenden.

**Hvordan det fungerer:**
- `routes.go` serverer statiske filer fra `../ui/` mappen
- `index.html` er tilgjengelig på `http://localhost:8000/`
- UI-en er allerede oppdatert til å bruke `/api/v1/` endpoints

**Ingen endringer nødvendig** - UI-en fungerer umiddelbart med den nye backend.

---

### 📁 `eino-server/` - Gamle Eino Proxy Server

**Status**: ⚠️ **Ikke lenger nødvendig, men kan beholdes**

Den gamle `eino-server/` mappen inneholder en proxy-server som forwarder til OpenAI.

**Hvordan det fungerer nå:**
- Den nye Go-backenden bruker **Eino Go SDK direkte** (`github.com/cloudwego/eino`)
- Den gamle proxy-serveren er ikke lenger nødvendig
- Du kan **slette** denne mappen hvis du vil, eller beholde den som backup

**Forskjell:**
- **Gammel**: Python backend → eino-server proxy → OpenAI
- **Ny**: Go backend → Eino Go SDK → OpenAI (direkte)

---

### 📁 `__pycache__/` - Python Cache

**Status**: 🗑️ **Kan slettes**

Dette er Python cache-filer fra den gamle Python-backenden. Kan trygt slettes.

---

## Oppsummering

| Mappe | Status | Handling |
|-------|--------|----------|
| `chroma_db/` | ✅ Beholdes | Brukes av ny backend via ChromaDB-server |
| `pdf/` | ✅ Beholdes | Brukes av ny backend for PDF-processing |
| `ui/` | ✅ Beholdes | Brukes av ny backend, allerede oppdatert |
| `eino-server/` | ⚠️ Valgfritt | Ikke lenger nødvendig, kan slettes |
| `__pycache__/` | 🗑️ Kan slettes | Python cache, ikke nødvendig |
| `backend/` | ✨ Ny | Den nye Go-backenden |

## Migrasjonssteg

1. **Behold alle mapper** som er markert med ✅
2. **Start ChromaDB-serveren** hvis den ikke allerede kjører (må peke til `chroma_db/`)
3. **Test den nye backend** - den vil automatisk bruke eksisterende ChromaDB-data hvis serveren kjører
4. **Valgfritt**: Slett `eino-server/` og `__pycache__/` hvis du vil rydde opp

## ChromaDB Server Konfigurasjon

Hvis du trenger å starte ChromaDB-serveren med eksisterende database:

```bash
# ChromaDB må være konfigurert til å bruke chroma_db/ mappen som persist_path
# Se ChromaDB dokumentasjon for hvordan du starter serveren med custom path
```

eller bruk ChromaDB via Docker:
```bash
docker run -p 8000:8000 -v "$(pwd)/chroma_db:/chroma/chroma" chromadb/chroma
```
