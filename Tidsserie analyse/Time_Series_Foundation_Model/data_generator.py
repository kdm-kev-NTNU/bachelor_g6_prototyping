"""
Syntetisk Energidata Generator

Genererer realistiske energiforbruksdata for et norsk hus i 2025 med:
- Sesongvariasjoner (høyere forbruk om vinteren)
- Daglige mønstre (morgen/kveld topper)
- Ukentlige mønstre (helg vs. ukedag)
- Tilfeldige variasjoner
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def generate_yearly_energy_data(
    year: int = 2025,
    base_consumption_kwh: float = 15.0,
    frequency: str = "h",
    seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Genererer syntetiske energiforbruksdata for et helt år.
    
    Args:
        year: År for datagenereringen
        base_consumption_kwh: Gjennomsnittlig daglig forbruk i kWh
        frequency: Dataooppløsning ('H' for time, 'D' for dag)
        seed: Random seed for reproduserbarhet
    
    Returns:
        DataFrame med tidsstempel og energiforbruk
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generer tidsstempel for hele året
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31 23:00:00" if frequency == "h" else f"{year}-12-31"
    timestamps = pd.date_range(start=start_date, end=end_date, freq=frequency)
    
    n_points = len(timestamps)
    consumption = np.zeros(n_points)
    
    for i, ts in enumerate(timestamps):
        # 1. Sesongvariasjon (høyere om vinteren i Norge)
        day_of_year = ts.dayofyear
        # Vintersesong: høyest i januar, lavest i juli
        seasonal_factor = 1.0 + 0.5 * np.cos(2 * np.pi * (day_of_year - 15) / 365)
        
        # 2. Daglig mønster (hvis timesoppløsning)
        if frequency == "h":
            hour = ts.hour
            # Morgentopp (7-9) og kveldstopp (17-21)
            if 7 <= hour <= 9:
                hourly_factor = 1.3 + 0.2 * np.sin(np.pi * (hour - 7) / 2)
            elif 17 <= hour <= 21:
                hourly_factor = 1.4 + 0.3 * np.sin(np.pi * (hour - 17) / 4)
            elif 0 <= hour <= 5:
                hourly_factor = 0.4  # Natt - lavt forbruk
            elif 10 <= hour <= 15:
                hourly_factor = 0.7  # Midt på dagen - folk på jobb
            else:
                hourly_factor = 0.9
        else:
            hourly_factor = 1.0
        
        # 3. Ukentlig mønster
        day_of_week = ts.dayofweek
        if day_of_week >= 5:  # Helg
            weekly_factor = 1.15  # Mer hjemme = høyere forbruk
        else:
            weekly_factor = 0.95
        
        # 4. Temperatureffekt (simulert)
        # Kaldere = høyere forbruk (oppvarming)
        temp_effect = 0.3 * np.cos(2 * np.pi * (day_of_year - 15) / 365)
        
        # 5. Tilfeldig variasjon
        noise = np.random.normal(0, 0.15)
        
        # Kombiner alle faktorer
        base = base_consumption_kwh / 24 if frequency == "h" else base_consumption_kwh
        consumption[i] = base * seasonal_factor * hourly_factor * weekly_factor * (1 + temp_effect + noise)
        
        # Sørg for at forbruk er positivt
        consumption[i] = max(0.1, consumption[i])
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "consumption_kwh": consumption
    })
    
    # Legg til nyttige kolonner
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["month"] = df["timestamp"].dt.month
    df["is_weekend"] = df["day_of_week"] >= 5
    
    return df


def generate_daily_summary(hourly_data: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregerer timedata til daglige sammendrag.
    
    Args:
        hourly_data: DataFrame med timebaserte data
    
    Returns:
        DataFrame med daglige aggregeringer
    """
    daily = hourly_data.groupby("date").agg({
        "consumption_kwh": ["sum", "mean", "max", "min"],
        "is_weekend": "first",
        "month": "first"
    }).reset_index()
    
    # Flatten column names
    daily.columns = [
        "date", "total_kwh", "avg_kwh", "max_kwh", "min_kwh", 
        "is_weekend", "month"
    ]
    
    return daily


def get_monthly_statistics(hourly_data: pd.DataFrame) -> pd.DataFrame:
    """
    Beregner månedlig statistikk.
    
    Args:
        hourly_data: DataFrame med timebaserte data
    
    Returns:
        DataFrame med månedlig statistikk
    """
    monthly = hourly_data.groupby("month").agg({
        "consumption_kwh": ["sum", "mean", "std"]
    }).reset_index()
    
    monthly.columns = ["month", "total_kwh", "avg_hourly_kwh", "std_kwh"]
    
    # Legg til månedsnavn
    month_names = [
        "Januar", "Februar", "Mars", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Desember"
    ]
    monthly["month_name"] = monthly["month"].apply(lambda x: month_names[x-1])
    
    return monthly


def generate_scenario_data(
    base_data: pd.DataFrame,
    scenario: str = "normal",
    reduction_percent: float = 10.0
) -> pd.DataFrame:
    """
    Genererer scenariodata basert på ulike tiltak.
    
    Args:
        base_data: Originale energidata
        scenario: Type scenario ('normal', 'reduced_heating', 'smart_home', 'solar')
        reduction_percent: Prosentvis reduksjon for enkle scenarioer
    
    Returns:
        DataFrame med modifiserte data
    """
    scenario_data = base_data.copy()
    
    if scenario == "reduced_heating":
        # Reduser vinterforbruk med gitt prosent
        winter_months = [1, 2, 3, 11, 12]
        mask = scenario_data["month"].isin(winter_months)
        scenario_data.loc[mask, "consumption_kwh"] *= (1 - reduction_percent / 100)
        
    elif scenario == "smart_home":
        # Reduser nattforbruk og optimaliser timing
        night_mask = scenario_data["hour"].between(0, 5)
        scenario_data.loc[night_mask, "consumption_kwh"] *= 0.7
        
        # Flytt noe forbruk til lavlast-timer
        peak_mask = scenario_data["hour"].between(17, 21)
        scenario_data.loc[peak_mask, "consumption_kwh"] *= 0.85
        
    elif scenario == "solar":
        # Simuler solceller - reduserer forbruk midt på dagen om sommeren
        summer_months = [4, 5, 6, 7, 8, 9]
        day_hours = scenario_data["hour"].between(10, 16)
        summer_day_mask = scenario_data["month"].isin(summer_months) & day_hours
        scenario_data.loc[summer_day_mask, "consumption_kwh"] *= 0.3
    
    return scenario_data


if __name__ == "__main__":
    # Test datagenerator
    print("Genererer syntetiske energidata for 2025...")
    
    hourly_data = generate_yearly_energy_data(2025, frequency="h")
    print(f"Genererte {len(hourly_data)} timeobservasjoner")
    print(f"\nFørste 5 rader:\n{hourly_data.head()}")
    
    daily_data = generate_daily_summary(hourly_data)
    print(f"\nDaglig sammendrag ({len(daily_data)} dager):")
    print(daily_data.head())
    
    monthly_stats = get_monthly_statistics(hourly_data)
    print(f"\nMånedlig statistikk:\n{monthly_stats}")
    
    print(f"\nTotalt årsforbruk: {hourly_data['consumption_kwh'].sum():.0f} kWh")
