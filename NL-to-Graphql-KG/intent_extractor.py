"""
Intent Extractor for Brick/Building Domain

Extracts semantic intent from natural language queries using LLM
with domain-specific Brick ontology context.
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from ontology import BrickOntology, BrickClass, IntentType


@dataclass
class ExtractedIntent:
    """Structured representation of extracted intent."""
    intent_type: IntentType
    entity_class: Optional[BrickClass]
    parameters: Dict[str, Any]
    traversal_hint: Optional[str]  # Hint for which traversal pattern to use
    confidence: float
    original_query: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent_type.value,
            "entity": self.entity_class.value if self.entity_class else None,
            "parameters": self.parameters,
            "traversal_hint": self.traversal_hint,
            "confidence": self.confidence,
            "query": self.original_query
        }


class IntentExtractor:
    """
    Extracts structured semantic intent from natural language queries.
    
    Supports both LLM-based extraction (with OpenAI) and rule-based fallback.
    """
    
    def __init__(self, ontology: BrickOntology, api_key: Optional[str] = None):
        self.ontology = ontology
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        self._system_prompt = self._build_system_prompt()
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                pass
        return self._client
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with Brick ontology context."""
        
        entity_list = []
        for brick_class, entity in self.ontology.entities.items():
            synonyms = entity.synonyms_no[:3] + entity.synonyms_en[:2]
            entity_list.append(f"  - {brick_class.value}: {entity.name} (synonyms: {', '.join(synonyms)})")
        
        traversal_list = []
        for name, pattern in self.ontology.traversals.items():
            traversal_list.append(f"  - {name}: {pattern.description}")
        
        return f"""Du er en semantisk parser for bygningsstyring og energisystemer.
Du ekstraherer strukturert informasjon fra naturlige språkspørringer om bygninger, 
HVAC-systemer, sensorer og målere.

## Brick Ontology Entity Types
{chr(10).join(entity_list)}

## Available Traversal Patterns
{chr(10).join(traversal_list)}

## Intent Types
- query_entity: Finn spesifikk enhet (f.eks. "vis meg bygningen", "hva er sensor X")
- query_list: List opp entiteter (f.eks. "vis alle sensorer", "hvilke soner finnes")
- query_traverse: Traverser relasjoner (f.eks. "sensorer i bygget", "soner som AHU mater")
- query_aggregate: Aggregering (f.eks. "hvor mange sensorer", "antall etasjer")
- query_path: Finn sti (f.eks. "kobling mellom AHU og sone")

## Output Format (ONLY valid JSON)
{{
    "intent_type": "query_traverse",
    "entity_class": "brick_Building",
    "parameters": {{"name": "Operahuset"}},
    "traversal_hint": "building_sensors",
    "confidence": 0.9
}}

## Examples

Query: "Vis alle sensorer i bygget"
{{
    "intent_type": "query_traverse",
    "entity_class": "brick_Building",
    "parameters": {{}},
    "traversal_hint": "building_sensors",
    "confidence": 0.95
}}

Query: "Hvilke soner mater hovedaggregatet?"
{{
    "intent_type": "query_traverse", 
    "entity_class": "brick_Air_Handling_Unit",
    "parameters": {{"name": "hovedaggregat"}},
    "traversal_hint": "ahu_zones",
    "confidence": 0.9
}}

Query: "List alle temperatursensorer"
{{
    "intent_type": "query_list",
    "entity_class": "brick_Temperature_Sensor",
    "parameters": {{}},
    "traversal_hint": null,
    "confidence": 0.95
}}

Query: "Hvor mange etasjer har bygningen?"
{{
    "intent_type": "query_aggregate",
    "entity_class": "brick_Floor",
    "parameters": {{}},
    "traversal_hint": null,
    "confidence": 0.9
}}
"""
    
    def extract(self, query: str) -> ExtractedIntent:
        """
        Extract structured intent from natural language query.
        
        Uses LLM if available, falls back to rule-based extraction.
        """
        # Try LLM extraction first
        if self.client:
            try:
                return self._extract_with_llm(query)
            except Exception as e:
                print(f"[WARN] LLM extraction failed: {e}, using fallback")
        
        # Fallback to rule-based
        return self._extract_rule_based(query)
    
    def _extract_with_llm(self, query: str) -> ExtractedIntent:
        """Extract intent using LLM."""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Map entity class string to enum
        entity_class = None
        if result.get("entity_class"):
            entity_str = result["entity_class"]
            for bc in BrickClass:
                if bc.value == entity_str:
                    entity_class = bc
                    break
        
        return ExtractedIntent(
            intent_type=IntentType(result.get("intent_type", "unknown")),
            entity_class=entity_class,
            parameters=result.get("parameters", {}),
            traversal_hint=result.get("traversal_hint"),
            confidence=result.get("confidence", 0.7),
            original_query=query
        )
    
    def _extract_rule_based(self, query: str) -> ExtractedIntent:
        """Rule-based fallback extraction."""
        query_lower = query.lower()
        
        # Detect intent type
        intent_type = self.ontology.detect_intent(query_lower)
        
        # Detect entity type
        entity_class = self.ontology.find_entity_by_text(query_lower)
        
        # Detect traversal hint
        traversal = self.ontology.find_traversal_by_intent(query_lower)
        traversal_hint = traversal.name if traversal else None
        
        # Extract parameters
        parameters = self._extract_parameters(query_lower)
        
        # Determine confidence
        confidence = 0.5
        if entity_class:
            confidence += 0.2
        if traversal_hint:
            confidence += 0.15
        if intent_type != IntentType.UNKNOWN:
            confidence += 0.1
        
        return ExtractedIntent(
            intent_type=intent_type,
            entity_class=entity_class,
            parameters=parameters,
            traversal_hint=traversal_hint,
            confidence=min(confidence, 0.85),
            original_query=query
        )
    
    def _extract_parameters(self, query: str) -> Dict[str, Any]:
        """Extract parameters from query text."""
        params = {}
        
        # Extract IDs
        id_match = re.search(r'\b(?:id|nummer|number)\s*[=:]?\s*([\'"]?)(\w+)\1', query, re.IGNORECASE)
        if id_match:
            params["id"] = id_match.group(2)
        
        # Extract names in quotes
        name_match = re.search(r'["\']([^"\']+)["\']', query)
        if name_match:
            params["name"] = name_match.group(1)
        
        # Extract specific building names
        building_names = ["operahuset", "opera", "hovedbygg"]
        for name in building_names:
            if name in query:
                params["building_name"] = name
                break
        
        # Extract zone references
        zone_patterns = ["foyer", "hovedsal", "backstage", "sone"]
        for zone in zone_patterns:
            if zone in query:
                params["zone_name"] = zone
                break
        
        # Extract equipment references
        equipment_patterns = ["ahu", "aggregat", "kjølemaskin", "chiller", "pumpe"]
        for eq in equipment_patterns:
            if eq in query:
                params["equipment_name"] = eq
                break
        
        return params
    
    def extract_batch(self, queries: List[str]) -> List[ExtractedIntent]:
        """Extract intents from multiple queries."""
        return [self.extract(q) for q in queries]
