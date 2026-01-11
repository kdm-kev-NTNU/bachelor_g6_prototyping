"""
GraphQL Server for Brick Ontology - Energy Data

This server exposes FalkorDB energy data via GraphQL for use with Apollo MCP Server.
Enables AI assistants to query building energy data through natural language.

Run: python graphql_server.py
Endpoint: http://localhost:4000/graphql
"""

import sys
import os
from typing import List, Optional
from contextlib import asynccontextmanager

import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add FalkorDB path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'FalkorDB'))

from falkor_client import FalkorDBClient, FalkorConfig


# =============================================================================
# FalkorDB Connection
# =============================================================================

_client: Optional[FalkorDBClient] = None


def get_client() -> FalkorDBClient:
    """Get or create FalkorDB client."""
    global _client
    if _client is None:
        config = FalkorConfig(
            host=os.getenv("FALKORDB_HOST", "localhost"),
            port=int(os.getenv("FALKORDB_PORT", "6379")),
            graph_name=os.getenv("FALKORDB_GRAPH", "energy_graph")
        )
        _client = FalkorDBClient(config)
        _client.connect()
    return _client


# =============================================================================
# GraphQL Types (Brick Ontology)
# =============================================================================

@strawberry.type
class Timeseries:
    """Reference to external timeseries data."""
    id: str
    external_id: str
    resolution: Optional[str] = None


@strawberry.type
class Sensor:
    """Sensor in the building (temperature, power, CO2, etc.)."""
    id: str
    name: str
    unit: Optional[str] = None
    sensor_type: str
    timeseries: Optional[Timeseries] = None


@strawberry.type
class Equipment:
    """Building equipment (AHU, Chiller, Pump, etc.)."""
    id: str
    name: str
    equipment_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    sensors: List[Sensor] = strawberry.field(default_factory=list)


@strawberry.type
class Meter:
    """Energy/water meters."""
    id: str
    name: str
    meter_type: str
    unit: Optional[str] = None
    sensors: List[Sensor] = strawberry.field(default_factory=list)


@strawberry.type
class HVACZone:
    """HVAC zone in a building."""
    id: str
    name: str
    sensors: List[Sensor] = strawberry.field(default_factory=list)
    fed_by: List[Equipment] = strawberry.field(default_factory=list)


@strawberry.type
class Floor:
    """Floor in a building."""
    id: str
    name: str
    level: Optional[int] = None
    zones: List[HVACZone] = strawberry.field(default_factory=list)


@strawberry.type
class System:
    """Building system (HVAC, Electrical, Lighting)."""
    id: str
    name: str
    system_type: str
    equipment: List[Equipment] = strawberry.field(default_factory=list)


@strawberry.type
class Building:
    """A building with all subsystems - root entity in Brick Ontology."""
    id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    area_sqm: Optional[float] = None
    year_built: Optional[int] = None
    energy_class: Optional[str] = None
    floors: List[Floor] = strawberry.field(default_factory=list)
    systems: List[System] = strawberry.field(default_factory=list)
    meters: List[Meter] = strawberry.field(default_factory=list)


# =============================================================================
# Helper Functions
# =============================================================================

def extract_props(node_data: dict) -> dict:
    """Extract properties from FalkorDB node."""
    if isinstance(node_data, dict):
        if 'properties' in node_data:
            return node_data['properties']
        return node_data
    return {}


def safe_get(data: dict, key: str, default=None):
    """Safely get value from dict."""
    return data.get(key, default)


# =============================================================================
# GraphQL Query Resolvers
# =============================================================================

