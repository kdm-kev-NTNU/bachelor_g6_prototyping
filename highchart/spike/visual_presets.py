"""
Deterministiske Visualiseringspresets for Highcharts

Mapper semantiske funn-typer til konkrete Highcharts-konfigurasjoner.
All visualiseringslogikk er samlet her - LLM vet INGENTING om dette.

Endringer i visualisering gjøres KUN her, ikke i LLM-prompts.
"""

from typing import TypedDict, Optional


# ==========================================
# TYPE DEFINITIONS
# ==========================================

class PlotBandPreset(TypedDict, total=False):
    """Preset for plotBand visualisering"""
    color: str
    label_text: str
    label_style: dict
    border_color: str
    border_width: int
    z_index: int


class PlotLinePreset(TypedDict, total=False):
    """Preset for plotLine visualisering"""
    color: str
    width: int
    dash_style: str
    label_text: str
    label_style: dict
    z_index: int


class AnnotationPreset(TypedDict, total=False):
    """Preset for annotation visualisering"""
    background_color: str
    border_color: str
    border_radius: int
    shape: str
    style: dict
    x_offset: int
    y_offset: int
    symbol: str
    symbol_size: int


class MarkerPreset(TypedDict, total=False):
    """Preset for serie-markers"""
    enabled: bool
    radius: int
    symbol: str
    fill_color: str
    line_color: str
    line_width: int


# ==========================================
# FARGEKODER
# ==========================================

COLORS = {
    # Trends
    "bullish": "#00ff88",          # Bright green
    "bullish_bg": "rgba(0, 255, 136, 0.12)",
    "bearish": "#ff4466",          # Bright red
    "bearish_bg": "rgba(255, 68, 102, 0.12)",
    "neutral": "#8888aa",          # Muted gray
    "neutral_bg": "rgba(136, 136, 170, 0.08)",
    
    # Volatility
    "high_volatility": "#ffaa00",   # Orange/warning
    "high_volatility_bg": "rgba(255, 170, 0, 0.12)",
    "low_volatility": "#00d4ff",    # Cyan/calm
    "low_volatility_bg": "rgba(0, 212, 255, 0.08)",
    
    # Events/Points
    "peak": "#ff00aa",              # Magenta
    "dip": "#00aaff",               # Blue
    "breakout": "#b4ff00",          # Lime
    "event": "#ff6b35",             # Orange
    "gap": "#9b59b6",               # Purple
    
    # Levels
    "support": "#00ff88",           # Green
    "resistance": "#ff4466",        # Red
    
    # Patterns
    "pattern": "#f39c12",           # Gold
}


# ==========================================
# PLOT BAND PRESETS (for perioder)
# ==========================================

PLOT_BAND_PRESETS: dict[str, PlotBandPreset] = {
    "BULLISH_TREND": {
        "color": COLORS["bullish_bg"],
        "label_text": "📈 Bullish",
        "label_style": {"color": COLORS["bullish"], "fontSize": "10px", "fontWeight": "600"},
        "z_index": 1
    },
    "BEARISH_TREND": {
        "color": COLORS["bearish_bg"],
        "label_text": "📉 Bearish",
        "label_style": {"color": COLORS["bearish"], "fontSize": "10px", "fontWeight": "600"},
        "z_index": 1
    },
    "CONSOLIDATION": {
        "color": COLORS["neutral_bg"],
        "label_text": "↔️ Konsolidering",
        "label_style": {"color": COLORS["neutral"], "fontSize": "10px"},
        "z_index": 1
    },
    "HIGH_VOLATILITY": {
        "color": COLORS["high_volatility_bg"],
        "label_text": "⚡ Høy volatilitet",
        "label_style": {"color": COLORS["high_volatility"], "fontSize": "10px", "fontWeight": "600"},
        "z_index": 2
    },
    "LOW_VOLATILITY": {
        "color": COLORS["low_volatility_bg"],
        "label_text": "〰️ Lav volatilitet",
        "label_style": {"color": COLORS["low_volatility"], "fontSize": "10px"},
        "z_index": 1
    }
}


# ==========================================
# PLOT LINE PRESETS (for nivåer)
# ==========================================

