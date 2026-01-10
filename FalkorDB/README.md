# FalkorDB Energy Knowledge Graph

> Brick Schema-basert kunnskapsgraf for energioppfølging i norske næringsbygg

## Forutsetninger

- **Docker Desktop** må være installert og kjøre
- Python 3.10+

---

## 🐳 Starte FalkorDB

### 1. Start databasen

```bash
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb
```

### 2. Start web-grensesnittet

```bash
docker run -d --name falkordb-browser -p 3000:3000 -e FALKORDB_URL=host.docker.internal:6379 falkordb/falkordb-browser
```

### 3. Åpne nettleseren

Gå til **http://localhost:3000** og logg inn med:

| Felt | Verdi |
|------|-------|
| Host | `host.docker.internal` |
| Port | `6379` |

---

## 📥 Laste inn grafen

```bash
cd FalkorDB
pip install -r requirements.txt
python load_graph.py --clear
```

---

## 🔍 Eksempel-spørringer (Cypher)

Kjør disse i FalkorDB Browser:

```cypher
-- Alle bygninger
MATCH (b:Building) RETURN b.name, b.area_sqm, b.energy_class

-- Målere for Operahuset
MATCH (m)-[:meters]->(b:Building)
WHERE b.name CONTAINS "Opera"
RETURN m.name, m.meter_type

-- Utstyr med sensorer
MATCH (s:Power_Sensor)-[:isPointOf]->(e)
RETURN e.name, s.current_value as power_kw

-- Hele grafen (maks 100 noder)
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
```

---

## ⏹️ Docker-kommandoer

| Kommando | Beskrivelse |
|----------|-------------|
| `docker start falkordb falkordb-browser` | Start serverne |
| `docker stop falkordb falkordb-browser` | Stopp serverne |
| `docker rm falkordb falkordb-browser` | Slett containerne |

---

## 📁 Filer

```
FalkorDB/
├── schema.py         # Brick-skjema
├── seed_data.py      # Bygningsdata
├── falkor_client.py  # Database-tilkobling
├── load_graph.py     # Last inn grafen
└── requirements.txt  # Avhengigheter
```

---

## 🏢 Bygninger i grafen

| Bygning | Sted | Areal |
|---------|------|-------|
| Operahuset | Oslo | 38 500 m² |
| Deichmanske Bibliotek | Oslo | 13 500 m² |
| Barcode B13 | Oslo | 22 000 m² |
| Powerhouse Brattørkaia | Trondheim | 8 800 m² |

---

*IDATT2901 Bachelor - Piscada AI Energy Assistant*