@strawberry.type
class Query:
    """GraphQL queries for Brick Ontology energy data."""
    
    @strawberry.field(description="Get a building by ID or name")
    def building(self, id: Optional[str] = None, name: Optional[str] = None) -> Optional[Building]:
        client = get_client()
        
        # Build WHERE clause
        conditions = []
        if id:
            conditions.append(f"b.id = '{id}'")
        if name:
            conditions.append(f"b.name CONTAINS '{name}'")
        
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        results = client.query(f"""
            MATCH (b:brick_Building)
            {where}
            RETURN b
            LIMIT 1
        """)
        
        if not results:
            return None
        
        props = extract_props(results[0].get('b', {}))
        
        return Building(
            id=props.get('id', ''),
            name=props.get('name', ''),
            description=props.get('description'),
            address=props.get('address'),
            area_sqm=props.get('area_sqm'),
            year_built=props.get('year_built'),
            energy_class=props.get('energy_class'),
            floors=get_floors_for_building(props.get('id', '')),
            systems=get_systems_for_building(props.get('id', '')),
            meters=get_meters_for_building(props.get('id', ''))
        )
    
    @strawberry.field(description="Get all buildings")
    def buildings(self) -> List[Building]:
        client = get_client()
        results = client.query("MATCH (b:brick_Building) RETURN b")
        
        buildings = []
        for row in results:
            props = extract_props(row.get('b', {}))
            buildings.append(Building(
                id=props.get('id', ''),
                name=props.get('name', ''),
                description=props.get('description'),
                address=props.get('address'),
                area_sqm=props.get('area_sqm'),
                year_built=props.get('year_built'),
                energy_class=props.get('energy_class')
            ))
        return buildings
    
    @strawberry.field(description="Get floors, optionally filtered by building")
    def floors(self, building_id: Optional[str] = None) -> List[Floor]:
        client = get_client()
        
        if building_id:
            results = client.query(f"""
                MATCH (b:brick_Building {{id: '{building_id}'}})-[:brick_hasPart]->(f:brick_Floor)
                RETURN f
                ORDER BY f.level
            """)
        else:
            results = client.query("MATCH (f:brick_Floor) RETURN f ORDER BY f.level")
        
        floors = []
        for row in results:
            props = extract_props(row.get('f', {}))
            floors.append(Floor(
                id=props.get('id', ''),
                name=props.get('name', ''),
                level=props.get('level')
            ))
        return floors
    
    @strawberry.field(description="Get HVAC zones")
    def zones(self, floor_id: Optional[str] = None, building_id: Optional[str] = None) -> List[HVACZone]:
        client = get_client()
        
        if floor_id:
            results = client.query(f"""
                MATCH (f:brick_Floor {{id: '{floor_id}'}})-[:brick_hasPart]->(z:brick_HVAC_Zone)
                RETURN z
            """)
        elif building_id:
            results = client.query(f"""
                MATCH (b:brick_Building {{id: '{building_id}'}})-[:brick_hasPart]->(:brick_Floor)
                      -[:brick_hasPart]->(z:brick_HVAC_Zone)
                RETURN z
            """)
        else:
            results = client.query("MATCH (z:brick_HVAC_Zone) RETURN z")
        
        zones = []
        for row in results:
            props = extract_props(row.get('z', {}))
            zone_id = props.get('id', '')
            zones.append(HVACZone(
                id=zone_id,
                name=props.get('name', ''),
                sensors=get_sensors_for_parent(zone_id),
                fed_by=get_equipment_feeding_zone(zone_id)
            ))
        return zones
    
    @strawberry.field(description="Get systems (HVAC, Electrical, Lighting)")
    def systems(self, building_id: Optional[str] = None, system_type: Optional[str] = None) -> List[System]:
        client = get_client()
        
        where_parts = []
        if system_type:
            where_parts.append(f"sys:brick_{system_type}_System")
        
        if building_id:
            match = f"MATCH (b:brick_Building {{id: '{building_id}'}})-[:brick_hasPart]->(sys)"
            where_parts.append("NOT sys:brick_Floor")
        else:
            match = "MATCH (sys) WHERE sys:brick_HVAC_System OR sys:brick_Electrical_System OR sys:brick_Lighting_System"
        
        where = f"WHERE {' AND '.join(where_parts)}" if where_parts and building_id else ""
        
        results = client.query(f"{match} {where} RETURN sys, labels(sys)[0] as type")
        
        systems = []
        for row in results:
            props = extract_props(row.get('sys', {}))
            sys_id = props.get('id', '')
            systems.append(System(
                id=sys_id,
                name=props.get('name', ''),
                system_type=row.get('type', '').replace('brick_', ''),
                equipment=get_equipment_for_system(sys_id)
            ))
        return systems
    
    @strawberry.field(description="Get equipment (AHU, Chiller, Pump, etc.)")
    def equipment(self, system_id: Optional[str] = None, equipment_type: Optional[str] = None) -> List[Equipment]:
        client = get_client()
        
        if system_id:
            results = client.query(f"""
                MATCH (sys {{id: '{system_id}'}})-[:brick_hasMember]->(eq)
                RETURN eq, labels(eq)[0] as type
            """)
        else:
            type_filter = f":brick_{equipment_type}" if equipment_type else ""
            results = client.query(f"""
                MATCH (eq{type_filter})
                WHERE eq:brick_Air_Handling_Unit OR eq:brick_Chiller OR eq:brick_Pump OR eq:brick_Boiler
                RETURN eq, labels(eq)[0] as type
            """)
        
        equipment = []
        for row in results:
            props = extract_props(row.get('eq', {}))
            eq_id = props.get('id', '')
            equipment.append(Equipment(
                id=eq_id,
                name=props.get('name', ''),
                equipment_type=row.get('type', '').replace('brick_', ''),
                manufacturer=props.get('manufacturer'),
                model=props.get('model'),
                capacity=props.get('capacity'),
                capacity_unit=props.get('capacity_unit'),
                sensors=get_sensors_for_parent(eq_id)
            ))
        return equipment
    
    @strawberry.field(description="Get sensors with optional filters")
    def sensors(
        self,
        zone_id: Optional[str] = None,
        equipment_id: Optional[str] = None,
        sensor_type: Optional[str] = None
    ) -> List[Sensor]:
        client = get_client()
        
        type_filter = f":brick_{sensor_type}" if sensor_type else ""
        
        if zone_id:
            results = client.query(f"""
                MATCH (z:brick_HVAC_Zone {{id: '{zone_id}'}})-[:brick_hasPoint]->(s{type_filter})
                OPTIONAL MATCH (s)-[:brick_hasTimeseries]->(ts)
                RETURN s, labels(s)[0] as type, ts
            """)
        elif equipment_id:
            results = client.query(f"""
                MATCH (eq {{id: '{equipment_id}'}})-[:brick_hasPoint]->(s{type_filter})
                OPTIONAL MATCH (s)-[:brick_hasTimeseries]->(ts)
                RETURN s, labels(s)[0] as type, ts
            """)
        else:
            results = client.query(f"""
                MATCH (s{type_filter})
                WHERE s:brick_Temperature_Sensor OR s:brick_Power_Sensor OR s:brick_CO2_Sensor 
                      OR s:brick_Energy_Sensor OR s:brick_Humidity_Sensor
                OPTIONAL MATCH (s)-[:brick_hasTimeseries]->(ts)
                RETURN s, labels(s)[0] as type, ts
            """)
        
        return parse_sensors(results)
    
    @strawberry.field(description="Get meters for a building")
    def meters(self, building_id: Optional[str] = None) -> List[Meter]:
        client = get_client()
        
        if building_id:
            results = client.query(f"""
                MATCH (b:brick_Building {{id: '{building_id}'}})-[:brick_isMeteredBy]->(m)
                RETURN m, labels(m)[0] as type
            """)
        else:
            results = client.query("""
                MATCH (m)
                WHERE m:brick_Electrical_Meter OR m:brick_Thermal_Energy_Meter OR m:brick_Water_Meter
                RETURN m, labels(m)[0] as type
            """)
        
        meters = []
        for row in results:
            props = extract_props(row.get('m', {}))
            meter_id = props.get('id', '')
            meters.append(Meter(
                id=meter_id,
                name=props.get('name', ''),
                meter_type=row.get('type', '').replace('brick_', ''),
                unit=props.get('unit'),
                sensors=get_sensors_for_parent(meter_id)
            ))
        return meters
    
    @strawberry.field(description="Get timeseries references")
    def timeseries(self, sensor_id: Optional[str] = None) -> List[Timeseries]:
        client = get_client()
        
        if sensor_id:
            results = client.query(f"""
                MATCH (s {{id: '{sensor_id}'}})-[:brick_hasTimeseries]->(ts:brick_Timeseries)
                RETURN ts
            """)
        else:
            results = client.query("""
                MATCH (ts:brick_Timeseries)
                RETURN ts
            """)
        
        timeseries = []
        for row in results:
            props = extract_props(row.get('ts', {}))
            timeseries.append(Timeseries(
                id=props.get('id', ''),
                external_id=props.get('external_id', ''),
                resolution=props.get('resolution')
            ))
        return timeseries
    
    @strawberry.field(description="Count sensors by type")
    def sensor_count(self, sensor_type: Optional[str] = None) -> int:
        client = get_client()
        
        if sensor_type:
            results = client.query(f"MATCH (s:brick_{sensor_type}) RETURN count(s) as count")
        else:
            results = client.query("""
                MATCH (s)
                WHERE s:brick_Temperature_Sensor OR s:brick_Power_Sensor OR s:brick_CO2_Sensor
                RETURN count(s) as count
            """)
        
        return results[0].get('count', 0) if results else 0
    
    @strawberry.field(description="Count equipment by type")
    def equipment_count(self, equipment_type: Optional[str] = None) -> int:
        client = get_client()
        
        if equipment_type:
            results = client.query(f"MATCH (eq:brick_{equipment_type}) RETURN count(eq) as count")
        else:
            results = client.query("""
                MATCH (eq)
                WHERE eq:brick_Air_Handling_Unit OR eq:brick_Chiller OR eq:brick_Pump
                RETURN count(eq) as count
            """)
        
        return results[0].get('count', 0) if results else 0