PLOT_LINE_PRESETS: dict[str, PlotLinePreset] = {
    "SUPPORT_LEVEL": {
        "color": COLORS["support"],
        "width": 2,
        "dash_style": "Dash",
        "label_text": "Støtte",
        "label_style": {"color": COLORS["support"], "fontSize": "10px"},
        "z_index": 3
    },
    "RESISTANCE_LEVEL": {
        "color": COLORS["resistance"],
        "width": 2,
        "dash_style": "Dash",
        "label_text": "Motstand",
        "label_style": {"color": COLORS["resistance"], "fontSize": "10px"},
        "z_index": 3
    }
}


# ==========================================
# ANNOTATION PRESETS (for punkthendelser)
# ==========================================

ANNOTATION_PRESETS: dict[str, AnnotationPreset] = {
    "UNUSUAL_PEAK": {
        "background_color": COLORS["peak"],
        "border_color": COLORS["peak"],
        "border_radius": 4,
        "shape": "connector",
        "style": {"color": "#ffffff", "fontSize": "10px", "fontWeight": "bold"},
        "x_offset": -60,
        "y_offset": -35,
        "symbol": "triangle",
        "symbol_size": 8
    },
    "UNUSUAL_DIP": {
        "background_color": COLORS["dip"],
        "border_color": COLORS["dip"],
        "border_radius": 4,
        "shape": "connector",
        "style": {"color": "#ffffff", "fontSize": "10px", "fontWeight": "bold"},
        "x_offset": -60,
        "y_offset": 35,
        "symbol": "triangle-down",
        "symbol_size": 8
    },
    "BREAKOUT": {
        "background_color": COLORS["breakout"],
        "border_color": COLORS["breakout"],
        "border_radius": 4,
        "shape": "connector",
        "style": {"color": "#000000", "fontSize": "10px", "fontWeight": "bold"},
        "x_offset": -70,
        "y_offset": -30,
        "symbol": "diamond",
        "symbol_size": 10
    },
    "SIGNIFICANT_EVENT": {
        "background_color": COLORS["event"],
        "border_color": COLORS["event"],
        "border_radius": 4,
        "shape": "connector",
        "style": {"color": "#ffffff", "fontSize": "10px", "fontWeight": "bold"},
        "x_offset": -80,
        "y_offset": -40,
        "symbol": "circle",
        "symbol_size": 8
    },
    "PRICE_GAP": {
        "background_color": COLORS["gap"],
        "border_color": COLORS["gap"],
        "border_radius": 4,
        "shape": "connector",
        "style": {"color": "#ffffff", "fontSize": "10px"},
        "x_offset": -50,
        "y_offset": -25,
        "symbol": "square",
        "symbol_size": 6
    },
    "DOUBLE_TOP": {
        "background_color": COLORS["pattern"],
        "border_color": COLORS["pattern"],
        "border_radius": 4,
        "shape": "connector",
        "style": {"color": "#000000", "fontSize": "10px", "fontWeight": "bold"},
        "x_offset": -70,
        "y_offset": -35,
        "symbol": "triangle",
        "symbol_size": 8
    },
    "DOUBLE_BOTTOM": {
        "background_color": COLORS["pattern"],
        "border_color": COLORS["pattern"],
        "border_radius": 4,
        "shape": "connector",
        "style": {"color": "#000000", "fontSize": "10px", "fontWeight": "bold"},
        "x_offset": -70,
        "y_offset": 35,
        "symbol": "triangle-down",
        "symbol_size": 8
    }
}


# ==========================================
# MARKER PRESETS (for serie-punkter)
# ==========================================

MARKER_PRESETS: dict[str, MarkerPreset] = {
    "UNUSUAL_PEAK": {
        "enabled": True,
        "radius": 8,
        "symbol": "triangle",
        "fill_color": COLORS["peak"],
        "line_color": "#ffffff",
        "line_width": 2
    },
    "UNUSUAL_DIP": {
        "enabled": True,
        "radius": 8,
        "symbol": "triangle-down",
        "fill_color": COLORS["dip"],
        "line_color": "#ffffff",
        "line_width": 2
    },
    "BREAKOUT": {
        "enabled": True,
        "radius": 10,
        "symbol": "diamond",
        "fill_color": COLORS["breakout"],
        "line_color": "#000000",
        "line_width": 2
    },
    "SIGNIFICANT_EVENT": {
        "enabled": True,
        "radius": 8,
        "symbol": "circle",
        "fill_color": COLORS["event"],
        "line_color": "#ffffff",
        "line_width": 2
    }
}


