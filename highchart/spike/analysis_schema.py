"""
Semantisk Analyse Schema for LLM Chart Analysis

VIKTIG: Dette skjemaet inneholder INGEN Highcharts-referanser.
LLM returnerer kun semantiske funn - visualisering skjer deterministisk i kode.

Inspirert av: chart-conditioned reasoning pattern
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FindingType(str, Enum):
    """
    Hardkodede funn-typer som LLM kan identifisere.
    Hver type har en tilhørende visualisering definert i visual_presets.py
    """
    # Trend-relaterte funn
    BULLISH_TREND = "BULLISH_TREND"
    BEARISH_TREND = "BEARISH_TREND"
    CONSOLIDATION = "CONSOLIDATION"
    
    # Punkthendelser
    UNUSUAL_PEAK = "UNUSUAL_PEAK"
    UNUSUAL_DIP = "UNUSUAL_DIP"
    BREAKOUT = "BREAKOUT"
    
    # Volatilitet
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    
    # Signifikante hendelser
    SIGNIFICANT_EVENT = "SIGNIFICANT_EVENT"
    PRICE_GAP = "PRICE_GAP"
    
    # Mønstergjenkjenning
    SUPPORT_LEVEL = "SUPPORT_LEVEL"
    RESISTANCE_LEVEL = "RESISTANCE_LEVEL"
    DOUBLE_TOP = "DOUBLE_TOP"
    DOUBLE_BOTTOM = "DOUBLE_BOTTOM"


class AnalysisFinding(BaseModel):
    """
    Et enkelt semantisk funn fra analysen.
    Inneholder kun HVA som ble funnet, ikke HVORDAN det skal vises.
    """
    type: FindingType = Field(
        ...,
        description="Type funn fra predefinert enum"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Konfidensgrad for dette funnet (0-1)"
    )
    
    time_range: Optional[tuple[str, str]] = Field(
        default=None,
        alias="timeRange",
        description="Tidsperiode [start, end] i ISO-format (YYYY-MM-DD) eller HH:mm"
    )
    
    point_date: Optional[str] = Field(
        default=None,
        alias="pointDate",
        description="Enkelt datopunkt i ISO-format for punkt-funn"
    )
    
    point_value: Optional[float] = Field(
        default=None,
        alias="pointValue",
        description="Y-verdi for punkt-funn (pris/verdi)"
    )
    
    series: Optional[str] = Field(
        default=None,
        description="Navn på relevant serie hvis flere serier"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Kort beskrivelse av funnet (maks 100 tegn)"
    )
    
    class Config:
        populate_by_name = True


class AnalysisResult(BaseModel):
    """
    Komplett analyse-respons fra LLM.
    Inneholder semantiske funn + tekstlig oppsummering.
    """
    findings: list[AnalysisFinding] = Field(
        default_factory=list,
        max_length=15,
        description="Liste med identifiserte funn (maks 15)"
    )
    
    summary: str = Field(
        ...,
        min_length=50,
        max_length=1500,
        description="Tekstlig analyse og forklaring"
    )
    
    overall_trend: Optional[str] = Field(
        default=None,
        alias="overallTrend",
        description="Overordnet trendvurdering: bullish/bearish/neutral"
    )
    
    risk_assessment: Optional[str] = Field(
        default=None,
        alias="riskAssessment",
        description="Risikovurdering: low/medium/high"
    )
    
    class Config:
        populate_by_name = True


# ==========================================
# SYSTEM PROMPT - INGEN HIGHCHARTS-REFERANSER
# ==========================================

ANALYSIS_SYSTEM_PROMPT = """Du er en analytisk motor for finansdata.

DU MÅ:
- Analysere de tilgjengelige dataene objektivt
- Identifisere semantiske funn i datasettet
- Returnere KUN det spesifiserte JSON-skjemaet
- Bruke BARE de predefinerte funn-typene

DU MÅ IKKE:
- Referere til Highcharts, grafer eller visualisering
- Foreslå UI-endringer, farger eller styling
- Foreslå annotasjoner, plot bands, markers eller andre visuelle elementer
- Inkludere noen form for rendering-instruksjoner
- Legge til felt som ikke finnes i skjemaet

