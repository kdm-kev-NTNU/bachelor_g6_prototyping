"""
RAG-based advisor for generating energy advice with citations.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from config import ADVISOR_SYSTEM_PROMPT, ADVISOR_MODEL
from retriever import hybrid_retrieve, format_context_for_prompt
from building_data import format_building_for_prompt
from eino_client import create_eino_client

load_dotenv()


class EnergyAdvisor:
    """RAG-based energy advisor."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize advisor with Eino client."""
        self.client = create_eino_client(api_key, base_url)
        self.model = ADVISOR_MODEL
    
    def generate_advice(self, building_data: Dict[str, Any], 
                      query: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate energy advice for a building using RAG.
        
        Args:
            building_data: Building data dictionary
            query: Optional specific query, otherwise generates general advice
        
        Returns:
            Dictionary with advice text, citations, and metadata
        """
        # Build query if not provided
        if not query:
            query = f"""
            Gi råd om energieffektivisering for en {building_data.get('age', '')} år gammel bygning 
            på {building_data.get('size_m2', '')} m² av type {building_data.get('construction_type', '')} 
            som bruker {building_data.get('current_energy_kwh', '')} kWh/år, 
            mens forventet bruk er {building_data.get('expected_energy_kwh', '')} kWh/år.
            """
        
        # Retrieve relevant documents
        retrieved_docs = hybrid_retrieve(query, building_data)
        
        if not retrieved_docs:
            return {
                "advice": "Beklager, jeg fant ikke relevant dokumentasjon for å gi råd.",
                "citations": [],
                "retrieved_docs": [],
                "error": "Ingen dokumenter funnet"
            }
        
        # Format context
        context = format_context_for_prompt(retrieved_docs)
        
        # Format building data
        building_text = format_building_for_prompt(
            type('Building', (), building_data)()  # Simple object-like access
        )
        
        # Build user prompt
        user_prompt = f"""{building_text}

Relevante dokumenter:
{context}

Basert på bygningsdataene og dokumentasjonen over, gi konkrete råd om energieffektivisering.
Husk å:
- Referere eksplisitt til bygningsdataene
- Sitere kildene du bruker
- Bruke rådgivende tone (foreslå, ikke instruer)
- Skille mellom fakta og antagelser
- Anerkjenne usikkerheter og begrensninger"""
        
        # Generate advice with LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ADVISOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            advice_text = response["choices"][0]["message"]["content"]
            
            # Extract citations from advice text
            citations = self._extract_citations(advice_text, retrieved_docs)
            
            # Handle usage - can be dict or object
            tokens_used = None
            if "usage" in response:
                if isinstance(response["usage"], dict):
                    tokens_used = response["usage"].get("total_tokens")
                else:
                    tokens_used = response["usage"].total_tokens if response["usage"] else None
            
            return {
                "advice": advice_text,
                "citations": citations,
                "retrieved_docs": [
                    {
                        "source": doc["source"],
                        "page": doc["page"],
                        "citation": doc["citation"]
                    }
                    for doc in retrieved_docs
                ],
                "metadata": {
                    "model": self.model,
                    "tokens_used": tokens_used,
                    "num_sources": len(retrieved_docs)
                }
            }
            
        except Exception as e:
            return {
                "advice": f"Feil ved generering av råd: {str(e)}",
                "citations": [],
                "retrieved_docs": [],
                "error": str(e)
            }
    
    def _extract_citations(self, advice_text: str, 
                          retrieved_docs: list) -> list:
        """Extract citations mentioned in advice text."""
        citations_found = []
        
        for doc in retrieved_docs:
            citation = doc.get("citation", "")
            if citation in advice_text:
                citations_found.append({
                    "citation": citation,
                    "source": doc.get("source", ""),
                    "page": doc.get("page", "")
                })
        
        return citations_found


def create_advisor() -> EnergyAdvisor:
    """Factory function to create advisor."""
    return EnergyAdvisor()


if __name__ == "__main__":
    # Test advisor
    from building_data import generate_buildings, get_building_dict
    
    buildings = generate_buildings(1)
    building_dict = get_building_dict(buildings[0])
    
    advisor = create_advisor()
    result = advisor.generate_advice(building_dict)
    
    print("RÅD:")
    print(result["advice"])
    print("\nSITATER:")
    for cit in result["citations"]:
        print(f"  - {cit['citation']}")
