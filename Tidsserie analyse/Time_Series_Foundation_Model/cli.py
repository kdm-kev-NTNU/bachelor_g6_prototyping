"""
Energi AI Assistent - CLI Tool

Kommandolinjeverktøy for energiprognose og analyse.
Genererer bilder og tekstforklaringer.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from data_generator import (
    generate_yearly_energy_data,
    get_monthly_statistics,
    generate_scenario_data
)
from timesfm_predictor import create_predictor
from llm_explainer import create_explainer


def setup_plot_style():
    """Sett opp enkel plotstil."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10


def plot_forecast(
    historical: pd.DataFrame,
    predictions: pd.DataFrame,
    output_path: str
) -> str:
    """Lag og lagre prognosegraf."""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Historiske data
    ax.plot(
        historical["timestamp"], 
        historical["consumption_kwh"],
        color="#3b82f6", 
        linewidth=1,
        label="Historisk forbruk",
        alpha=0.8
    )
    ax.fill_between(
        historical["timestamp"],
        historical["consumption_kwh"],
        alpha=0.2,
        color="#3b82f6"
    )
    
    # Prediksjoner
    ax.plot(
        predictions["timestamp"],
        predictions["predicted_kwh"],
        color="#f97316",
        linewidth=2,
        linestyle="--",
        label="Prognose"
    )
    ax.fill_between(
        predictions["timestamp"],
        predictions["predicted_kwh"],
        alpha=0.2,
        color="#f97316"
    )
    
    ax.set_xlabel("Dato")
    ax.set_ylabel("Forbruk (kWh)")
    ax.set_title("Energiforbruk - Historikk og Prognose")
    ax.legend(loc="upper right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(historical)//168)))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_monthly(monthly_stats: pd.DataFrame, output_path: str) -> str:
    """Lag og lagre månedlig oversikt."""
    fig, ax = plt.subplots(figsize=(12, 5))
    
    colors = ["#3b82f6" if i not in [5, 6, 7] else "#10b981" for i in range(12)]
    
    bars = ax.bar(
        monthly_stats["month_name"],
        monthly_stats["total_kwh"],
        color=colors,
        edgecolor="white",
        linewidth=0.5
    )
    
    # Legg til verdier på søylene
    for bar, val in zip(bars, monthly_stats["total_kwh"]):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 20,
            f'{val:.0f}',
            ha='center',
            va='bottom',
            fontsize=8
        )
    
    ax.set_xlabel("Måned")
    ax.set_ylabel("Totalt forbruk (kWh)")
    ax.set_title("Månedlig Energiforbruk 2025")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_daily_pattern(hourly_data: pd.DataFrame, output_path: str) -> str:
    """Lag og lagre daglig mønster."""
    hourly_avg = hourly_data.groupby("hour")["consumption_kwh"].agg(['mean', 'std']).reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(
        hourly_avg["hour"],
        hourly_avg["mean"],
        color="#3b82f6",
        linewidth=2,
        marker='o',
        markersize=4
    )
    ax.fill_between(
        hourly_avg["hour"],
        hourly_avg["mean"] - hourly_avg["std"],
        hourly_avg["mean"] + hourly_avg["std"],
        alpha=0.2,
        color="#3b82f6"
    )
    
    ax.set_xlabel("Time på døgnet")
    ax.set_ylabel("Gjennomsnitt forbruk (kWh)")
    ax.set_title("Daglig Forbruksmønster")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlim(0, 23)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def print_stats(data: pd.DataFrame, predictions: pd.DataFrame, analysis: dict):
    """Skriv ut statistikk til konsollen."""
    print("\n" + "="*50)
    print("ENERGIFORBRUK STATISTIKK")
    print("="*50)
    
    print(f"\n[Historisk data]")
    print(f"   Periode: {data['timestamp'].min().strftime('%d.%m.%Y')} - {data['timestamp'].max().strftime('%d.%m.%Y')}")
    print(f"   Totalt forbruk: {data['consumption_kwh'].sum():.0f} kWh")
    print(f"   Snitt per time: {data['consumption_kwh'].mean():.2f} kWh")
    print(f"   Maks: {data['consumption_kwh'].max():.2f} kWh")
    print(f"   Min: {data['consumption_kwh'].min():.2f} kWh")
    
    print(f"\n[Prognose]")
    print(f"   Periode: {predictions['timestamp'].min().strftime('%d.%m.%Y %H:%M')} - {predictions['timestamp'].max().strftime('%d.%m.%Y %H:%M')}")
    print(f"   Forventet forbruk: {predictions['predicted_kwh'].sum():.0f} kWh")
    print(f"   Snitt: {predictions['predicted_kwh'].mean():.2f} kWh")
    
    if 'comparison' in analysis:
        comp = analysis['comparison']
        print(f"\n[Sammenligning]")
        print(f"   Endring fra historikk: {comp['change_percent']:+.1f}%")
        trend_ascii = comp['trend_direction'].replace('ø', 'o').replace('æ', 'ae').replace('å', 'a')
        print(f"   Trend: {trend_ascii}")
    
    if 'insights' in analysis:
        print(f"\n[Innsikt]")
        for insight in analysis['insights']:
            # Fjern norske tegn for Windows-kompatibilitet
            insight_ascii = insight.replace('ø', 'o').replace('æ', 'ae').replace('å', 'a')
            print(f"   - {insight_ascii}")
    
    # Estimert kostnad
    total_kwh = data['consumption_kwh'].sum()
    cost = total_kwh * 1.50
    print(f"\n[Kostnad] Estimert: {cost:.0f} kr (ved 1.50 kr/kWh)")
    print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Energi AI Assistent - Prognose og analyse av energiforbruk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Eksempler:
  python cli.py                           # Kjør med standardverdier
  python cli.py --days 14 --forecast 72   # 14 dager historikk, 72 timer prognose
  python cli.py --question "Hvorfor er forbruket høyt?"
  python cli.py --scenario smart_home     # Simuler smart hjem-scenario
        """
    )
    
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=30,
        help="Antall dager med historiske data (default: 30)"
    )
    
    parser.add_argument(
        "--forecast", "-f",
        type=int,
        default=48,
        help="Antall timer å predikere fremover (default: 48)"
    )
    
    parser.add_argument(
        "--year", "-y",
        type=int,
        default=2025,
        help="År for syntetisk data (default: 2025)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Mappe for output-filer (default: output)"
    )
    
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Still et spørsmål til AI-assistenten"
    )
    
    parser.add_argument(
        "--scenario", "-s",
        type=str,
        choices=["normal", "reduced_heating", "smart_home", "solar"],
        default="normal",
        help="Scenario for analyse (default: normal)"
    )
    
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Hopp over bildegenerering"
    )
    
    parser.add_argument(
        "--quiet", "-Q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    # Setup
    setup_plot_style()
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    if not args.quiet:
        print("\n=== Energi AI Assistent ===")
        print("-" * 30)
    
    # Generer data
    if not args.quiet:
        print("Genererer syntetisk energidata...")
    
    full_data = generate_yearly_energy_data(args.year, frequency="h")
    
    # Filtrer til valgt periode
    end_date = full_data["timestamp"].max()
    start_date = end_date - timedelta(days=args.days)
    data = full_data[full_data["timestamp"] >= start_date].copy()
    
    # Scenario
    if args.scenario != "normal":
        if not args.quiet:
            print(f"Bruker scenario: {args.scenario}")
        scenario_data = generate_scenario_data(data, args.scenario, 15)
        savings = data['consumption_kwh'].sum() - scenario_data['consumption_kwh'].sum()
        print(f"\n[Scenario] '{args.scenario}': Sparer {savings:.0f} kWh ({(savings/data['consumption_kwh'].sum())*100:.1f}%)")
    
    # Prediksjon
    if not args.quiet:
        print("Kjorer prognose...")
    
    predictor = create_predictor()
    predictions, metadata = predictor.predict(data, forecast_horizon=args.forecast)
    analysis = predictor.analyze_prediction(data, predictions)
    
    if not args.quiet:
        print(f"Prediksjon: {metadata.get('method', 'ukjent')} metode")
    
    # Statistikk
    print_stats(data, predictions, analysis)
    
    # Generer bilder
    if not args.no_images:
        if not args.quiet:
            print("Genererer grafer...")
        
        forecast_path = plot_forecast(
            data, predictions,
            str(output_dir / "forecast.png")
        )
        print(f"[OK] Prognose: {forecast_path}")
        
        monthly_stats = get_monthly_statistics(full_data)
        monthly_path = plot_monthly(
            monthly_stats,
            str(output_dir / "monthly.png")
        )
        print(f"[OK] Manedlig: {monthly_path}")
        
        daily_path = plot_daily_pattern(
            data,
            str(output_dir / "daily_pattern.png")
        )
        print(f"[OK] Daglig monster: {daily_path}")
    
    # AI-spørsmål
    if args.question:
        print(f"\n[Sporsmaal] {args.question}")
        print("-" * 40)
        
        explainer = create_explainer()
        answer = explainer.answer_question(
            args.question,
            data,
            predictions,
            analysis
        )
        print(answer)
        print("-" * 40)
    
    if not args.quiet:
        print("\nFerdig!")
        if not args.no_images:
            print(f"Bilder lagret i: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
