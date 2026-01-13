"""
LLM-as-Judge for evaluating advice quality based on fixed rubric.
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from config import JUDGE_SYSTEM_PROMPT, JUDGE_RUBRIC, JUDGE_MODEL
from eino_client import create_eino_client

load_dotenv()


class JudgeEvaluation(BaseModel):
    """Evaluation result from LLM judge."""
    data_referencing: int = Field(ge=0, le=2, description="References input data explicitly")
    internal_consistency: int = Field(ge=0, le=2, description="No self-contradictions")
    fact_vs_assumption: int = Field(ge=0, le=2, description="Distinguishes observation from interpretation")
    uncertainty_acknowledgement: int = Field(ge=0, le=2, description="Acknowledges data/conclusion limitations")
    advisory_tone: int = Field(ge=0, le=2, description="Suggests, doesn't instruct")
    total_score: int = Field(ge=0, le=10, description="Total score out of 10")
    comment: str = Field(description="Neutral explanation of evaluation")


class LLMJudge:
    """LLM-as-Judge for evaluating advice structure."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize judge with Eino client."""
        self.client = create_eino_client(api_key, base_url)
        self.model = JUDGE_MODEL
    
    def evaluate(self, advice_text: str, building_data: Optional[Dict[str, Any]] = None) -> JudgeEvaluation:
        """
        Evaluate advice quality using fixed rubric.
        
        Args:
            advice_text: The advice text to evaluate
            building_data: Optional building data for context
        
        Returns:
            JudgeEvaluation with scores and comment
        """
        # Build evaluation prompt
        evaluation_prompt = self._build_evaluation_prompt(advice_text, building_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": evaluation_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistency
                max_tokens=500
            )
            
            # Parse response - handle both dict and object formats
            if isinstance(response, dict):
                content = response["choices"][0]["message"]["content"]
            else:
                content = response.choices[0].message.content
            
            result_json = json.loads(content)
            
            # Validate and create evaluation
            evaluation = JudgeEvaluation(**result_json)
            
            # Ensure total_score matches sum
            calculated_total = (
                evaluation.data_referencing +
                evaluation.internal_consistency +
                evaluation.fact_vs_assumption +
                evaluation.uncertainty_acknowledgement +
                evaluation.advisory_tone
            )
            
            if evaluation.total_score != calculated_total:
                evaluation.total_score = calculated_total
            
            return evaluation
            
        except json.JSONDecodeError as e:
            # Fallback evaluation if JSON parsing fails
            return JudgeEvaluation(
                data_referencing=0,
                internal_consistency=0,
                fact_vs_assumption=0,
                uncertainty_acknowledgement=0,
                advisory_tone=0,
                total_score=0,
                comment=f"Feil ved parsing av evaluering: {str(e)}"
            )
        except Exception as e:
            return JudgeEvaluation(
                data_referencing=0,
                internal_consistency=0,
                fact_vs_assumption=0,
                uncertainty_acknowledgement=0,
                advisory_tone=0,
                total_score=0,
                comment=f"Feil ved evaluering: {str(e)}"
            )
    
    def _build_evaluation_prompt(self, advice_text: str, 
                                 building_data: Optional[Dict[str, Any]]) -> str:
        """Build prompt for judge evaluation."""
        prompt = f"""Evaluér følgende råd basert på den faste rubrikken:

RUBRIKK:
{JUDGE_RUBRIC}

RÅDET SOM SKAL EVALUERES:
{advice_text}
"""
        
        if building_data:
            prompt += f"""

KONTEKST (bygningsdata som rådet skulle referere til):
- Alder: {building_data.get('age', 'N/A')} år
- Størrelse: {building_data.get('size_m2', 'N/A')} m²
- Konstruksjonstype: {building_data.get('construction_type', 'N/A')}
- Nåværende energibruk: {building_data.get('current_energy_kwh', 'N/A')} kWh/år
- Forventet energibruk: {building_data.get('expected_energy_kwh', 'N/A')} kWh/år
"""
        
        prompt += """

HUSK: Du evaluerer KUN struktur, tydelighet og sporbarhet. IKKE om rådet er faglig korrekt.
Returner JSON med poeng for hvert kriterium (0-2) og total score (0-10)."""
        
        return prompt
    
    def evaluate_batch(self, advice_texts: list[str], 
                      building_data_list: Optional[list[Dict[str, Any]]] = None) -> list[JudgeEvaluation]:
        """
        Evaluate multiple advice texts.
        
        Args:
            advice_texts: List of advice texts
            building_data_list: Optional list of building data (must match advice_texts length)
        
        Returns:
            List of evaluations
        """
        evaluations = []
        
        for i, advice in enumerate(advice_texts):
            building_data = building_data_list[i] if building_data_list and i < len(building_data_list) else None
            evaluation = self.evaluate(advice, building_data)
            evaluations.append(evaluation)
        
        return evaluations


def create_judge() -> LLMJudge:
    """Factory function to create judge."""
    return LLMJudge()


if __name__ == "__main__":
    # Test judge
    test_advice = """
    Basert på bygningsdataene ser jeg at bygningen bruker betydelig mer energi enn forventet.
    Du kan vurdere å forbedre isolasjonen, spesielt i taket og veggene.
    Det kan også være lurt å vurdere å bytte ut vinduer til mer energieffektive alternativer.
    Basert på tilgjengelige data kan dette potensielt redusere energibruken med 20-30%.
    """
    
    test_building = {
        "age": 50,
        "size_m2": 500,
        "construction_type": "brick",
        "current_energy_kwh": 100000,
        "expected_energy_kwh": 75000
    }
    
    judge = create_judge()
    evaluation = judge.evaluate(test_advice, test_building)
    
    print("EVALUERING:")
    print(f"Dataforankring: {evaluation.data_referencing}/2")
    print(f"Intern konsistens: {evaluation.internal_consistency}/2")
    print(f"Fakta vs antagelser: {evaluation.fact_vs_assumption}/2")
    print(f"Usikkerhet: {evaluation.uncertainty_acknowledgement}/2")
    print(f"Rådgivende tone: {evaluation.advisory_tone}/2")
    print(f"Total score: {evaluation.total_score}/10")
    print(f"\nKommentar: {evaluation.comment}")
