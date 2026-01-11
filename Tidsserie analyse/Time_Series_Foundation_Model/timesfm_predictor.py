"""
TimesFM Predictor Module

Wrapper for Google TimesFM time series foundation model.
Brukes for å predikere fremtidig energiforbruk basert på historiske data.
"""

import os
import numpy as np
import pandas as pd
from typing import Optional, Tuple, List
from datetime import datetime, timedelta

# Fix Windows symlink issue for HuggingFace
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Prøv å importere timesfm, fall tilbake til mock hvis ikke tilgjengelig
try:
    import timesfm
    TIMESFM_AVAILABLE = True
except ImportError:
    TIMESFM_AVAILABLE = False
    print("TimesFM ikke installert. Bruker fallback-prediksjon.")


class TimesFMPredictor:
    """
    Wrapper klasse for Google TimesFM modellen.
    """
    
    def __init__(self, model_path: str = "google/timesfm-1.0-200m-pytorch"):
        """
        Initialiser TimesFM prediktor.
        
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
            # Disable symlinks for Windows compatibility
            from huggingface_hub import constants
            constants.HF_HUB_ENABLE_HF_TRANSFER = False
            
            # TimesFM 1.2+ bruker forenklet API
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
            print(f"TimesFM modell lastet: {self.model_path}")
        except OSError as e:
            # Windows symlink error - bruk fallback
            if "WinError 1314" in str(e):
                print("Windows symlink-feil. Bruker fallback-prediksjon.")
                print("Tips: Aktiver Developer Mode i Windows for full TimesFM-støtte.")
            else:
                print(f"Kunne ikke laste TimesFM modell: {e}")
            self.is_initialized = False
        except Exception as e:
            print(f"Kunne ikke laste TimesFM modell: {e}")
            self.is_initialized = False
    
    def predict(
        self,
        historical_data: pd.DataFrame,
        forecast_horizon: int = 24,
        frequency: str = "H"
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Lag prediksjon basert på historiske data.
        
        Args:
            historical_data: DataFrame med 'timestamp' og 'consumption_kwh' kolonner
            forecast_horizon: Antall tidspunkter å predikere fremover
            frequency: Tidsfrekvens ('H' for time, 'D' for dag)
        
        Returns:
            Tuple med (predictions DataFrame, metadata dict)
        """
        if not TIMESFM_AVAILABLE or not self.is_initialized:
            return self._fallback_predict(historical_data, forecast_horizon, frequency)
        
        try:
            # Forbered data for TimesFM
            values = historical_data["consumption_kwh"].values.astype(np.float32)
            
            # Kjør prediksjon
            forecast, _ = self.model.forecast(
                [values],
                freq=[self._get_timesfm_freq(frequency)],
            )
            
            # Lag predictions DataFrame
            last_timestamp = historical_data["timestamp"].iloc[-1]
            freq_delta = timedelta(hours=1) if frequency == "h" else timedelta(days=1)
            
            future_timestamps = [
                last_timestamp + freq_delta * (i + 1) 
                for i in range(min(forecast_horizon, len(forecast[0])))
            ]
            
            predictions = pd.DataFrame({
                "timestamp": future_timestamps,
                "predicted_kwh": forecast[0][:forecast_horizon],
                "type": "forecast"
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
            print(f"TimesFM prediksjon feilet: {e}")
            return self._fallback_predict(historical_data, forecast_horizon, frequency)
    
    def _fallback_predict(
        self,
        historical_data: pd.DataFrame,
        forecast_horizon: int,
        frequency: str
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Fallback-prediksjon når TimesFM ikke er tilgjengelig.
        Bruker sesongbasert gjennomsnitt med trend.
        """
        values = historical_data["consumption_kwh"].values
        
        # Beregn sesongmønster (24 timer eller 7 dager)
        season_length = 24 if frequency == "h" else 7
        n_complete_seasons = len(values) // season_length
        
        if n_complete_seasons > 0:
            # Beregn gjennomsnittlig sesongmønster
            seasonal_values = values[-(n_complete_seasons * season_length):]
            seasonal_pattern = np.array([
                np.mean(seasonal_values[i::season_length])
                for i in range(season_length)
            ])
        else:
            seasonal_pattern = np.full(season_length, np.mean(values))
        
        # Enkel trend (lineær)
        if len(values) > season_length:
            recent_mean = np.mean(values[-season_length:])
            older_mean = np.mean(values[-2*season_length:-season_length]) if len(values) > 2*season_length else recent_mean
            trend = (recent_mean - older_mean) / season_length
        else:
            trend = 0
        
        # Generer prediksjoner
        last_timestamp = historical_data["timestamp"].iloc[-1]
        freq_delta = timedelta(hours=1) if frequency == "h" else timedelta(days=1)
        
        predictions_list = []
        for i in range(forecast_horizon):
            idx = i % season_length
            pred_value = seasonal_pattern[idx] + trend * (i + 1)
            # Legg til litt usikkerhet
            pred_value *= (1 + np.random.normal(0, 0.05))
            pred_value = max(0.1, pred_value)  # Alltid positiv
            
            predictions_list.append({
                "timestamp": last_timestamp + freq_delta * (i + 1),
                "predicted_kwh": pred_value,
                "type": "forecast"
            })
        
        predictions = pd.DataFrame(predictions_list)
        
        metadata = {
            "model": "fallback_seasonal",
            "method": "seasonal_decomposition",
            "horizon": forecast_horizon,
            "frequency": frequency,
            "context_length": len(values),
            "note": "TimesFM ikke tilgjengelig, bruker sesongbasert fallback"
        }
        
        return predictions, metadata
    
    def _get_timesfm_freq(self, frequency: str) -> int:
        """Konverter pandas frequency til TimesFM frequency."""
        freq_map = {
            "H": 0,   # Hourly
            "D": 1,   # Daily
            "W": 2,   # Weekly
            "M": 3,   # Monthly
        }
        return freq_map.get(frequency, 0)
    
    def analyze_prediction(
        self,
        historical_data: pd.DataFrame,
        predictions: pd.DataFrame
    ) -> dict:
        """
        Analyser prediksjonene og generer innsikt.
        
        Args:
            historical_data: Historiske data
            predictions: Prediksjoner
        
        Returns:
            Dict med analyse og innsikt
        """
        hist_values = historical_data["consumption_kwh"].values
        pred_values = predictions["predicted_kwh"].values
        
        # Beregn statistikk
        hist_mean = np.mean(hist_values)
        hist_std = np.std(hist_values)
        pred_mean = np.mean(pred_values)
        pred_sum = np.sum(pred_values)
        
        # Trend analyse
        if len(predictions) > 1:
            trend_direction = "økende" if pred_values[-1] > pred_values[0] else "synkende"
            trend_change = ((pred_values[-1] - pred_values[0]) / pred_values[0]) * 100
        else:
            trend_direction = "stabil"
            trend_change = 0
        
        # Sammenlign med historikk
        change_from_hist = ((pred_mean - hist_mean) / hist_mean) * 100
        
        analysis = {
            "historical": {
                "mean_kwh": round(hist_mean, 2),
                "std_kwh": round(hist_std, 2),
                "total_kwh": round(np.sum(hist_values), 2)
            },
            "forecast": {
                "mean_kwh": round(pred_mean, 2),
                "total_kwh": round(pred_sum, 2),
                "min_kwh": round(np.min(pred_values), 2),
                "max_kwh": round(np.max(pred_values), 2)
            },
            "comparison": {
                "change_percent": round(change_from_hist, 1),
                "trend_direction": trend_direction,
                "trend_change_percent": round(trend_change, 1)
            },
            "insights": self._generate_insights(change_from_hist, trend_direction, pred_values)
        }
        
        return analysis
    
    def _generate_insights(
        self,
        change_percent: float,
        trend: str,
        predictions: np.ndarray
    ) -> List[str]:
        """Generer tekstbaserte innsikter fra analysen."""
        insights = []
        
        if change_percent > 10:
            insights.append(f"Forventet forbruk er {abs(change_percent):.0f}% høyere enn historisk gjennomsnitt.")
        elif change_percent < -10:
            insights.append(f"Forventet forbruk er {abs(change_percent):.0f}% lavere enn historisk gjennomsnitt.")
        else:
            insights.append("Forventet forbruk er relativt stabilt sammenlignet med historikk.")
        
        if trend == "økende":
            insights.append("Trenden viser økende forbruk i prognoseperioden.")
        elif trend == "synkende":
            insights.append("Trenden viser synkende forbruk i prognoseperioden.")
        
        # Identifiser potensielle topper
        mean_pred = np.mean(predictions)
        high_periods = np.where(predictions > mean_pred * 1.3)[0]
        if len(high_periods) > 0:
            insights.append(f"Det forventes {len(high_periods)} perioder med høyt forbruk.")
        
        return insights


def create_predictor() -> TimesFMPredictor:
    """Factory function for å opprette prediktor."""
    return TimesFMPredictor()


if __name__ == "__main__":
    # Test prediktor
    from data_generator import generate_yearly_energy_data
    
    print("Tester TimesFM prediktor...")
    
    # Generer testdata
    data = generate_yearly_energy_data(2025, frequency="H")
    
    # Bruk siste 7 dager som historikk
    historical = data.tail(168)  # 7 dager * 24 timer
    
    # Lag prediksjon
    predictor = create_predictor()
    predictions, metadata = predictor.predict(historical, forecast_horizon=48, frequency="h")
    
    print(f"\nMetadata: {metadata}")
    print(f"\nPrediksjoner ({len(predictions)} timer):")
    print(predictions.head(10))
    
    # Analyser
    analysis = predictor.analyze_prediction(historical, predictions)
    print(f"\nAnalyse:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")
