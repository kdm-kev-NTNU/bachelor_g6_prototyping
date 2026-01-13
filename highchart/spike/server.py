"""
FastAPI Backend for Highcharts-LLM Chart Analyzer

REFAKTORERT: Deterministisk Chart-Conditioned Reasoning
- LLM returnerer KUN semantiske funn
- All Highcharts-manipulasjon skjer i kode via presets
- Streng schema-validering
"""

import os
import json
from datetime import datetime
from typing import Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

# Nye semantiske moduler
from analysis_schema import (
    AnalysisResult,
    AnalysisFinding,
    ANALYSIS_SYSTEM_PROMPT,
    ANALYSIS_JSON_SCHEMA,
    EXAMPLE_ANALYSIS
)
from apply_findings import generate_chart_response

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
    description="Deterministisk chart-analyse med semantiske funn",
    version="0.2.0"
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


# ==========================================
# INPUT SCHEMA
# ==========================================

class ChartStateInput(BaseModel):
    """Input fra frontend - chart-state som sendes til LLM."""
    
    series_data: list[list] = Field(
        ...,
        alias="seriesData",
        description="Tidsseriedata som [[timestamp, value], ...]"
    )
    
    title: Optional[str] = Field(default=None, description="Chart-tittel")
    
    time_range: dict = Field(
        ...,
        alias="timeRange",
        description="{'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}"
    )
    
    y_axis_label: Optional[str] = Field(
        default="Value",
        alias="yAxisLabel",
        description="Enhet/label for Y-aksen"
    )
    
    existing_annotations: Optional[list[dict]] = Field(
        default=None,
        alias="existingAnnotations",
        description="Eksisterende annotasjoner (for å unngå duplisering)"
    )
    
    class Config:
        populate_by_name = True


# ==========================================
# PROMPT BUILDING
# ==========================================

def build_analysis_prompt(chart_state: ChartStateInput) -> str:
    """
    Bygger prompt med chart-data for LLM.
    VIKTIG: Inneholder INGEN Highcharts-referanser.
    """
    
    data = chart_state.series_data
    sample_size = min(100, len(data))
    
    # Ta jevnt fordelte samples
    if len(data) > sample_size:
        step = len(data) // sample_size
        sampled_data = [data[i] for i in range(0, len(data), step)][:sample_size]
    else:
        sampled_data = data
    
    # Beregn statistikk
    values = [d[1] for d in data if d[1] is not None]
    if not values:
        raise ValueError("Ingen gyldige verdier i datasettet")
    
    stats = {
        "total_points": len(data),
        "sampled_points": len(sampled_data),
        "min_value": round(min(values), 2),
        "max_value": round(max(values), 2),
        "start_value": round(values[0], 2),
        "end_value": round(values[-1], 2),
        "change_percent": round(((values[-1] - values[0]) / values[0]) * 100, 2) if values[0] != 0 else 0,
        "avg_value": round(sum(values) / len(values), 2),
        "volatility": round(
            (max(values) - min(values)) / (sum(values) / len(values)) * 100, 2
        ) if sum(values) != 0 else 0
    }
    
    # Formater data for LLM
    formatted_data = []
    for point in sampled_data:
        if point[0] and point[1] is not None:
            ts = point[0]
            if isinstance(ts, (int, float)):
                date_str = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
            else:
                date_str = str(ts)
            formatted_data.append(f"{date_str}: {round(point[1], 2)}")
    
    # Finn lokale topper og bunner for kontekst
    local_extremes = find_local_extremes(data)
    
    prompt = f"""Analyser følgende tidsseriedata:

DATASETT INFO:
- Tittel: {chart_state.title or 'Ukjent'}
- Periode: {chart_state.time_range.get('start', 'N/A')} til {chart_state.time_range.get('end', 'N/A')}
- Måleenhet: {chart_state.y_axis_label or 'Verdi'}

STATISTIKK:
{json.dumps(stats, indent=2)}

IDENTIFISERTE EKSTREMPUNKTER:
{json.dumps(local_extremes, indent=2)}

DATA (samplet fra {stats['total_points']} punkter):
{chr(10).join(formatted_data[:40])}
{"... og " + str(len(formatted_data) - 40) + " flere punkter" if len(formatted_data) > 40 else ""}

KJENTE HENDELSER (ikke dupliser disse i funn):
{json.dumps([ann.get('text', '') for ann in (chart_state.existing_annotations or [])], indent=2)}

Analyser dataene og identifiser semantiske funn.
Fokuser på mønstre som IKKE allerede er kjent fra hendelseslisten.
Returner KUN det spesifiserte JSON-skjemaet."""
    
    return prompt


