"""
Brick Ontology for NL-to-KG Pipeline

Domain ontology mapping natural language concepts to Brick Schema classes,
relations, and Cypher patterns for FalkorDB.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class IntentType(Enum):
    """Types of user intents for KG queries."""
    QUERY_ENTITY = "query_entity"           # Get specific entity by ID/name
    QUERY_LIST = "query_list"               # List entities of a type
    QUERY_TRAVERSE = "query_traverse"       # Traverse relationships
    QUERY_AGGREGATE = "query_aggregate"     # Aggregation (count, sum)
    QUERY_PATH = "query_path"               # Find path between entities
    UNKNOWN = "unknown"


class BrickClass(Enum):
    """Brick Schema classes (node labels)."""
    # Locations
    BUILDING = "brick_Building"
    FLOOR = "brick_Floor"
    ROOM = "brick_Room"
    HVAC_ZONE = "brick_HVAC_Zone"
    
    # Systems
    HVAC_SYSTEM = "brick_HVAC_System"
    ELECTRICAL_SYSTEM = "brick_Electrical_System"
    LIGHTING_SYSTEM = "brick_Lighting_System"
    
    # Equipment
    AHU = "brick_Air_Handling_Unit"
    VAV = "brick_Variable_Air_Volume_Box"
    CHILLER = "brick_Chiller"
    BOILER = "brick_Boiler"
    PUMP = "brick_Pump"
    FAN = "brick_Fan"
    
    # Meters
    ELECTRICAL_METER = "brick_Electrical_Meter"
    THERMAL_METER = "brick_Thermal_Energy_Meter"
    WATER_METER = "brick_Water_Meter"
    
    # Sensors
    TEMPERATURE_SENSOR = "brick_Temperature_Sensor"
    HUMIDITY_SENSOR = "brick_Humidity_Sensor"
    CO2_SENSOR = "brick_CO2_Sensor"
    POWER_SENSOR = "brick_Power_Sensor"
    ENERGY_SENSOR = "brick_Energy_Sensor"
    FLOW_SENSOR = "brick_Flow_Sensor"
    PRESSURE_SENSOR = "brick_Pressure_Sensor"
    
    # Timeseries
    TIMESERIES = "brick_Timeseries"


class BrickRelation(Enum):
    """Brick Schema relations (edge types)."""
    HAS_PART = "brick_hasPart"
    IS_PART_OF = "brick_isPartOf"
    HAS_LOCATION = "brick_hasLocation"
    HAS_POINT = "brick_hasPoint"
    IS_POINT_OF = "brick_isPointOf"
    HAS_MEMBER = "brick_hasMember"
    IS_MEMBER_OF = "brick_isMemberOf"
    FEEDS = "brick_feeds"
    IS_FED_BY = "brick_isFedBy"
    METERS = "brick_meters"
    IS_METERED_BY = "brick_isMeteredBy"
    HAS_TIMESERIES = "brick_hasTimeseries"


@dataclass
class EntityDefinition:
    """Definition of a Brick entity type."""
    brick_class: BrickClass
    name: str
    description: str
    properties: List[str]
    synonyms_no: List[str]  # Norwegian synonyms
    synonyms_en: List[str]  # English synonyms


@dataclass
class TraversalPattern:
    """Common traversal pattern through the graph."""
    name: str
    description: str
    cypher_pattern: str
    return_fields: List[str]


class BrickOntology:
    """
    Brick Ontology for building/energy domain.
    
    Maps natural language concepts to Brick Schema for Cypher generation.
    """
    
    def __init__(self):
        self.entities: Dict[BrickClass, EntityDefinition] = {}
        self.traversals: Dict[str, TraversalPattern] = {}
        self.intent_patterns: Dict[IntentType, List[str]] = {}
        
        self._init_entities()
        self._init_traversals()
        self._init_intent_patterns()
    
    def _init_entities(self):
        """Define Brick entities with multilingual synonyms."""
        
        self.entities[BrickClass.BUILDING] = EntityDefinition(
            brick_class=BrickClass.BUILDING,
            name="Building",
            description="A building with HVAC and energy systems",
            properties=["id", "name", "description", "address", "area_sqm", "year_built", "energy_class"],
            synonyms_no=["bygning", "bygg", "hus", "operahus", "operahuset"],
            synonyms_en=["building", "facility", "structure"]
        )
        
        self.entities[BrickClass.FLOOR] = EntityDefinition(
            brick_class=BrickClass.FLOOR,
            name="Floor",
            description="A floor/level in a building",
            properties=["id", "name", "level"],
            synonyms_no=["etasje", "plan", "nivå"],
            synonyms_en=["floor", "level", "story"]
        )
        
        self.entities[BrickClass.HVAC_ZONE] = EntityDefinition(
            brick_class=BrickClass.HVAC_ZONE,
            name="HVAC Zone",
            description="A zone controlled by HVAC system",
            properties=["id", "name"],
            synonyms_no=["sone", "ventilasjonsone", "hvac-sone", "rom", "område"],
            synonyms_en=["zone", "hvac zone", "area", "space"]
        )
        
        self.entities[BrickClass.HVAC_SYSTEM] = EntityDefinition(
            brick_class=BrickClass.HVAC_SYSTEM,
            name="HVAC System",
            description="Heating, ventilation and air conditioning system",
            properties=["id", "name"],
            synonyms_no=["ventilasjonsanlegg", "hvac", "klimaanlegg", "varmeanlegg"],
            synonyms_en=["hvac system", "hvac", "ventilation system", "climate system"]
        )
        
        self.entities[BrickClass.AHU] = EntityDefinition(
            brick_class=BrickClass.AHU,
            name="Air Handling Unit",
            description="Air handling unit for ventilation",
            properties=["id", "name", "manufacturer", "model", "capacity", "capacity_unit"],
            synonyms_no=["aggregat", "ahu", "luftbehandler", "ventilasjonsenhet"],
            synonyms_en=["ahu", "air handling unit", "air handler"]
        )
        
        self.entities[BrickClass.CHILLER] = EntityDefinition(
            brick_class=BrickClass.CHILLER,
            name="Chiller",
            description="Chiller for cooling",
            properties=["id", "name", "manufacturer", "model", "capacity", "capacity_unit"],
            synonyms_no=["kjølemaskin", "chiller", "kjøleanlegg"],
            synonyms_en=["chiller", "cooling unit", "cooling machine"]
        )
        
        self.entities[BrickClass.PUMP] = EntityDefinition(
            brick_class=BrickClass.PUMP,
            name="Pump",
            description="Pump for fluid circulation",
            properties=["id", "name", "manufacturer", "capacity", "capacity_unit"],
            synonyms_no=["pumpe", "sirkulasjonspumpe", "vannpumpe"],
            synonyms_en=["pump", "circulation pump"]
        )
        
        self.entities[BrickClass.ELECTRICAL_METER] = EntityDefinition(
            brick_class=BrickClass.ELECTRICAL_METER,
            name="Electrical Meter",
            description="Meter for measuring electricity consumption",
            properties=["id", "name", "unit"],
            synonyms_no=["strømmåler", "elmåler", "elektrisitetsmåler", "hovedmåler"],
            synonyms_en=["electrical meter", "power meter", "electricity meter"]
        )
        
        self.entities[BrickClass.TEMPERATURE_SENSOR] = EntityDefinition(
            brick_class=BrickClass.TEMPERATURE_SENSOR,
            name="Temperature Sensor",
            description="Sensor measuring temperature",
            properties=["id", "name", "unit"],
            synonyms_no=["temperatursensor", "temperaturføler", "temp", "temperatur"],
            synonyms_en=["temperature sensor", "temp sensor", "temperature"]
        )
        
        self.entities[BrickClass.POWER_SENSOR] = EntityDefinition(
            brick_class=BrickClass.POWER_SENSOR,
            name="Power Sensor",
            description="Sensor measuring power consumption",
            properties=["id", "name", "unit"],
            synonyms_no=["effektmåler", "wattmåler", "strømsensor", "effekt"],
            synonyms_en=["power sensor", "watt sensor", "power meter"]
        )
        
        self.entities[BrickClass.CO2_SENSOR] = EntityDefinition(
            brick_class=BrickClass.CO2_SENSOR,
            name="CO2 Sensor",
            description="Sensor measuring CO2 levels",
            properties=["id", "name", "unit"],
            synonyms_no=["co2-sensor", "co2", "luftkvalitet"],
            synonyms_en=["co2 sensor", "carbon dioxide sensor", "air quality"]
        )
        
        self.entities[BrickClass.TIMESERIES] = EntityDefinition(
            brick_class=BrickClass.TIMESERIES,
            name="Timeseries",
            description="Reference to external timeseries data",
            properties=["id", "external_id", "resolution"],
            synonyms_no=["tidsserie", "data", "målinger", "historikk"],
            synonyms_en=["timeseries", "time series", "data", "measurements", "history"]
        )
    
    def _init_traversals(self):
        """Define common traversal patterns."""
        
        self.traversals["building_sensors"] = TraversalPattern(
            name="building_sensors",
            description="All sensors in a building (through systems and equipment)",
            cypher_pattern="""