# =============================================================================
# Helper Query Functions
# =============================================================================

def get_floors_for_building(building_id: str) -> List[Floor]:
    """Get floors for a building."""
    if not building_id:
        return []
    client = get_client()
    results = client.query(f"""
        MATCH (b:brick_Building {{id: '{building_id}'}})-[:brick_hasPart]->(f:brick_Floor)
        RETURN f
        ORDER BY f.level
    """)
    
    floors = []
    for row in results:
        props = extract_props(row.get('f', {}))
        floors.append(Floor(
            id=props.get('id', ''),
            name=props.get('name', ''),
            level=props.get('level')
        ))
    return floors


def get_systems_for_building(building_id: str) -> List[System]:
    """Get systems for a building."""
    if not building_id:
        return []
    client = get_client()
    results = client.query(f"""
        MATCH (b:brick_Building {{id: '{building_id}'}})-[:brick_hasPart]->(sys)
        WHERE NOT sys:brick_Floor
        RETURN sys, labels(sys)[0] as type
    """)
    
    systems = []
    for row in results:
        props = extract_props(row.get('sys', {}))
        systems.append(System(
            id=props.get('id', ''),
            name=props.get('name', ''),
            system_type=row.get('type', '').replace('brick_', '')
        ))
    return systems


def get_meters_for_building(building_id: str) -> List[Meter]:
    """Get meters for a building."""
    if not building_id:
        return []
    client = get_client()
    results = client.query(f"""
        MATCH (b:brick_Building {{id: '{building_id}'}})-[:brick_isMeteredBy]->(m)
        RETURN m, labels(m)[0] as type
    """)
    
    meters = []
    for row in results:
        props = extract_props(row.get('m', {}))
        meters.append(Meter(
            id=props.get('id', ''),
            name=props.get('name', ''),
            meter_type=row.get('type', '').replace('brick_', ''),
            unit=props.get('unit')
        ))
    return meters


