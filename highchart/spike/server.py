"""
FastAPI Backend for Highcharts-LLM Chart Analyzer

Mottar chart-state fra frontend, sender til GPT-4o for analyse,
og returnerer gyldige Highcharts-modifikasjoner.
"""

import os
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from dotenv import load_dotenv

from schema import ChartStateInput, ChartAnalysisResponse

# Last miljøvariabler
load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARN] OpenAI ikke installert. Kjor: pip install openai")

app = FastAPI(
    title="Highcharts LLM Analyzer",
    description="Spike: Tester LLM-basert chart-analyse med strukturert output",
    version="0.1.0"
)

# CORS for lokal utvikling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI klient
client: Optional[OpenAI] = None
if OPENAI_AVAILABLE:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        print("[WARN] OPENAI_API_KEY ikke satt i miljovariabler")


SYSTEM_PROMPT = """Du er en finansanalytiker som analyserer aksjedata visualisert i Highcharts.

Din oppgave er å:
1. ANALYSERE dataene og identifisere viktige mønstre, trender og hendelser
2. FORESLÅ visuelle annotasjoner som hjelper brukeren å forstå dataene
3. SKILLE mellom analyse (summary) og visualisering (annotations/plotBands)

VIKTIGE REGLER:
- Returner KUN gyldig JSON som matcher det spesifiserte skjemaet
- Datoer må være i formatet YYYY-MM-DD
- Koordinater (y-verdier) må matche faktiske verdier i datasettet
- Annotasjoner skal plasseres på reelle datapunkter
- Ikke foreslå mer enn 5-8 annotasjoner for å unngå visuelt rot
- plotBands brukes for å markere perioder (bullish/bearish/konsolidering)
- plotLines brukes for viktige enkeltdatoer

OUTPUT SCHEMA:
{
  "annotations": [
    {
      "point": {"x": "YYYY-MM-DD", "y": <faktisk verdi>},
      "text": "Kort beskrivelse (maks 50 tegn)",
      "xOffset": -50,  // plassering av label
      "yOffset": -30
    }
  ],
  "plotBands": [
    {
      "from": "YYYY-MM-DD",
      "to": "YYYY-MM-DD", 
      "color": "rgba(R, G, B, 0.1)",  // bruk lav opacity
      "label": "Periode-beskrivelse"
    }
  ],
  "plotLines": [
    {
      "value": "YYYY-MM-DD",
      "color": "#hexcolor",
      "width": 2,
      "label": "Hendelse",
      "dashStyle": "Dash"
    }
  ],
  "summary": "Detaljert tekstlig analyse av dataene...",
  "confidence": 0.85
}

ANALYSETIPS:
- Se etter lokale topper og bunner
- Identifiser trender (bullish/bearish/sidelengs)
- Finn volatilitetsendringer
- Marker signifikante prosentvise endringer (>10% på kort tid)
- Korreler med kjente markedshendelser hvis relevant"""


def build_analysis_prompt(chart_state: ChartStateInput) -> str:
    """Bygger prompt med chart-data for LLM."""
    
    # Sample data for å holde token-bruk nede
    data = chart_state.series_data
    sample_size = min(100, len(data))
    
    # Ta jevnt fordelte samples
    if len(data) > sample_size:
        step = len(data) // sample_size
        sampled_data = [data[i] for i in range(0, len(data), step)][:sample_size]
    else:
        sampled_data = data
    
    # Beregn grunnleggende statistikk
    values = [d[1] for d in data if d[1] is not None]
    stats = {
        "total_points": len(data),
        "sampled_points": len(sampled_data),
        "min_value": round(min(values), 2) if values else 0,
        "max_value": round(max(values), 2) if values else 0,
        "start_value": round(values[0], 2) if values else 0,
        "end_value": round(values[-1], 2) if values else 0,
        "change_percent": round(((values[-1] - values[0]) / values[0]) * 100, 2) if values and values[0] != 0 else 0
    }
    
    # Formater data for LLM
    formatted_data = []
    for point in sampled_data:
        if point[0] and point[1] is not None:
            # Konverter timestamp til lesbar dato
            ts = point[0]
            if isinstance(ts, (int, float)):
                date_str = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
            else:
                date_str = str(ts)
            formatted_data.append(f"{date_str}: {round(point[1], 2)}")
    
    prompt = f"""Analyser følgende aksjedata:

CHART INFO:
- Tittel: {chart_state.title or 'Ukjent'}
- Periode: {chart_state.time_range.get('start', 'N/A')} til {chart_state.time_range.get('end', 'N/A')}
- Y-akse: {chart_state.y_axis_label or 'Pris'}

STATISTIKK:
{json.dumps(stats, indent=2)}

DATA (samplet fra {stats['total_points']} punkter):
{chr(10).join(formatted_data[:50])}
{"... og " + str(len(formatted_data) - 50) + " flere punkter" if len(formatted_data) > 50 else ""}

EKSISTERENDE ANNOTASJONER (ikke dupliser disse):
{json.dumps(chart_state.existing_annotations, indent=2) if chart_state.existing_annotations else "Ingen"}

Gi meg en analyse med forslag til nye annotasjoner, plotBands og en tekstlig oppsummering.
Fokuser på mønstre og hendelser som IKKE allerede er annotert."""
    
    return prompt


