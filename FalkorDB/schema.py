"""
Brick Ontology Schema for FalkorDB

Strict implementation following https://ontology.brickschema.org/
All classes and relations are prefixed with 'brick_' for Cypher compatibility.

Supported traversal pattern:
Building → System → Equipment → Point → Timeseries
"""

# ============================================================================
# BRICK CLASSES (Node Labels)
# ============================================================================

BRICK_CLASSES = {
    # Locations
    "Building": "brick_Building",
    "Floor": "brick_Floor",
    "Room": "brick_Room",
    "HVAC_Zone": "brick_HVAC_Zone",
    
    # Systems
    "HVAC_System": "brick_HVAC_System",
    "Electrical_System": "brick_Electrical_System",
    "Lighting_System": "brick_Lighting_System",
    "Hot_Water_System": "brick_Hot_Water_System",
    
    # Equipment
    "AHU": "brick_Air_Handling_Unit",
    "VAV": "brick_Variable_Air_Volume_Box",
    "Chiller": "brick_Chiller",
    "Boiler": "brick_Boiler",
    "Pump": "brick_Pump",
    "Fan": "brick_Fan",
    
    # Meters
    "Electrical_Meter": "brick_Electrical_Meter",
    "Thermal_Energy_Meter": "brick_Thermal_Energy_Meter",
    "Water_Meter": "brick_Water_Meter",
    
    # Points (Sensors/Setpoints)
    "Temperature_Sensor": "brick_Temperature_Sensor",
    "Humidity_Sensor": "brick_Humidity_Sensor",
    "CO2_Sensor": "brick_CO2_Sensor",
    "Power_Sensor": "brick_Power_Sensor",
    "Energy_Sensor": "brick_Energy_Sensor",
    "Flow_Sensor": "brick_Flow_Sensor",
    "Pressure_Sensor": "brick_Pressure_Sensor",
    
    # Setpoints
    "Temperature_Setpoint": "brick_Temperature_Setpoint",
    "Pressure_Setpoint": "brick_Pressure_Setpoint",
    
    # Timeseries
    "Timeseries": "brick_Timeseries",
}


# ============================================================================
# BRICK RELATIONS (Edge Types)
# ============================================================================

BRICK_RELATIONS = {
    # Topology relations
    "hasPart": "brick_hasPart",           # Building hasPart Floor
    "isPartOf": "brick_isPartOf",         # Floor isPartOf Building
    
    # Location relations
    "hasLocation": "brick_hasLocation",   # Equipment hasLocation Room
    "isLocationOf": "brick_isLocationOf", # Room isLocationOf Equipment
    
    # Point relations
    "hasPoint": "brick_hasPoint",         # Equipment hasPoint Sensor
    "isPointOf": "brick_isPointOf",       # Sensor isPointOf Equipment
    
    # System relations
    "hasMember": "brick_hasMember",       # System hasMember Equipment
    "isMemberOf": "brick_isMemberOf",     # Equipment isMemberOf System
    
    # Flow relations
    "feeds": "brick_feeds",               # AHU feeds Zone
    "isFedBy": "brick_isFedBy",           # Zone isFedBy AHU
    
    # Metering relations
    "meters": "brick_meters",             # Meter meters Building
    "isMeteredBy": "brick_isMeteredBy",   # Building isMeteredBy Meter
    
    # Timeseries relation
    "hasTimeseries": "brick_hasTimeseries",  # Sensor hasTimeseries Timeseries
}


# ============================================================================
# SCHEMA DOCUMENTATION
# ============================================================================

SCHEMA_DESCRIPTION = """
BRICK ONTOLOGY GRAPH SCHEMA
===========================

TRAVERSAL PATTERN:
  brick_Building
    └─[brick_hasPart]→ brick_Floor
    └─[brick_hasPart]→ brick_HVAC_System
        └─[brick_hasMember]→ brick_Air_Handling_Unit
            └─[brick_hasPoint]→ brick_Temperature_Sensor
                └─[brick_hasTimeseries]→ brick_Timeseries
            └─[brick_feeds]→ brick_HVAC_Zone
    └─[brick_isMeteredBy]→ brick_Electrical_Meter
        └─[brick_hasPoint]→ brick_Power_Sensor
            └─[brick_hasTimeseries]→ brick_Timeseries

NODE PROPERTIES:
  - id: Unique identifier (required)
  - name: Human-readable name (required)
  - description: Optional description
  
BUILDING PROPERTIES:
  - address, area_sqm, year_built, energy_class

EQUIPMENT PROPERTIES:
  - manufacturer, model, capacity, capacity_unit

SENSOR PROPERTIES:
  - unit (e.g., "degC", "kW", "ppm")

TIMESERIES PROPERTIES:
  - external_id: Reference to external timeseries database
  - resolution: Data resolution (e.g., "PT15M" for 15 minutes)
"""


def get_label(brick_class: str) -> str:
    """Get FalkorDB label for a Brick class."""
    return BRICK_CLASSES.get(brick_class, f"brick_{brick_class}")


def get_relation(brick_relation: str) -> str:
    """Get FalkorDB relation type for a Brick relation."""
    return BRICK_RELATIONS.get(brick_relation, f"brick_{brick_relation}")
