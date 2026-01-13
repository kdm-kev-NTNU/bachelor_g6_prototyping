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
from typing import Optional, Any, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

    analysis_period: Optional[str] = Field(
        default="auto",
        alias="analysisPeriod",
        description="Periode å analysere: 'auto', 'all', '1y', '6m', '3m', '1m', 'custom'"
    )

    custom_start: Optional[str] = Field(
        default=None,
        alias="customStart",
        description="Start-dato for custom periode (YYYY-MM-DD)"
    )

    custom_end: Optional[str] = Field(
        default=None,
        alias="customEnd",
        description="Slutt-dato for custom periode (YYYY-MM-DD)"
    )

    class Config:
        populate_by_name = True


# ==========================================
# PROMPT BUILDING
# ==========================================

def build_analysis_prompt(chart_state: ChartStateInput) -> tuple[str, int, int]:
    """
    Bygger prompt med chart-data for LLM.
    VIKTIG: Inneholder INGEN Highcharts-referanser.

    Returns:
        Tuple av (prompt, filtered_count, original_count)
    """

    # Filtrer data basert på periode
    filtered_data, original_count = filter_data_by_period(
        chart_state.series_data,
        chart_state.analysis_period,
        chart_state.custom_start,
        chart_state.custom_end
    )

    data = filtered_data if filtered_data else chart_state.series_data
    filtered_count = len(data)

    # Sampling kun hvis periode er "auto" eller data er veldig stor
    if chart_state.analysis_period == "auto":
        sample_size = min(100, len(data))
        use_sampling = len(data) > sample_size
    else:
        # For bruker-valgte perioder, bruk all data (ingen sampling)
        sample_size = len(data)
        use_sampling = False

    if use_sampling:
        # Ta jevnt fordelte samples
        step = len(data) // sample_size
        sampled_data = [data[i] for i in range(0, len(data), step)][:sample_size]
        actual_sample_size = len(sampled_data)
    else:
        sampled_data = data
        actual_sample_size = len(data)
    
    # Beregn statistikk
    values = [d[1] for d in data if d[1] is not None]
    if not values:
        raise ValueError("Ingen gyldige verdier i datasettet")
    
    stats = {
        "total_points": len(data),
        "sampled_points": len(sampled_data),
        "filtered_points": filtered_count,
        "original_points": original_count,
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

DATA ({stats['sampled_points']} punkter fra {stats['filtered_points']} filtrerte, opprinnelig {stats['original_points']}):
{chr(10).join(formatted_data[:40])}
{"... og " + str(len(formatted_data) - 40) + " flere punkter" if len(formatted_data) > 40 else ""}

KJENTE HENDELSER (ikke dupliser disse i funn):
{json.dumps([ann.get('text', '') for ann in (chart_state.existing_annotations or [])], indent=2)}

Analyser dataene og identifiser semantiske funn.
Fokuser på mønstre som IKKE allerede er kjent fra hendelseslisten.
Returner KUN det spesifiserte JSON-skjemaet."""
    
    return prompt, filtered_count, original_count


def filter_data_by_period(data: list[list], period: str, custom_start: str = None, custom_end: str = None) -> tuple[list[list], int]:
    """
    Filtrer data basert på valgt periode.

    Returns:
        Tuple av (filtrert_data, original_count)
    """
    if not data:
        return [], 0

    original_count = len(data)

    # Ingen filtrering for 'auto' eller 'all'
    if period in ["auto", "all"]:
        return data, original_count

    try:
        import pandas as pd

        # Konverter til DataFrame for enklere dato-håndtering
        df = pd.DataFrame(data, columns=['timestamp', 'value'])
        df['timestamp'] = pd.to_datetime(df['timestamp'] / 1000, unit='s')
        df = df.sort_values('timestamp')

        # Bruk siste datapunkt som referansetid (ikke "nå" på veggen)
        if df.empty:
            return data, original_count
        reference_end = df['timestamp'].max()

        if period == "1y":
            cutoff = reference_end - pd.Timedelta(days=365)
        elif period == "6m":
            cutoff = reference_end - pd.Timedelta(days=180)
        elif period == "3m":
            cutoff = reference_end - pd.Timedelta(days=90)
        elif period == "1m":
            cutoff = reference_end - pd.Timedelta(days=30)
        elif period == "custom" and custom_start:
            cutoff = pd.to_datetime(custom_start)
            if custom_end:
                end_cutoff = pd.to_datetime(custom_end)
                # Filtrer mellom start og slutt
                filtered_df = df[(df['timestamp'] >= cutoff) & (df['timestamp'] <= end_cutoff)]
                filtered_data = filtered_df[['timestamp', 'value']].values.tolist()
                # Konverter timestamp tilbake til millisekunder
                filtered_data = [[int(ts.timestamp() * 1000), val] for ts, val in filtered_data]
                return filtered_data, original_count
        else:
            return data, original_count

        # Filtrer fra cutoff til nå
        filtered_df = df[df['timestamp'] >= cutoff]
        filtered_data = filtered_df[['timestamp', 'value']].values.tolist()

        # Konverter timestamp tilbake til millisekunder
        filtered_data = [[int(ts.timestamp() * 1000), val] for ts, val in filtered_data]

        return filtered_data, original_count

    except Exception as e:
        print(f"[WARN] Kunne ikke filtrere data: {e}")
        return data, original_count


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
async def serve_index():
    """Serve frontend HTML."""
    import os
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))


@app.get("/health")
async def health_check():
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
    user_prompt, filtered_count, original_count = build_analysis_prompt(chart_state)
    
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

        # Legg til informasjon om datapunkter brukt
        chart_response["dataPointsUsed"] = filtered_count
        chart_response["originalDataPoints"] = original_count
        chart_response["analysisPeriod"] = chart_state.analysis_period

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


# ==========================================
# CHAT ENDPOINT
# ==========================================

class ChatMessage(BaseModel):
    """Input for chat-meldinger fra bruker."""
    message: str = Field(..., min_length=1, max_length=1000)
    chart_context: Optional[dict] = Field(
        default=None,
        alias="chartContext",
        description="Kontekst fra chartet for mer relevant respons"
    )
    series_data: Optional[list[list]] = Field(
        default=None,
        alias="seriesData",
        description="Chart-data for prediksjon (valgfritt)"
    )
    analysis_period: Optional[str] = Field(
        default="auto",
        alias="analysisPeriod",
        description="Periode å bruke for analyse/prediksjon"
    )
    custom_start: Optional[str] = Field(
        default=None,
        alias="customStart",
        description="Start-dato for custom periode"
    )
    custom_end: Optional[str] = Field(
        default=None,
        alias="customEnd",
        description="Slutt-dato for custom periode"
    )

    class Config:
        populate_by_name = True


# Nøkkelord for å oppdage prediksjons-spørsmål
PREDICTION_KEYWORDS = [
    "hva skjer", "hva kan skje", "fremtid", "fremover", "prediksjon", 
    "prognose", "forutsi", "spå", "neste", "om en", "om to",
    "kommer til", "vil", "kan", "mulig", "forecast", "predict"
]

# Nøkkelord for scenarioer
SCENARIO_KEYWORDS = {
    "bullish": ["oppgang", "øker", "stiger", "positiv", "bullish", "vekst"],
    "bearish": ["nedgang", "synker", "faller", "negativ", "bearish", "krasj"],
    "volatile": ["volatil", "svinger", "usikker", "ustabil"]
}


def detect_prediction_intent(message: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Oppdager om meldingen er et prediksjons-spørsmål.
    
    Returns:
        Tuple av (is_prediction, horizon_days, scenario)
    """
    message_lower = message.lower()
    
    # Sjekk om det er et prediksjons-spørsmål
    is_prediction = any(kw in message_lower for kw in PREDICTION_KEYWORDS)
    
    if not is_prediction:
        return False, None, None
    
    # Forsøk å ekstrahere tidshorisont
    horizon = extract_horizon(message_lower)
    
    # Forsøk å oppdage scenario
    scenario = None
    for scenario_name, keywords in SCENARIO_KEYWORDS.items():
        if any(kw in message_lower for kw in keywords):
            scenario = scenario_name
            break
    
    return True, horizon, scenario


def extract_horizon(message: str) -> int:
    """Ekstraher tidshorisont fra melding."""
    import re
    
    # Mønstre for tidsekstraksjon
    patterns = [
        (r'(\d+)\s*dag', 1),           # "30 dager"
        (r'(\d+)\s*uke', 7),            # "2 uker"
        (r'(\d+)\s*måned', 30),         # "3 måneder"
        (r'en\s+uke', 7),               # "en uke"
        (r'to\s+uker?', 14),            # "to uker"
        (r'en\s+måned', 30),            # "en måned"
        (r'to\s+måned', 60),            # "to måneder"
        (r'neste\s+uke', 7),            # "neste uke"
        (r'neste\s+måned', 30),         # "neste måned"
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, message)
        if match:
            if match.groups():
                return int(match.group(1)) * multiplier
            return multiplier
    
    # Default: 30 dager
    return 30


CHAT_SYSTEM_PROMPT = """Du er en intelligent finansanalytiker-assistent som hjelper brukere med å forstå chart-data og analyser.

Din oppgave er å:
- Svare på spørsmål om chart-dataene og trender
- Forklare tekniske konsepter på en forståelig måte
- Gi kontekst til analysefunn
- Hjelpe brukeren å forstå markedsmønstre

REGLER:
1. Svar alltid på norsk
2. Vær konsis men informativ (maks 2-3 avsnitt)
3. Bruk **bold** for viktige tall og begreper
4. Referer til chart-konteksten når relevant
5. Ikke gi investeringsråd - bare analyser og forklaringer
6. Vær vennlig og hjelpsom

Chart-kontekst du kan referere til:
- Tittel: {title}
- Antall datapunkter: {data_points}
- Tidsperiode: {time_range}
- Siste analyse: {analysis}"""


@app.post("/chat")
async def chat_with_assistant(chat_input: ChatMessage) -> dict:
    """
    Chat-endpoint for å stille spørsmål om chartet og analysen.
    Oppdager automatisk prediksjons-spørsmål og inkluderer prediksjon.
    """
    if not client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API ikke tilgjengelig. Sjekk at OPENAI_API_KEY er satt."
        )
    
    # Oppdage prediksjons-intent
    is_prediction, horizon, scenario = detect_prediction_intent(chat_input.message)
    
    # Hvis det er et prediksjons-spørsmål og vi har data
    prediction_data = None
    if is_prediction and chat_input.series_data:
        try:
            # Filtrer data basert på periode (bruker "auto" som standard for chat)
            period = getattr(chat_input, 'analysis_period', 'auto')
            custom_start = getattr(chat_input, 'custom_start', None)
            custom_end = getattr(chat_input, 'custom_end', None)

            filtered_data, original_count = filter_data_by_period(
                chat_input.series_data,
                period,
                custom_start,
                custom_end
            )

            service = get_prediction_service()
            prediction_result = service.predict_from_chart_data(
                series_data=filtered_data if filtered_data else chat_input.series_data,
                forecast_horizon=horizon or 30,
                frequency="D",
                scenario=scenario
            )
            
            if prediction_result.get("success"):
                analysis = service.analyze_prediction(
                    filtered_data if filtered_data else chat_input.series_data,
                    prediction_result
                )
                prediction_data = {
                    "predictions": prediction_result.get("predictions", []),
                    "confidenceRange": prediction_result.get("confidenceRange", []),
                    "metadata": prediction_result.get("metadata", {}),
                    "analysis": analysis,
                    "horizon": horizon or 30,
                    "scenario": scenario,
                    "dataPointsUsed": len(filtered_data) if filtered_data else len(chat_input.series_data),
                    "periodUsed": period
                }
        except Exception as e:
            print(f"[WARN] Prediksjon i chat feilet: {e}")
    
    # Bygg kontekst fra chart
    context = chat_input.chart_context or {}
    title = context.get("title", "Ukjent chart")
    data_points = context.get("dataPoints", "ukjent")
    time_range = context.get("timeRange", {})
    time_range_str = f"{time_range.get('start', 'N/A')} til {time_range.get('end', 'N/A')}"
    current_analysis = context.get("currentAnalysis", "Ingen analyse utført ennå")
    
    # Legg til prediksjonsinformasjon i system prompt hvis relevant
    prediction_context = ""
    if prediction_data:
        pred_analysis = prediction_data.get("analysis", {})
        insights = pred_analysis.get("insights", [])
        stats = pred_analysis.get("stats", {})
        prediction_context = f"""

PREDIKSJON UTFØRT:
- Horisont: {prediction_data.get('horizon')} dager
- Scenario: {prediction_data.get('scenario') or 'standard'}
- Forventet endring: {stats.get('change_percent', 'N/A')}%
- Innsikt: {'; '.join(insights[:2]) if insights else 'Ingen'}

Inkluder prediksjonsinformasjonen i svaret ditt."""
    
    system_prompt = CHAT_SYSTEM_PROMPT.format(
        title=title,
        data_points=data_points,
        time_range=time_range_str,
        analysis=current_analysis or "Ingen analyse utført"
    ) + prediction_context
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chat_input.message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        assistant_response = response.choices[0].message.content
        
        result = {
            "response": assistant_response,
            "tokens_used": response.usage.total_tokens if response.usage else None,
            "hasPrediction": prediction_data is not None
        }
        
        if prediction_data:
            result["predictionData"] = prediction_data
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feil ved chat: {str(e)}"
        )


