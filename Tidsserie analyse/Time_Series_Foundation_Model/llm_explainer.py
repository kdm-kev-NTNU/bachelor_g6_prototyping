"""
LLM Explainer Module

Bruker OpenAI GPT-4 for å forklare energidata og prediksjoner
på naturlig norsk språk.
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Last miljøvariabler
load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI ikke installert.")


class EnergyExplainer:
    """
    Klasse for å forklare energidata ved hjelp av GPT-4.
    """
    
    SYSTEM_PROMPT = """Du er en hjelpsom energirådgiver som forklarer energiforbruk og gir råd på norsk.

Du har tilgang til energidata fra et hus og kan:
- Forklare mønstre i energiforbruket
- Identifisere årsaker til høyt eller lavt forbruk
- Gi konkrete råd for å spare energi
- Predikere fremtidig forbruk basert på historikk

Svar alltid på norsk, vær konkret og bruk tall fra dataene.
Hvis du er usikker, si det tydelig.

Format svarene dine pent med overskrifter og punktlister når det passer."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialiser explainer med OpenAI API.
        
        Args:
            api_key: OpenAI API nøkkel (ellers fra miljøvariabel)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.model = "gpt-4o"  # Bruk gpt-4o for best ytelse
        
        if OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Sjekk om OpenAI er tilgjengelig."""
        return self.client is not None
    
    def explain_data(
        self,
        historical_data: pd.DataFrame,
        predictions: Optional[pd.DataFrame] = None,
        analysis: Optional[dict] = None,
        user_question: Optional[str] = None
    ) -> str:
        """
        Generer forklaring av energidata.
        
        Args:
            historical_data: Historiske forbruksdata
            predictions: Prediksjoner (valgfritt)
            analysis: Analyseresultater fra predictor (valgfritt)
            user_question: Spesifikt spørsmål fra bruker (valgfritt)
        
        Returns:
            Forklaring som tekst
        """
        if not self.is_available():
            return self._fallback_explanation(historical_data, predictions, analysis, user_question)
        
        # Forbered kontekst
        context = self._prepare_context(historical_data, predictions, analysis)
        
        # Lag prompt
        if user_question:
            user_prompt = f"""Brukerens spørsmål: {user_question}

Her er energidataene:
{context}

Svar på brukerens spørsmål basert på dataene."""
        else:
            user_prompt = f"""Her er energidataene for et hus:
{context}