MATCH (b:brick_Building)-[:brick_hasPart*1..2]->(sys)
      -[:brick_hasMember]->(eq)-[:brick_hasPoint]->(s)
WHERE b.id = $building_id OR b.name CONTAINS $building_name
RETURN eq.name as equipment, s.name as sensor, s.unit as unit""",
            return_fields=["equipment", "sensor", "unit"]
        )
        
        self.traversals["zone_sensors"] = TraversalPattern(
            name="zone_sensors",
            description="All sensors in a specific zone",
            cypher_pattern="""
MATCH (z:brick_HVAC_Zone)-[:brick_hasPoint]->(s)
WHERE z.id = $zone_id OR z.name CONTAINS $zone_name
RETURN z.name as zone, s.name as sensor, labels(s)[0] as type, s.unit as unit""",
            return_fields=["zone", "sensor", "type", "unit"]
        )
        
        self.traversals["equipment_timeseries"] = TraversalPattern(
            name="equipment_timeseries",
            description="Timeseries data references for equipment sensors",
            cypher_pattern="""
MATCH (eq)-[:brick_hasPoint]->(s)-[:brick_hasTimeseries]->(ts)
WHERE eq.id = $equipment_id OR eq.name CONTAINS $equipment_name
RETURN eq.name as equipment, s.name as sensor, ts.external_id as timeseries_id""",
            return_fields=["equipment", "sensor", "timeseries_id"]
        )
        
        self.traversals["ahu_zones"] = TraversalPattern(
            name="ahu_zones",
            description="Which zones an AHU feeds",
            cypher_pattern="""