TILGJENGELIGE FUNN-TYPER:
- BULLISH_TREND: Sterk oppadgående trend
- BEARISH_TREND: Sterk nedadgående trend
- CONSOLIDATION: Sidelengs bevegelse
- UNUSUAL_PEAK: Signifikant topp
- UNUSUAL_DIP: Signifikant bunn
- BREAKOUT: Prisbrudd gjennom støtte/motstand
- HIGH_VOLATILITY: Periode med høy volatilitet
- LOW_VOLATILITY: Periode med lav volatilitet
- SIGNIFICANT_EVENT: Stor prisbevegelse (mulig ekstern hendelse)
- PRICE_GAP: Gap i pris mellom perioder
- SUPPORT_LEVEL: Identifisert støttenivå
- RESISTANCE_LEVEL: Identifisert motstandsnivå
- DOUBLE_TOP: Dobbel topp-mønster
- DOUBLE_BOTTOM: Dobbel bunn-mønster

REGLER FOR FUNN:
1. Hvert funn MÅ ha type (fra listen) og confidence (0-1)
2. Periode-funn (trender, volatilitet) bruker timeRange: ["YYYY-MM-DD", "YYYY-MM-DD"]
3. Punkt-funn (peaks, dips, events) bruker pointDate og pointValue
4. Hold confidence realistisk - over 0.9 kun ved svært tydelige mønstre
5. Begrens til maks 10 funn for å unngå støy

OUTPUT SCHEMA:
{
  "findings": [
    {
      "type": "FINDING_TYPE",
      "confidence": 0.85,
      "timeRange": ["YYYY-MM-DD", "YYYY-MM-DD"],
      "pointDate": "YYYY-MM-DD",
      "pointValue": 123.45,
      "description": "Kort beskrivelse"
    }
  ],
  "summary": "Detaljert tekstlig analyse...",
  "overallTrend": "bullish|bearish|neutral",
  "riskAssessment": "low|medium|high"
}

Returner KUN semantiske funn. Ikke foreslå visualiseringer."""


# ==========================================
# JSON SCHEMA FOR STRUCTURED OUTPUT
# ==========================================

ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "required": ["findings", "summary"],
    "properties": {
        "summary": {
            "type": "string",
            "minLength": 50,
            "maxLength": 1500
        },
        "overallTrend": {
            "type": "string",
            "enum": ["bullish", "bearish", "neutral"]
        },
        "riskAssessment": {
            "type": "string",
            "enum": ["low", "medium", "high"]
        },
        "findings": {
            "type": "array",
            "maxItems": 15,
            "items": {
                "type": "object",
                "required": ["type", "confidence"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "BULLISH_TREND",
                            "BEARISH_TREND",
                            "CONSOLIDATION",
                            "UNUSUAL_PEAK",
                            "UNUSUAL_DIP",
                            "BREAKOUT",
                            "HIGH_VOLATILITY",
                            "LOW_VOLATILITY",
                            "SIGNIFICANT_EVENT",
                            "PRICE_GAP",
                            "SUPPORT_LEVEL",
                            "RESISTANCE_LEVEL",
                            "DOUBLE_TOP",
                            "DOUBLE_BOTTOM"
                        ]
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "timeRange": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "pointDate": {
                        "type": "string"
                    },
                    "pointValue": {
                        "type": "number"
                    },
                    "series": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string",
                        "maxLength": 100
                    }
                }
            }
        }
    }
}


# ==========================================
# EKSEMPEL OUTPUT FOR TESTING
# ==========================================

EXAMPLE_ANALYSIS = AnalysisResult(
    findings=[
        AnalysisFinding(
            type=FindingType.BULLISH_TREND,
            confidence=0.88,
            time_range=("2024-11-01", "2024-12-31"),
            description="Sterk oppgang etter valget"
        ),
        AnalysisFinding(
            type=FindingType.UNUSUAL_PEAK,
            confidence=0.92,
            point_date="2021-11-04",
            point_value=402.86,
            description="Historisk høy pris"
        ),
        AnalysisFinding(
            type=FindingType.HIGH_VOLATILITY,
            confidence=0.75,
            time_range=("2022-01-01", "2022-06-30"),
            description="Høy volatilitet i første halvår 2022"
        )
    ],
    summary="Analysen viser at TSLA har hatt betydelig volatilitet de siste årene. "
            "En tydelig bullish trend er observert etter november 2024, sannsynligvis "
            "påvirket av eksterne faktorer. Historisk topp ble nådd i november 2021. "
            "Perioden januar-juni 2022 viste høy volatilitet med betydelige svingninger.",
    overall_trend="bullish",
    risk_assessment="medium"
)


if __name__ == "__main__":
    print("Testing semantic analysis schema...")
    print(f"\nExample output:\n{EXAMPLE_ANALYSIS.model_dump_json(indent=2, by_alias=True)}")
