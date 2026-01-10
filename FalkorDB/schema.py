"""
Brick-based Knowledge Graph Schema for FalkorDB

Based on the Brick Schema ontology (https://brickschema.org/)
Adapted for energy management in Norwegian commercial buildings.

Node Types (Brick Classes):
- Building: Physical building structure
- Floor: A floor/level within a building  
- Zone: A thermal/ventilation zone
- Room: Individual rooms
- Equipment: HVAC, electrical, and other equipment
- Point: Sensor readings and setpoints
- Meter: Energy meters (electrical, gas, water)
- System: HVAC systems, electrical systems, etc.

Relationship Types (Brick Relations):
- hasLocation: Entity is located in a location
- isPartOf: Entity is part of another entity
- hasPoint: Equipment/Zone has a sensor point
- feeds: Equipment feeds another equipment/zone
- isFedBy: Inverse of feeds
- meters: Meter measures an entity
- hasSubMeter: Meter has a sub-meter
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# BRICK ENTITY TYPES (Node Labels)
# ============================================================================

class BrickClass(Enum):
    """Brick ontology classes mapped to FalkorDB node labels."""
    
    # Locations
    BUILDING = "Building"
    FLOOR = "Floor"
    ZONE = "Zone"
    ROOM = "Room"
    
    # Equipment
    EQUIPMENT = "Equipment"
    HVAC_EQUIPMENT = "HVAC_Equipment"
    AHU = "Air_Handling_Unit"  # Air Handling Unit
    VAV = "Variable_Air_Volume_Box"
    CHILLER = "Chiller"
    BOILER = "Boiler"
    PUMP = "Pump"
    FAN = "Fan"
    HEAT_EXCHANGER = "Heat_Exchanger"
    
    # Meters
    METER = "Meter"
    ELECTRICAL_METER = "Building_Electrical_Meter"
    GAS_METER = "Building_Gas_Meter"
    WATER_METER = "Building_Water_Meter"
    THERMAL_METER = "Thermal_Power_Meter"
    SUB_METER = "Electrical_Sub_Meter"
    
    # Points (Sensors/Setpoints)
    POINT = "Point"
    SENSOR = "Sensor"
    SETPOINT = "Setpoint"
    COMMAND = "Command"
    ALARM = "Alarm"
    
    # Specific sensor types
    TEMPERATURE_SENSOR = "Temperature_Sensor"
    HUMIDITY_SENSOR = "Humidity_Sensor"
    CO2_SENSOR = "CO2_Sensor"
    OCCUPANCY_SENSOR = "Occupancy_Sensor"
    POWER_SENSOR = "Power_Sensor"
    ENERGY_SENSOR = "Energy_Sensor"
    
    # Systems
    SYSTEM = "System"
    HVAC_SYSTEM = "HVAC_System"
    ELECTRICAL_SYSTEM = "Electrical_System"
    LIGHTING_SYSTEM = "Lighting_System"
    HOT_WATER_SYSTEM = "Hot_Water_System"
    CHILLED_WATER_SYSTEM = "Chilled_Water_System"
    VENTILATION_SYSTEM = "Ventilation_Air_System"


class BrickRelation(Enum):
    """Brick ontology relationships mapped to FalkorDB edge types."""
    
    # Location relationships
    HAS_LOCATION = "hasLocation"
    IS_LOCATION_OF = "isLocationOf"
    IS_PART_OF = "isPartOf"
    HAS_PART = "hasPart"
    
    # Equipment relationships
    HAS_POINT = "hasPoint"
    IS_POINT_OF = "isPointOf"
    FEEDS = "feeds"
    IS_FED_BY = "isFedBy"
    
    # Metering relationships
    METERS = "meters"
    IS_METERED_BY = "isMeteredBy"
    HAS_SUB_METER = "hasSubMeter"
    IS_SUB_METER_OF = "isSubMeterOf"
    
    # System relationships
    HAS_MEMBER = "hasMember"
    IS_MEMBER_OF = "isMemberOf"
    
    # Temporal relationships (for time series)
    HAS_TIMESERIES = "hasTimeseries"


# ============================================================================
# NODE DEFINITIONS
# ============================================================================

@dataclass
class BrickEntity:
    """Base class for all Brick entities."""
    id: str
    name: str
    brick_class: BrickClass = field(default=None)  # Set by subclasses in __post_init__
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_cypher_properties(self) -> str:
        """Convert to Cypher property string."""
        props = {
            "id": self.id,
            "name": self.name,
            "brick_class": self.brick_class.value,
        }
        if self.description:
            props["description"] = self.description
        props.update(self.properties)
        
        prop_strings = []
        for k, v in props.items():
            if isinstance(v, str):
                prop_strings.append(f'{k}: "{v}"')
            elif isinstance(v, (int, float)):
                prop_strings.append(f'{k}: {v}')
            elif isinstance(v, bool):
                prop_strings.append(f'{k}: {"true" if v else "false"}')
        
        return "{" + ", ".join(prop_strings) + "}"


@dataclass 
class Building(BrickEntity):
    """A building in the energy management system."""
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_sqm: Optional[float] = None
    year_built: Optional[int] = None
    energy_class: Optional[str] = None  # A, B, C, D, E, F, G
    
    def __post_init__(self):
        self.brick_class = BrickClass.BUILDING
        self.properties.update({
            k: v for k, v in {
                "address": self.address,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "area_sqm": self.area_sqm,
                "year_built": self.year_built,
                "energy_class": self.energy_class,
            }.items() if v is not None
        })


@dataclass
class Floor(BrickEntity):
    """A floor/level within a building."""
    level: int = 0
    area_sqm: Optional[float] = None
    
    def __post_init__(self):
        self.brick_class = BrickClass.FLOOR
        self.properties.update({
            "level": self.level,
        })
        if self.area_sqm:
            self.properties["area_sqm"] = self.area_sqm


@dataclass
class Meter(BrickEntity):
    """Energy meter node."""
    meter_type: str = "electrical"  # electrical, gas, water, thermal
    unit: str = "kWh"
    
    def __post_init__(self):
        meter_class_map = {
            "electrical": BrickClass.ELECTRICAL_METER,
            "gas": BrickClass.GAS_METER,
            "water": BrickClass.WATER_METER,
            "thermal": BrickClass.THERMAL_METER,
        }
        self.brick_class = meter_class_map.get(self.meter_type, BrickClass.METER)
        self.properties.update({
            "meter_type": self.meter_type,
            "unit": self.unit,
        })


@dataclass
class Equipment(BrickEntity):
    """HVAC or other equipment."""
    equipment_type: str = "generic"
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    
    def __post_init__(self):
        equipment_class_map = {
            "ahu": BrickClass.AHU,
            "vav": BrickClass.VAV,
            "chiller": BrickClass.CHILLER,
            "boiler": BrickClass.BOILER,
            "pump": BrickClass.PUMP,
            "fan": BrickClass.FAN,
            "heat_exchanger": BrickClass.HEAT_EXCHANGER,
        }
        self.brick_class = equipment_class_map.get(
            self.equipment_type.lower(), 
            BrickClass.HVAC_EQUIPMENT
        )
        self.properties["equipment_type"] = self.equipment_type
        if self.manufacturer:
            self.properties["manufacturer"] = self.manufacturer
        if self.model:
            self.properties["model"] = self.model
        if self.capacity:
            self.properties["capacity"] = self.capacity
        if self.capacity_unit:
            self.properties["capacity_unit"] = self.capacity_unit


@dataclass
class Sensor(BrickEntity):
    """Sensor point for measurements."""
    sensor_type: str = "temperature"
    unit: str = "°C"
    current_value: Optional[float] = None
    
    def __post_init__(self):
        sensor_class_map = {
            "temperature": BrickClass.TEMPERATURE_SENSOR,
            "humidity": BrickClass.HUMIDITY_SENSOR,
            "co2": BrickClass.CO2_SENSOR,
            "occupancy": BrickClass.OCCUPANCY_SENSOR,
            "power": BrickClass.POWER_SENSOR,
            "energy": BrickClass.ENERGY_SENSOR,
        }
        self.brick_class = sensor_class_map.get(
            self.sensor_type.lower(),
            BrickClass.SENSOR
        )
        self.properties.update({
            "sensor_type": self.sensor_type,
            "unit": self.unit,
        })
        if self.current_value is not None:
            self.properties["current_value"] = self.current_value


@dataclass
class Zone(BrickEntity):
    """HVAC zone or thermal zone."""
    zone_type: str = "hvac"  # hvac, lighting, fire
    
    def __post_init__(self):
        self.brick_class = BrickClass.ZONE
        self.properties["zone_type"] = self.zone_type


@dataclass
class System(BrickEntity):
    """Building system (HVAC, electrical, etc.)"""
    system_type: str = "hvac"
    
    def __post_init__(self):
        system_class_map = {
            "hvac": BrickClass.HVAC_SYSTEM,
            "electrical": BrickClass.ELECTRICAL_SYSTEM,
            "lighting": BrickClass.LIGHTING_SYSTEM,
            "hot_water": BrickClass.HOT_WATER_SYSTEM,
            "chilled_water": BrickClass.CHILLED_WATER_SYSTEM,
            "ventilation": BrickClass.VENTILATION_SYSTEM,
        }
        self.brick_class = system_class_map.get(
            self.system_type.lower(),
            BrickClass.SYSTEM
        )
        self.properties["system_type"] = self.system_type


# ============================================================================
# RELATIONSHIP DEFINITIONS
# ============================================================================

@dataclass
class BrickRelationship:
    """Represents a relationship between two Brick entities."""
    from_id: str
    to_id: str
    relation_type: BrickRelation
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_cypher(self) -> str:
        """Generate Cypher MATCH-CREATE statement for this relationship."""
        props = ""
        if self.properties:
            prop_strings = []
            for k, v in self.properties.items():
                if isinstance(v, str):
                    prop_strings.append(f'{k}: "{v}"')
                else:
                    prop_strings.append(f'{k}: {v}')
            props = " {" + ", ".join(prop_strings) + "}"
        
        return f"""
        MATCH (a {{id: "{self.from_id}"}}), (b {{id: "{self.to_id}"}})
        CREATE (a)-[:{self.relation_type.value}{props}]->(b)
        """


# ============================================================================
# SCHEMA HELPER FUNCTIONS
# ============================================================================

def create_index_queries() -> List[str]:
    """Generate Cypher queries to create indexes for better performance."""
    return [
        "CREATE INDEX ON :Building(id)",
        "CREATE INDEX ON :Building(name)",
        "CREATE INDEX ON :Floor(id)",
        "CREATE INDEX ON :Zone(id)",
        "CREATE INDEX ON :Equipment(id)",
        "CREATE INDEX ON :Meter(id)",
        "CREATE INDEX ON :Sensor(id)",
        "CREATE INDEX ON :System(id)",
    ]


def get_schema_description() -> str:
    """Get human-readable schema description for LLM context."""
    return """
    FalkorDB Knowledge Graph Schema - Brick Ontology for Energy Management
    
    NODE TYPES:
    - Building: Commercial buildings with energy data
      Properties: id, name, address, latitude, longitude, area_sqm, year_built, energy_class
    
    - Floor: Building floors/levels
      Properties: id, name, level, area_sqm
    
    - Zone: HVAC/thermal zones
      Properties: id, name, zone_type
    
    - Equipment: HVAC equipment (AHU, VAV, Chiller, Boiler, Pump, Fan)
      Properties: id, name, equipment_type, manufacturer, model, capacity
    
    - Meter: Energy meters (Electrical, Gas, Water, Thermal)
      Properties: id, name, meter_type, unit
    
    - Sensor: Measurement points (Temperature, Humidity, CO2, Power, Energy)
      Properties: id, name, sensor_type, unit, current_value
    
    - System: Building systems (HVAC, Electrical, Lighting)
      Properties: id, name, system_type
    
    RELATIONSHIPS:
    - hasLocation: Entity → Location (Building, Floor, Zone)
    - isPartOf: Entity → Parent entity
    - hasPoint: Equipment/Zone → Sensor
    - feeds: Equipment → Equipment/Zone (airflow, water flow)
    - meters: Meter → Entity (what the meter measures)
    - hasSubMeter: Meter → Sub-meter
    - hasMember: System → Equipment (equipment belonging to system)
    
    EXAMPLE QUERIES:
    1. Get all buildings: MATCH (b:Building) RETURN b
    2. Get building meters: MATCH (m:Meter)-[:meters]->(b:Building) RETURN m, b
    3. Get equipment in building: MATCH (e:Equipment)-[:hasLocation]->(b:Building) RETURN e
    4. Get sensor readings: MATCH (s:Sensor)-[:isPointOf]->(e:Equipment) RETURN s, e
    """