@app.get("/")
async def root():
    """Helse-sjekk endpoint."""
    return {
        "status": "running",
        "openai_available": client is not None,
        "version": "0.1.0"
    }


@app.post("/analyze", response_model=ChartAnalysisResponse)
async def analyze_chart(chart_state: ChartStateInput):
    """
    Analyserer chart-data og returnerer forslag til visuelle endringer.
    
    Args:
        chart_state: JSON med chart-data fra frontend
        
    Returns:
        ChartAnalysisResponse med annotasjoner, plotBands og tekstlig analyse
    """
    if not client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API ikke tilgjengelig. Sjekk at OPENAI_API_KEY er satt."
        )
    
    # Bygg prompt
    user_prompt = build_analysis_prompt(chart_state)
    
    try:
        # Kall GPT-4o med JSON mode
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse respons
        raw_response = response.choices[0].message.content
        response_data = json.loads(raw_response)
        
        # Valider mot schema
        try:
            validated_response = ChartAnalysisResponse(**response_data)
            return validated_response
        except ValidationError as ve:
            # Logg valideringsfeil for debugging
            print(f"[WARN] Valideringsfeil fra LLM output: {ve}")
            
            # Prøv å reparere vanlige feil
            repaired = attempt_repair(response_data)
            if repaired:
                return ChartAnalysisResponse(**repaired)
            
            raise HTTPException(
                status_code=422,
                detail=f"LLM returnerte ugyldig format: {str(ve)}"
            )
            
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kunne ikke parse LLM respons som JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feil ved LLM-kall: {str(e)}"
        )


def attempt_repair(data: dict) -> Optional[dict]:
    """
    Forsøker å reparere vanlige feil i LLM output.
    """
    repaired = data.copy()
    
    # Sørg for at summary finnes og er lang nok
    if "summary" not in repaired or len(repaired.get("summary", "")) < 50:
        repaired["summary"] = repaired.get("summary", "") + " " + "Analysen er basert på de tilgjengelige dataene i chartet."
    
    # Fjern ugyldige annotasjoner
    if "annotations" in repaired:
        valid_annotations = []
        for ann in repaired["annotations"]:
            if isinstance(ann, dict) and "point" in ann and "text" in ann:
                point = ann["point"]
                if isinstance(point, dict) and "x" in point and "y" in point:
                    valid_annotations.append(ann)
        repaired["annotations"] = valid_annotations
    
    # Fjern ugyldige plotBands
    if "plotBands" in repaired:
        valid_bands = []
        for band in repaired["plotBands"]:
            if isinstance(band, dict) and "from" in band and "to" in band:
                # Fiks manglende farge
                if "color" not in band:
                    band["color"] = "rgba(100, 100, 100, 0.1)"
                valid_bands.append(band)
        repaired["plotBands"] = valid_bands
    
    # Sett default confidence
    if "confidence" not in repaired:
        repaired["confidence"] = 0.7
    
    return repaired


@app.post("/test")
async def test_with_mock():
    """
    Test-endpoint som returnerer mock-data uten LLM-kall.
    Nyttig for frontend-utvikling og testing.
    """
    from schema import EXAMPLE_RESPONSE
    return EXAMPLE_RESPONSE


if __name__ == "__main__":
    import uvicorn
    
    print("=== Starter Highcharts LLM Analyzer ===")
    print(f"    OpenAI tilgjengelig: {client is not None}")
    print("    Apne http://localhost:8000/docs for API-dokumentasjon")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
