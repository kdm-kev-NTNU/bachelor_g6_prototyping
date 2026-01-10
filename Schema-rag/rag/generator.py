"""Generate GraphQL queries from natural language using RAG."""
from rag.retriever import retrieve_schema_info
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_graphql_query(natural_language_query: str) -> str:
    """
    Generate GraphQL query from natural language using RAG.
    
    Args:
        natural_language_query: User's natural language query
        
    Returns:
        Generated GraphQL query string
    """
    # Retrieve relevant schema information
    schema_docs = retrieve_schema_info(natural_language_query, n_results=5)
    
    # Build context from retrieved documents
    context = "\n\n".join([
        f"- {doc['text']}" for doc in schema_docs
    ])
    
    # Create prompt for GPT
    prompt = f"""You are a GraphQL query generator. Given a natural language query and relevant schema information, generate a valid GraphQL query.

GraphQL Schema Information:
{context}

User Query: {natural_language_query}

Instructions:
1. Generate ONLY the GraphQL query, nothing else
2. Use proper GraphQL syntax
3. Include only the fields that are relevant to the query
4. Use camelCase for field names (e.g., authorId not author_id)
5. For mutations, use camelCase (e.g., createUser, createPost)
6. Do not include any explanations or markdown formatting
7. Return only the raw GraphQL query

GraphQL Query:"""

    # Generate query using GPT
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a GraphQL expert. Generate valid GraphQL queries based on natural language and schema information."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )
    
    graphql_query = response.choices[0].message.content.strip()
    
    # Clean up the query (remove markdown code blocks if present)
    graphql_query = re.sub(r'```graphql\n?', '', graphql_query)
    graphql_query = re.sub(r'```\n?', '', graphql_query)
    graphql_query = graphql_query.strip()
    
    return graphql_query


def validate_graphql_query(query: str) -> tuple[bool, str]:
    """
    Basic validation of GraphQL query syntax.
    
    Args:
        query: GraphQL query string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query:
        return False, "Query is empty"
    
    # Basic checks
    if not (query.strip().startswith("query") or query.strip().startswith("mutation") or query.strip().startswith("{")):
        return False, "Query must start with 'query', 'mutation', or '{'"
    
    # Check for balanced braces
    if query.count("{") != query.count("}"):
        return False, "Unbalanced braces in query"
    
    return True, ""

