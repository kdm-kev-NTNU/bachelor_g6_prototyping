"""
Deterministisk Mapping av Semantiske Funn til Highcharts

Denne modulen tar semantiske funn fra LLM og konverterer dem til
konkrete Highcharts-konfigurasjoner ved hjelp av predefinerte presets.

LLM har INGEN kontroll over visualiseringen - alt bestemmes her.
"""

from typing import Any, Optional
from datetime import datetime

from analysis_schema import AnalysisFinding, AnalysisResult, FindingType
from visual_presets import (
    get_plot_band_preset,
    get_plot_line_preset,
    get_annotation_preset,
    get_marker_preset,
    format_label,
    is_period_finding,
    is_point_finding,
    is_level_finding,
    get_opacity_for_confidence,
    CONFIDENCE_THRESHOLDS
)


def parse_date_to_timestamp(date_str: str) -> int:
    """Konverterer ISO-dato til timestamp i millisekunder"""
    try:
        dt = datetime.fromisoformat(date_str)
        return int(dt.timestamp() * 1000)
    except ValueError:
        # Prøv å parse som bare dato
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp() * 1000)


def apply_opacity_to_color(color: str, confidence: float) -> str:
    """
    Justerer opacity i en rgba-farge basert på konfidensgrad.
    """
    opacity = get_opacity_for_confidence(confidence)
    
    if color.startswith("rgba"):
        # Erstatt eksisterende opacity
        import re
        match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color)
        if match:
            r, g, b = match.groups()
            base_opacity = float(color.split(',')[-1].replace(')', '').strip())
            new_opacity = base_opacity * opacity
            return f"rgba({r}, {g}, {b}, {new_opacity:.2f})"
    elif color.startswith("#"):
        # Konverter hex til rgba med opacity
        hex_color = color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {opacity})"
    
    return color


def build_plot_band(finding: AnalysisFinding) -> Optional[dict[str, Any]]:
    """
    Bygger plotBand-konfigurasjon for et periode-funn.
    """
    preset = get_plot_band_preset(finding.type.value)
    if not preset or not finding.time_range:
        return None
    
    start, end = finding.time_range
    
    return {
        "from": parse_date_to_timestamp(start),
        "to": parse_date_to_timestamp(end),
        "color": apply_opacity_to_color(preset["color"], finding.confidence),
        "zIndex": preset.get("z_index", 1),
        "label": {
            "text": format_label(finding.type.value, finding.description),
            "style": preset.get("label_style", {"color": "#ffffff", "fontSize": "10px"}),
            "align": "center",
            "verticalAlign": "top",
            "y": 10
        }
    }


def build_plot_line(finding: AnalysisFinding) -> Optional[dict[str, Any]]:
    """
    Bygger plotLine-konfigurasjon for et nivå-funn.
    """
    preset = get_plot_line_preset(finding.type.value)
    if not preset:
        return None
    
    # For nivåer bruker vi point_value som y-verdi
    if finding.point_value is None:
        return None
    
    return {
        "value": finding.point_value,
        "color": preset["color"],
        "width": preset.get("width", 2),
        "dashStyle": preset.get("dash_style", "Solid"),
        "zIndex": preset.get("z_index", 3),
        "label": {
            "text": format_label(finding.type.value, finding.description),
            "style": preset.get("label_style", {"color": "#ffffff", "fontSize": "10px"}),
            "align": "right"
        }
    }


def build_annotation(finding: AnalysisFinding) -> Optional[dict[str, Any]]:
    """
    Bygger annotation-konfigurasjon for et punkt-funn.
    """
    preset = get_annotation_preset(finding.type.value)
    if not preset or not finding.point_date:
        return None
    
    point_timestamp = parse_date_to_timestamp(finding.point_date)
    point_y = finding.point_value or 0
    
    return {
        "point": {
            "xAxis": 0,
            "yAxis": 0,
            "x": point_timestamp,
            "y": point_y
        },
        "text": format_label(finding.type.value, finding.description),
        "backgroundColor": preset["background_color"],
        "borderColor": preset["border_color"],
        "borderRadius": preset.get("border_radius", 4),
        "shape": preset.get("shape", "connector"),
        "style": preset.get("style", {"color": "#ffffff", "fontSize": "10px"}),
        "x": preset.get("x_offset", -50),
        "y": preset.get("y_offset", -30)
    }


