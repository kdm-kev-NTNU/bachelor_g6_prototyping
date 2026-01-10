# FalkorDB Brick Ontology Knowledge Graph

> Strict Brick Schema implementation for semantic query planning

## Brick Ontology

All classes and relations follow [Brick Schema](https://ontology.brickschema.org/):

- Labels prefixed with `brick_` (e.g., `brick_Building`)
- Relations prefixed with `brick_` (e.g., `brick_hasPart`)

## Graph Structure

```
brick_Building (ROOT)
├── brick_hasPart → brick_Floor
│   └── brick_hasPart → brick_HVAC_Zone
│       └── brick_hasPoint → brick_Temperature_Sensor
│           └── brick_hasTimeseries → brick_Timeseries
├── brick_hasPart → brick_HVAC_System
│   └── brick_hasMember → brick_Air_Handling_Unit
│       ├── brick_hasPoint → brick_Temperature_Sensor
│       │   └── brick_hasTimeseries → brick_Timeseries
│       └── brick_feeds → brick_HVAC_Zone
└── brick_isMeteredBy → brick_Electrical_Meter
    └── brick_hasPoint → brick_Power_Sensor
        └── brick_hasTimeseries → brick_Timeseries
```

---

## Start FalkorDB

```bash
# Database
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb

# Browser (http://localhost:3000)
docker run -d --name falkordb-browser -p 3000:3000 \
  -e FALKORDB_URL=host.docker.internal:6379 falkordb/falkordb-browser
```

## Load Graph

```bash
pip install -r requirements.txt
python load_graph.py --clear
```

---

## Cypher Queries

### Traversal: Building → System → Equipment → Sensor → Timeseries

```cypher
MATCH (b:brick_Building)-[:brick_hasPart]->(sys:brick_HVAC_System)
      -[:brick_hasMember]->(eq:brick_Air_Handling_Unit)
      -[:brick_hasPoint]->(s:brick_Temperature_Sensor)
      -[:brick_hasTimeseries]->(ts:brick_Timeseries)
RETURN b.name, eq.name, s.name, ts.external_id
```

### All sensors in a zone

```cypher
MATCH (z:brick_HVAC_Zone)-[:brick_hasPoint]->(s)
RETURN z.name, s.name, s.unit
```

### Equipment feeding zones

```cypher
MATCH (ahu:brick_Air_Handling_Unit)-[:brick_feeds]->(z:brick_HVAC_Zone)
RETURN ahu.name, collect(z.name) as zones
```

### Meters for building

```cypher
MATCH (b:brick_Building)-[:brick_isMeteredBy]->(m)
RETURN b.name, m.name, labels(m)[0] as type
```

---

## Files

| File | Description |
|------|-------------|
| `schema.py` | Brick classes and relations |
| `seed_data.py` | Cypher generation for seeding |
| `load_graph.py` | Load graph into FalkorDB |
| `falkor_client.py` | Database client |

---

## Docker Commands

```bash
docker start falkordb falkordb-browser   # Start
docker stop falkordb falkordb-browser    # Stop
docker logs falkordb                     # Logs
```

## Browser Login

| Field | Value |
|-------|-------|
| Host | `host.docker.internal` |
| Port | `6379` |
