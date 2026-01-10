"""
GraphQL to Cypher Resolver

Translates GraphQL queries to Cypher queries for FalkorDB.
This is the bridge between the GraphQL layer and the graph database.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class CypherQuery:
    """Cypher query with parameters."""
    cypher: str
    parameters: Dict[str, Any]
    description: str


class GraphQLToCypherResolver:
    """
    Resolves GraphQL queries to Cypher for FalkorDB.
    
    Maps GraphQL operations to appropriate Cypher traversal patterns
    following the Brick Ontology structure.
    """
    
    def __init__(self):
        # GraphQL field to Brick label mapping
        self.type_mapping = {
            "Building": "brick_Building",
            "Floor": "brick_Floor",
            "HVACZone": "brick_HVAC_Zone",
            "System": "brick_HVAC_System",  # Default, can be overridden
            "Equipment": "brick_Air_Handling_Unit",  # Default
            "Sensor": "brick_Temperature_Sensor",  # Default
            "Meter": "brick_Electrical_Meter",  # Default
            "Timeseries": "brick_Timeseries",
        }
        
        # System type mapping
        self.system_types = {
            "HVAC": "brick_HVAC_System",
            "Electrical": "brick_Electrical_System",
            "Lighting": "brick_Lighting_System",
        }
        
        # Equipment type mapping
        self.equipment_types = {
            "AHU": "brick_Air_Handling_Unit",
            "Air_Handling_Unit": "brick_Air_Handling_Unit",
            "Chiller": "brick_Chiller",
            "Pump": "brick_Pump",
            "Boiler": "brick_Boiler",
            "Fan": "brick_Fan",
        }
        
        # Sensor type mapping
        self.sensor_types = {
            "Temperature": "brick_Temperature_Sensor",
            "Temperature_Sensor": "brick_Temperature_Sensor",
            "Power": "brick_Power_Sensor",
            "Power_Sensor": "brick_Power_Sensor",
            "CO2": "brick_CO2_Sensor",
            "CO2_Sensor": "brick_CO2_Sensor",
            "Energy": "brick_Energy_Sensor",
            "Energy_Sensor": "brick_Energy_Sensor",
            "Humidity": "brick_Humidity_Sensor",
            "Humidity_Sensor": "brick_Humidity_Sensor",
        }
    
    def resolve(self, graphql_query: str, variables: Dict[str, Any] = None) -> CypherQuery:
        """
        Resolve a GraphQL query string to Cypher.
        
        This is a simplified parser - in production you'd use a proper GraphQL parser.
        """
        variables = variables or {}
        query_lower = graphql_query.lower()
        
        # Detect query type and delegate
        if "building(" in query_lower or "building {" in query_lower:
            if "buildings" in query_lower:
                return self._resolve_buildings()
            return self._resolve_building(variables)
        
        elif "floors" in query_lower:
            return self._resolve_floors(variables)
        
        elif "zones" in query_lower:
            return self._resolve_zones(variables)
        
        elif "systems" in query_lower:
            return self._resolve_systems(variables)
        
        elif "equipment" in query_lower:
            return self._resolve_equipment(variables)
        
        elif "sensors" in query_lower:
            return self._resolve_sensors(variables)
        
        elif "meters" in query_lower:
            return self._resolve_meters(variables)
        
        elif "timeseries" in query_lower:
            return self._resolve_timeseries(variables)
        
        elif "sensorcount" in query_lower:
            return self._resolve_sensor_count(variables)
        
        elif "equipmentcount" in query_lower:
            return self._resolve_equipment_count(variables)
        
        # Default fallback
        return CypherQuery(
            cypher="MATCH (n) RETURN labels(n)[0] as type, count(*) as count",
            parameters={},
            description="Default query - node type counts"
        )
    
    def _resolve_building(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve building query."""
        building_id = variables.get("id", "")
        building_name = variables.get("name", "")
        
        return CypherQuery(
            cypher="""
MATCH (b:brick_Building)
WHERE ($id = '' OR b.id = $id) AND ($name = '' OR b.name CONTAINS $name)
OPTIONAL MATCH (b)-[:brick_hasPart]->(f:brick_Floor)
OPTIONAL MATCH (b)-[:brick_hasPart]->(sys)
WHERE NOT sys:brick_Floor
OPTIONAL MATCH (b)-[:brick_isMeteredBy]->(m)
RETURN b {
    .id, .name, .description, .address, .area_sqm, .year_built, .energy_class,
    floors: collect(DISTINCT f {.id, .name, .level}),
    systems: collect(DISTINCT sys {.id, .name, type: labels(sys)[0]}),
    meters: collect(DISTINCT m {.id, .name, type: labels(m)[0], .unit})
}
LIMIT 1""",
            parameters={"id": building_id, "name": building_name},
            description="Get building with related entities"
        )
    
    def _resolve_buildings(self) -> CypherQuery:
        """Resolve all buildings query."""
        return CypherQuery(
            cypher="""
MATCH (b:brick_Building)
RETURN b {.id, .name, .address, .area_sqm, .energy_class}""",
            parameters={},
            description="Get all buildings"
        )
    
    def _resolve_floors(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve floors query."""
        building_id = variables.get("buildingId", variables.get("building_id", ""))
        
        if building_id:
            return CypherQuery(
                cypher="""
MATCH (b:brick_Building {id: $building_id})-[:brick_hasPart]->(f:brick_Floor)
OPTIONAL MATCH (f)-[:brick_hasPart]->(z:brick_HVAC_Zone)
RETURN f {.id, .name, .level, zones: collect(z {.id, .name})}
ORDER BY f.level""",
                parameters={"building_id": building_id},
                description="Get floors for building"
            )
        
        return CypherQuery(
            cypher="""
MATCH (f:brick_Floor)
RETURN f {.id, .name, .level}
ORDER BY f.level""",
            parameters={},
            description="Get all floors"
        )
    
    def _resolve_zones(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve zones query."""
        floor_id = variables.get("floorId", variables.get("floor_id", ""))
        building_id = variables.get("buildingId", variables.get("building_id", ""))
        
        if floor_id:
            return CypherQuery(
                cypher="""
MATCH (f:brick_Floor {id: $floor_id})-[:brick_hasPart]->(z:brick_HVAC_Zone)
OPTIONAL MATCH (z)-[:brick_hasPoint]->(s)
OPTIONAL MATCH (eq)-[:brick_feeds]->(z)
RETURN z {
    .id, .name,
    sensors: collect(DISTINCT s {.id, .name, .unit, type: labels(s)[0]}),
    fedBy: collect(DISTINCT eq {.id, .name, type: labels(eq)[0]})
}""",
                parameters={"floor_id": floor_id},
                description="Get zones for floor"
            )
        
        if building_id:
            return CypherQuery(
                cypher="""
MATCH (b:brick_Building {id: $building_id})-[:brick_hasPart]->(:brick_Floor)
      -[:brick_hasPart]->(z:brick_HVAC_Zone)
RETURN z {.id, .name}""",
                parameters={"building_id": building_id},
                description="Get zones for building"
            )
        
        return CypherQuery(
            cypher="MATCH (z:brick_HVAC_Zone) RETURN z {.id, .name}",
            parameters={},
            description="Get all zones"
        )
    
    def _resolve_systems(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve systems query."""
        building_id = variables.get("buildingId", variables.get("building_id", ""))
        system_type = variables.get("systemType", variables.get("system_type", ""))
        
        # Map system type to label
        label_filter = ""
        if system_type:
            brick_label = self.system_types.get(system_type, f"brick_{system_type}")
            label_filter = f" AND sys:{brick_label}"
        
        if building_id:
            return CypherQuery(
                cypher=f"""
MATCH (b:brick_Building {{id: $building_id}})-[:brick_hasPart]->(sys)
WHERE NOT sys:brick_Floor{label_filter}
OPTIONAL MATCH (sys)-[:brick_hasMember]->(eq)
RETURN sys {{
    .id, .name, systemType: labels(sys)[0],
    equipment: collect(eq {{.id, .name, type: labels(eq)[0]}})
}}""",
                parameters={"building_id": building_id},
                description="Get systems for building"
            )
        
        return CypherQuery(
            cypher=f"""
MATCH (sys)
WHERE (sys:brick_HVAC_System OR sys:brick_Electrical_System OR sys:brick_Lighting_System){label_filter}
RETURN sys {{.id, .name, systemType: labels(sys)[0]}}""",
            parameters={},
            description="Get all systems"
        )
    
    def _resolve_equipment(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve equipment query."""
        system_id = variables.get("systemId", variables.get("system_id", ""))
        equipment_type = variables.get("equipmentType", variables.get("equipment_type", ""))
        
        # Map equipment type
        label_filter = ""
        if equipment_type:
            brick_label = self.equipment_types.get(equipment_type, f"brick_{equipment_type}")
            label_filter = f":{brick_label}"
        
        if system_id:
            return CypherQuery(
                cypher=f"""
MATCH (sys {{id: $system_id}})-[:brick_hasMember]->(eq{label_filter})
OPTIONAL MATCH (eq)-[:brick_hasPoint]->(s)
OPTIONAL MATCH (eq)-[:brick_feeds]->(z:brick_HVAC_Zone)
RETURN eq {{
    .id, .name, equipmentType: labels(eq)[0],
    .manufacturer, .model, .capacity, .capacity_unit,
    sensors: collect(DISTINCT s {{.id, .name, .unit, type: labels(s)[0]}}),
    zones: collect(DISTINCT z.name)
}}""",
                parameters={"system_id": system_id},
                description="Get equipment for system"
            )
        
        return CypherQuery(
            cypher=f"""
MATCH (eq{label_filter if label_filter else ''})
WHERE eq:brick_Air_Handling_Unit OR eq:brick_Chiller OR eq:brick_Pump OR eq:brick_Boiler
RETURN eq {{.id, .name, equipmentType: labels(eq)[0], .manufacturer, .model}}""",
            parameters={},
            description="Get all equipment"
        )
    
    def _resolve_sensors(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve sensors query."""
        zone_id = variables.get("zoneId", variables.get("zone_id", ""))
        equipment_id = variables.get("equipmentId", variables.get("equipment_id", ""))
        sensor_type = variables.get("sensorType", variables.get("sensor_type", ""))
        
        # Map sensor type
        label_filter = ""
        if sensor_type:
            brick_label = self.sensor_types.get(sensor_type, f"brick_{sensor_type}")
            label_filter = f":{brick_label}"
        
        if zone_id:
            return CypherQuery(
                cypher=f"""
MATCH (z:brick_HVAC_Zone {{id: $zone_id}})-[:brick_hasPoint]->(s{label_filter})
OPTIONAL MATCH (s)-[:brick_hasTimeseries]->(ts)
RETURN s {{
    .id, .name, .unit, sensorType: labels(s)[0],
    timeseries: ts {{.id, .external_id, .resolution}}
}}""",
                parameters={"zone_id": zone_id},
                description="Get sensors for zone"
            )
        
        if equipment_id:
            return CypherQuery(
                cypher=f"""
MATCH (eq {{id: $equipment_id}})-[:brick_hasPoint]->(s{label_filter})
OPTIONAL MATCH (s)-[:brick_hasTimeseries]->(ts)
RETURN s {{
    .id, .name, .unit, sensorType: labels(s)[0],
    timeseries: ts {{.id, .external_id, .resolution}}
}}""",
                parameters={"equipment_id": equipment_id},
                description="Get sensors for equipment"
            )
        
        # All sensors
        return CypherQuery(
            cypher=f"""
MATCH (s{label_filter if label_filter else ''})
WHERE s:brick_Temperature_Sensor OR s:brick_Power_Sensor OR s:brick_CO2_Sensor 
      OR s:brick_Energy_Sensor OR s:brick_Humidity_Sensor
RETURN s {{.id, .name, .unit, sensorType: labels(s)[0]}}""",
            parameters={},
            description="Get all sensors"
        )
    
    def _resolve_meters(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve meters query."""
        building_id = variables.get("buildingId", variables.get("building_id", ""))
        
        if building_id:
            return CypherQuery(
                cypher="""
MATCH (b:brick_Building {id: $building_id})-[:brick_isMeteredBy]->(m)
OPTIONAL MATCH (m)-[:brick_hasPoint]->(s)
RETURN m {
    .id, .name, .unit, meterType: labels(m)[0],
    sensors: collect(s {.id, .name, .unit})
}""",
                parameters={"building_id": building_id},
                description="Get meters for building"
            )
        
        return CypherQuery(
            cypher="""
MATCH (m)
WHERE m:brick_Electrical_Meter OR m:brick_Thermal_Energy_Meter OR m:brick_Water_Meter
RETURN m {.id, .name, .unit, meterType: labels(m)[0]}""",
            parameters={},
            description="Get all meters"
        )
    
    def _resolve_timeseries(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve timeseries query."""
        sensor_id = variables.get("sensorId", variables.get("sensor_id", ""))
        
        if sensor_id:
            return CypherQuery(
                cypher="""
MATCH (s {id: $sensor_id})-[:brick_hasTimeseries]->(ts:brick_Timeseries)
RETURN ts {.id, .external_id, .resolution}""",
                parameters={"sensor_id": sensor_id},
                description="Get timeseries for sensor"
            )
        
        return CypherQuery(
            cypher="""
MATCH (s)-[:brick_hasTimeseries]->(ts:brick_Timeseries)
RETURN s.name as sensor, ts {.id, .external_id, .resolution}""",
            parameters={},
            description="Get all timeseries"
        )
    
    def _resolve_sensor_count(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve sensor count query."""
        sensor_type = variables.get("sensorType", variables.get("sensor_type", ""))
        
        if sensor_type:
            brick_label = self.sensor_types.get(sensor_type, f"brick_{sensor_type}")
            return CypherQuery(
                cypher=f"MATCH (s:{brick_label}) RETURN count(s) as count",
                parameters={},
                description=f"Count {sensor_type} sensors"
            )
        
        return CypherQuery(
            cypher="""
MATCH (s)
WHERE s:brick_Temperature_Sensor OR s:brick_Power_Sensor OR s:brick_CO2_Sensor
RETURN count(s) as count""",
            parameters={},
            description="Count all sensors"
        )
    
    def _resolve_equipment_count(self, variables: Dict[str, Any]) -> CypherQuery:
        """Resolve equipment count query."""
        equipment_type = variables.get("equipmentType", variables.get("equipment_type", ""))
        
        if equipment_type:
            brick_label = self.equipment_types.get(equipment_type, f"brick_{equipment_type}")
            return CypherQuery(
                cypher=f"MATCH (eq:{brick_label}) RETURN count(eq) as count",
                parameters={},
                description=f"Count {equipment_type} equipment"
            )
        
        return CypherQuery(
            cypher="""
MATCH (eq)
WHERE eq:brick_Air_Handling_Unit OR eq:brick_Chiller OR eq:brick_Pump
RETURN count(eq) as count""",
            parameters={},
            description="Count all equipment"
        )
