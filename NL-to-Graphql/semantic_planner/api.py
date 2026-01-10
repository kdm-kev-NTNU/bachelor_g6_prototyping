"""
FastAPI endpoints for the Semantic Planner.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from .pipeline import SemanticPipeline


# Create FastAPI app
app = FastAPI(
    title="Semantic GraphQL Planner",
    description="Natural language to GraphQL using semantic planning",
    version="1.0.0"
)

# Initialize pipeline (singleton)
_pipeline: Optional[SemanticPipeline] = None


def get_pipeline() -> SemanticPipeline:
    """Get or create the pipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = SemanticPipeline()
    return _pipeline


class QueryRequest(BaseModel):
    """Request model for natural language query."""
    query: str
    language: Optional[str] = "no"
    include_debug: Optional[bool] = False


class QueryResponse(BaseModel):
    """Response model for processed query."""
    success: bool
    query: str
    response: str
    graphql: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    debug: Optional[Dict[str, Any]] = None


@app.post("/semantic-query", response_model=QueryResponse)
async def semantic_query(request: QueryRequest) -> QueryResponse:
    """
    Process a natural language query using semantic planning.
    
    Pipeline:
    1. NL → Intent Extraction (LLM)
    2. Intent → Query Plan
    3. Plan → GraphQL Query
    4. Execute GraphQL
    5. Result → Natural Response (LLM)
    """
    pipeline = get_pipeline()
    pipeline.language = request.language or "no"
    
    result = await pipeline.process(request.query)
    
    return QueryResponse(
        success=result.success,
        query=result.original_query,
        response=result.natural_response,
        graphql=result.graphql_query,
        result=result.graphql_result,
        debug=result.debug_info if request.include_debug else None
    )


@app.get("/semantic-query/operations")
async def get_operations():
    """Get list of supported operations."""
    pipeline = get_pipeline()
    return pipeline.get_supported_operations()


@app.get("/semantic-query/ontology")
async def get_ontology():
    """Get the domain ontology as JSON."""
    pipeline = get_pipeline()
    return pipeline.ontology.to_dict()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "semantic-planner"}


# For running standalone
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