def get_equipment_for_system(system_id: str) -> List[Equipment]:
    """Get equipment for a system."""
    if not system_id:
        return []
    client = get_client()
    results = client.query(f"""
        MATCH (sys {{id: '{system_id}'}})-[:brick_hasMember]->(eq)
        RETURN eq, labels(eq)[0] as type
    """)
    
    equipment = []
    for row in results:
        props = extract_props(row.get('eq', {}))
        equipment.append(Equipment(
            id=props.get('id', ''),
            name=props.get('name', ''),
            equipment_type=row.get('type', '').replace('brick_', ''),
            manufacturer=props.get('manufacturer'),
            model=props.get('model')
        ))
    return equipment


def get_sensors_for_parent(parent_id: str) -> List[Sensor]:
    """Get sensors for an equipment or zone."""
    if not parent_id:
        return []
    client = get_client()
    results = client.query(f"""
        MATCH (p {{id: '{parent_id}'}})-[:brick_hasPoint]->(s)
        OPTIONAL MATCH (s)-[:brick_hasTimeseries]->(ts)
        RETURN s, labels(s)[0] as type, ts
    """)
    
    return parse_sensors(results)


def get_equipment_feeding_zone(zone_id: str) -> List[Equipment]:
    """Get equipment that feeds a zone."""
    if not zone_id:
        return []
    client = get_client()
    results = client.query(f"""
        MATCH (eq)-[:brick_feeds]->(z:brick_HVAC_Zone {{id: '{zone_id}'}})
        RETURN eq, labels(eq)[0] as type
    """)
    
    equipment = []
    for row in results:
        props = extract_props(row.get('eq', {}))
        equipment.append(Equipment(
            id=props.get('id', ''),
            name=props.get('name', ''),
            equipment_type=row.get('type', '').replace('brick_', '')
        ))
    return equipment


