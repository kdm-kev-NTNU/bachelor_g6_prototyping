"""
GraphQL Query Generator

Generates GraphQL queries from extracted intents.
This is the NL → GraphQL step of the pipeline.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from ontology import BrickOntology, BrickClass, IntentType


@dataclass
class GeneratedGraphQL:
    """Generated GraphQL query with metadata."""
    query: str
    variables: Dict[str, Any]
    operation_name: str
    description: str
    requested_fields: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "variables": self.variables,
            "operation": self.operation_name,
            "description": self.description,
            "fields": self.requested_fields
        }


class GraphQLGenerator:
    """
    Generates GraphQL queries from semantic intents.
    
    Maps Brick ontology concepts to GraphQL schema operations.
    """
    
    def __init__(self, ontology: BrickOntology):
        self.ontology = ontology
        
        # Map BrickClass to GraphQL query/type
        self.entity_to_query = {
            BrickClass.BUILDING: ("building", "Building"),
            BrickClass.FLOOR: ("floors", "Floor"),
            BrickClass.HVAC_ZONE: ("zones", "HVACZone"),
            BrickClass.HVAC_SYSTEM: ("systems", "System"),
            BrickClass.ELECTRICAL_SYSTEM: ("systems", "System"),
            BrickClass.AHU: ("equipment", "Equipment"),
            BrickClass.CHILLER: ("equipment", "Equipment"),
            BrickClass.PUMP: ("equipment", "Equipment"),
            BrickClass.TEMPERATURE_SENSOR: ("sensors", "Sensor"),
            BrickClass.POWER_SENSOR: ("sensors", "Sensor"),
            BrickClass.CO2_SENSOR: ("sensors", "Sensor"),
            BrickClass.ELECTRICAL_METER: ("meters", "Meter"),
            BrickClass.TIMESERIES: ("timeseries", "Timeseries"),
        }
        
        # Fields for each GraphQL type
        self.type_fields = {
            "Building": ["id", "name", "address", "areaSqm", "yearBuilt", "energyClass"],
            "Floor": ["id", "name", "level"],
            "HVACZone": ["id", "name"],
            "System": ["id", "name", "systemType"],
            "Equipment": ["id", "name", "equipmentType", "manufacturer", "model"],
            "Sensor": ["id", "name", "unit", "sensorType"],
            "Meter": ["id", "name", "meterType", "unit"],
            "Timeseries": ["id", "externalId", "resolution"],
        }
    
    def generate(
        self,
        intent_type: IntentType,
        entity_class: Optional[BrickClass],
        parameters: Dict[str, Any],
        requested_fields: List[str] = None
    ) -> GeneratedGraphQL:
        """
        Generate a GraphQL query from intent.
        """
        
        if intent_type == IntentType.QUERY_ENTITY:
            return self._generate_single_query(entity_class, parameters, requested_fields)
        
        elif intent_type == IntentType.QUERY_LIST:
            return self._generate_list_query(entity_class, parameters, requested_fields)
        
        elif intent_type == IntentType.QUERY_TRAVERSE:
            return self._generate_traverse_query(entity_class, parameters, requested_fields)
        
        elif intent_type == IntentType.QUERY_AGGREGATE:
            return self._generate_aggregate_query(entity_class, parameters)
        
        else:
            return self._generate_default_query(entity_class, parameters)
    
    def _generate_single_query(
        self,
        entity_class: Optional[BrickClass],
        parameters: Dict[str, Any],
        requested_fields: List[str] = None
    ) -> GeneratedGraphQL:
        """Generate query for single entity."""
        
        if entity_class is None:
            entity_class = BrickClass.BUILDING
        
        query_name, type_name = self.entity_to_query.get(
            entity_class, ("building", "Building")
        )
        
        # Build fields
        fields = requested_fields or self.type_fields.get(type_name, ["id", "name"])
        field_str = "\n      ".join(fields)
        
        # Build arguments
        args = []
        variables = {}
        
        if "id" in parameters:
            args.append("id: $id")
            variables["id"] = parameters["id"]
        if "name" in parameters or "building_name" in parameters:
            args.append("name: $name")
            variables["name"] = parameters.get("name", parameters.get("building_name", ""))
        
        args_str = f"({', '.join(args)})" if args else ""
        
        # For single entity, use singular query
        if query_name.endswith("s"):
            singular_query = query_name[:-1]  # buildings -> building
        else:
            singular_query = query_name
        
        query = f"""query Get{type_name}($id: String, $name: String) {{
  {singular_query}{args_str} {{
      {field_str}
  }}
}}"""
        
        return GeneratedGraphQL(
            query=query,
            variables=variables,
            operation_name=f"Get{type_name}",
            description=f"Get {type_name} by ID or name",
            requested_fields=fields
        )
    
    def _generate_list_query(
        self,
        entity_class: Optional[BrickClass],
        parameters: Dict[str, Any],
        requested_fields: List[str] = None
    ) -> GeneratedGraphQL:
        """Generate query for listing entities."""
        
        if entity_class is None:
            # Default to buildings
            return GeneratedGraphQL(
                query="""query ListBuildings {
  buildings {
      id
      name
      address
  }
}""",
                variables={},
                operation_name="ListBuildings",
                description="List all buildings",
                requested_fields=["id", "name", "address"]
            )
        
        query_name, type_name = self.entity_to_query.get(
            entity_class, ("buildings", "Building")
        )
        
        # Ensure plural
        if not query_name.endswith("s"):
            query_name = query_name + "s"
        
        fields = requested_fields or self.type_fields.get(type_name, ["id", "name"])
        field_str = "\n      ".join(fields)
        
        # Build filter arguments based on entity type
        args = []
        variables = {}
        var_declarations = []
        
        # Add type-specific filters
        if entity_class in [BrickClass.TEMPERATURE_SENSOR, BrickClass.POWER_SENSOR, BrickClass.CO2_SENSOR]:
            sensor_type = entity_class.value.replace("brick_", "")
            args.append(f'sensorType: "{sensor_type}"')
        elif entity_class in [BrickClass.AHU, BrickClass.CHILLER, BrickClass.PUMP]:
            equip_type = entity_class.value.replace("brick_", "")
            args.append(f'equipmentType: "{equip_type}"')
        elif entity_class in [BrickClass.HVAC_SYSTEM, BrickClass.ELECTRICAL_SYSTEM]:
            sys_type = entity_class.value.replace("brick_", "").replace("_System", "")
            args.append(f'systemType: "{sys_type}"')
        
        # Building filter
        if "building_id" in parameters:
            args.append("buildingId: $buildingId")
            variables["buildingId"] = parameters["building_id"]
            var_declarations.append("$buildingId: String")
        
        args_str = f"({', '.join(args)})" if args else ""
        var_str = f"({', '.join(var_declarations)})" if var_declarations else ""
        
        query = f"""query List{type_name}s{var_str} {{
  {query_name}{args_str} {{
      {field_str}
  }}
}}"""
        
        return GeneratedGraphQL(
            query=query,
            variables=variables,
            operation_name=f"List{type_name}s",
            description=f"List all {type_name}s",
            requested_fields=fields
        )
    
    def _generate_traverse_query(
        self,
        entity_class: Optional[BrickClass],
        parameters: Dict[str, Any],
        requested_fields: List[str] = None
    ) -> GeneratedGraphQL:
        """Generate traversal query with nested fields."""
        
        # Determine what kind of traversal based on entity and parameters
        
        if entity_class == BrickClass.BUILDING or "building" in str(parameters).lower():
            # Building with all nested entities
            return GeneratedGraphQL(
                query="""query BuildingWithDetails($name: String) {
  building(name: $name) {
      id
      name
      address
      areaSqm
      energyClass
      floors {
          id
          name
          level
          zones {
              id
              name
          }
      }
      systems {
          id
          name
          systemType
          equipment {
              id
              name
              equipmentType
          }
      }
      meters {
          id
          name
          meterType
      }
  }
}""",
                variables={"name": parameters.get("name", parameters.get("building_name", ""))},
                operation_name="BuildingWithDetails",
                description="Get building with all details",
                requested_fields=["id", "name", "floors", "systems", "meters"]
            )
        
        elif entity_class == BrickClass.HVAC_ZONE or "zone" in str(parameters).lower():
            # Zone with sensors
            zone_name = parameters.get("zone_name", parameters.get("name", ""))
            return GeneratedGraphQL(
                query="""query ZoneWithSensors($name: String) {
  zones {
      id
      name
      sensors {
          id
          name
          unit
          sensorType
          timeseries {
              externalId
              resolution
          }
      }
      fedBy {
          id
          name
          equipmentType
      }
  }
}""",
                variables={"name": zone_name},
                operation_name="ZoneWithSensors",
                description="Get zones with sensors",
                requested_fields=["id", "name", "sensors", "fedBy"]
            )
        
        elif entity_class == BrickClass.AHU or "ahu" in str(parameters).lower() or "aggregat" in str(parameters).lower():
            # AHU with zones it feeds
            return GeneratedGraphQL(
                query="""query AHUWithZones($name: String) {
  equipment(equipmentType: "Air_Handling_Unit") {
      id
      name
      manufacturer
      model
      sensors {
          id
          name
          unit
          sensorType
      }
  }
}""",
                variables={"name": parameters.get("name", parameters.get("ahu_name", ""))},
                operation_name="AHUWithZones",
                description="Get AHU with zones and sensors",
                requested_fields=["id", "name", "sensors"]
            )
        
        elif entity_class in [BrickClass.TEMPERATURE_SENSOR, BrickClass.POWER_SENSOR, BrickClass.CO2_SENSOR]:
            # Sensors with timeseries
            sensor_type = entity_class.value.replace("brick_", "") if entity_class else ""
            return GeneratedGraphQL(
                query=f"""query SensorsWithTimeseries {{
  sensors(sensorType: "{sensor_type}") {{
      id
      name
      unit
      sensorType
      timeseries {{
          id
          externalId
          resolution
      }}
  }}
}}""",
                variables={},
                operation_name="SensorsWithTimeseries",
                description=f"Get {sensor_type} sensors with timeseries",
                requested_fields=["id", "name", "unit", "timeseries"]
            )
        
        # Default: sensors in building
        return GeneratedGraphQL(
            query="""query AllSensors {
  sensors {
      id
      name
      unit
      sensorType
      timeseries {
          externalId
      }
  }
}""",
            variables={},
            operation_name="AllSensors",
            description="Get all sensors with timeseries",
            requested_fields=["id", "name", "unit", "sensorType"]
        )
    
    def _generate_aggregate_query(
        self,
        entity_class: Optional[BrickClass],
        parameters: Dict[str, Any]
    ) -> GeneratedGraphQL:
        """Generate aggregation query."""
        
        if entity_class in [BrickClass.TEMPERATURE_SENSOR, BrickClass.POWER_SENSOR, 
                           BrickClass.CO2_SENSOR, BrickClass.HUMIDITY_SENSOR]:
            sensor_type = entity_class.value.replace("brick_", "") if entity_class else ""
            return GeneratedGraphQL(
                query=f"""query CountSensors {{
  sensorCount(sensorType: "{sensor_type}")
}}""",
                variables={},
                operation_name="CountSensors",
                description=f"Count {sensor_type if sensor_type else 'all'} sensors",
                requested_fields=["count"]
            )
        
        elif entity_class in [BrickClass.AHU, BrickClass.CHILLER, BrickClass.PUMP]:
            equip_type = entity_class.value.replace("brick_", "") if entity_class else ""
            return GeneratedGraphQL(
                query=f"""query CountEquipment {{
  equipmentCount(equipmentType: "{equip_type}")
}}""",
                variables={},
                operation_name="CountEquipment",
                description=f"Count {equip_type if equip_type else 'all'} equipment",
                requested_fields=["count"]
            )
        
        elif entity_class == BrickClass.FLOOR:
            return GeneratedGraphQL(
                query="""query CountFloors {
  floors {
      id
  }
}""",
                variables={},
                operation_name="CountFloors",
                description="Count floors",
                requested_fields=["count"]
            )
        
        # Default count
        return GeneratedGraphQL(
            query="""query CountSensors {
  sensorCount
}""",
            variables={},
            operation_name="CountSensors",
            description="Count all sensors",
            requested_fields=["count"]
        )
    
    def _generate_default_query(
        self,
        entity_class: Optional[BrickClass],
        parameters: Dict[str, Any]
    ) -> GeneratedGraphQL:
        """Generate default query."""
        return GeneratedGraphQL(
            query="""query Overview {
  buildings {
      id
      name
      address
  }
}""",
            variables={},
            operation_name="Overview",
            description="Get building overview",
            requested_fields=["id", "name", "address"]
        )
