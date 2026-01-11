# ⚡ Energi AI Assistent - CLI

Kommandolinjeverktøy for energiprognose og analyse med Google TimesFM og OpenAI GPT-4.

## Kom i gang

### 1. Installer avhengigheter

```bash
cd "Tidsserie analyse/Time_Series_Foundation_Model"
pip install -r requirements.txt
```

### 2. Sett OpenAI API-nøkkel (valgfritt, for AI-forklaringer)

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "din-api-nøkkel"

# Linux/Mac
export OPENAI_API_KEY="din-api-nøkkel"
```

### 3. Kjør CLI

```bash
python cli.py
```

## Bruk

```
python cli.py [OPTIONS]

Options:
  -d, --days INT       Antall dager historikk (default: 30)
  -f, --forecast INT   Timer å predikere (default: 48)
  -y, --year INT       År for data (default: 2025)
  -o, --output PATH    Output-mappe (default: output)
  -q, --question TEXT  Still spørsmål til AI
  -s, --scenario       Scenario: normal, reduced_heating, smart_home, solar
  --no-images          Hopp over bildegenerering
  -Q, --quiet          Minimal output
```

## Eksempler

```bash
# Standard kjøring - genererer grafer
python cli.py

# 14 dager historikk, 72 timer prognose
python cli.py --days 14 --forecast 72

# Still spørsmål til AI
python cli.py -q "Hvorfor er forbruket høyt om vinteren?"

# Simuler solcelle-scenario
python cli.py --scenario solar

# Kun statistikk, ingen bilder
python cli.py --no-images
```

## Output

Kjøring genererer tre bilder i `output/`-mappen:

- `forecast.png` - Historikk og prognose
- `monthly.png` - Månedlig forbruksoversikt
- `daily_pattern.png` - Daglig forbruksmønster

## Filstruktur

```
Time_Series_Foundation_Model/
├── cli.py              # CLI-verktøy
├── data_generator.py   # Syntetisk data
├── timesfm_predictor.py # TimesFM wrapper
├── llm_explainer.py    # GPT-4 forklaringer
├── requirements.txt    # Avhengigheter
└── output/             # Genererte bilder
```

## Notater

- Uten TimesFM brukes sesongbasert fallback-prediksjon
- Uten OpenAI API-nøkkel får du enkle automatiske svar
- Data er syntetisk generert for demonstrasjon