MATCH (ahu:brick_Air_Handling_Unit)-[:brick_feeds]->(z:brick_HVAC_Zone)
WHERE ahu.id = $ahu_id OR ahu.name CONTAINS $ahu_name
RETURN ahu.name as ahu, collect(z.name) as zones""",
            return_fields=["ahu", "zones"]
        )
        
        self.traversals["building_meters"] = TraversalPattern(
            name="building_meters",
            description="All meters for a building",
            cypher_pattern="""
MATCH (b:brick_Building)-[:brick_isMeteredBy]->(m)
WHERE b.id = $building_id OR b.name CONTAINS $building_name
RETURN m.name as meter, labels(m)[0] as type, m.unit as unit""",
            return_fields=["meter", "type", "unit"]
        )
        
        self.traversals["full_hierarchy"] = TraversalPattern(
            name="full_hierarchy",
            description="Full hierarchy from building to timeseries",
            cypher_pattern="""
MATCH path = (b:brick_Building)-[:brick_hasPart|brick_hasMember|brick_hasPoint|brick_hasTimeseries*1..5]->(end)
WHERE b.id = $building_id OR b.name CONTAINS $building_name
RETURN [node in nodes(path) | {label: labels(node)[0], name: node.name}] as hierarchy
LIMIT 20""",
            return_fields=["hierarchy"]
        )
    
    def _init_intent_patterns(self):
        """Define patterns for intent detection."""
        
        self.intent_patterns[IntentType.QUERY_ENTITY] = [
            # Norwegian
            "hva er", "vis meg", "finn", "hent", "gi meg info om",
            "detaljer om", "informasjon om",
            # English
            "what is", "show me", "find", "get", "give me info about",
            "details about", "information about"
        ]
        
        self.intent_patterns[IntentType.QUERY_LIST] = [
            # Norwegian
            "vis alle", "list opp", "hvilke", "gi meg alle", "hent alle",
            "hvor mange", "list alle",
            # English
            "show all", "list all", "which", "give me all", "get all",
            "how many", "what are the"
        ]
        
        self.intent_patterns[IntentType.QUERY_TRAVERSE] = [
            # Norwegian  
            "sensorer i", "utstyr i", "soner som", "som mater", "koblet til",
            "relatert til", "i bygget", "i sonen", "tilhører",
            # English
            "sensors in", "equipment in", "zones that", "feeds", "connected to",
            "related to", "in building", "in zone", "belongs to"
        ]
        
        self.intent_patterns[IntentType.QUERY_AGGREGATE] = [
            # Norwegian
            "antall", "totalt", "sum", "gjennomsnitt", "tell",
            # English
            "count", "total", "sum", "average", "number of"
        ]
        
        self.intent_patterns[IntentType.QUERY_PATH] = [
            # Norwegian
            "vei mellom", "sti fra", "kobling mellom", "forbindelse",
            # English
            "path between", "path from", "connection between", "link"
        ]
    
    def find_entity_by_text(self, text: str) -> Optional[BrickClass]:
        """Find entity type from natural language text."""
        text_lower = text.lower()
        
        for brick_class, entity in self.entities.items():
            # Check synonyms (Norwegian and English)
            all_synonyms = entity.synonyms_no + entity.synonyms_en + [entity.name.lower()]
            for synonym in all_synonyms:
                if synonym in text_lower:
                    return brick_class
        
        return None
    
    def find_traversal_by_intent(self, text: str) -> Optional[TraversalPattern]:
        """Find best matching traversal pattern for query."""
        text_lower = text.lower()
        
        # Keywords to traversal mapping
        traversal_keywords = {
            "building_sensors": ["sensorer i bygg", "sensors in building", "alle sensorer"],
            "zone_sensors": ["sensorer i sone", "sensors in zone", "sone sensor"],
            "equipment_timeseries": ["tidsserie", "timeseries", "data for", "målinger"],
            "ahu_zones": ["soner som", "zones fed", "mater", "feeds"],
            "building_meters": ["målere", "meters", "strømmåler", "electrical meter"],
            "full_hierarchy": ["hierarki", "hierarchy", "full oversikt", "alt i"]
        }
        
        for traversal_name, keywords in traversal_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return self.traversals.get(traversal_name)
        
        return None
    
    def detect_intent(self, text: str) -> IntentType:
        """Detect intent type from text."""
        text_lower = text.lower()
        
        for intent_type, patterns in self.intent_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return intent_type
        
        return IntentType.UNKNOWN
    
    def to_llm_context(self) -> str:
        """Export ontology as LLM context string."""
        lines = ["BRICK ONTOLOGY CONTEXT", "=" * 40, ""]
        
        lines.append("ENTITY TYPES:")
        for brick_class, entity in self.entities.items():
            lines.append(f"  - {entity.name} ({brick_class.value})")
            lines.append(f"    Norwegian: {', '.join(entity.synonyms_no[:3])}")
            lines.append(f"    Properties: {', '.join(entity.properties)}")
        
        lines.append("\nTRAVERSAL PATTERNS:")
        for name, pattern in self.traversals.items():
            lines.append(f"  - {name}: {pattern.description}")
        
        return "\n".join(lines)
