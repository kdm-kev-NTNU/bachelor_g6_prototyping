"""
Pydantic Schema for Highcharts LLM Output

Definerer streng kontrakt mellom LLM og Highcharts API.
Validerer at LLM-output kan mappes direkte til gyldige Highcharts-opsjoner.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class AnnotationPoint(BaseModel):
    """Punkt for en annotasjon i Highcharts."""
    x: str = Field(..., description="Dato i ISO-format (YYYY-MM-DD)")
    y: float = Field(..., description="Y-verdi (pris/verdi)")
    
    @field_validator('x')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validerer at x er en gyldig ISO-dato."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError(f"Dato må være i format YYYY-MM-DD, fikk: {v}")
        return v


class AnnotationLabel(BaseModel):
    """En annotasjon-label som kan legges til i Highcharts."""
    point: AnnotationPoint
    text: str = Field(..., min_length=1, max_length=200, description="Tekst som vises")
    x_offset: Optional[int] = Field(default=-50, alias="xOffset", description="X-offset for label plassering")
    y_offset: Optional[int] = Field(default=-30, alias="yOffset", description="Y-offset for label plassering")
    
    class Config:
        populate_by_name = True


class PlotBand(BaseModel):
    """En plotBand som markerer en periode i chartet."""
    from_date: str = Field(..., alias="from", description="Start-dato (YYYY-MM-DD)")
    to_date: str = Field(..., alias="to", description="Slutt-dato (YYYY-MM-DD)")
    color: str = Field(
        default="rgba(255, 0, 0, 0.1)",
        description="Farge i rgba() eller hex format"
    )
    label: Optional[str] = Field(default=None, description="Valgfri label for båndet")
    
    class Config:
        populate_by_name = True
    
    @field_validator('from_date', 'to_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validerer datoformat."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError(f"Dato må være i format YYYY-MM-DD, fikk: {v}")
        return v
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validerer at fargen er gyldig rgba eller hex."""
        rgba_pattern = r'^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(,\s*[\d.]+\s*)?\)$'
        hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        
        if not (re.match(rgba_pattern, v) or re.match(hex_pattern, v)):
            raise ValueError(f"Ugyldig fargeformat: {v}. Bruk rgba() eller hex.")
        return v


class PlotLine(BaseModel):
    """En vertikal eller horisontal linje i chartet."""
    value: str = Field(..., description="Dato (YYYY-MM-DD) for vertikal linje")
    color: str = Field(default="#ff0000", description="Linjefarge")
    width: int = Field(default=2, ge=1, le=10, description="Linjebredde")
    label: Optional[str] = Field(default=None, description="Valgfri label")
    dash_style: Optional[str] = Field(
        default="Solid",
        alias="dashStyle",
        description="Linjestil: Solid, Dash, Dot, etc."
    )
    
    class Config:
        populate_by_name = True
    
    @field_validator('value')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validerer datoformat."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError(f"Dato må være i format YYYY-MM-DD, fikk: {v}")
        return v


class ChartAnalysisResponse(BaseModel):
    """
    Hovedresponsen fra LLM - inneholder både visuelle endringer og tekstlig analyse.
    
    Dette er kontrakten mellom LLM og frontend.
    Frontend mapper dette deterministisk til Highcharts API.
    """
    
    annotations: list[AnnotationLabel] = Field(
        default_factory=list,
        max_length=10,
        description="Liste med annotasjoner å legge til chartet (maks 10)"
    )
    
    plot_bands: list[PlotBand] = Field(
        default_factory=list,
        alias="plotBands",
        max_length=5,
        description="Liste med plot bands for å markere perioder (maks 5)"
    )
    
    plot_lines: list[PlotLine] = Field(
        default_factory=list,
        alias="plotLines",
        max_length=5,
        description="Liste med vertikale linjer for viktige datoer (maks 5)"
    )
    
    summary: str = Field(
        ...,
        min_length=50,
        max_length=1000,
        description="Tekstlig analyse og forklaring for chat-visning"
    )
    
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Modellens konfidensgrad i analysen (0-1)"
    )
    
    class Config:
        populate_by_name = True


class ChartStateInput(BaseModel):
    """
    Input fra frontend - chart-state som sendes til LLM.
    """
    
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
        description="Eksisterende annotasjoner som allerede er i chartet"
    )
    
    class Config:
        populate_by_name = True


# Eksempel på gyldig output for testing
EXAMPLE_RESPONSE = ChartAnalysisResponse(
    annotations=[
        AnnotationLabel(
            point=AnnotationPoint(x="2024-11-05", y=251.44),
            text="Signifikant prisøkning etter valg",
            x_offset=-70,
            y_offset=-40
        )
    ],
    plot_bands=[
        PlotBand(
            from_date="2022-01-01",
            to_date="2022-06-30",
            color="rgba(255, 0, 0, 0.1)",
            label="Bearish periode"
        )
    ],
    plot_lines=[
        PlotLine(
            value="2020-08-31",
            color="#00ff00",
            width=2,
            label="Stock split",
            dash_style="Dash"
        )
    ],
    summary="Analysen viser en tydelig bullish trend etter november 2024...",
    confidence=0.85
)


if __name__ == "__main__":
    # Test schema validering
    print("Testing schema...")
    print(f"Example response valid: {EXAMPLE_RESPONSE.model_dump_json(indent=2, by_alias=True)}")