Gi en kort oppsummering av energiforbruket og eventuelle anbefalinger."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API feil: {e}")
            return self._fallback_explanation(historical_data, predictions, analysis, user_question)
    
    def answer_question(
        self,
        question: str,
        historical_data: pd.DataFrame,
        predictions: Optional[pd.DataFrame] = None,
        analysis: Optional[dict] = None,
        chat_history: Optional[List[dict]] = None
    ) -> str:
        """
        Svar på et spesifikt spørsmål om energidata.
        
        Args:
            question: Brukerens spørsmål
            historical_data: Historiske data
            predictions: Prediksjoner
            analysis: Analyseresultater
            chat_history: Tidligere meldinger i samtalen
        
        Returns:
            Svar på spørsmålet
        """
        if not self.is_available():
            return self._fallback_answer(question, historical_data, predictions)
        
        context = self._prepare_context(historical_data, predictions, analysis)
        
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
        # Legg til chat-historikk hvis tilgjengelig
        if chat_history:
            for msg in chat_history[-6:]:  # Siste 6 meldinger
                messages.append(msg)
        
        # Legg til kontekst og spørsmål
        messages.append({
            "role": "user",
            "content": f"""Energidata for kontekst:
{context}

Spørsmål: {question}"""
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Beklager, kunne ikke svare på spørsmålet: {e}"
    
    def generate_scenario_explanation(
        self,
        base_consumption: float,
        scenario_consumption: float,
        scenario_name: str,
        time_period: str = "år"
    ) -> str:
        """
        Forklar konsekvenser av et energisparings-scenario.
        
        Args:
            base_consumption: Originalt forbruk i kWh
            scenario_consumption: Forbruk etter tiltak i kWh
            scenario_name: Navn på scenarioet
            time_period: Tidsperiode for beregningen
        
        Returns:
            Forklaring av scenarioet
        """
        savings = base_consumption - scenario_consumption
        savings_percent = (savings / base_consumption) * 100
        
        # Estimert strømpris (NOK/kWh)
        price_per_kwh = 1.50
        money_saved = savings * price_per_kwh
        
        if not self.is_available():
            return f"""## Scenario: {scenario_name}

**Resultat:**
- Originalt forbruk: {base_consumption:.0f} kWh per {time_period}
- Nytt forbruk: {scenario_consumption:.0f} kWh per {time_period}
- Besparelse: {savings:.0f} kWh ({savings_percent:.1f}%)
- Estimert sparte kostnader: {money_saved:.0f} kr per {time_period}

Dette er en automatisk beregning basert på dine energidata."""
        
        prompt = f"""Forklar dette energisparingsscenariet for en huseier:

Scenario: {scenario_name}
Tidsperiode: {time_period}
Originalt forbruk: {base_consumption:.0f} kWh
Forbruk etter tiltak: {scenario_consumption:.0f} kWh
Besparelse: {savings:.0f} kWh ({savings_percent:.1f}%)
Estimert spart (ved {price_per_kwh} kr/kWh): {money_saved:.0f} kr

Forklar hva dette betyr i praksis, og gi eventuelle tilleggsråd."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Kunne ikke generere forklaring: {e}"
    
    def _prepare_context(
        self,
        historical_data: pd.DataFrame,
        predictions: Optional[pd.DataFrame] = None,
        analysis: Optional[dict] = None
    ) -> str:
        """Forbered datakontext for LLM."""
        context_parts = []
        
        # Historisk data sammendrag
        hist_summary = {
            "periode": f"{historical_data['timestamp'].min()} til {historical_data['timestamp'].max()}",
            "antall_observasjoner": int(len(historical_data)),
            "totalt_forbruk_kwh": float(round(historical_data['consumption_kwh'].sum(), 2)),
            "gjennomsnitt_kwh": float(round(historical_data['consumption_kwh'].mean(), 2)),
            "maks_kwh": float(round(historical_data['consumption_kwh'].max(), 2)),
            "min_kwh": float(round(historical_data['consumption_kwh'].min(), 2))
        }
        context_parts.append(f"**Historisk data:**\n{json.dumps(hist_summary, indent=2, ensure_ascii=False)}")
        
        # Månedlig fordeling hvis tilgjengelig
        if 'month' in historical_data.columns:
            monthly = {int(k): float(v) for k, v in historical_data.groupby('month')['consumption_kwh'].sum().to_dict().items()}
            context_parts.append(f"**Maanedlig forbruk (kWh):**\n{json.dumps(monthly, indent=2)}")
        
        # Prediksjoner
        if predictions is not None and len(predictions) > 0:
            pred_summary = {
                "prognose_periode": f"{predictions['timestamp'].min()} til {predictions['timestamp'].max()}",
                "forventet_totalt": float(round(predictions['predicted_kwh'].sum(), 2)),
                "forventet_snitt": float(round(predictions['predicted_kwh'].mean(), 2))
            }
            context_parts.append(f"**Prognose:**\n{json.dumps(pred_summary, indent=2, ensure_ascii=False)}")
        
        # Analyse - konverter numpy typer til Python typer
        if analysis:
            def convert_numpy(obj):
                if isinstance(obj, dict):
                    return {k: convert_numpy(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(i) for i in obj]
                elif hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                return obj
            analysis_clean = convert_numpy(analysis)
            context_parts.append(f"**Analyse:**\n{json.dumps(analysis_clean, indent=2, ensure_ascii=False)}")
        
        return "\n\n".join(context_parts)
    
    def _fallback_explanation(
        self,
        historical_data: pd.DataFrame,
        predictions: Optional[pd.DataFrame],
        analysis: Optional[dict],
        user_question: Optional[str]
    ) -> str:
        """Fallback forklaring når OpenAI ikke er tilgjengelig."""
        total = historical_data['consumption_kwh'].sum()
        avg = historical_data['consumption_kwh'].mean()
        
        explanation = f"""## Energiforbruk Oppsummering

**Historisk forbruk:**
- Totalt: {total:.0f} kWh
- Gjennomsnitt per time: {avg:.2f} kWh

"""
        
        if predictions is not None and len(predictions) > 0:
            pred_total = predictions['predicted_kwh'].sum()
            explanation += f"""**Prognose:**
- Forventet forbruk: {pred_total:.0f} kWh
- Antall timer i prognosen: {len(predictions)}

"""
        
        if analysis and 'insights' in analysis:
            explanation += "**Innsikt:**\n"
            for insight in analysis['insights']:
                explanation += f"- {insight}\n"
        
        explanation += "\n*Merk: OpenAI API er ikke konfigurert. Sett OPENAI_API_KEY i .env fil for mer detaljerte forklaringer.*"
        
        return explanation
    
    def _fallback_answer(
        self,
        question: str,
        historical_data: pd.DataFrame,
        predictions: Optional[pd.DataFrame]
    ) -> str:
        """Enkelt svar når OpenAI ikke er tilgjengelig."""
        total = historical_data['consumption_kwh'].sum()
        avg = historical_data['consumption_kwh'].mean()
        
        # Enkel keyword-matching
        question_lower = question.lower()
        
        if "hvor mye" in question_lower or "total" in question_lower:
            return f"Totalt energiforbruk i perioden er {total:.0f} kWh."
        
        if "gjennomsnitt" in question_lower or "snitt" in question_lower:
            return f"Gjennomsnittlig forbruk per time er {avg:.2f} kWh."
        
        if "prediksjon" in question_lower or "prognose" in question_lower or "fremtid" in question_lower:
            if predictions is not None:
                pred_total = predictions['predicted_kwh'].sum()
                return f"Prognosen viser et forventet forbruk på {pred_total:.0f} kWh for de neste {len(predictions)} timene."
            return "Ingen prognosedata tilgjengelig."
        
        if "spare" in question_lower or "reduser" in question_lower:
            return """Her er noen tips for å spare energi:
1. Senk innetemperaturen med 1-2 grader
2. Skru av lys i rom som ikke brukes
3. Bruk varmepumpe effektivt
4. Tørk klær utendørs når mulig
5. Installer smarte termostater"""
        
        return f"""Beklager, jeg kan ikke svare detaljert uten OpenAI API.

Nøkkeltall fra dataene:
- Totalt forbruk: {total:.0f} kWh
- Gjennomsnitt per time: {avg:.2f} kWh

Sett OPENAI_API_KEY i .env for mer avanserte svar."""


def create_explainer(api_key: Optional[str] = None) -> EnergyExplainer:
    """Factory function for å opprette explainer."""
    return EnergyExplainer(api_key)


if __name__ == "__main__":
    # Test explainer
    from data_generator import generate_yearly_energy_data
    from timesfm_predictor import create_predictor
    
    print("Tester LLM Explainer...")
    
    # Generer testdata
    data = generate_yearly_energy_data(2025, frequency="h")
    historical = data.tail(168)  # Siste 7 dager
    
    # Lag prediksjon
    predictor = create_predictor()
    predictions, metadata = predictor.predict(historical, forecast_horizon=48)
    analysis = predictor.analyze_prediction(historical, predictions)
    
    # Test explainer
    explainer = create_explainer()
    
    print("\n--- Generell forklaring ---")
    explanation = explainer.explain_data(historical, predictions, analysis)
    print(explanation)
    
    print("\n--- Svar på spørsmål ---")
    answer = explainer.answer_question(
        "Hvorfor var forbruket høyt i går?",
        historical,
        predictions,
        analysis
    )
    print(answer)