def build_marker_point(finding: AnalysisFinding) -> Optional[dict[str, Any]]:
    """
    Bygger marker-punkt for et punkt-funn.
    Brukes for å legge til visuelle markører på serie-punkter.
    """
    preset = get_marker_preset(finding.type.value)
    if not preset or not finding.point_date:
        return None
    
    point_timestamp = parse_date_to_timestamp(finding.point_date)
    
    return {
        "x": point_timestamp,
        "y": finding.point_value,
        "marker": {
            "enabled": True,
            "radius": preset.get("radius", 8),
            "symbol": preset.get("symbol", "circle"),
            "fillColor": preset.get("fill_color"),
            "lineColor": preset.get("line_color"),
            "lineWidth": preset.get("line_width", 2)
        }
    }


def apply_findings_to_response(analysis: AnalysisResult) -> dict[str, Any]:
    """
    Hovedfunksjon: Konverterer AnalysisResult til Highcharts-konfigurasjoner.
    
    Args:
        analysis: Semantisk analyse-resultat fra LLM
        
    Returns:
        Dict med plotBands, plotLines, annotations og summary for frontend
    """
    plot_bands: list[dict] = []
    plot_lines_x: list[dict] = []  # X-axis (datoer)
    plot_lines_y: list[dict] = []  # Y-axis (verdier/nivåer)
    annotations: list[dict] = []
    marker_points: list[dict] = []
    
    for finding in analysis.findings:
        # Filtrer ut funn med for lav konfidensgrad
        if finding.confidence < CONFIDENCE_THRESHOLDS["show"]:
            continue
        
        finding_type = finding.type.value
        
        # Periode-funn → plotBand
        if is_period_finding(finding_type):
            band = build_plot_band(finding)
            if band:
                plot_bands.append(band)
        
        # Nivå-funn → plotLine (Y-akse)
        elif is_level_finding(finding_type):
            line = build_plot_line(finding)
            if line:
                plot_lines_y.append(line)
        
        # Punkt-funn → annotation + marker
        elif is_point_finding(finding_type):
            ann = build_annotation(finding)
            if ann:
                annotations.append(ann)
            
            marker = build_marker_point(finding)
            if marker:
                marker_points.append(marker)
    
    return {
        "plotBands": plot_bands,
        "plotLinesX": plot_lines_x,  # Vertikale linjer på X-aksen
        "plotLinesY": plot_lines_y,  # Horisontale linjer på Y-aksen
        "annotations": annotations,
        "markerPoints": marker_points,
        "summary": analysis.summary,
        "overallTrend": analysis.overall_trend,
        "riskAssessment": analysis.risk_assessment,
        "findingsCount": len([f for f in analysis.findings if f.confidence >= CONFIDENCE_THRESHOLDS["show"]])
    }


def generate_chart_response(analysis: AnalysisResult) -> dict[str, Any]:
    """
    Wrapper-funksjon som genererer komplett respons for frontend.
    
    Inkluderer:
    - Highcharts-visualiseringer
    - Analyse-metadata
    - Formatert output
    """
    visualizations = apply_findings_to_response(analysis)
    
    # Beregn gjennomsnittlig konfidensgrad
    confidences = [f.confidence for f in analysis.findings]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
    
    return {
        # Highcharts-elementer
        "plotBands": visualizations["plotBands"],
        "plotLinesX": visualizations["plotLinesX"],
        "plotLinesY": visualizations["plotLinesY"],
        "annotations": visualizations["annotations"],
        "markerPoints": visualizations["markerPoints"],
        
        # Analyse-resultat
        "summary": analysis.summary,
        "overallTrend": analysis.overall_trend,
        "riskAssessment": analysis.risk_assessment,
        
        # Metadata
        "confidence": round(avg_confidence, 2),
        "findingsCount": visualizations["findingsCount"],
        
        # Raw findings for debugging/display
        "findings": [
            {
                "type": f.type.value,
                "confidence": f.confidence,
                "description": f.description,
                "timeRange": list(f.time_range) if f.time_range else None,
                "pointDate": f.point_date,
                "pointValue": f.point_value
            }
            for f in analysis.findings
            if f.confidence >= CONFIDENCE_THRESHOLDS["show"]
        ]
    }


# ==========================================
# TESTING
# ==========================================

if __name__ == "__main__":
    from analysis_schema import EXAMPLE_ANALYSIS
    
    print("Testing apply_findings...")
    print("=" * 60)
    
    result = generate_chart_response(EXAMPLE_ANALYSIS)
    
    import json
    print(json.dumps(result, indent=2, default=str))
