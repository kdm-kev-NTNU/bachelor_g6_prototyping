"""
Prediction Service for Highcharts-LLM Analyzer

Wrapper for TimesFM tidsserie-prediksjon tilpasset Highcharts data.
Konverterer mellom Highcharts format og pandas DataFrame.
"""

import os
import numpy as np
import pandas as pd
from typing import Optional, Tuple, List
from datetime import datetime, timedelta

# Fix Windows symlink issue for HuggingFace
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Prøv å importere timesfm
try:
    import timesfm
    TIMESFM_AVAILABLE = True
except ImportError:
    TIMESFM_AVAILABLE = False
    print("[INFO] TimesFM ikke installert. Bruker fallback-prediksjon.")


class ChartPredictionService:
    """
    Prediksjonstjeneste for Highcharts tidsseriedata.
    Bruker TimesFM eller fallback sesongbasert prediksjon.
    """
    
    def __init__(self, model_path: str = "google/timesfm-1.0-200m-pytorch"):
        """
        Initialiser prediction service.
        
        Args:
            model_path: HuggingFace model path for TimesFM
        """
        self.model_path = model_path
        self.model = None
        self.is_initialized = False
        
        if TIMESFM_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialiser TimesFM modellen."""
        try:
            from huggingface_hub import constants
            constants.HF_HUB_ENABLE_HF_TRANSFER = False
            
            self.model = timesfm.TimesFm(
                hparams=timesfm.TimesFmHparams(
                    backend="cpu",
                    per_core_batch_size=32,
                    horizon_len=128,
                ),
                checkpoint=timesfm.TimesFmCheckpoint(
                    huggingface_repo_id=self.model_path
                ),
            )
            self.is_initialized = True
            print(f"[OK] TimesFM modell lastet: {self.model_path}")
        except OSError as e:
            if "WinError 1314" in str(e):
                print("[WARN] Windows symlink-feil. Bruker fallback-prediksjon.")
            else:
                print(f"[WARN] Kunne ikke laste TimesFM: {e}")
            self.is_initialized = False
        except Exception as e:
            print(f"[WARN] TimesFM init feilet: {e}")
            self.is_initialized = False
    
    def predict_from_chart_data(
        self,
        series_data: List[List],
        forecast_horizon: int = 30,
        frequency: str = "D",
        scenario: Optional[str] = None
    ) -> dict:
        """
        Lag prediksjon fra Highcharts seriedata.
        
        Args:
            series_data: Liste med [timestamp, value] par fra Highcharts
            forecast_horizon: Antall perioder å predikere fremover
            frequency: 'D' for daglig, 'H' for time
            scenario: Valgfritt scenario - 'bullish', 'bearish', 'volatile'
        
        Returns:
            Dict med predictions, confidence bounds og metadata
        """
        # Konverter til pandas DataFrame
        df = self._chart_data_to_dataframe(series_data)
        
        if df is None or len(df) < 10:
            return self._empty_prediction_response("Utilstrekkelig data")
        
        # Kjør prediksjon
        if TIMESFM_AVAILABLE and self.is_initialized:
            predictions, metadata = self._timesfm_predict(df, forecast_horizon, frequency)
        else:
            predictions, metadata = self._fallback_predict(df, forecast_horizon, frequency)
        
        # Appliser scenario-modifikasjoner
        if scenario:
            predictions = self._apply_scenario(predictions, scenario)
        
        # Beregn konfidensintervall
        confidence = self._calculate_confidence_bounds(predictions, df)
        
        # Konverter til Highcharts-format
        return self._format_for_highcharts(predictions, confidence, metadata)
    
    def _chart_data_to_dataframe(self, series_data: List[List]) -> Optional[pd.DataFrame]:
        """Konverter Highcharts data til pandas DataFrame."""
        if not series_data:
            return None
        
        try:
            timestamps = []
            values = []
            
            for point in series_data:
                if len(point) >= 2 and point[1] is not None:
                    ts = point[0]
                    # Highcharts bruker millisekunder
                    if isinstance(ts, (int, float)):
                        dt = datetime.fromtimestamp(ts / 1000)
                    else:
                        dt = pd.to_datetime(ts)
                    timestamps.append(dt)
                    values.append(float(point[1]))
            
            if not timestamps:
                return None
            
            df = pd.DataFrame({
                'timestamp': timestamps,
                'value': values
            })
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"[ERROR] Kunne ikke konvertere data: {e}")
            return None
    
    def _timesfm_predict(
        self,
        df: pd.DataFrame,
        forecast_horizon: int,
        frequency: str
    ) -> Tuple[pd.DataFrame, dict]:
        """Kjør TimesFM prediksjon."""
        try:
            values = df["value"].values.astype(np.float32)
            
            # Kjør prediksjon
            freq_map = {"H": 0, "D": 1, "W": 2, "M": 3}
            forecast, _ = self.model.forecast(
                [values],
                freq=[freq_map.get(frequency, 1)],
            )
            
            # Lag predictions DataFrame
            last_timestamp = df["timestamp"].iloc[-1]
            freq_delta = timedelta(hours=1) if frequency == "H" else timedelta(days=1)
            
            future_timestamps = [
                last_timestamp + freq_delta * (i + 1)
                for i in range(min(forecast_horizon, len(forecast[0])))
            ]
            
            predictions = pd.DataFrame({
                "timestamp": future_timestamps,
                "predicted_value": forecast[0][:forecast_horizon]
            })
            
            metadata = {
                "model": self.model_path,
                "method": "timesfm",
                "horizon": forecast_horizon,
                "frequency": frequency,
                "context_length": len(values)
            }
            
            return predictions, metadata
            
        except Exception as e:
            print(f"[WARN] TimesFM prediksjon feilet: {e}")
            return self._fallback_predict(df, forecast_horizon, frequency)
    
    def _fallback_predict(
        self,
        df: pd.DataFrame,
        forecast_horizon: int,
        frequency: str
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Fallback prediksjon basert på trend og sesongmønster.
        Brukes når TimesFM ikke er tilgjengelig.
        """
        values = df["value"].values
        
        # Beregn lineær trend
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        trend_slope = coeffs[0]
        trend_intercept = coeffs[1]
        
        # Beregn sesongmønster (siste 7 eller 24 perioder)
        season_length = 7 if frequency == "D" else 24
        if len(values) >= season_length * 2:
            seasonal_values = values[-(season_length * 2):]
            seasonal_pattern = np.array([
                np.mean(seasonal_values[i::season_length])
                for i in range(season_length)
            ])
            seasonal_pattern = seasonal_pattern - np.mean(seasonal_pattern)
        else:
            seasonal_pattern = np.zeros(season_length)
        
        # Generer prediksjoner
        last_timestamp = df["timestamp"].iloc[-1]
        freq_delta = timedelta(hours=1) if frequency == "H" else timedelta(days=1)
        
        predictions_list = []
        base_idx = len(values)
        
        for i in range(forecast_horizon):
            # Trend-komponent
            trend_value = trend_slope * (base_idx + i) + trend_intercept
            
            # Sesong-komponent
            seasonal_value = seasonal_pattern[i % season_length]
            
            # Kombiner med litt støy
            noise = np.random.normal(0, np.std(values) * 0.05)
            pred_value = trend_value + seasonal_value + noise
            
            # Sørg for positiv verdi hvis originale data er positive
            if np.min(values) > 0:
                pred_value = max(pred_value, np.min(values) * 0.5)
            
            predictions_list.append({
                "timestamp": last_timestamp + freq_delta * (i + 1),
                "predicted_value": pred_value
            })
        
        predictions = pd.DataFrame(predictions_list)
        
        metadata = {
            "model": "fallback_trend_seasonal",
            "method": "linear_trend_with_seasonality",
            "horizon": forecast_horizon,
            "frequency": frequency,
            "context_length": len(values),
            "trend_slope": float(trend_slope),
            "note": "TimesFM ikke tilgjengelig, bruker fallback"
        }
        
        return predictions, metadata
    
    def _apply_scenario(
        self,
        predictions: pd.DataFrame,
        scenario: str
    ) -> pd.DataFrame:
        """Appliser scenario-modifikasjoner på prediksjonene."""
        df = predictions.copy()
        values = df["predicted_value"].values
        
        if scenario == "bullish":
            # Øk trenden med 20%
            growth = np.linspace(1.0, 1.2, len(values))
            df["predicted_value"] = values * growth
            
        elif scenario == "bearish":
            # Reduser trenden med 20%
            decline = np.linspace(1.0, 0.8, len(values))
            df["predicted_value"] = values * decline
            
        elif scenario == "volatile":
            # Legg til høyere volatilitet
            volatility = np.random.normal(1.0, 0.15, len(values))
            df["predicted_value"] = values * volatility
        
        return df
    
    def _calculate_confidence_bounds(
        self,
        predictions: pd.DataFrame,
        historical_df: pd.DataFrame
    ) -> dict:
        """Beregn konfidensintervall basert på historisk volatilitet."""
        hist_std = historical_df["value"].std()
        pred_values = predictions["predicted_value"].values
        
        # Øk usikkerhet over tid
        uncertainty_growth = np.linspace(1.0, 2.0, len(pred_values))
        
        upper = pred_values + (hist_std * 1.96 * uncertainty_growth)
        lower = pred_values - (hist_std * 1.96 * uncertainty_growth)
        
        # Sørg for at lower ikke går under 0 hvis originale verdier er positive
        if historical_df["value"].min() > 0:
            lower = np.maximum(lower, 0)
        
        return {
            "upper": upper.tolist(),
            "lower": lower.tolist()
        }
    
    def _format_for_highcharts(
        self,
        predictions: pd.DataFrame,
        confidence: dict,
        metadata: dict
    ) -> dict:
        """Formater output for Highcharts."""
        # Hovedprediksjoner som [[timestamp_ms, value], ...]
        prediction_series = [
            [int(row["timestamp"].timestamp() * 1000), round(row["predicted_value"], 2)]
            for _, row in predictions.iterrows()
        ]
        
        # Konfidensintervall som [[timestamp_ms, low, high], ...]
        confidence_range = [
            [
                int(predictions.iloc[i]["timestamp"].timestamp() * 1000),
                round(confidence["lower"][i], 2),
                round(confidence["upper"][i], 2)
            ]
            for i in range(len(predictions))
        ]
        
        return {
            "predictions": prediction_series,
            "confidenceRange": confidence_range,
            "metadata": metadata,
            "success": True
        }
    
    def _empty_prediction_response(self, reason: str) -> dict:
        """Returner tom respons ved feil."""
        return {
            "predictions": [],
            "confidenceRange": [],
            "metadata": {"error": reason},
            "success": False
        }
    
    def analyze_prediction(
        self,
        historical_data: List[List],
        prediction_result: dict
    ) -> dict:
        """
        Analyser prediksjonen og generer innsikt.
        """
        if not prediction_result.get("success") or not prediction_result.get("predictions"):
            return {"insights": ["Ingen prediksjon tilgjengelig"]}
        
        # Konverter historisk data
        hist_values = [p[1] for p in historical_data if p[1] is not None]
        pred_values = [p[1] for p in prediction_result["predictions"]]
        
        if not hist_values or not pred_values:
            return {"insights": ["Utilstrekkelig data for analyse"]}
        
        hist_mean = np.mean(hist_values)
        hist_last = hist_values[-1]
        pred_mean = np.mean(pred_values)
        pred_last = pred_values[-1]
        
        insights = []
        
        # Trend-analyse
        change_from_last = ((pred_last - hist_last) / hist_last) * 100 if hist_last != 0 else 0
        
        if change_from_last > 10:
            insights.append(f"Prognosen indikerer en oppgang på {change_from_last:.1f}% fra nåværende nivå")
        elif change_from_last < -10:
            insights.append(f"Prognosen indikerer en nedgang på {abs(change_from_last):.1f}% fra nåværende nivå")
        else:
            insights.append("Prognosen viser relativt stabile verdier fremover")
        
        # Volatilitet
        pred_std = np.std(pred_values)
        hist_std = np.std(hist_values)
        
        if pred_std > hist_std * 1.5:
            insights.append("Forventet høyere volatilitet i prognoseperioden")
        elif pred_std < hist_std * 0.7:
            insights.append("Forventet lavere volatilitet i prognoseperioden")
        
        # Konfidensintervall
        if prediction_result.get("confidenceRange"):
            last_range = prediction_result["confidenceRange"][-1]
            spread = last_range[2] - last_range[1]
            spread_pct = (spread / pred_last) * 100 if pred_last != 0 else 0
            insights.append(f"Usikkerhetsmargin ved slutten av perioden: ±{spread_pct/2:.1f}%")
        
        return {
            "insights": insights,
            "stats": {
                "historical_mean": round(hist_mean, 2),
                "predicted_mean": round(pred_mean, 2),
                "change_percent": round(change_from_last, 2),
                "method": prediction_result.get("metadata", {}).get("method", "unknown")
            }
        }


def create_prediction_service() -> ChartPredictionService:
    """Factory function for prediction service."""
    return ChartPredictionService()


if __name__ == "__main__":
    # Test
    print("Tester ChartPredictionService...")
    
    # Generer test-data (simulerer Highcharts format)
    import random
    base_time = datetime(2024, 1, 1).timestamp() * 1000
    test_data = []
    price = 100
    
    for i in range(365):
        ts = base_time + (i * 24 * 60 * 60 * 1000)
        price = price * (1 + random.uniform(-0.02, 0.025))
        test_data.append([ts, price])
    
    service = create_prediction_service()
    result = service.predict_from_chart_data(
        test_data,
        forecast_horizon=30,
        frequency="D"
    )
    
    print(f"\nMetadata: {result['metadata']}")
    print(f"Antall prediksjoner: {len(result['predictions'])}")
    
    if result['predictions']:
        print(f"Første prediksjon: {result['predictions'][0]}")
        print(f"Siste prediksjon: {result['predictions'][-1]}")
    
    # Test analyse
    analysis = service.analyze_prediction(test_data, result)
    print(f"\nInnsikt:")
    for insight in analysis.get("insights", []):
        print(f"  - {insight}")
