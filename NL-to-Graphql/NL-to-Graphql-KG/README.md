# NL-to-KG: Natural Language to Knowledge Graph

> Spør kunnskapsgrafen med naturlig språk via GraphQL

## Pipeline Oversikt

```
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐     ┌──────────┐
│   NL    │ ──► │  Intent  │ ──► │ GraphQL │ ──► │ Cypher  │ ──► │ FalkorDB │
│  Query  │     │ Extract  │     │  Query  │     │  Query  │     │  Execute │
└─────────┘     └──────────┘     └─────────┘     └─────────┘     └──────────┘
     │                                                                 │
     │                         ┌──────────┐                           │
     └─────────────────────────│ Response │◄──────────────────────────┘
                               │ Format   │
                               └──────────┘
```

### Pipeline Stages

| Stage | Input | Output | Component |
|-------|-------|--------|-----------|
| 1️⃣ Intent Extraction | "Vis alle sensorer" | `{type: QUERY_LIST, entity: Sensor}` | `IntentExtractor` |
| 2️⃣ GraphQL Generation | Intent object | `{ sensors { id name } }` | `GraphQLGenerator` |
| 3️⃣ Cypher Resolution | GraphQL query | `MATCH (s:brick_Sensor)...` | `GraphQLToCypherResolver` |
| 4️⃣ Query Execution | Cypher query | `[{name: "Temp1"}, ...]` | `FalkorDBClient` |
| 5️⃣ Response Formatting | Results | "Fant 10 sensorer: ..." | `KGPipeline` |

---

## Hurtigstart

### 1. Start FalkorDB

```bash
docker start falkordb falkordb-browser
```

### 2. Last inn data

```bash
cd ../FalkorDB
python load_graph.py --clear
```

### 3. Installer avhengigheter

```bash
pip install -r requirements.txt
```

### 4. Start Web UI 🌐

```bash
python api.py
```

Åpne **http://localhost:8080** i nettleseren!

![Web UI](static/screenshot.png)

### 5. Alternativ: CLI

```bash
# Interaktiv modus
python cli.py

# Med pipeline-visning
python cli.py "Vis alle sensorer" --pipeline

# JSON output
python cli.py "List sensors" --format json --lang en
```

---

## Eksempel: Full Pipeline

**Spørring:** "Vis alle temperatursensorer i bygget"

### Stage 1: Intent Extraction
```json
{
  "intent_type": "query_list",
  "entity_class": "brick_Temperature_Sensor",
  "parameters": {},
  "confidence": 0.85
}
```

### Stage 2: GraphQL Query
```graphql
query ListSensors {
  sensors(sensorType: "Temperature_Sensor") {
    id
    name
    unit
    sensorType
  }
}
```

### Stage 3: Cypher Query
```cypher
MATCH (s:brick_Temperature_Sensor)
RETURN s {.id, .name, .unit, sensorType: labels(s)[0]}
```

### Stage 4: FalkorDB Results
```json
[
  {"id": "sensor_temp_foyer", "name": "Temperatur Foyer", "unit": "degC"},
  {"id": "sensor_temp_hall", "name": "Temperatur Hovedsal", "unit": "degC"}
]
```

### Stage 5: Natural Response
```
Fant 2 resultater:

  1. Temperatur Foyer | unit: degC | sensor: Temperature_Sensor
  2. Temperatur Hovedsal | unit: degC | sensor: Temperature_Sensor
```

---

## GraphQL Schema

Pipelinen bruker et GraphQL-skjema som mapper til Brick Ontology:

### Queries

```graphql
type Query {
    # Single entity
    building(id: String, name: String): Building
    
    # Lists
    buildings: [Building!]!
    floors(buildingId: String): [Floor!]!
    zones(floorId: String, buildingId: String): [HVACZone!]!
    systems(buildingId: String, systemType: String): [System!]!
    equipment(systemId: String, equipmentType: String): [Equipment!]!
    sensors(zoneId: String, equipmentId: String, sensorType: String): [Sensor!]!
    meters(buildingId: String): [Meter!]!
    timeseries(sensorId: String): [Timeseries!]!
    
    # Aggregations
    sensorCount(sensorType: String): Int!
    equipmentCount(equipmentType: String): Int!
}
```

