"""
GraphQL Schema for Brick Ontology

Defines the GraphQL schema that maps to FalkorDB Brick entities.
This is the intermediate layer between NL and Cypher.
"""

import strawberry
from typing import List, Optional
from dataclasses import dataclass


# ============================================================================
# GraphQL Types (matching Brick Ontology)
# ============================================================================

@strawberry.type
class Timeseries:
    """Reference to external timeseries data."""
    id: str
    external_id: str
    resolution: Optional[str] = None


@strawberry.type
class Sensor:
    """Base sensor type."""
    id: str
    name: str
    unit: Optional[str] = None
    sensor_type: str  # brick_Temperature_Sensor, etc.
    timeseries: Optional[Timeseries] = None


@strawberry.type
class Equipment:
    """Equipment like AHU, Chiller, Pump."""
    id: str
    name: str
    equipment_type: str  # brick_Air_Handling_Unit, etc.
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    sensors: List[Sensor] = strawberry.field(default_factory=list)


@strawberry.type
class Meter:
    """Meters for energy/water measurement."""
    id: str
    name: str
    meter_type: str  # brick_Electrical_Meter, etc.
    unit: Optional[str] = None
    sensors: List[Sensor] = strawberry.field(default_factory=list)


@strawberry.type
class HVACZone:
    """HVAC Zone in a building."""
    id: str
    name: str
    sensors: List[Sensor] = strawberry.field(default_factory=list)
    fed_by: List[Equipment] = strawberry.field(default_factory=list)


@strawberry.type
class Floor:
    """Floor/level in a building."""
    id: str
    name: str
    level: Optional[int] = None
    zones: List[HVACZone] = strawberry.field(default_factory=list)


@strawberry.type 
class System:
    """Building system (HVAC, Electrical, etc.)."""
    id: str
    name: str
    system_type: str  # brick_HVAC_System, etc.
    equipment: List[Equipment] = strawberry.field(default_factory=list)


@strawberry.type
class Building:
    """A building with all its subsystems."""
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


# ============================================================================
# Query Type
# ============================================================================

@strawberry.type
class Query:
    """GraphQL Query root for Brick Ontology."""
    
    @strawberry.field
    def building(self, id: Optional[str] = None, name: Optional[str] = None) -> Optional[Building]:
        """Get a building by ID or name."""
        # Resolved by CypherResolver
        pass
    
    @strawberry.field
    def buildings(self) -> List[Building]:
        """Get all buildings."""
        pass
    
    @strawberry.field
    def floors(self, building_id: Optional[str] = None) -> List[Floor]:
        """Get floors, optionally filtered by building."""
        pass
    
    @strawberry.field
    def zones(self, floor_id: Optional[str] = None, building_id: Optional[str] = None) -> List[HVACZone]:
        """Get HVAC zones."""
        pass
    
    @strawberry.field
    def systems(self, building_id: Optional[str] = None, system_type: Optional[str] = None) -> List[System]:
        """Get systems, optionally filtered."""
        pass
    
    @strawberry.field
    def equipment(
        self, 
        system_id: Optional[str] = None,
        equipment_type: Optional[str] = None
    ) -> List[Equipment]:
        """Get equipment."""
        pass
    
    @strawberry.field
    def sensors(
        self,
        zone_id: Optional[str] = None,
        equipment_id: Optional[str] = None,
        sensor_type: Optional[str] = None
    ) -> List[Sensor]:
        """Get sensors with optional filters."""
        pass
    
    @strawberry.field
    def meters(self, building_id: Optional[str] = None) -> List[Meter]:
        """Get meters for a building."""
        pass
    
    @strawberry.field
    def timeseries(self, sensor_id: Optional[str] = None) -> List[Timeseries]:
        """Get timeseries references."""
        pass
    
    @strawberry.field
    def sensor_count(self, sensor_type: Optional[str] = None) -> int:
        """Count sensors."""
        pass
    
    @strawberry.field
    def equipment_count(self, equipment_type: Optional[str] = None) -> int:
        """Count equipment."""
        pass


# ============================================================================
# Schema Definition
# ============================================================================

# Schema will be created with resolvers attached
SCHEMA_SDL = """
type Query {
    building(id: String, name: String): Building
    buildings: [Building!]!
    floors(buildingId: String): [Floor!]!
    zones(floorId: String, buildingId: String): [HVACZone!]!
    systems(buildingId: String, systemType: String): [System!]!
    equipment(systemId: String, equipmentType: String): [Equipment!]!
    sensors(zoneId: String, equipmentId: String, sensorType: String): [Sensor!]!
    meters(buildingId: String): [Meter!]!
    timeseries(sensorId: String): [Timeseries!]!
    sensorCount(sensorType: String): Int!
    equipmentCount(equipmentType: String): Int!
}

type Building {
    id: String!
    name: String!
    description: String
    address: String
    areaSqm: Float
    yearBuilt: Int
    energyClass: String
    floors: [Floor!]!
    systems: [System!]!
    meters: [Meter!]!
}

type Floor {
    id: String!
    name: String!
    level: Int
    zones: [HVACZone!]!
}

type HVACZone {
    id: String!
    name: String!
    sensors: [Sensor!]!
    fedBy: [Equipment!]!
}

type System {
    id: String!
    name: String!
    systemType: String!
    equipment: [Equipment!]!
}

type Equipment {
    id: String!
    name: String!
    equipmentType: String!
    manufacturer: String
    model: String
    capacity: Float
    capacityUnit: String
    sensors: [Sensor!]!
}

type Meter {
    id: String!
    name: String!
    meterType: String!
    unit: String
    sensors: [Sensor!]!
}

type Sensor {
    id: String!
    name: String!
    unit: String
    sensorType: String!
    timeseries: Timeseries
}

type Timeseries {
    id: String!
    externalId: String!
    resolution: String
}
"""


def get_schema_description() -> str:
    """Get human-readable schema description for LLM context."""
    return """
GRAPHQL SCHEMA FOR BRICK ONTOLOGY
=================================

QUERIES:
  building(id, name)     → Get single building
  buildings              → Get all buildings
  floors(buildingId)     → Get floors
  zones(floorId, buildingId) → Get HVAC zones
  systems(buildingId, systemType) → Get systems (HVAC, Electrical, etc.)
  equipment(systemId, equipmentType) → Get equipment (AHU, Chiller, etc.)
  sensors(zoneId, equipmentId, sensorType) → Get sensors
  meters(buildingId)     → Get meters
  timeseries(sensorId)   → Get timeseries references
  sensorCount(sensorType) → Count sensors
  equipmentCount(equipmentType) → Count equipment

TYPES:
  Building: id, name, address, areaSqm, yearBuilt, energyClass, floors, systems, meters
  Floor: id, name, level, zones
  HVACZone: id, name, sensors, fedBy
  System: id, name, systemType, equipment
  Equipment: id, name, equipmentType, manufacturer, model, capacity, sensors
  Sensor: id, name, unit, sensorType, timeseries
  Meter: id, name, meterType, unit, sensors
  Timeseries: id, externalId, resolution

SENSOR TYPES: Temperature_Sensor, Power_Sensor, CO2_Sensor, Energy_Sensor, Humidity_Sensor
EQUIPMENT TYPES: Air_Handling_Unit, Chiller, Pump, Boiler, Fan
SYSTEM TYPES: HVAC_System, Electrical_System, Lighting_System
"""
