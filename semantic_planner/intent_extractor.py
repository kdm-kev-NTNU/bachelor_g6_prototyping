"""
Intent Extractor - LLM-based semantic extraction from natural language.

Pipeline Step 1: NL → Semantic Object
"""
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from openai import OpenAI

from .ontology import DomainOntology, IntentType, EntityType


@dataclass
class ExtractedIntent:
    """Structured representation of extracted intent from natural language."""
    intent_type: IntentType
    entity_type: Optional[EntityType]
    parameters: Dict[str, Any]
    requested_fields: List[str]
    confidence: float
    original_query: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent_type.value,
            "entity": self.entity_type.value if self.entity_type else None,
            "parameters": self.parameters,
            "fields": self.requested_fields,
            "confidence": self.confidence,
            "query": self.original_query
        }


class IntentExtractor:
    """
    Extracts structured semantic intent from natural language queries.
    
    Uses LLM to parse natural language and map to domain ontology.
    """
    
    def __init__(self, ontology: DomainOntology, api_key: Optional[str] = None):
        self.ontology = ontology
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self._system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with ontology context."""
        ontology_context = json.dumps(self.ontology.to_dict(), indent=2)
        
        return f"""You are a semantic parser that extracts structured intent from natural language queries.

## Domain Ontology
{ontology_context}

## Your Task
Given a natural language query, extract:
1. **intent_type**: One of: query_list, query_single, mutation_create, mutation_update, mutation_delete, unknown
2. **entity_type**: One of: user, post, product, or null
3. **parameters**: Any specific values mentioned (IDs, names, emails, etc.)
4. **requested_fields**: Which fields the user wants to see (empty = all fields)
5. **confidence**: How confident you are (0.0 to 1.0)

## Output Format
Respond ONLY with valid JSON:
{{
    "intent_type": "query_list",
    "entity_type": "user",
    "parameters": {{}},
    "requested_fields": [],
    "confidence": 0.95
}}

## Examples

Query: "Show me all users"
{{
    "intent_type": "query_list",
    "entity_type": "user",
    "parameters": {{}},
    "requested_fields": [],
    "confidence": 0.98
}}

Query: "Get the product with id 5"
{{
    "intent_type": "query_single",
    "entity_type": "product",
    "parameters": {{"id": 5}},
    "requested_fields": [],
    "confidence": 0.95
}}

Query: "Create a new user named John with email john@example.com"
{{
    "intent_type": "mutation_create",
    "entity_type": "user",
    "parameters": {{"name": "John", "email": "john@example.com"}},
    "requested_fields": [],
    "confidence": 0.92
}}

Query: "Vis meg alle innlegg med tittel og forfatter"
{{
    "intent_type": "query_list",
    "entity_type": "post",
    "parameters": {{}},
    "requested_fields": ["title", "author"],
    "confidence": 0.90
}}
"""
    
    def extract(self, query: str) -> ExtractedIntent:
        """
        Extract structured intent from a natural language query.
        
        Args:
            query: Natural language query string
            
        Returns:
            ExtractedIntent with structured semantic information
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,  # Low temperature for deterministic output
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return ExtractedIntent(
                intent_type=IntentType(result.get("intent_type", "unknown")),
                entity_type=EntityType(result["entity_type"]) if result.get("entity_type") else None,
                parameters=result.get("parameters", {}),
                requested_fields=result.get("requested_fields", []),
                confidence=result.get("confidence", 0.5),
                original_query=query
            )
            
        except Exception as e:
            # Fallback to rule-based extraction
            return self._fallback_extraction(query)
    
    def _fallback_extraction(self, query: str) -> ExtractedIntent:
        """Rule-based fallback when LLM extraction fails."""
        query_lower = query.lower()
        
        # Detect intent type
        intent_type = IntentType.UNKNOWN
        for intent, patterns in self.ontology.intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                intent_type = intent
                break
        
        # Detect entity type
        entity_type = self.ontology.find_entity_by_text(query)
        
        # Extract ID if present
        parameters = {}
        import re
        id_match = re.search(r'\b(?:id|nummer|number)\s*[=:]?\s*(\d+)\b', query_lower)
        if not id_match:
            id_match = re.search(r'\b(\d+)\b', query_lower)
        if id_match:
            parameters["id"] = int(id_match.group(1))
        
        return ExtractedIntent(
            intent_type=intent_type,
            entity_type=entity_type,
            parameters=parameters,
            requested_fields=[],
            confidence=0.5,  # Lower confidence for fallback
            original_query=query
        )
    
    def extract_batch(self, queries: List[str]) -> List[ExtractedIntent]:
        """Extract intents from multiple queries."""
        return [self.extract(q) for q in queries]