def find_local_extremes(data: list[list], window: int = 20) -> dict:
    """Finner lokale topper og bunner i datasettet."""
    if len(data) < window * 2:
        return {"peaks": [], "dips": []}
    
    peaks = []
    dips = []
    
    for i in range(window, len(data) - window):
        if data[i][1] is None:
            continue
            
        window_values = [d[1] for d in data[i-window:i+window] if d[1] is not None]
        if not window_values:
            continue
            
        current = data[i][1]
        
        if current == max(window_values):
            ts = data[i][0]
            if isinstance(ts, (int, float)):
                date_str = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
            else:
                date_str = str(ts)
            peaks.append({"date": date_str, "value": round(current, 2)})
        
        elif current == min(window_values):
            ts = data[i][0]
            if isinstance(ts, (int, float)):
                date_str = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
            else:
                date_str = str(ts)
            dips.append({"date": date_str, "value": round(current, 2)})
    
    # Begrens til de mest signifikante
    peaks = sorted(peaks, key=lambda x: x["value"], reverse=True)[:5]
    dips = sorted(dips, key=lambda x: x["value"])[:5]
    
    return {"peaks": peaks, "dips": dips}


# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/")
async def root():
    """Helse-sjekk endpoint."""
    return {
        "status": "running",
        "openai_available": client is not None,
        "version": "0.2.0",
        "mode": "semantic-analysis"
    }


@app.post("/analyze")
async def analyze_chart(chart_state: ChartStateInput) -> dict[str, Any]:
    """
    Analyserer chart-data og returnerer semantiske funn + deterministiske visualiseringer.
    
    Flyt:
    1. Bygg prompt med data (ingen Highcharts-refs)
    2. LLM analyserer og returnerer semantiske funn
    3. apply_findings mapper til Highcharts-konfigurasjon
    4. Returner komplett respons til frontend
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
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5,  # Lavere for mer konsistent output
            max_tokens=2000
        )
        
        # Parse LLM respons
        raw_response = response.choices[0].message.content
        response_data = json.loads(raw_response)
        
        # Valider mot semantisk schema
        try:
            analysis = AnalysisResult(**response_data)
        except ValidationError as ve:
            print(f"[WARN] Valideringsfeil fra LLM output: {ve}")
            analysis = attempt_repair(response_data)
            if not analysis:
                raise HTTPException(
                    status_code=422,
                    detail=f"LLM returnerte ugyldig format: {str(ve)}"
                )
        
        # DETERMINISTISK MAPPING: Konverter semantiske funn til Highcharts
        chart_response = generate_chart_response(analysis)
        
        return chart_response
        
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


def attempt_repair(data: dict) -> Optional[AnalysisResult]:
    """
    Forsøker å reparere vanlige feil i LLM output.
    """
    repaired = data.copy()
    
    # Sørg for at summary finnes og er lang nok
    if "summary" not in repaired or len(repaired.get("summary", "")) < 50:
        repaired["summary"] = repaired.get("summary", "Analysen identifiserte flere mønstre i datasettet. ") + " " + "Basert på de tilgjengelige dataene er det identifisert signifikante trender."
    
    # Filtrer ut ugyldige funn
    if "findings" in repaired:
        valid_findings = []
        for finding in repaired["findings"]:
            if isinstance(finding, dict) and "type" in finding and "confidence" in finding:
                # Sørg for at type er gyldig
                valid_types = [
                    "BULLISH_TREND", "BEARISH_TREND", "CONSOLIDATION",
                    "UNUSUAL_PEAK", "UNUSUAL_DIP", "BREAKOUT",
                    "HIGH_VOLATILITY", "LOW_VOLATILITY",
                    "SIGNIFICANT_EVENT", "PRICE_GAP",
                    "SUPPORT_LEVEL", "RESISTANCE_LEVEL",
                    "DOUBLE_TOP", "DOUBLE_BOTTOM"
                ]
                if finding["type"] in valid_types:
                    valid_findings.append(finding)
        repaired["findings"] = valid_findings
    else:
        repaired["findings"] = []
    
    try:
        return AnalysisResult(**repaired)
    except ValidationError:
        return None


@app.post("/test")
async def test_with_mock():
    """
    Test-endpoint som returnerer mock-data uten LLM-kall.
    Bruker EXAMPLE_ANALYSIS fra analysis_schema.
    """
    chart_response = generate_chart_response(EXAMPLE_ANALYSIS)
    return chart_response


@app.get("/schema")
async def get_schema():
    """Returnerer JSON-skjemaet for analyse-output."""
    return ANALYSIS_JSON_SCHEMA


@app.get("/finding-types")
async def get_finding_types():
    """Returnerer alle tilgjengelige funn-typer."""
    from analysis_schema import FindingType
    from visual_presets import (
        PLOT_BAND_PRESETS,
        PLOT_LINE_PRESETS,
        ANNOTATION_PRESETS,
        LABEL_TEMPLATES
    )
    
    return {
        "types": [ft.value for ft in FindingType],
        "period_types": list(PLOT_BAND_PRESETS.keys()),
        "level_types": list(PLOT_LINE_PRESETS.keys()),
        "point_types": list(ANNOTATION_PRESETS.keys()),
        "labels": LABEL_TEMPLATES
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=== Starter Highcharts LLM Analyzer v0.2 ===")
    print(f"    Mode: Deterministisk semantisk analyse")
    print(f"    OpenAI tilgjengelig: {client is not None}")
    print("    Apne http://localhost:8000/docs for API-dokumentasjon")
    print("    Apne http://localhost:8000/schema for JSON-skjema")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
