# LLM-as-Judge Testing System for Energy Advice

Testing system for evaluating energy advice quality using LLM-as-judge methodology with Eino platform.

## Overview

This system generates energy advice based on building data using RAG (Retrieval-Augmented Generation), then evaluates the advice structure using a fixed rubric via LLM-as-judge. The system uses **Eino platform** for all LLM calls.

## Architecture

```
PDF Documents → Docling → Text Chunks → Chroma Vector DB
                                 ↓
Building Data → Hybrid Retrieval → RAG Advisor (Eino) → Advice
                                                          ↓
Fixed Rubric → LLM-as-Judge (Eino) → Evaluation Scores
```

## Setup

### 1. Install Dependencies

```bash
cd "Eino testing"
pip install -r requirements.txt
```

### 2. Configure Eino Platform

Set environment variables for Eino platform:

```bash
# Windows PowerShell
$env:EINO_API_KEY = "your-eino-api-key"
$env:EINO_BASE_URL = "http://localhost:8080/v1"  # Or your Eino server URL

# Linux/Mac
export EINO_API_KEY="your-eino-api-key"
export EINO_BASE_URL="http://localhost:8080/v1"
```

**Note**: Eino is a Golang-based framework. You need either:
- An Eino server running (configure base URL)
- Or Eino API gateway endpoint
- See [Eino Documentation](https://www.cloudwego.io/docs/eino/) for setup

### 3. Initialize Vector Database

Process PDFs and store in Chroma:

```bash
python vector_db.py
```

Or via API:

```bash
curl -X POST http://localhost:8000/initialize-db
```

### 4. Run Server

```bash
python app.py
```

Server starts on `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```

### List Buildings
```
GET /buildings
```

### Get Building
```
GET /buildings/{building_id}
```

### Generate Advice
```
POST /advice
{
  "building_id": "building_1",
  "query": "Optional specific query"
}
```

### Evaluate Advice (Judge Only)
```
POST /judge
{
  "advice": "Advice text to evaluate",
  "building_data": {...}  // Optional
}
```

### Full Pipeline (Advice + Judge)
```
POST /evaluate
{
  "building_id": "building_1",
  "query": "Optional query"
}
```

## Judge Rubric

The LLM-as-judge evaluates advice based on fixed criteria (0-2 points each, max 10):

- **Dataforankring**: References input data explicitly
- **Intern konsistens**: No self-contradictions  
- **Fakta vs antagelser**: Distinguishes observation from interpretation
- **Usikkerhet**: Acknowledges data/conclusion limitations
- **Rådgivende tone**: Suggests, doesn't instruct

**Important**: Judge evaluates ONLY structure, NOT professional correctness.

## Components

- **`eino_client.py`**: Eino platform client wrapper
- **`pdf_processor.py`**: PDF parsing with Docling
- **`vector_db.py`**: Chroma vector database setup
- **`retriever.py`**: Hybrid retrieval (semantic + keyword)
- **`advisor.py`**: RAG-based advice generation using Eino
- **`judge.py`**: LLM-as-judge evaluation using Eino
- **`building_data.py`**: Fictional building data generator
- **`app.py`**: FastAPI backend server
- **`config.py`**: Configuration and prompts

## Eino Platform Integration

All LLM calls go through Eino platform:
- Chat completions (advisor and judge)
- Embeddings (vector database)

The `eino_client.py` provides an OpenAI-compatible interface, making it easy to swap between providers.

## Testing

Open `ui/index.html` in browser or access via `http://localhost:8000` to test the system with multiple building scenarios.

## References

- [Eino Documentation](https://www.cloudwego.io/docs/eino/)
- [Eino ChatModel Guide](https://www.cloudwego.io/docs/eino/core_modules/components/chat_model/)
