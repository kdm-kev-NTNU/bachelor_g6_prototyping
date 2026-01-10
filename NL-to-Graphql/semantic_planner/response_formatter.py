"""
Response Formatter - LLM-based natural language response generation.

Pipeline Step 4: Result → Explanatory Text
"""
import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI

from .ontology import DomainOntology
from .query_planner import QueryPlan


class ResponseFormatter:
    """
    Formats GraphQL results into natural language explanations.
    
    Uses LLM to generate human-friendly responses.
    """
    
    def __init__(self, ontology: DomainOntology, api_key: Optional[str] = None):
        self.ontology = ontology
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def format(
        self,
        result: Dict[str, Any],
        plan: QueryPlan,
        original_query: str,
        language: str = "no"  # Norwegian default
    ) -> str:
        """
        Format GraphQL result into natural language.
        
        Args:
            result: GraphQL query result
            plan: The query plan that was executed
            original_query: Original natural language query
            language: Response language (no=Norwegian, en=English)
            
        Returns:
            Natural language explanation of the result
        """
        # Handle errors
        if "errors" in result:
            return self._format_error(result["errors"], language)
        
        # Get the data
        data = result.get("data", {})
        operation_data = data.get(plan.operation.graphql_name)
        
        if operation_data is None:
            return self._no_results_message(plan, language)
        
        # Use LLM to format the response
        return self._llm_format(
            data=operation_data,
            plan=plan,
            original_query=original_query,
            language=language
        )
    
    def _llm_format(
        self,
        data: Any,
        plan: QueryPlan,
        original_query: str,
        language: str
    ) -> str:
        """Use LLM to generate natural language response."""
        
        lang_instruction = "Respond in Norwegian." if language == "no" else "Respond in English."
        
        system_prompt = f"""You are a helpful assistant that explains database query results in natural language.

{lang_instruction}

Guidelines:
- Be concise but informative
- Use bullet points for lists
- Highlight important information
- If the result is empty, explain that no data was found
- Format numbers and dates nicely
- For prices, use currency formatting
"""
        
        user_prompt = f"""Original question: "{original_query}"

Query executed: {plan.operation.description}

Result data:
{json.dumps(data, indent=2, ensure_ascii=False)}

Please explain this result in a natural, friendly way."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Fallback to simple formatting
            return self._simple_format(data, plan)
    
    def _simple_format(self, data: Any, plan: QueryPlan) -> str:
        """Simple fallback formatting without LLM."""
        if isinstance(data, list):
            if len(data) == 0:
                return f"Ingen {plan.operation.entity.value}er funnet."
            
            result = f"Fant {len(data)} {plan.operation.entity.value}(er):\n\n"
            for i, item in enumerate(data, 1):
                result += f"{i}. "
                if isinstance(item, dict):
                    parts = []
                    if "name" in item:
                        parts.append(item["name"])
                    if "title" in item:
                        parts.append(item["title"])
                    if "email" in item:
                        parts.append(f"({item['email']})")
                    if "price" in item:
                        parts.append(f"kr {item['price']:.2f}")
                    result += " - ".join(parts) + "\n"
                else:
                    result += str(item) + "\n"
            return result
        
        elif isinstance(data, dict):
            result = f"{plan.operation.entity.value.title()}:\n"
            for key, value in data.items():
                if isinstance(value, dict):
                    result += f"  {key}: {value.get('name', value)}\n"
                else:
                    result += f"  {key}: {value}\n"
            return result
        
        return str(data)
    
    def _format_error(self, errors: list, language: str) -> str:
        """Format GraphQL errors."""
        if language == "no":
            msg = "Det oppstod en feil:\n"
        else:
            msg = "An error occurred:\n"
        
        for error in errors:
            msg += f"- {error.get('message', 'Unknown error')}\n"
        
        return msg
    
    def _no_results_message(self, plan: QueryPlan, language: str) -> str:
        """Generate a 'no results' message."""
        entity = plan.operation.entity.value
        
        if language == "no":
            return f"Ingen {entity} funnet med de angitte kriteriene."
        else:
            return f"No {entity} found matching the specified criteria."
    
    def format_simple(self, data: Any, plan: QueryPlan) -> str:
        """Format without using LLM (for testing or when LLM is unavailable)."""
        return self._simple_format(data, plan)
