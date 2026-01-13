# Highcharts-LLM Analyzer v0.3

**Deterministisk Chart-Conditioned Reasoning + Tidsserie-prediksjon**

Prototype for semantisk chart-analyse hvor LLM kun identifiserer mønstre, og all visualisering skjer deterministisk i kode. Nå med TimesFM-basert prediksjon og interaktiv chat.

## 🏗️ Arkitektur

```
┌─────────────┐    ┌────────────────────┐    ┌─────────────────┐    ┌───────────┐
│ Chart Data  │───▶│ LLM Analyse        │───▶│ Deterministisk  │───▶│ Highcharts│
│ (Frontend)  │    │ (Semantiske funn)  │    │ Mapping (Kode)  │    │ API       │
└─────────────┘    └────────────────────┘    └─────────────────┘    └───────────┘
       │
       │           ┌────────────────────┐    ┌─────────────────┐
       └──────────▶│ TimesFM Prediksjon │───▶│ Prognose-serie  │───────────┘
                   │ (eller fallback)   │    │ + Konfidensint. │
                   └────────────────────┘    └─────────────────┘
```

## 🎯 Kjerneprinsipper

| Prinsipp | Beskrivelse |
|----------|-------------|
| **Semantisk output** | LLM returnerer kun funn-typer, ikke Highcharts-kode |
| **Determinisme** | Samme funn → alltid samme visualisering |
| **Separasjon** | Analyse-logikk og UI-logikk er fullstendig adskilt |
| **Strenge enums** | Kun predefinerte FindingTypes aksepteres |
| **Interaktiv chat** | Still spørsmål om data og få prediksjoner |

## 📁 Filstruktur

```
highchart/spike/
├── analysis_schema.py    # Semantiske funn-typer + JSON schema
├── visual_presets.py     # Deterministiske Highcharts-presets
├── apply_findings.py     # Mapper findings → Highcharts config
├── prediction_service.py # TimesFM wrapper for prediksjoner (NY)
├── server.py             # FastAPI backend (v0.3)
├── index.html            # Frontend med chat og prediksjon
├── schema.py             # ⚠️ DEPRECATED - kun for referanse
├── requirements.txt      # Python-avhengigheter
├── 101.txt               # Dokumentasjon av dataflyt
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

Naviger til `http://localhost:8000` i nettleseren.

## 💬 Chat og Prediksjon

### Prediksjons-spørsmål

Skriv i chatten for å få automatiske prognoser:

- "Hva kan skje neste 30 dager?"
- "Hvordan ser fremtiden ut de neste 2 ukene?"
- "Prediksjon for neste måned med bullish scenario"
- "Hva skjer hvis markedet blir bearish?"

### Scenarioer

| Scenario | Effekt |
|----------|--------|
| `bullish` | Øker trenden med 20% |
| `bearish` | Reduserer trenden med 20% |
| `volatile` | Legger til høyere volatilitet |

### Visualisering

Prognoser vises på chartet som:
- **Stiplet oransje linje** - Hovedprediksjon
- **Oransje skyggefelt** - 95% konfidensintervall
- **Vertikal markør** - Skille mellom historikk og prognose

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
| `/` | GET | Serve frontend HTML |
| `/health` | GET | Helse-sjekk + modus-info |
| `/analyze` | POST | Semantisk analyse → deterministisk output |
| `/chat` | POST | Interaktiv chat med automatisk prediksjon |
| `/predict` | POST | Direkte tidsserie-prediksjon |
| `/test` | POST | Mock-data uten LLM-kall |
| `/schema` | GET | JSON-skjema for analyse |
| `/finding-types` | GET | Liste over alle funn-typer |
| `/docs` | GET | Swagger API-dokumentasjon |

## 📊 Chat Respons-format

```json
{
  "response": "Prognosen viser en mulig oppgang på 15%...",
  "hasPrediction": true,
  "predictionData": {
    "predictions": [[1704067200000, 250.5], ...],
    "confidenceRange": [[1704067200000, 220.0, 280.0], ...],
    "metadata": {
      "method": "timesfm",
      "horizon": 30,
      "frequency": "D"
    },
    "analysis": {
      "insights": ["Forventet oppgang på 15%", ...],
      "stats": {
        "historical_mean": 200.5,
        "predicted_mean": 230.2,
        "change_percent": 14.8
      }
    }
  }
}
```

## 🔮 Prediksjon API

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "seriesData": [[1704067200000, 100], [1704153600000, 102], ...],
    "horizon": 30,
    "frequency": "D",
    "scenario": "bullish"
  }'
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

## ⚡ Forskjell fra tidligere versjoner

| v0.1 | v0.2 | v0.3 (Nå) |
|------|------|-----------|
| LLM returnerer Highcharts | LLM returnerer FindingType | + Tidsserie-prediksjon |
| Ustabil output | Strengt JSON schema | + Interaktiv chat |
| - | - | + TimesFM / fallback |
| - | - | + Scenario-støtte |

## 🛠️ Feilsøking

**Backend starter ikke:**
- Sjekk at du er i riktig mappe (`highchart/spike`)
- Sjekk at alle avhengigheter er installert

**Import-feil:**
- Kjør `pip install -r requirements.txt` på nytt

**LLM returnerer ugyldig format:**
- Backend har automatisk reparasjon av vanlige feil
- Sjekk `/schema` for forventet format

**TimesFM ikke tilgjengelig:**
- Fallback til sesongbasert prediksjon brukes automatisk
- For full TimesFM: `pip install timesfm huggingface_hub`

**CORS-feil:**
- Backend må kjøre på port 8000
- Frontend må bruke `http://localhost:8000` som API_URL

## 📝 Neste steg

- [ ] Støtte for flere serier (multi-series charts)
- [ ] Historikk av analyser og prediksjoner
- [ ] Eksport av funn til rapport
- [ ] Konfidensgrad-filtrering i UI
- [ ] Custom funn-typer via konfigurasjon
- [ ] Sammenligning av scenarioer