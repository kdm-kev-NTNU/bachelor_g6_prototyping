"""
FastAPI Interface for NL-to-KG Pipeline

Web API and UI for querying the Brick Ontology knowledge graph
with natural language.

Pipeline: NL → Intent → GraphQL → Cypher → FalkorDB → Response
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import KGPipeline


# ============================================================================
# Models
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for NL query."""
    query: str
    language: str = "no"


class QueryResponse(BaseModel):
    """Response model for NL query."""
    success: bool
    query: str
    response: str
    # Pipeline stages
    intent: Optional[Dict[str, Any]] = None
    graphql: Optional[str] = None
    graphql_variables: Optional[Dict[str, Any]] = None
    cypher: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None


class ExplainResponse(BaseModel):
    """Response for pipeline explanation."""
    original_query: str
    stage_1_intent: Dict[str, Any]
    stage_2_graphql: Dict[str, Any]
    stage_3_cypher: Dict[str, Any]


class CypherRequest(BaseModel):
    """Request model for direct Cypher query."""
    cypher: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database_connected: bool
    graph_name: str
    pipeline: str


# ============================================================================
# App Setup
# ============================================================================

# Global pipeline instance
_pipeline: Optional[KGPipeline] = None

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"


def get_pipeline() -> KGPipeline:
    """Get or create pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = KGPipeline(
            falkor_host=os.getenv("FALKORDB_HOST", "localhost"),
            falkor_port=int(os.getenv("FALKORDB_PORT", "6379")),
            graph_name=os.getenv("FALKORDB_GRAPH", "energy_graph"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        _pipeline.connect()
    return _pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print("\n" + "=" * 60)
    print("  NL-to-KG: Natural Language to Knowledge Graph")
    print("  Pipeline: NL → Intent → GraphQL → Cypher → FalkorDB")
    print("=" * 60)
    
    try:
        get_pipeline()
        print("\n✓ Pipeline initialized")
        print("✓ FalkorDB connected")
    except Exception as e:
        print(f"\n⚠ Pipeline initialization failed: {e}")
    
    print(f"\n🌐 Web UI: http://localhost:8080")
    print(f"📚 API Docs: http://localhost:8080/docs")
    print("=" * 60 + "\n")
    
    yield
    
    # Shutdown
    global _pipeline
    if _pipeline:
        _pipeline.close()
        _pipeline = None


app = FastAPI(
    title="NL-to-KG",
    description="""
Natural Language to Knowledge Graph API for Brick Ontology.

**Pipeline:** NL → Intent → GraphQL → Cypher → FalkorDB → Response

Query the building knowledge graph using natural language in Norwegian or English.
    """,
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Static Files & UI
# ============================================================================

@app.get("/", include_in_schema=False)
async def serve_ui():
    """Serve the web UI."""
    return FileResponse(STATIC_DIR / "index.html")


# Mount static files (if needed for additional assets)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API and database health."""
    pipeline = get_pipeline()
    connected = pipeline._client is not None
    
    return HealthResponse(
        status="ok" if connected else "degraded",
        database_connected=connected,
        graph_name=pipeline._falkor_config["graph_name"],
        pipeline="NL → Intent → GraphQL → Cypher → FalkorDB"
    )


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query through the full pipeline.
    
    Pipeline: NL → Intent → GraphQL → Cypher → FalkorDB
    
    Examples:
    - "Vis alle sensorer i bygget"
    - "Which zones does the AHU feed?"
    - "List temperatursensorer"
    """
    pipeline = get_pipeline()
    
    # Set language
    pipeline.language = request.language
    
    result = pipeline.process(request.query)
    
    return QueryResponse(
        success=result.success,
        query=result.original_query,
        response=result.natural_response,
        intent=result.extracted_intent.to_dict() if result.extracted_intent else None,
        graphql=result.graphql_query.query if result.graphql_query else None,
        graphql_variables=result.graphql_query.variables if result.graphql_query else None,
        cypher=result.cypher_query.cypher if result.cypher_query else None,
        results=result.raw_results
    )


@app.get("/query")
async def query_get(
    q: str = Query(..., description="Natural language query"),
    lang: str = Query("no", description="Response language (no/en)")
):
    """
    Process a natural language query (GET method).
    
    Example: /query?q=Vis%20alle%20sensorer&lang=no
    """
    request = QueryRequest(query=q, language=lang)
    return await process_query(request)


@app.post("/explain", response_model=ExplainResponse)
async def explain_query(request: QueryRequest):
    """
    Explain how a query would be processed without executing it.
    
    Shows all pipeline stages: Intent → GraphQL → Cypher
    """
    pipeline = get_pipeline()
    explanation = pipeline.explain(request.query)
    
    return ExplainResponse(
        original_query=explanation["original_query"],
        stage_1_intent=explanation["stage_1_intent"],
        stage_2_graphql=explanation["stage_2_graphql"],
        stage_3_cypher=explanation["stage_3_cypher"]
    )


@app.post("/cypher")
async def execute_cypher(request: CypherRequest):
    """
    Execute a raw Cypher query directly against FalkorDB.
    
    Warning: This bypasses the NL→GraphQL pipeline.
    For debugging/admin use only.
    """
    pipeline = get_pipeline()
    
    if pipeline._client is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        results = pipeline._client.query(request.cypher)
        return {
            "success": True,
            "cypher": request.cypher,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/schema")
async def get_schema():
    """
    Get the Brick ontology schema information.
    
    Shows entities, GraphQL types, and available queries.
    """
    pipeline = get_pipeline()
    
    entities = {}
    for brick_class, entity in pipeline.ontology.entities.items():
        entities[brick_class.value] = {
            "name": entity.name,
            "description": entity.description,
            "properties": entity.properties,
            "synonyms_no": entity.synonyms_no[:3],
            "synonyms_en": entity.synonyms_en[:3]
        }
    
    graphql_queries = [
        "building(id, name) → Building",
        "buildings → [Building]",
        "floors(buildingId) → [Floor]",
        "zones(floorId, buildingId) → [HVACZone]",
        "systems(buildingId, systemType) → [System]",
        "equipment(systemId, equipmentType) → [Equipment]",
        "sensors(zoneId, equipmentId, sensorType) → [Sensor]",
        "meters(buildingId) → [Meter]",
        "timeseries(sensorId) → [Timeseries]",
        "sensorCount(sensorType) → Int",
        "equipmentCount(equipmentType) → Int"
    ]
    
    return {
        "pipeline": "NL → Intent → GraphQL → Cypher → FalkorDB",
        "brick_entities": entities,
        "graphql_queries": graphql_queries
    }


@app.get("/examples")
async def get_examples():
    """Get example queries in Norwegian and English."""
    return {
        "norwegian": [
            "Vis alle sensorer i bygget",
            "Hvilke soner mater AHU-en?",
            "List alle temperatursensorer",
            "Hva er bygningens adresse?",
            "Vis tidsserie-IDer",
            "Sensorer i Foyer",
            "Antall etasjer",
            "Vis alle målere",
            "Hvilket utstyr finnes i HVAC-systemet?",
        ],
        "english": [
            "Show all sensors in the building",
            "Which zones does the AHU feed?",
            "List all temperature sensors",
            "What is the building address?",
            "Show timeseries IDs",
            "Sensors in Foyer zone",
            "Number of floors",
            "Show all meters",
            "What equipment is in the HVAC system?",
        ]
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
