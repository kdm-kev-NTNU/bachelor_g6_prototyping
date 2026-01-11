# Energy Data MCP Server

MCP-server som kobler AI-assistenter (Claude, Cursor) til energidata fra FalkorDB via GraphQL.

## Arkitektur

```
┌─────────────────┐     MCP Protocol     ┌─────────────────────┐
│  Claude/Cursor  │ ◄──────────────────► │    mcp-graphql      │
└─────────────────┘                      └──────────┬──────────┘
                                                    │
                                           GraphQL Queries
                                                    │
                                                    ▼
                                         ┌─────────────────────┐
                                         │ Strawberry GraphQL  │
                                         │   (localhost:4000)  │
                                         └──────────┬──────────┘
                                                    │
                                               Cypher Queries
                                                    │
                                                    ▼
                                         ┌─────────────────────┐
                                         │     FalkorDB        │
                                         │   (energy_graph)    │
                                         │   Brick Ontology    │
                                         └─────────────────────┘
```

## Datamodell (Brick Ontology)

Grafen følger [Brick Schema](https://brickschema.org/) for semantisk beskrivelse av bygningsdata:

```
Building
├── Floor → HVAC_Zone → Sensor → Timeseries
├── System (HVAC/Electrical/Lighting)
│   └── Equipment (AHU, Chiller, Pump) → Sensor → Timeseries
└── Meter (Electrical/Thermal/Water) → Sensor → Timeseries
```

## Hurtigstart

### 1. Forutsetninger

| Krav | Versjon | Sjekk |
|------|---------|-------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| FalkorDB | Docker | `docker ps` |

### 2. Start FalkorDB

```powershell
# Start FalkorDB container
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb

# Seed data (fra FalkorDB-mappen)
cd ..\..\..\FalkorDB
python load_graph.py --clear
```

### 3. Installer avhengigheter

```powershell
cd "NL-to-Graphql\MCP graphql"
pip install -r requirements.txt
```

### 4. Start GraphQL-server

```powershell
python graphql_server.py
```

Server kjører på: **http://localhost:4000/graphql**

### 5. Test GraphQL

Åpne GraphQL Playground i nettleseren og kjør:

```graphql
{
  buildings {
    name
    address
    energyClass
  }
}
```

```graphql
{
  building(name: "Opera") {
    name
    address
    floors {
      name
      level
    }
    systems {
      name
      systemType
    }
    meters {
      name
      meterType
    }
  }
}
```

```graphql
{
  sensors(sensorType: "Temperature_Sensor") {
    name
    unit
    timeseries {
      externalId
    }
  }
}
```

---

## MCP Konfigurasjon

### For Claude Desktop

1. Åpne konfigurasjonsfilen:
```powershell
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

2. Legg til (eller erstatt innholdet med):
```json
{
  "mcpServers": {
    "energy-graphql": {
      "command": "npx",
      "args": ["-y", "mcp-graphql"],
      "env": {
        "ENDPOINT": "http://localhost:4000/graphql"
      }
    }
  }
}
```

3. **Restart Claude Desktop** (høyreklikk i system tray → Quit)

### For Cursor

Legg til i `.cursor/mcp.json` i prosjektet eller globalt:

```json
{
  "mcpServers": {
    "energy-graphql": {
      "command": "npx",
      "args": ["-y", "mcp-graphql"],
      "env": {
        "ENDPOINT": "http://localhost:4000/graphql"
      }
    }
  }
}
```

---

## Eksempel-spørsmål for AI

Når MCP er konfigurert, kan du stille spørsmål som:

### Norsk
- "Hvilke bygninger finnes i databasen?"
- "Vis alle sensorer i Operahuset"
- "Hvilke soner mater AHU-en?"
- "List alle temperatursensorer med tidsserie-ID"
- "Hva er energimerket til bygningen?"
- "Vis alt utstyr i HVAC-systemet"

### English
- "Show me all buildings"
- "What sensors are in the Foyer zone?"
- "List all meters for the building"
- "What equipment feeds the main hall?"
- "How many temperature sensors are there?"

---

## Filer

| Fil | Beskrivelse |
|-----|-------------|
| `graphql_server.py` | Strawberry GraphQL server med FalkorDB resolvers |
| `requirements.txt` | Python-avhengigheter |
| `start-mcp-server.ps1` | PowerShell script for å starte alt |
| `claude_desktop_config.json` | Eksempel MCP-konfig for Claude |
| `cursor_mcp_config.json` | Eksempel MCP-konfig for Cursor |

---

## GraphQL Schema

### Queries

| Query | Beskrivelse |
|-------|-------------|
| `building(id, name)` | Hent en bygning med detaljer |
| `buildings` | List alle bygninger |
| `floors(buildingId)` | Hent etasjer |
| `zones(floorId, buildingId)` | Hent HVAC-soner |
| `systems(buildingId, systemType)` | Hent systemer |
| `equipment(systemId, equipmentType)` | Hent utstyr |
| `sensors(zoneId, equipmentId, sensorType)` | Hent sensorer |
| `meters(buildingId)` | Hent målere |
| `timeseries(sensorId)` | Hent tidsserie-referanser |
| `sensorCount(sensorType)` | Tell sensorer |
| `equipmentCount(equipmentType)` | Tell utstyr |

### Types

```graphql
type Building {
  id: String!
  name: String!
  address: String
  areaSqm: Float
  yearBuilt: Int
  energyClass: String
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
  manufacturer: String
  model: String
  sensors: [Sensor!]!
}
```

---

## Feilsøking

### GraphQL-server starter ikke

```powershell
# Sjekk at FalkorDB kjører
docker ps | findstr falkor

# Sjekk at port 4000 er ledig
netstat -ano | findstr :4000
```

### MCP vises ikke i Claude

1. Sjekk at GraphQL-server kjører: http://localhost:4000/graphql
2. Sjekk Claude logs:
```powershell
Get-Content "$env:APPDATA\Claude\logs\mcp*.log" -Tail 50
```

### Ingen data returneres

```powershell
# Seed databasen på nytt
cd ..\..\..\FalkorDB
python load_graph.py --clear
```

---

## Referanser

- [mcp-graphql (npm)](https://www.npmjs.com/package/mcp-graphql)
- [Apollo MCP Server Docs](https://www.apollographql.com/docs/apollo-mcp-server) *(ikke på npm ennå)*
- [Brick Schema](https://brickschema.org/)
- [FalkorDB](https://www.falkordb.com/)
- [Strawberry GraphQL](https://strawberry.rocks/)
