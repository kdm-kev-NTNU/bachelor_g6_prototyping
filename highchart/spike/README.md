# Highcharts-LLM Analyzer Spike

Prototype for å teste om GPT-4o kan analysere chart-state og returnere gyldige Highcharts-modifikasjoner.

## Hurtigstart

### 1. Sett opp miljøvariabler

Opprett en `.env` fil i `highchart/spike/` mappen:

**Windows (PowerShell):**
```powershell
echo "OPENAI_API_KEY=sk-din-api-nokkel-her" > .env
```

**Eller manuelt:** Lag en fil kalt `.env` med innhold:
```
OPENAI_API_KEY=sk-din-api-nokkel-her
```

### 2. Installer avhengigheter

```bash
cd highchart/spike
pip install -r requirements.txt
```

### 3. Start backend-server

```bash
python server.py
```

Serveren starter på `http://localhost:8000`

### 4. Åpne frontend

Åpne `index.html` i en nettleser. Du kan bruke Live Server i VS Code eller:

```bash
# Alternativ: start enkel HTTP-server
python -m http.server 5500
# Åpne http://localhost:5500/index.html
```

### 5. Test

1. Vent til chartet er lastet med Tesla-data
2. Klikk **"Analyser med AI"**
3. Se AI-genererte annotasjoner og analyse

## API Endepunkter

| Endepunkt | Metode | Beskrivelse |
|-----------|--------|-------------|
| `/` | GET | Helse-sjekk, viser om OpenAI er tilgjengelig |
| `/analyze` | POST | Analyserer chart-data, returnerer annotasjoner |
| `/test` | POST | Returnerer mock-data for testing uten LLM |
| `/docs` | GET | Swagger API-dokumentasjon |

## Filstruktur

```
highchart/spike/
├── index.html        # Frontend med Highcharts og Morningstar-data
├── server.py         # FastAPI backend med GPT-4o integrasjon
├── schema.py         # Pydantic models for validering
├── requirements.txt  # Python-avhengigheter
└── README.md         # Denne filen
```

## Evalueringskriterier

| Kriterie | Suksess | Feil |
|----------|---------|------|
| Schema-overholdelse | LLM returnerer gyldig JSON 90%+ | Konsekvent ugyldig format |
| Highcharts-validitet | Annotasjoner rendrer korrekt | JS-feil ved addAnnotation() |
| Meningsfullhet | Identifiserer reelle mønstre | Tilfeldige/irrelevante merknader |
| Separasjon | Analyse i summary, visuelt i annotations | Blander tekst og kode |

## Feilsøking

**Backend starter ikke:**
- Sjekk at du er i riktig mappe (`highchart/spike`)
- Sjekk at alle avhengigheter er installert

**"Mangler API-nøkkel" i frontend:**
- Opprett `.env` fil med `OPENAI_API_KEY`
- Restart backend-serveren

**CORS-feil:**
- Sørg for at backend kjører på port 8000
- Sjekk at frontend bruker riktig API_URL

**Morningstar-data laster ikke:**
- Demo-API kan være nede
- Systemet faller tilbake til mock-data automatisk
