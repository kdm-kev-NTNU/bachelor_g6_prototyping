"""
NL-to-KG Pipeline - Complete Orchestrator

Complete pipeline for Natural Language to Knowledge Graph queries:

    ┌─────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐     ┌──────────┐
    │   NL    │ ──► │  Intent  │ ──► │ GraphQL │ ──► │ Cypher  │ ──► │ FalkorDB │
    │  Query  │     │ Extract  │     │  Query  │     │  Query  │     │  Execute │
    └─────────┘     └──────────┘     └─────────┘     └─────────┘     └──────────┘
                                                                          │
    ┌─────────┐                                                           │
    │   NL    │ ◄─────────────────────────────────────────────────────────┘
    │Response │
    └─────────┘

Pipeline stages:
1. NL → Intent Extraction (LLM/Rule-based)
2. Intent → GraphQL Query Generation
3. GraphQL → Cypher Translation
4. Cypher → FalkorDB Execution
5. Results → Natural Language Response
"""

import sys
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# Add FalkorDB path for importing client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'FalkorDB'))

from ontology import BrickOntology, IntentType
from intent_extractor import IntentExtractor, ExtractedIntent
from graphql_generator import GraphQLGenerator, GeneratedGraphQL
from graphql_to_cypher import GraphQLToCypherResolver, CypherQuery


@dataclass
class PipelineResult:
    """Complete result from the NL-to-KG pipeline."""
    success: bool
    original_query: str
    extracted_intent: Optional[ExtractedIntent]
    graphql_query: Optional[GeneratedGraphQL]
    cypher_query: Optional[CypherQuery]
    raw_results: Optional[List[Dict]]
    natural_response: str
    debug_info: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "query": self.original_query,
            "intent": self.extracted_intent.to_dict() if self.extracted_intent else None,
            "graphql": self.graphql_query.to_dict() if self.graphql_query else None,
            "cypher": self.cypher_query.cypher if self.cypher_query else None,
            "results": self.raw_results,
            "response": self.natural_response,
            "debug": self.debug_info
        }


