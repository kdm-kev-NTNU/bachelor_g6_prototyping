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

**Note**: If you encounter NumPy 2.0 compatibility issues with ChromaDB, ensure NumPy < 2.0.0 is installed:
```bash
pip install "numpy>=1.24.0,<2.0.0"
```

### 2. Configure API Key

Set environment variable for API key (OpenAI or Eino):

```bash
# Windows PowerShell
$env:EINO_API_KEY = "your-openai-api-key"  # Can use OpenAI key directly

# For Eino server (optional):
$env:EINO_BASE_URL = "http://localhost:8080/v1"  # Only if using Eino server

# Linux/Mac
export EINO_API_KEY="your-openai-api-key"
export EINO_BASE_URL="http://localhost:8080/v1"  # Optional
```

**Note**: 
- If `EINO_BASE_URL` is not set, the system will use OpenAI directly
- If `EINO_BASE_URL` is set, it will use Eino server
- You can use your OpenAI API key directly: `$env:EINO_API_KEY = "sk-..."`

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