def parse_sensors(results: list) -> List[Sensor]:
    """Parse sensor results from Cypher query."""
    sensors = []
    for row in results:
        props = extract_props(row.get('s', {}))
        ts_data = row.get('ts')
        
        timeseries = None
        if ts_data:
            ts_props = extract_props(ts_data)
            timeseries = Timeseries(
                id=ts_props.get('id', ''),
                external_id=ts_props.get('external_id', ''),
                resolution=ts_props.get('resolution')
            )
        
        sensors.append(Sensor(
            id=props.get('id', ''),
            name=props.get('name', ''),
            unit=props.get('unit'),
            sensor_type=row.get('type', '').replace('brick_', ''),
            timeseries=timeseries
        ))
    return sensors


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    print("\n" + "=" * 60)
    print("  🏢 Energy Data GraphQL Server")
    print("  Brick Ontology → FalkorDB → GraphQL → MCP")
    print("=" * 60)
    
    try:
        get_client()
        print("\n✅ FalkorDB connected")
    except Exception as e:
        print(f"\n⚠️  FalkorDB connection failed: {e}")
        print("   Start FalkorDB: docker start falkordb")
    
    print(f"\n🌐 GraphQL Playground: http://localhost:4000/graphql")
    print("=" * 60 + "\n")
    
    yield
    
    global _client
    if _client:
        _client.close()
        _client = None


# Create Strawberry schema
schema = strawberry.Schema(query=Query)

# Create FastAPI app
app = FastAPI(
    title="Energy Data GraphQL API",
    description="GraphQL API for Brick Ontology energy data from FalkorDB",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        client = get_client()
        results = client.query("MATCH (b:brick_Building) RETURN count(b) as count")
        return {
            "status": "healthy",
            "database": "connected",
            "buildings": results[0].get('count', 0) if results else 0
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