class KGPipeline:
    """
    Complete NL-to-KG Pipeline for Brick Ontology queries.
    
    Pipeline flow:
    NL → Intent → GraphQL → Cypher → FalkorDB → Response
    
    The GraphQL layer provides:
    - Structured query interface
    - Type safety
    - Introspection capabilities
    - Standard query language
    """
    
    def __init__(
        self,
        falkor_host: str = "localhost",
        falkor_port: int = 6379,
        graph_name: str = "energy_graph",
        api_key: Optional[str] = None,
        language: str = "no"
    ):
        self.language = language
        
        # Initialize pipeline components
        self.ontology = BrickOntology()
        self.intent_extractor = IntentExtractor(self.ontology, api_key)
        self.graphql_generator = GraphQLGenerator(self.ontology)
        self.cypher_resolver = GraphQLToCypherResolver()
        
        # FalkorDB connection
        self._falkor_config = {
            "host": falkor_host,
            "port": falkor_port,
            "graph_name": graph_name
        }
        self._client = None
    
    def connect(self) -> bool:
        """Connect to FalkorDB."""
        try:
            from falkor_client import FalkorDBClient, FalkorConfig
            
            config = FalkorConfig(
                host=self._falkor_config["host"],
                port=self._falkor_config["port"],
                graph_name=self._falkor_config["graph_name"]
            )
            self._client = FalkorDBClient(config)
            self._client.connect()
            return True
        except Exception as e:
            print(f"[ERROR] Could not connect to FalkorDB: {e}")
            return False
    
    def process(self, query: str) -> PipelineResult:
        """
        Process a natural language query through the complete pipeline.
        
        Pipeline: NL → Intent → GraphQL → Cypher → FalkorDB → Response
        
        Args:
            query: Natural language query
            
        Returns:
            PipelineResult with all intermediate and final results
        """
        debug_info = {"stages": [], "pipeline": "NL → Intent → GraphQL → Cypher → FalkorDB"}
        
        # =====================================================================
        # Stage 1: Intent Extraction (NL → Semantic Object)
        # =====================================================================
        debug_info["stages"].append("1_intent_extraction")
        intent = self.intent_extractor.extract(query)
        debug_info["intent_confidence"] = intent.confidence
        debug_info["intent_type"] = intent.intent_type.value
        debug_info["entity_class"] = intent.entity_class.value if intent.entity_class else None
        
        if intent.confidence < 0.3:
            return PipelineResult(
                success=False,
                original_query=query,
                extracted_intent=intent,
                graphql_query=None,
                cypher_query=None,
                raw_results=None,
                natural_response=self._low_confidence_response(intent),
                debug_info=debug_info
            )
        
        # =====================================================================
        # Stage 2: GraphQL Generation (Intent → GraphQL)
        # =====================================================================
        debug_info["stages"].append("2_graphql_generation")
        graphql_query = self.graphql_generator.generate(
            intent_type=intent.intent_type,
            entity_class=intent.entity_class,
            parameters=intent.parameters,
            requested_fields=None  # Let generator decide
        )
        debug_info["graphql_operation"] = graphql_query.operation_name
        
        # =====================================================================
        # Stage 3: Cypher Resolution (GraphQL → Cypher)
        # =====================================================================
        debug_info["stages"].append("3_cypher_resolution")
        cypher_query = self.cypher_resolver.resolve(
            graphql_query=graphql_query.query,
            variables=graphql_query.variables
        )
        debug_info["cypher_description"] = cypher_query.description
        
        # =====================================================================
        # Stage 4: FalkorDB Execution (Cypher → Results)
        # =====================================================================
        debug_info["stages"].append("4_falkordb_execution")
        
        if self._client is None:
            if not self.connect():
                return PipelineResult(
                    success=False,
                    original_query=query,
                    extracted_intent=intent,
                    graphql_query=graphql_query,
                    cypher_query=cypher_query,
                    raw_results=None,
                    natural_response=self._connection_error_response(),
                    debug_info=debug_info
                )
        
        try:
            # Build parameterized query (substitute variables)
            cypher_with_params = cypher_query.cypher
            for key, value in cypher_query.parameters.items():
                if isinstance(value, str):
                    cypher_with_params = cypher_with_params.replace(f"${key}", f"'{value}'")
                else:
                    cypher_with_params = cypher_with_params.replace(f"${key}", str(value))
            
            results = self._client.query(cypher_with_params)
            debug_info["result_count"] = len(results)
            
        except Exception as e:
            debug_info["error"] = str(e)
            return PipelineResult(
                success=False,
                original_query=query,
                extracted_intent=intent,
                graphql_query=graphql_query,
                cypher_query=cypher_query,
                raw_results=None,
                natural_response=self._query_error_response(str(e)),
                debug_info=debug_info
            )
        
        # =====================================================================
        # Stage 5: Response Formatting (Results → NL)
        # =====================================================================
        debug_info["stages"].append("5_response_formatting")
        natural_response = self._format_response(results, intent, graphql_query)
        
        return PipelineResult(
            success=True,
            original_query=query,
            extracted_intent=intent,
            graphql_query=graphql_query,
            cypher_query=cypher_query,
            raw_results=results,
            natural_response=natural_response,
            debug_info=debug_info
        )
    
    def _format_response(
        self, 
        results: List[Dict], 
        intent: ExtractedIntent,
        graphql_query: GeneratedGraphQL
    ) -> str:
        """Format query results as natural language."""
        
        # Convert OrderedDict to regular dict recursively
        results = self._clean_results(results)
        
        if not results:
            if self.language == "no":
                return "Ingen resultater funnet for spørringen din."
            return "No results found for your query."
        
        # Check if this is a specific question about a field
        specific_answer = self._try_extract_specific_answer(results, intent)
        if specific_answer:
            return specific_answer
        
        # Build response based on intent type
        if intent.intent_type == IntentType.QUERY_AGGREGATE:
            return self._format_aggregate_response(results)
        
        elif intent.intent_type == IntentType.QUERY_LIST:
            return self._format_list_response(results, graphql_query)
        
        elif intent.intent_type == IntentType.QUERY_ENTITY:
            return self._format_entity_response(results)
        
        elif intent.intent_type == IntentType.QUERY_TRAVERSE:
            return self._format_traversal_response(results, graphql_query)
        
        # Default formatting
        return self._format_default_response(results)
    
    def _clean_results(self, data: Any) -> Any:
        """Convert OrderedDict and clean up nested structures."""
        from collections import OrderedDict
        
        if isinstance(data, (dict, OrderedDict)):
            cleaned = {}
            for key, value in data.items():
                cleaned_value = self._clean_results(value)
                # Skip None values
                if cleaned_value is not None:
                    cleaned[key] = cleaned_value
            return cleaned if cleaned else None
        elif isinstance(data, list):
            cleaned = [self._clean_results(item) for item in data]
            return [item for item in cleaned if item is not None]
        else:
            return data
    
    def _try_extract_specific_answer(self, results: List[Dict], intent: ExtractedIntent) -> Optional[str]:
        """Try to extract a specific answer for targeted questions."""
        if not results or not intent.original_query:
            return None
        
        query_lower = intent.original_query.lower()
        result = results[0] if results else {}
        
        # Flatten nested 'b' key if present (from Cypher RETURN b {...})
        if 'b' in result and isinstance(result['b'], dict):
            result = result['b']
        
        # Map question patterns to field names
        field_mappings = {
            # Norwegian
            "energimerke": ("energy_class", "Energimerket er: {value}"),
            "energiklasse": ("energy_class", "Energiklassen er: {value}"),
            "adresse": ("address", "Adressen er: {value}"),
            "areal": ("area_sqm", "Arealet er: {value} m²"),
            "størrelse": ("area_sqm", "Størrelsen er: {value} m²"),
            "byggeår": ("year_built", "Bygget ble bygget i: {value}"),
            "når ble": ("year_built", "Bygget ble bygget i: {value}"),
            "navn": ("name", "Navnet er: {value}"),
            "hva heter": ("name", "Navnet er: {value}"),
            # English
            "energy class": ("energy_class", "The energy class is: {value}"),
            "energy rating": ("energy_class", "The energy rating is: {value}"),
            "address": ("address", "The address is: {value}"),
            "area": ("area_sqm", "The area is: {value} m²"),
            "size": ("area_sqm", "The size is: {value} m²"),
            "built": ("year_built", "It was built in: {value}"),
            "year": ("year_built", "Year built: {value}"),
        }
        
        for pattern, (field_name, template) in field_mappings.items():
            if pattern in query_lower:
                value = result.get(field_name)
                if value is not None:
                    return template.format(value=value)
                else:
                    # Try to find the field in nested structures
                    value = self._find_field_value(result, field_name)
                    if value is not None:
                        return template.format(value=value)
        
        return None
    
    def _find_field_value(self, data: Any, field_name: str) -> Any:
        """Recursively search for a field value in nested structures."""
        if isinstance(data, dict):
            if field_name in data:
                return data[field_name]
            for value in data.values():
                found = self._find_field_value(value, field_name)
                if found is not None:
                    return found
        elif isinstance(data, list):
            for item in data:
                found = self._find_field_value(item, field_name)
                if found is not None:
                    return found
        return None
    
    def _format_aggregate_response(self, results: List[Dict]) -> str:
        """Format aggregation results."""
        if results and "count" in results[0]:
            count = results[0]["count"]
            if self.language == "no":
                return f"Antall: {count}"
            return f"Count: {count}"
        
        # Handle count from list length
        if results:
            count = len(results)
            if self.language == "no":
                return f"Antall: {count}"
            return f"Count: {count}"
        
        return str(results)
    
    def _format_list_response(self, results: List[Dict], graphql_query: GeneratedGraphQL) -> str:
        """Format list results."""
        lines = []
        
        if self.language == "no":
            lines.append(f"Fant {len(results)} resultater:")
        else:
            lines.append(f"Found {len(results)} results:")
        
        lines.append("")
        
        for i, row in enumerate(results[:15], 1):  # Limit to 15
            row_parts = []
            
            # Extract name first if available
            name = self._extract_name(row)
            if name:
                row_parts.append(name)
            
            # Add other relevant fields
            for key, value in row.items():
                if key in ["name", "id"] or value is None or value == "":
                    continue
                if isinstance(value, dict):
                    continue  # Skip nested objects in list view
                if isinstance(value, list) and len(value) == 0:
                    continue
                    
                # Format key nicely
                nice_key = key.replace("_", " ").replace("Type", "")
                if isinstance(value, list):
                    value = f"[{len(value)} items]"
                row_parts.append(f"{nice_key}: {value}")
            
            lines.append(f"  {i}. " + " | ".join(row_parts))
        
        if len(results) > 15:
            remaining = len(results) - 15
            if self.language == "no":
                lines.append(f"\n  ... og {remaining} flere resultater")
            else:
                lines.append(f"\n  ... and {remaining} more results")
        
        return "\n".join(lines)
    
    def _format_entity_response(self, results: List[Dict]) -> str:
        """Format single entity response."""
        if not results:
            return "Entitet ikke funnet." if self.language == "no" else "Entity not found."
        
        entity = results[0]
        
        # Handle wrapped results like {'b': {...}}
        if len(entity) == 1:
            key = list(entity.keys())[0]
            if isinstance(entity[key], dict):
                entity = entity[key]
        
        lines = []
        
        # Title with name
        name = self._extract_name(entity)
        if name:
            lines.append(f"📍 {name}")
            lines.append("")
        
        for key, value in entity.items():
            if value is None or key == "name" or key == "id":
                continue
            
            # Make keys readable
            readable_key = self._format_field_name(key)
            
            if isinstance(value, dict):
                lines.append(f"  {readable_key}:")
                for k, v in value.items():
                    if v is not None:
                        nice_k = self._format_field_name(k)
                        lines.append(f"    • {nice_k}: {v}")
            elif isinstance(value, list):
                if len(value) > 0:
                    lines.append(f"  {readable_key}:")
                    for item in value[:5]:  # Show first 5
                        if isinstance(item, dict):
                            item_name = item.get('name', item.get('id', str(item)))
                            item_type = item.get('type', item.get('level', ''))
                            if item_type:
                                lines.append(f"    • {item_name} ({item_type})")
                            else:
                                lines.append(f"    • {item_name}")
                        else:
                            lines.append(f"    • {item}")
                    if len(value) > 5:
                        lines.append(f"    ... +{len(value)-5} mer")
            else:
                lines.append(f"  {readable_key}: {value}")
        
        return "\n".join(lines)
    
    def _format_traversal_response(self, results: List[Dict], graphql_query: GeneratedGraphQL) -> str:
        """Format traversal results."""
        lines = []
        
        # Header from GraphQL description
        header = graphql_query.description if graphql_query else "Results"
        lines.append(f"📊 {header}")
        lines.append("")
        
        for row in results[:20]:
            row_lines = []
            
            name = self._extract_name(row)
            if name:
                row_lines.append(f"  • {name}")
            else:
                row_lines.append("  •")
            
            # Format nested data
            for key, value in row.items():
                if key in ["name", "id"] or value is None:
                    continue
                
                nice_key = key.replace("_", " ").title()
                
                if isinstance(value, dict):
                    nested_items = [f"{k}={v}" for k, v in value.items() if v]
                    if nested_items:
                        row_lines.append(f"      {nice_key}: {', '.join(nested_items)}")
                elif isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict):
                        row_lines.append(f"      {nice_key}:")
                        for item in value[:5]:
                            item_name = self._extract_name(item)
                            if item_name:
                                row_lines.append(f"        - {item_name}")
                        if len(value) > 5:
                            row_lines.append(f"        ... +{len(value)-5} more")
                    else:
                        row_lines.append(f"      {nice_key}: {', '.join(str(v) for v in value[:5])}")
                elif value != "":
                    row_lines.append(f"      {nice_key}: {value}")
            
            lines.extend(row_lines)
            lines.append("")
        
        if len(results) > 20:
            remaining = len(results) - 20
            if self.language == "no":
                lines.append(f"... og {remaining} flere resultater")
            else:
                lines.append(f"... and {remaining} more results")
        
        return "\n".join(lines)
    
    def _format_default_response(self, results: List[Dict]) -> str:
        """Default response formatting."""
        lines = [f"Resultater ({len(results)}):"]
        lines.append("")
        
        for row in results[:10]:
            name = self._extract_name(row)
            parts = [name] if name else []
            parts.extend(f"{k}: {v}" for k, v in row.items() 
                        if v is not None and k != "name" and not isinstance(v, (dict, list)))
            lines.append("  • " + ", ".join(parts))
        
        return "\n".join(lines)
    
    def _extract_name(self, data: Dict) -> Optional[str]:
        """Extract name from result dict."""
        if "name" in data:
            return data["name"]
        if "n.name" in data:
            return data["n.name"]
        for key in data:
            if "name" in key.lower():
                return data[key]
        return None
    
    def _format_field_name(self, key: str) -> str:
        """Format a field name for display."""
        # Field name translations
        translations = {
            "energy_class": "Energimerke" if self.language == "no" else "Energy Class",
            "area_sqm": "Areal (m²)" if self.language == "no" else "Area (m²)",
            "year_built": "Byggeår" if self.language == "no" else "Year Built",
            "address": "Adresse" if self.language == "no" else "Address",
            "description": "Beskrivelse" if self.language == "no" else "Description",
            "floors": "Etasjer" if self.language == "no" else "Floors",
            "systems": "Systemer" if self.language == "no" else "Systems",
            "meters": "Målere" if self.language == "no" else "Meters",
            "sensors": "Sensorer" if self.language == "no" else "Sensors",
            "equipment": "Utstyr" if self.language == "no" else "Equipment",
            "zones": "Soner" if self.language == "no" else "Zones",
            "unit": "Enhet" if self.language == "no" else "Unit",
            "external_id": "Ekstern ID" if self.language == "no" else "External ID",
            "timeseries": "Tidsserie" if self.language == "no" else "Timeseries",
        }
        
        if key in translations:
            return translations[key]
        
        # Default: title case with underscores replaced
        return key.replace("_", " ").title()
    
    def _low_confidence_response(self, intent: ExtractedIntent) -> str:
        """Response when intent confidence is too low."""
        if self.language == "no":
            return (
                f"Beklager, jeg forstod ikke helt spørsmålet: \"{intent.original_query}\"\n\n"
                "Prøv å spørre om:\n"
                "  • Sensorer i bygget eller en sone\n"
                "  • Utstyr som AHU, kjølemaskin, pumper\n"
                "  • Målere og energidata\n"
                "  • Soner og etasjer"
            )
        return (
            f"Sorry, I didn't understand: \"{intent.original_query}\"\n\n"
            "Try asking about:\n"
            "  • Sensors in building or zone\n"
            "  • Equipment like AHU, chiller, pumps\n"
            "  • Meters and energy data\n"
            "  • Zones and floors"
        )
    
    def _connection_error_response(self) -> str:
        """Response when FalkorDB connection fails."""
        if self.language == "no":
            return (
                "Kunne ikke koble til FalkorDB.\n"
                "Sjekk at databasen kjører: docker start falkordb"
            )
        return (
            "Could not connect to FalkorDB.\n"
            "Make sure the database is running: docker start falkordb"
        )
    
    def _query_error_response(self, error: str) -> str:
        """Response when query execution fails."""
        if self.language == "no":
            return f"Feil ved kjøring av spørring: {error}"
        return f"Query execution error: {error}"
    
    def close(self):
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
    
    # =========================================================================
    # Debug/inspection methods
    # =========================================================================
    
    def explain(self, query: str) -> Dict[str, Any]:
        """
        Explain how a query would be processed without executing it.
        
        Shows all intermediate stages.
        """
        # Stage 1: Intent
        intent = self.intent_extractor.extract(query)
        
        # Stage 2: GraphQL
        graphql = self.graphql_generator.generate(
            intent_type=intent.intent_type,
            entity_class=intent.entity_class,
            parameters=intent.parameters
        )
        
        # Stage 3: Cypher
        cypher = self.cypher_resolver.resolve(
            graphql_query=graphql.query,
            variables=graphql.variables
        )
        
        return {
            "original_query": query,
            "stage_1_intent": {
                "type": intent.intent_type.value,
                "entity": intent.entity_class.value if intent.entity_class else None,
                "parameters": intent.parameters,
                "confidence": intent.confidence
            },
            "stage_2_graphql": {
                "query": graphql.query,
                "variables": graphql.variables,
                "operation": graphql.operation_name
            },
            "stage_3_cypher": {
                "query": cypher.cypher,
                "parameters": cypher.parameters,
                "description": cypher.description
            }
        }


# ============================================================================
# Quick query function
# ============================================================================

def query(
    natural_language: str,
    host: str = "localhost",
    port: int = 6379,
    graph: str = "energy_graph",
    language: str = "no"
) -> str:
    """
    Quick function to query the knowledge graph.
    
    Args:
        natural_language: Question in natural language
        host: FalkorDB host
        port: FalkorDB port
        graph: Graph name
        language: Response language ('no' or 'en')
        
    Returns:
        Natural language response
    """
    pipeline = KGPipeline(
        falkor_host=host,
        falkor_port=port,
        graph_name=graph,
        language=language
    )
    
    try:
        result = pipeline.process(natural_language)
        return result.natural_response
    finally:
        pipeline.close()
