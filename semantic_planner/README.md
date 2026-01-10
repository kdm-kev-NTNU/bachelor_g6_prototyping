# Semantic Planner for GraphQL

En strukturert pipeline for å konvertere naturlig språk til GraphQL queries ved hjelp av semantisk planlegging.

## Arkitektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Semantic Pipeline                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │    NL    │───▶│  Intent  │───▶│  Query   │───▶│ GraphQL  │      │
│  │  Input   │    │Extractor │    │ Planner  │    │ Executor │      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│       │               │               │               │             │
│       │          (LLM-basert)    (Deterministisk) (Mekanisk)        │
│       │               │               │               │             │
│       │               ▼               ▼               ▼             │
│       │         ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│       │         │ Semantic │    │  Query   │    │  Result  │      │
│       │         │  Object  │    │   Plan   │    │   Data   │      │
│       │         └──────────┘    └──────────┘    └──────────┘      │
│       │                                               │             │
│       │                                               ▼             │
│       │                                         ┌──────────┐       │
│       └────────────────────────────────────────▶│ Response │       │
│                                                 │Formatter │       │
│                                                 └──────────┘       │
│                                                 (LLM-basert)        │
│                                                       │             │
│                                                       ▼             │
│                                                 ┌──────────┐       │
│                                                 │  Naturlig│       │
│                                                 │  Respons │       │
│                                                 └──────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

## Pipeline Steg

### 1. NL → Semantic Extraction (LLM)
- **Input**: Naturlig språk query
- **Output**: Strukturert `ExtractedIntent`
- **Inneholder**: Intent type, entity type, parametere, ønskede felter

### 2. Semantic Object → Query Plan (Deterministisk)
- **Input**: `ExtractedIntent`
- **Output**: `QueryPlan`
- **Inneholder**: Operation, validerte parametere, felt-seleksjon

### 3. Query Plan → GraphQL (Mekanisk)
- **Input**: `QueryPlan`
- **Output**: GraphQL query string
- **100% deterministisk** - ingen LLM involvert

### 4. Result → Explanatory Text (LLM)
- **Input**: GraphQL resultat + kontekst
- **Output**: Naturlig språk respons
- **Støtter**: Norsk og engelsk

## Installasjon

```bash
cd semantic-planner
pip install -r requirements.txt
```

## Bruk

### CLI - Interaktiv modus

```bash
python -m semantic_planner.cli --interactive --verbose
```

### CLI - Enkelt spørsmål

```bash
python -m semantic_planner.cli "Vis meg alle brukere"
python -m semantic_planner.cli "Get the product with id 1" --language en
```

### API Server

```bash
# Start semantic planner API på port 8001
python -m semantic_planner.api

# Eller integrer i eksisterende FastAPI app
```

### Programmatisk

```python
import asyncio
from semantic_planner import SemanticPipeline

async def main():
    pipeline = SemanticPipeline(
        graphql_endpoint="http://localhost:8000/graphql",
        language="no"
    )
    
    result = await pipeline.process("Vis meg alle produkter")
    
    print(result.natural_response)
    print(result.graphql_query)

asyncio.run(main())
```

## API Endpoints

| Endpoint | Metode | Beskrivelse |
|----------|--------|-------------|
| `/semantic-query` | POST | Prosesser naturlig språk query |
| `/semantic-query/operations` | GET | Liste støttede operasjoner |
| `/semantic-query/ontology` | GET | Hent domene-ontologien |
| `/health` | GET | Health check |

### Eksempel Request

```bash
curl -X POST http://localhost:8001/semantic-query \
  -H "Content-Type: application/json" \
  -d '{"query": "Vis meg alle brukere", "include_debug": true}'
```

### Eksempel Response

```json
{
  "success": true,
  "query": "Vis meg alle brukere",
  "response": "Fant 4 brukere:\n1. Alice Johnson (alice@example.com)\n...",
  "graphql": "{ users { id name email } }",
  "result": {"data": {"users": [...]}},
  "debug": {"stages": ["intent_extraction", "query_planning", "graphql_execution", "response_formatting"]}
}
```

## Domain Ontology

Ontologien definerer:

### Entiteter
- **User**: id, name, email
- **Post**: id, title, content, authorId, author
- **Product**: id, name, price, description

### Operasjoner
- `get_users` / `get_user(id)`
- `get_posts` / `get_post(id)`
- `get_products` / `get_product(id)`
- `create_user(name, email)`
- `create_post(title, content, authorId)`

### Intent Types
- `QUERY_LIST` - Hent alle
- `QUERY_SINGLE` - Hent én med ID
- `MUTATION_CREATE` - Opprett ny
- `MUTATION_UPDATE` - Oppdater
- `MUTATION_DELETE` - Slett

## Styrker vs RAG

| Aspekt | Semantic Planner | RAG |
|--------|------------------|-----|
| **Skalerbarhet** | ✅ Skalerer i antall spørsmål | ❌ Trenger mer kontekst |
| **Determinisme** | ✅ Query-generering er 100% testbar | ❌ Varierende output |
| **Testbarhet** | ✅ Enkelt å enhetsteste | ❌ Vanskelig å teste |
| **Ontologi-fit** | ✅ Perfekt for strukturerte domener | ❌ Bedre for ustrukturert |
| **Oppsett** | ❌ Krever ontologi-design | ✅ Raskere å sette opp |

## Utvidelse

### Legge til ny entitet

1. Definer i `ontology.py`:
```python
self.entities[EntityType.NEW_ENTITY] = Entity(
    name="new_entity",
    graphql_type="NewEntityType",
    fields=[...],
    synonyms=["synonym1", "synonym2"]
)
```

2. Legg til operasjoner:
```python
self.operations["get_new_entities"] = Operation(...)
```

### Legge til nye intent patterns

```python
self.intent_patterns[IntentType.QUERY_LIST].extend([
    "new pattern", "another pattern"
])
```

## Filstruktur

```
semantic-planner/
├── __init__.py          # Package exports
├── ontology.py          # Domain model og entiteter
├── intent_extractor.py  # LLM-basert intent ekstraksjon
├── query_planner.py     # Deterministisk query planning
├── response_formatter.py # LLM-basert respons formatering
├── pipeline.py          # Hovedpipeline orchestration
├── api.py               # FastAPI endpoints
├── cli.py               # Command-line interface
├── requirements.txt     # Dependencies
└── README.md            # Dokumentasjon
```

## Miljøvariabler

```bash
OPENAI_API_KEY=sk-...  # Required for LLM components
```

## Fremtidig arbeid

- [ ] Støtte for mer komplekse queries (filtering, pagination)
- [ ] Caching av intent ekstraksjon
- [ ] Støtte for flere språk
- [ ] GraphQL subscriptions
- [ ] Batch processing