### Types

```graphql
type Building {
    id: String!
    name: String!
    address: String
    areaSqm: Float
    floors: [Floor!]!
    systems: [System!]!
    meters: [Meter!]!
}

type Sensor {
    id: String!
    name: String!
    unit: String
    sensorType: String!
    timeseries: Timeseries
}

type Equipment {
    id: String!
    name: String!
    equipmentType: String!
    sensors: [Sensor!]!
}
```

---

## Web UI 🌐

Start serveren og åpne http://localhost:8080:

```bash
python api.py
```

**Funksjoner:**
- 📝 Skriv spørringer på norsk eller engelsk
- ⚡ Se GraphQL og Cypher som genereres
- 📊 Vis rådata fra databasen
- 🎨 Moderne, mørkt tema

---

## CLI (Alternativ)

```bash
# Interaktiv modus
python cli.py

# I interaktiv modus:
help      # Vis hjelp
debug     # Toggle debug info
graphql   # Vis siste GraphQL-spørring
cypher    # Vis siste Cypher-spørring
explain   # Full pipeline forklaring
exit      # Avslutt
```

---

## API

```bash
# Start API server
python api.py

# Endpoints:
# POST /query       - NL query
# GET  /query?q=... - NL query (GET)
# POST /cypher      - Direct Cypher
# GET  /schema      - GraphQL schema info
# GET  /health      - Health check
```

### Eksempel API-kall

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Vis alle sensorer", "language": "no"}'
```

Response:
```json
{
  "success": true,
  "query": "Vis alle sensorer",
  "response": "Fant 14 resultater: ...",
  "graphql": "query ListSensors { sensors { ... } }",
  "cypher": "MATCH (s) WHERE s:brick_Temperature_Sensor...",
  "results": [...]
}
```

---

## Arkitektur

```
NL-to-Graphql-KG/
├── __init__.py           # Package exports
├── ontology.py           # Brick Schema ontology
├── intent_extractor.py   # NL → Intent (LLM/rules)
├── graphql_schema.py     # GraphQL type definitions
├── graphql_generator.py  # Intent → GraphQL
├── graphql_to_cypher.py  # GraphQL → Cypher resolver
├── pipeline.py           # Main orchestrator
├── cli.py                # Command-line interface
├── api.py                # REST API
└── test_pipeline.py      # Tests
```

### Komponent-ansvar

| Komponent | Ansvar |
|-----------|--------|
| `BrickOntology` | Definerer entiteter, relasjoner, synonymer |
| `IntentExtractor` | Parser NL til strukturert intent |
| `GraphQLGenerator` | Lager GraphQL fra intent |
| `GraphQLToCypherResolver` | Oversetter GraphQL til Cypher |
| `KGPipeline` | Orkestrerer hele flyten |

---

## Brick Ontology Mapping

| Brick Class | GraphQL Type | Cypher Label |
|-------------|--------------|--------------|
| Building | `Building` | `:brick_Building` |
| Floor | `Floor` | `:brick_Floor` |
| HVAC_Zone | `HVACZone` | `:brick_HVAC_Zone` |
| Air_Handling_Unit | `Equipment` | `:brick_Air_Handling_Unit` |
| Temperature_Sensor | `Sensor` | `:brick_Temperature_Sensor` |
| Timeseries | `Timeseries` | `:brick_Timeseries` |

---

## Konfigurasjon

### Miljøvariabler

```bash
export FALKORDB_HOST=localhost
export FALKORDB_PORT=6379
export FALKORDB_GRAPH=energy_graph
export OPENAI_API_KEY=sk-...  # For LLM intent extraction
```

---

## Relaterte Prosjekter

- [FalkorDB](../FalkorDB/) - Graf-database med Brick data
- [Schema-RAG](../NL-to-Graphql/Schema-rag/) - RAG for schema
- [Semantic Planner](../NL-to-Graphql/semantic_planner/) - Original NL→GraphQL

---

## Lisens

MIT