# ==========================================
# PREDICTION ENDPOINT
# ==========================================

class PredictionRequest(BaseModel):
    """Input for prediksjon."""
    series_data: list[list] = Field(
        ...,
        alias="seriesData",
        description="Tidsseriedata som [[timestamp, value], ...]"
    )
    horizon: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Antall perioder å predikere fremover"
    )
    frequency: str = Field(
        default="D",
        description="Frekvens: 'D' for daglig, 'H' for time"
    )
    scenario: Optional[str] = Field(
        default=None,
        description="Scenario: 'bullish', 'bearish', 'volatile'"
    )
    period: Optional[str] = Field(
        default="auto",
        description="Periode å bruke for prediksjon"
    )
    custom_start: Optional[str] = Field(
        default=None,
        alias="customStart",
        description="Start-dato for custom periode"
    )
    custom_end: Optional[str] = Field(
        default=None,
        alias="customEnd",
        description="Slutt-dato for custom periode"
    )
    
    class Config:
        populate_by_name = True


# Lazy-load prediction service
_prediction_service = None

def get_prediction_service():
    """Lazy-load prediction service."""
    global _prediction_service
    if _prediction_service is None:
        from prediction_service import create_prediction_service
        _prediction_service = create_prediction_service()
    return _prediction_service


@app.post("/predict")
async def predict_future(request: PredictionRequest) -> dict:
    """
    Prediker fremtidige verdier basert på historiske data.

    Bruker TimesFM hvis tilgjengelig, ellers fallback til sesongbasert prediksjon.
    Returnerer data klart for Highcharts visualisering.
    """
    # Filtrer data først hvis periode er spesifisert
    filtered_data, original_count = filter_data_by_period(
        request.series_data,
        request.period,
        request.custom_start,
        request.custom_end
    )


    service = get_prediction_service()

    # Kjør prediksjon på filtrert data
    result = service.predict_from_chart_data(
        series_data=filtered_data if filtered_data else request.series_data,
        forecast_horizon=request.horizon,
        frequency=request.frequency,
        scenario=request.scenario
    )

    # Legg til informasjon om filtrering
    result["dataPointsUsed"] = len(filtered_data) if filtered_data else len(request.series_data)
    result["originalDataPoints"] = original_count
    result["periodUsed"] = request.period

    # Oppdater metadata med periode-info
    if "metadata" in result:
        result["metadata"]["periodUsed"] = request.period
        result["metadata"]["dataPointsUsed"] = result["dataPointsUsed"]
        result["metadata"]["originalDataPoints"] = original_count
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("metadata", {}).get("error", "Prediksjon feilet")
        )
    
    # Legg til analyse
    analysis = service.analyze_prediction(request.series_data, result)
    result["analysis"] = analysis
    
    # Generer tekstforklaring med LLM hvis tilgjengelig
    if client:
        try:
            explanation = await generate_prediction_explanation(
                result, request.scenario
            )
            result["explanation"] = explanation
        except Exception as e:
            print(f"[WARN] Kunne ikke generere forklaring: {e}")
            result["explanation"] = format_fallback_explanation(analysis)
    else:
        result["explanation"] = format_fallback_explanation(analysis)
    
    return result