# ==========================================
# LABEL TEMPLATES
# ==========================================

LABEL_TEMPLATES: dict[str, str] = {
    "BULLISH_TREND": "📈 {description}",
    "BEARISH_TREND": "📉 {description}",
    "CONSOLIDATION": "↔️ {description}",
    "UNUSUAL_PEAK": "⬆️ {description}",
    "UNUSUAL_DIP": "⬇️ {description}",
    "BREAKOUT": "🚀 {description}",
    "HIGH_VOLATILITY": "⚡ {description}",
    "LOW_VOLATILITY": "〰️ {description}",
    "SIGNIFICANT_EVENT": "⭐ {description}",
    "PRICE_GAP": "🔲 {description}",
    "SUPPORT_LEVEL": "🟢 {description}",
    "RESISTANCE_LEVEL": "🔴 {description}",
    "DOUBLE_TOP": "🔻🔻 {description}",
    "DOUBLE_BOTTOM": "🔺🔺 {description}"
}


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_plot_band_preset(finding_type: str) -> Optional[PlotBandPreset]:
    """Henter plotBand-preset for en funn-type"""
    return PLOT_BAND_PRESETS.get(finding_type)


def get_plot_line_preset(finding_type: str) -> Optional[PlotLinePreset]:
    """Henter plotLine-preset for en funn-type"""
    return PLOT_LINE_PRESETS.get(finding_type)


def get_annotation_preset(finding_type: str) -> Optional[AnnotationPreset]:
    """Henter annotation-preset for en funn-type"""
    return ANNOTATION_PRESETS.get(finding_type)


def get_marker_preset(finding_type: str) -> Optional[MarkerPreset]:
    """Henter marker-preset for en funn-type"""
    return MARKER_PRESETS.get(finding_type)


def format_label(finding_type: str, description: str = "") -> str:
    """Formaterer label-tekst basert på funn-type"""
    template = LABEL_TEMPLATES.get(finding_type, "{description}")
    return template.format(description=description or finding_type.replace("_", " ").title())


def is_period_finding(finding_type: str) -> bool:
    """Sjekker om funn-typen representerer en periode (bruker plotBand)"""
    return finding_type in PLOT_BAND_PRESETS


def is_point_finding(finding_type: str) -> bool:
    """Sjekker om funn-typen representerer et punkt (bruker annotation)"""
    return finding_type in ANNOTATION_PRESETS


def is_level_finding(finding_type: str) -> bool:
    """Sjekker om funn-typen representerer et nivå (bruker plotLine)"""
    return finding_type in PLOT_LINE_PRESETS


# ==========================================
# CONFIDENCE THRESHOLDS
# ==========================================

# Minimums-konfidensgrad for å vise et funn
CONFIDENCE_THRESHOLDS = {
    "show": 0.5,           # Vis funnet
    "highlight": 0.7,      # Fremhev funnet
    "emphasize": 0.85      # Sterk vektlegging
}


def get_opacity_for_confidence(confidence: float) -> float:
    """
    Returnerer opacity-verdi basert på konfidensgrad.
    Høyere konfidensgrad = mer synlig.
    """
    if confidence >= CONFIDENCE_THRESHOLDS["emphasize"]:
        return 1.0
    elif confidence >= CONFIDENCE_THRESHOLDS["highlight"]:
        return 0.8
    elif confidence >= CONFIDENCE_THRESHOLDS["show"]:
        return 0.6
    else:
        return 0.4


if __name__ == "__main__":
    print("Visual Presets Test")
    print("=" * 50)
    print(f"\nPlotBand types: {list(PLOT_BAND_PRESETS.keys())}")
    print(f"PlotLine types: {list(PLOT_LINE_PRESETS.keys())}")
    print(f"Annotation types: {list(ANNOTATION_PRESETS.keys())}")
    print(f"Marker types: {list(MARKER_PRESETS.keys())}")
    print(f"\nExample label: {format_label('BULLISH_TREND', 'Sterk oppgang')}")
