"""
Semantic Pipeline - Complete NL to GraphQL pipeline.

Pipeline:
1. NL → Semantic Extraction (LLM)
2. Semantic Object → Query Plan
3. Query Plan → GraphQL (mechanical)
4. Result → Explanatory Text (LLM)
"""
import httpx
from dataclasses import dataclass
from typing import Dict, Any, Optional

from .ontology import DomainOntology
from .intent_extractor import IntentExtractor, ExtractedIntent
from .query_planner import QueryPlanner, QueryPlan
from .response_formatter import ResponseFormatter


@dataclass
class PipelineResult:
    """Complete result from the semantic pipeline."""
    success: bool
    original_query: str
    extracted_intent: Optional[ExtractedIntent]
    query_plan: Optional[QueryPlan]
    graphql_query: Optional[str]
    graphql_result: Optional[Dict[str, Any]]
    natural_response: str
    debug_info: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "query": self.original_query,
            "intent": self.extracted_intent.to_dict() if self.extracted_intent else None,
            "plan": self.query_plan.to_dict() if self.query_plan else None,
            "graphql": self.graphql_query,
            "result": self.graphql_result,
            "response": self.natural_response,
            "debug": self.debug_info
        }


class SemanticPipeline:
    """
    Complete semantic pipeline for NL to GraphQL transformation.
    
    This orchestrates the entire flow:
    NL → Intent → Plan → GraphQL → Result → Response
    """
    
    def __init__(
        self,
        graphql_endpoint: str = "http://localhost:8000/graphql",
        api_key: Optional[str] = None,
        language: str = "no"
    ):
        self.graphql_endpoint = graphql_endpoint
        self.language = language
        
        # Initialize components
        self.ontology = DomainOntology()
        self.intent_extractor = IntentExtractor(self.ontology, api_key)
        self.query_planner = QueryPlanner(self.ontology)
        self.response_formatter = ResponseFormatter(self.ontology, api_key)
    
    async def process(self, query: str) -> PipelineResult:
        """
        Process a natural language query through the complete pipeline.
        
        Args:
            query: Natural language query
            
        Returns:
            PipelineResult with all intermediate and final results
        """
        debug_info = {"stages": []}
        
        # Stage 1: Extract intent
        debug_info["stages"].append("intent_extraction")
        intent = self.intent_extractor.extract(query)
        
        if intent.confidence < 0.3:
            return PipelineResult(
                success=False,
                original_query=query,
                extracted_intent=intent,
                query_plan=None,
                graphql_query=None,
                graphql_result=None,
                natural_response=self._low_confidence_message(intent),
                debug_info=debug_info
            )
        
        # Stage 2 & 3: Plan query
        debug_info["stages"].append("query_planning")
        plan = self.query_planner.plan(intent)
        
        if plan is None:
            return PipelineResult(
                success=False,
                original_query=query,
                extracted_intent=intent,
                query_plan=None,
                graphql_query=None,
                graphql_result=None,
                natural_response=self._planning_failed_message(intent),
                debug_info=debug_info
            )
        
        # Stage 3: Execute GraphQL
        debug_info["stages"].append("graphql_execution")
        graphql_result = await self._execute_graphql(plan.graphql_query)
        
        if "errors" in graphql_result and not graphql_result.get("data"):
            return PipelineResult(
                success=False,
                original_query=query,
                extracted_intent=intent,
                query_plan=plan,
                graphql_query=plan.graphql_query,
                graphql_result=graphql_result,
                natural_response=self.response_formatter._format_error(
                    graphql_result["errors"], self.language
                ),
                debug_info=debug_info
            )
        
        # Stage 4: Format response
        debug_info["stages"].append("response_formatting")
        response = self.response_formatter.format(
            result=graphql_result,
            plan=plan,
            original_query=query,
            language=self.language
        )
        
        return PipelineResult(
            success=True,
            original_query=query,
            extracted_intent=intent,
            query_plan=plan,
            graphql_query=plan.graphql_query,
            graphql_result=graphql_result,
            natural_response=response,
            debug_info=debug_info
        )
    
    def process_sync(self, query: str) -> PipelineResult:
        """Synchronous version of process()."""
        import asyncio
        return asyncio.run(self.process(query))
    
    async def _execute_graphql(self, query: str) -> Dict[str, Any]:
        """Execute a GraphQL query against the endpoint."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.graphql_endpoint,
                    json={"query": query},
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                return response.json()
            except Exception as e:
                return {"errors": [{"message": str(e)}]}
    
    def _low_confidence_message(self, intent: ExtractedIntent) -> str:
        """Message when intent extraction has low confidence."""
        if self.language == "no":
            return (
                f"Beklager, jeg forstod ikke helt hva du mente med: \"{intent.original_query}\"\n"
                "Kan du prøve å omformulere spørsmålet?"
            )
        return (
            f"Sorry, I didn't quite understand: \"{intent.original_query}\"\n"
            "Could you try rephrasing your question?"
        )
    
    def _planning_failed_message(self, intent: ExtractedIntent) -> str:
        """Message when query planning fails."""
        if self.language == "no":
            entity = intent.entity_type.value if intent.entity_type else "ukjent"
            return (
                f"Beklager, jeg kunne ikke lage en spørring for {entity}.\n"
                "Operasjonen du ba om er kanskje ikke støttet."
            )
        entity = intent.entity_type.value if intent.entity_type else "unknown"
        return (
            f"Sorry, I couldn't create a query for {entity}.\n"
            "The operation you requested may not be supported."
        )
    
    def get_supported_operations(self) -> Dict[str, Any]:
        """Get information about supported operations."""
        return {
            "entities": list(e.value for e in self.ontology.entities.keys()),
            "operations": [
                {
                    "name": op.name,
                    "description": op.description,
                    "entity": op.entity.value,
                    "type": op.intent_type.value
                }
                for op in self.ontology.operations.values()
            ]
        }


# Convenience function for quick usage
async def query(
    natural_language: str,
    endpoint: str = "http://localhost:8000/graphql",
    language: str = "no"
) -> str:
    """
    Quick function to process a natural language query.
    
    Args:
        natural_language: The question in natural language
        endpoint: GraphQL endpoint URL
        language: Response language ('no' or 'en')
        
    Returns:
        Natural language response
    """
    pipeline = SemanticPipeline(graphql_endpoint=endpoint, language=language)
    result = await pipeline.process(natural_language)
    return result.natural_response
