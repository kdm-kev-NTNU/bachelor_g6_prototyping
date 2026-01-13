"""
FastAPI backend server for LLM-as-Judge testing system.
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from building_data import generate_buildings, get_building_dict, Building
from advisor import create_advisor, EnergyAdvisor
from judge import create_judge, LLMJudge, JudgeEvaluation
from vector_db import initialize_vector_db, get_collection

load_dotenv()

app = FastAPI(
    title="LLM-as-Judge Testing System",
    description="Testing system for evaluating energy advice quality",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
_advisor: Optional[EnergyAdvisor] = None
_judge: Optional[LLMJudge] = None
_buildings: List[Building] = []


def get_advisor() -> EnergyAdvisor:
    """Lazy-load advisor."""
    global _advisor
    if _advisor is None:
        _advisor = create_advisor()
    return _advisor


def get_judge() -> LLMJudge:
    """Lazy-load judge."""
    global _judge
    if _judge is None:
        _judge = create_judge()
    return _judge


def get_buildings() -> List[Building]:
    """Lazy-load buildings."""
    global _buildings
    if not _buildings:
        _buildings = generate_buildings(10)
    return _buildings


# Request/Response Models
class BuildingResponse(BaseModel):
    """Building data response."""
    id: str
    name: str
    age: int
    size_m2: float
    construction_type: str
    building_type: str
    current_energy_kwh: float
    expected_energy_kwh: float
    energy_excess_percent: float
    details: Dict[str, Any]


class AdviceRequest(BaseModel):
    """Request for advice generation."""
    building_id: str
    query: Optional[str] = None


class AdviceResponse(BaseModel):
    """Advice response."""
    advice: str
    citations: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    building: BuildingResponse


class JudgeRequest(BaseModel):
    """Request for judge evaluation."""
    advice: str
    building_data: Optional[Dict[str, Any]] = None


class JudgeResponse(BaseModel):
    """Judge evaluation response."""
    data_referencing: int
    internal_consistency: int
    fact_vs_assumption: int
    uncertainty_acknowledgement: int
    advisory_tone: int
    total_score: int
    comment: str


class EvaluateRequest(BaseModel):
    """Request for full pipeline (advice + judge)."""
    building_id: str
    query: Optional[str] = None


class EvaluateResponse(BaseModel):
    """Full evaluation response."""
    building: BuildingResponse
    advice: str
    citations: List[Dict[str, Any]]
    evaluation: JudgeResponse
    metadata: Dict[str, Any]


# Endpoints
@app.get("/")
async def serve_index():
    """Serve frontend HTML."""
    ui_path = os.path.join(os.path.dirname(__file__), "ui", "index.html")
    if os.path.exists(ui_path):
        return FileResponse(ui_path)
    return {"message": "UI ikke funnet. Åpne ui/index.html direkte."}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    collection = get_collection()
    doc_count = collection.count()
    
    return {
        "status": "running",
        "version": "1.0.0",
        "vector_db_documents": doc_count,
        "advisor_available": _advisor is not None,
        "judge_available": _judge is not None
    }


@app.get("/buildings", response_model=List[BuildingResponse])
async def list_buildings():
    """List all test buildings."""
    buildings = get_buildings()
    return [get_building_dict(b) for b in buildings]


@app.get("/buildings/{building_id}", response_model=BuildingResponse)
async def get_building(building_id: str):
    """Get specific building."""
    buildings = get_buildings()
    building = next((b for b in buildings if b.id == building_id), None)
    
    if not building:
        raise HTTPException(status_code=404, detail="Bygning ikke funnet")
    
    return get_building_dict(building)


@app.post("/advice", response_model=AdviceResponse)
async def generate_advice(request: AdviceRequest):
    """Generate advice for a building."""
    buildings = get_buildings()
    building = next((b for b in buildings if b.id == request.building_id), None)
    
    if not building:
        raise HTTPException(status_code=404, detail="Bygning ikke funnet")
    
    building_dict = get_building_dict(building)
    
    advisor = get_advisor()
    result = advisor.generate_advice(building_dict, request.query)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return AdviceResponse(
        advice=result["advice"],
        citations=result["citations"],
        retrieved_docs=result["retrieved_docs"],
        metadata=result.get("metadata", {}),
        building=BuildingResponse(**building_dict)
    )


@app.post("/judge", response_model=JudgeResponse)
async def evaluate_advice(request: JudgeRequest):
    """Evaluate advice quality using LLM-as-judge."""
    judge = get_judge()
    evaluation = judge.evaluate(request.advice, request.building_data)
    
    return JudgeResponse(
        data_referencing=evaluation.data_referencing,
        internal_consistency=evaluation.internal_consistency,
        fact_vs_assumption=evaluation.fact_vs_assumption,
        uncertainty_acknowledgement=evaluation.uncertainty_acknowledgement,
        advisory_tone=evaluation.advisory_tone,
        total_score=evaluation.total_score,
        comment=evaluation.comment
    )


@app.post("/evaluate", response_model=EvaluateResponse)
async def full_evaluation(request: EvaluateRequest):
    """Full pipeline: generate advice and evaluate it."""
    buildings = get_buildings()
    building = next((b for b in buildings if b.id == request.building_id), None)
    
    if not building:
        raise HTTPException(status_code=404, detail="Bygning ikke funnet")
    
    building_dict = get_building_dict(building)
    
    # Generate advice
    advisor = get_advisor()
    advice_result = advisor.generate_advice(building_dict, request.query)
    
    if "error" in advice_result:
        raise HTTPException(status_code=500, detail=advice_result["error"])
    
    # Evaluate advice
    judge = get_judge()
    evaluation = judge.evaluate(advice_result["advice"], building_dict)
    
    return EvaluateResponse(
        building=BuildingResponse(**building_dict),
        advice=advice_result["advice"],
        citations=advice_result["citations"],
        evaluation=JudgeResponse(
            data_referencing=evaluation.data_referencing,
            internal_consistency=evaluation.internal_consistency,
            fact_vs_assumption=evaluation.fact_vs_assumption,
            uncertainty_acknowledgement=evaluation.uncertainty_acknowledgement,
            advisory_tone=evaluation.advisory_tone,
            total_score=evaluation.total_score,
            comment=evaluation.comment
        ),
        metadata={
            **advice_result.get("metadata", {}),
            "evaluation_timestamp": "now"
        }
    )


@app.post("/initialize-db")
async def initialize_database(force_reload: bool = False):
    """Initialize vector database with PDF documents."""
    try:
        initialize_vector_db(force_reload=force_reload)
        collection = get_collection()
        count = collection.count()
        return {
            "status": "success",
            "documents_stored": count,
            "message": f"Vector database initialisert med {count} dokumenter"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("=== LLM-as-Judge Testing System ===")
    print("Starter server på http://localhost:8000")
    print("Åpne http://localhost:8000/docs for API-dokumentasjon")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