async def generate_prediction_explanation(
    prediction_result: dict,
    scenario: Optional[str]
) -> str:
    """Generer tekstforklaring av prediksjonen med LLM."""
    analysis = prediction_result.get("analysis", {})
    insights = analysis.get("insights", [])
    stats = analysis.get("stats", {})
    metadata = prediction_result.get("metadata", {})
    
    prompt = f"""Forklar denne prediksjonen på norsk (2-3 setninger):

Metode: {metadata.get('method', 'ukjent')}
Horisont: {metadata.get('horizon', 'ukjent')} perioder
Scenario: {scenario or 'standard'}

Statistikk:
- Historisk snitt: {stats.get('historical_mean', 'N/A')}
- Predikert snitt: {stats.get('predicted_mean', 'N/A')}
- Endring: {stats.get('change_percent', 'N/A')}%

Innsikt:
{chr(10).join('- ' + i for i in insights)}

Vær kort og konkret. Ikke gi investeringsråd."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du er en finansanalytiker som forklarer prediksjoner på norsk. Vær konsis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )
    
    return response.choices[0].message.content


def format_fallback_explanation(analysis: dict) -> str:
    """Fallback forklaring uten LLM."""
    insights = analysis.get("insights", [])
    stats = analysis.get("stats", {})
    
    parts = []
    
    change = stats.get("change_percent", 0)
    if change > 0:
        parts.append(f"Prognosen indikerer en mulig oppgang på {change:.1f}%.")
    elif change < 0:
        parts.append(f"Prognosen indikerer en mulig nedgang på {abs(change):.1f}%.")
    else:
        parts.append("Prognosen viser relativt stabile verdier.")
    
    if insights:
        parts.append(insights[0])
    
    return " ".join(parts)


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
