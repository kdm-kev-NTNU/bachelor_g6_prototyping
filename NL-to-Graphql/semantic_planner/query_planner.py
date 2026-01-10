"""
Query Planner - Converts semantic objects to GraphQL queries.

Pipeline Step 2: Semantic Object → Query Plan
Pipeline Step 3: Query Plan → GraphQL (mechanical)
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from .ontology import DomainOntology, IntentType, EntityType, Operation
from .intent_extractor import ExtractedIntent


@dataclass
class QueryPlan:
    """Represents a planned GraphQL query with all necessary information."""
    operation: Operation
    parameters: Dict[str, Any]
    selected_fields: List[str]
    include_relations: bool
    graphql_query: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation.name,
            "graphql_name": self.operation.graphql_name,
            "parameters": self.parameters,
            "fields": self.selected_fields,
            "graphql": self.graphql_query
        }


class QueryPlanner:
    """
    Plans and generates GraphQL queries from semantic intents.
    
    This is the deterministic, mechanical part of the pipeline.
    """
    
    def __init__(self, ontology: DomainOntology):
        self.ontology = ontology
    
    def plan(self, intent: ExtractedIntent) -> Optional[QueryPlan]:
        """
        Create a query plan from an extracted intent.
        
        Args:
            intent: Extracted semantic intent
            
        Returns:
            QueryPlan with GraphQL query, or None if planning fails
        """
        if intent.entity_type is None:
            return None
        
        # Find the matching operation
        operation = self.ontology.find_operation(intent.intent_type, intent.entity_type)
        if operation is None:
            return None
        
        # Get entity definition for field information
        entity = self.ontology.get_entity(intent.entity_type)
        if entity is None:
            return None
        
        # Determine which fields to select
        if intent.requested_fields:
            selected_fields = intent.requested_fields
        else:
            # Default: all non-relation fields
            selected_fields = [f.graphql_name for f in entity.fields if not f.is_relation]
        
        # Check if we need to include relations
        include_relations = any(
            f.graphql_name in intent.requested_fields or "author" in intent.requested_fields
            for f in entity.fields if f.is_relation
        )
        
        # Validate and prepare parameters
        validated_params = self._validate_parameters(intent.parameters, operation)
        
        # Generate the GraphQL query
        graphql_query = self._generate_graphql(
            operation=operation,
            parameters=validated_params,
            fields=selected_fields,
            entity=entity,
            include_relations=include_relations or not intent.requested_fields
        )
        
        return QueryPlan(
            operation=operation,
            parameters=validated_params,
            selected_fields=selected_fields,
            include_relations=include_relations,
            graphql_query=graphql_query
        )
    
    def _validate_parameters(self, params: Dict[str, Any], operation: Operation) -> Dict[str, Any]:
        """Validate and type-cast parameters according to operation definition."""
        validated = {}
        
        for param_name, param_type in operation.parameters.items():
            if param_name in params:
                value = params[param_name]
                
                # Type casting based on GraphQL type
                if "Int" in param_type:
                    validated[param_name] = int(value)
                elif "Float" in param_type:
                    validated[param_name] = float(value)
                elif "String" in param_type:
                    validated[param_name] = str(value)
                elif "Boolean" in param_type:
                    validated[param_name] = bool(value)
                else:
                    validated[param_name] = value
        
        return validated
    
    def _generate_graphql(
        self,
        operation: Operation,
        parameters: Dict[str, Any],
        fields: List[str],
        entity,
        include_relations: bool = True
    ) -> str:
        """Generate a GraphQL query string."""
        
        # Build field selection
        field_selection = self._build_field_selection(entity, fields, include_relations)
        
        # Handle mutations vs queries
        if operation.intent_type == IntentType.MUTATION_CREATE:
            return self._generate_mutation(operation, parameters, field_selection)
        else:
            return self._generate_query(operation, parameters, field_selection)
    
    def _build_field_selection(self, entity, fields: List[str], include_relations: bool) -> str:
        """Build the field selection part of a GraphQL query."""
        lines = []
        
        for f in entity.fields:
            if f.graphql_name in fields or not fields:
                if f.is_relation and include_relations:
                    # Get related entity fields
                    related_entity_type = EntityType(f.related_entity)
                    related_entity = self.ontology.get_entity(related_entity_type)
                    if related_entity:
                        related_fields = " ".join(
                            rf.graphql_name for rf in related_entity.fields 
                            if not rf.is_relation
                        )
                        lines.append(f"    {f.graphql_name} {{ {related_fields} }}")
                elif not f.is_relation:
                    lines.append(f"    {f.graphql_name}")
        
        return "\n".join(lines)
    
    def _generate_query(self, operation: Operation, parameters: Dict[str, Any], fields: str) -> str:
        """Generate a GraphQL query."""
        if parameters:
            # Query with parameters
            param_str = ", ".join(f"{k}: {self._format_value(v)}" for k, v in parameters.items())
            return f"""{{
  {operation.graphql_name}({param_str}) {{
{fields}
  }}
}}"""
        else:
            # Query without parameters
            return f"""{{
  {operation.graphql_name} {{
{fields}
  }}
}}"""
    
    def _generate_mutation(self, operation: Operation, parameters: Dict[str, Any], fields: str) -> str:
        """Generate a GraphQL mutation."""
        param_str = ", ".join(f"{k}: {self._format_value(v)}" for k, v in parameters.items())
        
        return f"""mutation {{
  {operation.graphql_name}({param_str}) {{
{fields}
  }}
}}"""
    
    def _format_value(self, value: Any) -> str:
        """Format a Python value for GraphQL."""
        if isinstance(value, str):
            # Escape quotes and wrap in quotes
            escaped = value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif value is None:
            return "null"
        else:
            return str(value)
    
    def explain_plan(self, plan: QueryPlan) -> str:
        """Generate a human-readable explanation of the query plan."""
        op = plan.operation
        
        explanation = f"Operation: {op.description}\n"
        explanation += f"GraphQL Operation: {op.graphql_name}\n"
        
        if plan.parameters:
            explanation += f"Parameters: {plan.parameters}\n"
        
        explanation += f"Selected Fields: {', '.join(plan.selected_fields)}\n"
        explanation += f"Include Relations: {plan.include_relations}\n"
        
        return explanation
