# Highcharts-LLM Analyzer v0.2

**Deterministisk Chart-Conditioned Reasoning**

Prototype for semantisk chart-analyse hvor LLM kun identifiserer mønstre, og all visualisering skjer deterministisk i kode.

## 🏗️ Arkitektur

```
┌─────────────┐    ┌────────────────────┐    ┌─────────────────┐    ┌───────────┐
│ Chart Data  │───▶│ LLM Analyse        │───▶│ Deterministisk  │───▶│ Highcharts│
│ (Frontend)  │    │ (Semantiske funn)  │    │ Mapping (Kode)  │    │ API       │
└─────────────┘    └────────────────────┘    └─────────────────┘    └───────────┘

LLM returnerer KUN:              Koden mapper:
- FindingType enum               - BULLISH_TREND → grønn plotBand
- confidence (0-1)               - UNUSUAL_PEAK → magenta annotation
- timeRange/pointDate            - HIGH_VOLATILITY → oransje band
- description                    - etc. (se visual_presets.py)
```

## 🎯 Kjerneprinsipper

| Prinsipp | Beskrivelse |
|----------|-------------|
| **Semantisk output** | LLM returnerer kun funn-typer, ikke Highcharts-kode |
| **Determinisme** | Samme funn → alltid samme visualisering |
| **Separasjon** | Analyse-logikk og UI-logikk er fullstendig adskilt |
| **Strenge enums** | Kun predefinerte FindingTypes aksepteres |

## 📁 Filstruktur

```
highchart/spike/
├── analysis_schema.py    # Semantiske funn-typer + JSON schema
├── visual_presets.py     # Deterministiske Highcharts-presets
├── apply_findings.py     # Mapper findings → Highcharts config
├── server.py             # FastAPI backend (v0.2)
├── index.html            # Frontend med ny respons-håndtering
├── schema.py             # ⚠️ DEPRECATED - kun for referanse
├── requirements.txt      # Python-avhengigheter
└── README.md             # Denne filen
```

## 🚀 Hurtigstart

### 1. Sett opp miljøvariabler

Opprett `.env` fil i `highchart/spike/`:

```bash
OPENAI_API_KEY=sk-din-api-nokkel-her
```

### 2. Installer avhengigheter

```bash
cd highchart/spike
pip install -r requirements.txt
```

### 3. Start backend

```bash
python server.py
```

Server starter på `http://localhost:8000`

### 4. Åpne frontend

Åpne `index.html` i nettleser eller bruk Live Server.

## 🔍 Finding Types (Semantiske Funn)

| Type | Beskrivelse | Visualisering |
|------|-------------|---------------|
| `BULLISH_TREND` | Oppadgående trend | Grønn plotBand |
| `BEARISH_TREND` | Nedadgående trend | Rød plotBand |
| `CONSOLIDATION` | Sidelengs bevegelse | Grå plotBand |
| `UNUSUAL_PEAK` | Signifikant topp | Magenta annotation |
| `UNUSUAL_DIP` | Signifikant bunn | Blå annotation |
| `BREAKOUT` | Prisbrudd | Lime annotation |
| `HIGH_VOLATILITY` | Høy volatilitet | Oransje plotBand |
| `LOW_VOLATILITY` | Lav volatilitet | Cyan plotBand |
| `SIGNIFICANT_EVENT` | Viktig hendelse | Oransje annotation |
| `SUPPORT_LEVEL` | Støttenivå | Grønn plotLine (Y) |
| `RESISTANCE_LEVEL` | Motstandsnivå | Rød plotLine (Y) |
| `DOUBLE_TOP` | Dobbel topp-mønster | Gull annotation |
| `DOUBLE_BOTTOM` | Dobbel bunn-mønster | Gull annotation |

## 🔌 API Endepunkter

| Endepunkt | Metode | Beskrivelse |
|-----------|--------|-------------|
| `/` | GET | Helse-sjekk + modus-info |
| `/analyze` | POST | Semantisk analyse → deterministisk output |
| `/test` | POST | Mock-data uten LLM-kall |
| `/schema` | GET | JSON-skjema for analyse |
| `/finding-types` | GET | Liste over alle funn-typer |
| `/docs` | GET | Swagger API-dokumentasjon |

## 📊 Respons-format

```json
{
  "findings": [
    {
      "type": "BULLISH_TREND",
      "confidence": 0.88,
      "timeRange": ["2024-11-01", "2024-12-31"],
      "description": "Sterk oppgang etter valget"
    }
  ],
  "summary": "Tekstlig analyse...",
  "overallTrend": "bullish",
  "riskAssessment": "medium",
  
  // Deterministisk generert fra findings:
  "plotBands": [...],
  "plotLinesY": [...],
  "annotations": [...],
  "confidence": 0.85,
  "findingsCount": 5
}
```

## 🎨 Tilpasse Visualiseringer

All visualisering styres fra `visual_presets.py`:

```python
# Endre farge for bullish trend
PLOT_BAND_PRESETS["BULLISH_TREND"]["color"] = "rgba(0, 200, 100, 0.15)"

# Endre annotation-stil for peaks
ANNOTATION_PRESETS["UNUSUAL_PEAK"]["background_color"] = "#ff00ff"
```

**Ingen endringer i LLM-prompts påvirker visualiseringen!**

## ⚡ Forskjell fra v0.1

| v0.1 (Gammel) | v0.2 (Ny) |
|---------------|-----------|
| LLM returnerer `annotations`, `plotBands` | LLM returnerer `FindingType` enums |
| LLM velger farger og offsets | Farger/styling er hardkodet i presets |
| Highcharts-referanser i prompt | Ingen Highcharts i prompt |
| Ustabil output-format | Strengt JSON schema |
| `schema.py` med Highcharts-typer | `analysis_schema.py` med semantiske typer |

## 🛠️ Feilsøking

**Backend starter ikke:**
- Sjekk at du er i riktig mappe (`highchart/spike`)
- Sjekk at alle avhengigheter er installert

**Import-feil:**
- Kjør `pip install -r requirements.txt` på nytt

**LLM returnerer ugyldig format:**
- Backend har automatisk reparasjon av vanlige feil
- Sjekk `/schema` for forventet format

**CORS-feil:**
- Backend må kjøre på port 8000
- Frontend må bruke `http://localhost:8000` som API_URL

## 📝 Neste steg

- [ ] Støtte for flere serier (multi-series charts)
- [ ] Historikk av analyser
- [ ] Eksport av funn til rapport
- [ ] Konfidensgrad-filtrering i UI
- [ ] Custom funn-typer via konfigurasjon
