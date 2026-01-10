"""API routes for the application."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag.generator import generate_graphql_query, validate_graphql_query
from graphql.schema import schema
from strawberry.fastapi import GraphQLRouter


class NLQueryRequest(BaseModel):
    """Request model for natural language query."""
    query: str


class NLQueryResponse(BaseModel):
    """Response model for natural language query."""
    graphql_query: str
    result: dict


# Create FastAPI app
app = FastAPI(title="RAG-Enhanced GraphQL API", version="1.0.0")

# Add GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAG-Enhanced GraphQL API",
        "endpoints": {
            "/graphql": "GraphQL endpoint",
            "/nl-to-graphql": "Convert natural language to GraphQL"
        }
    }


@app.post("/nl-to-graphql", response_model=NLQueryResponse)
async def nl_to_graphql(request: NLQueryRequest):
    """
    Convert natural language query to GraphQL and execute it.
    
    Args:
        request: Natural language query request
        
    Returns:
        Generated GraphQL query and execution result
    """
    try:
        # Generate GraphQL query from natural language
        graphql_query = generate_graphql_query(request.query)
        
        # Validate the query
        is_valid, error_msg = validate_graphql_query(graphql_query)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid GraphQL query: {error_msg}")
        
        # Execute the GraphQL query
        result = await schema.execute(graphql_query)
        
        if result.errors:
            raise HTTPException(
                status_code=400,
                detail=f"GraphQL execution errors: {[str(e) for e in result.errors]}"
            )
        
        return NLQueryResponse(
            graphql_query=graphql_query,
            result=result.data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

