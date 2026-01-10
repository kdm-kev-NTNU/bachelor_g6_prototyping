"""
Seed Data for FalkorDB Energy Knowledge Graph

Sample data based on real Norwegian buildings that use Piscada's 
energy management solutions. This provides realistic test data for
exploring the knowledge graph.

Buildings included:
- Operahuset (Oslo Opera House)
- Deichmanske Hovedbibliotek (Deichman Main Library)
- Barcode B13 (Commercial building in Bjørvika)
- Powerhouse Brattørkaia (Energy-positive building in Trondheim)
"""

from schema import (
    Building, Floor, Zone, Meter, Equipment, Sensor, System,
    BrickRelationship, BrickRelation, BrickClass
)
from typing import List, Tuple


def create_buildings() -> List[Building]:
    """Create sample Norwegian buildings."""
    return [
        Building(
            id="building_opera",
            name="Operahuset",
            description="Oslo Opera House - Iconic cultural building in Bjørvika",
            address="Kirsten Flagstads Plass 1, 0150 Oslo",
            latitude=59.9075,
            longitude=10.7531,
            area_sqm=38500,
            year_built=2008,
            energy_class="B"
        ),
        Building(
            id="building_deichman",
            name="Deichmanske Hovedbibliotek",
            description="New main library in Bjørvika, Oslo",
            address="Anne-Cath. Vestlys plass 1, 0150 Oslo",
            latitude=59.9082,
            longitude=10.7503,
            area_sqm=13500,
            year_built=2020,
            energy_class="A"
        ),
        Building(
            id="building_barcode_b13",
            name="Barcode B13",
            description="Modern office building in Barcode development, Oslo",
            address="Dronning Eufemias gate 30, 0191 Oslo",
            latitude=59.9088,
            longitude=10.7572,
            area_sqm=22000,
            year_built=2016,
            energy_class="A"
        ),
        Building(
            id="building_powerhouse",
            name="Powerhouse Brattørkaia",
            description="Energy-positive office building in Trondheim",
            address="Brattørkaia 17A, 7010 Trondheim",
            latitude=63.4390,
            longitude=10.4025,
            area_sqm=8800,
            year_built=2019,
            energy_class="A"  # Actually energy-positive!
        ),
        Building(
            id="building_pir2",
            name="Pir 2",
            description="Sustainable office building at Aker Brygge",
            address="Stranden 1, 0250 Oslo",
            latitude=59.9110,
            longitude=10.7250,
            area_sqm=16000,
            year_built=2015,
            energy_class="A"
        ),
    ]


def create_floors(buildings: List[Building]) -> List[Floor]:
    """Create floors for each building."""
    floors = []
    
    # Opera House floors
    for level in range(-2, 6):  # Basement -2 to floor 5
        floors.append(Floor(
            id=f"floor_opera_{level}",
            name=f"Etasje {level}" if level >= 0 else f"Kjeller {abs(level)}",
            description=f"Floor {level} of Oslo Opera House",
            level=level,
            area_sqm=38500 / 8  # Simplified
        ))
    
    # Deichman floors
    for level in range(0, 6):
        floors.append(Floor(
            id=f"floor_deichman_{level}",
            name=f"Etasje {level}",
            description=f"Floor {level} of Deichman Library",
            level=level,
            area_sqm=13500 / 6
        ))
    
    # Barcode B13 floors
    for level in range(-1, 13):
        floors.append(Floor(
            id=f"floor_barcode_{level}",
            name=f"Etasje {level}" if level >= 0 else "Kjeller",
            description=f"Floor {level} of Barcode B13",
            level=level,
            area_sqm=22000 / 14
        ))
    
    # Powerhouse floors
    for level in range(0, 8):
        floors.append(Floor(
            id=f"floor_powerhouse_{level}",
            name=f"Etasje {level}",
            description=f"Floor {level} of Powerhouse Brattørkaia",
            level=level,
            area_sqm=8800 / 8
        ))
    
    return floors


def create_meters(buildings: List[Building]) -> List[Meter]:
    """Create energy meters for buildings."""
    meters = []
    
    for building in buildings:
        bid = building.id.replace("building_", "")
        
        # Main electrical meter
        meters.append(Meter(
            id=f"meter_elec_main_{bid}",
            name=f"Hovedmåler Elektrisitet - {building.name}",
            description=f"Main electrical meter for {building.name}",
            meter_type="electrical",
            unit="kWh"
        ))
        
        # Sub-meters
        meters.append(Meter(
            id=f"meter_elec_hvac_{bid}",
            name=f"Undermåler HVAC - {building.name}",
            description=f"HVAC electrical sub-meter for {building.name}",
            meter_type="electrical",
            unit="kWh"
        ))
        
        meters.append(Meter(
            id=f"meter_elec_lighting_{bid}",
            name=f"Undermåler Belysning - {building.name}",
            description=f"Lighting electrical sub-meter for {building.name}",
            meter_type="electrical",
            unit="kWh"
        ))
        
        # Thermal/heating meter
        meters.append(Meter(
            id=f"meter_thermal_{bid}",
            name=f"Varmemåler - {building.name}",
            description=f"Thermal energy meter for {building.name}",
            meter_type="thermal",
            unit="kWh"
        ))
        
        # Water meter
        meters.append(Meter(
            id=f"meter_water_{bid}",
            name=f"Vannmåler - {building.name}",
            description=f"Water meter for {building.name}",
            meter_type="water",
            unit="m3"
        ))
    
    return meters


def create_equipment(buildings: List[Building]) -> List[Equipment]:
    """Create HVAC equipment for buildings."""
    equipment = []
    
    # Opera House - Large HVAC system
    equipment.extend([
        Equipment(
            id="ahu_opera_main",
            name="Hovedaggregat AHU-01",
            description="Main air handling unit for Opera House",
            equipment_type="ahu",
            manufacturer="Swegon",
            model="Gold RX",
            capacity=50000,
            capacity_unit="m3/h"
        ),
        Equipment(
            id="ahu_opera_stage",
            name="Sceneaggregat AHU-02",
            description="Stage area air handling unit",
            equipment_type="ahu",
            manufacturer="Swegon",
            capacity=25000,
            capacity_unit="m3/h"
        ),
        Equipment(
            id="chiller_opera",
            name="Kjølemaskin CH-01",
            description="Main chiller for Opera House",
            equipment_type="chiller",
            manufacturer="Carrier",
            model="AquaEdge 23XRV",
            capacity=2000,
            capacity_unit="kW"
        ),
        Equipment(
            id="pump_opera_chw",
            name="Kjølevannspumpe P-01",
            description="Chilled water pump",
            equipment_type="pump",
            manufacturer="Grundfos",
            model="TPE 150-70/4",
            capacity=75,
            capacity_unit="kW"
        ),
    ])
    
    # Deichman Library
    equipment.extend([
        Equipment(
            id="ahu_deichman_main",
            name="Hovedaggregat AHU-01",
            description="Main air handling unit for Deichman",
            equipment_type="ahu",
            manufacturer="Systemair",
            model="Topvex TR",
            capacity=30000,
            capacity_unit="m3/h"
        ),
        Equipment(
            id="heat_pump_deichman",
            name="Varmepumpe HP-01",
            description="Heat pump system",
            equipment_type="heat_exchanger",
            manufacturer="NIBE",
            model="F1355",
            capacity=400,
            capacity_unit="kW"
        ),
    ])
    
    # Barcode B13
    equipment.extend([
        Equipment(
            id="ahu_barcode_main",
            name="Hovedaggregat AHU-01",
            description="Main air handling unit for Barcode B13",
            equipment_type="ahu",
            manufacturer="Fläkt Group",
            model="eQ Prime",
            capacity=35000,
            capacity_unit="m3/h"
        ),
        Equipment(
            id="vav_barcode_1",
            name="VAV-boks Etasje 3",
            description="Variable air volume box floor 3",
            equipment_type="vav",
            manufacturer="Lindab",
            model="ULA",
            capacity=2500,
            capacity_unit="m3/h"
        ),
        Equipment(
            id="vav_barcode_2",
            name="VAV-boks Etasje 4",
            description="Variable air volume box floor 4",
            equipment_type="vav",
            manufacturer="Lindab",
            model="ULA",
            capacity=2500,
            capacity_unit="m3/h"
        ),
    ])
    
    # Powerhouse (energy-positive building - special equipment)
    equipment.extend([
        Equipment(
            id="ahu_powerhouse",
            name="Energiaggregat AHU-01",
            description="High-efficiency air handling unit",
            equipment_type="ahu",
            manufacturer="Swegon",
            model="Gold PX",
            capacity=15000,
            capacity_unit="m3/h"
        ),
        Equipment(
            id="heat_pump_powerhouse",
            name="Sjøvannsvarmepumpe HP-01",
            description="Seawater heat pump for heating/cooling",
            equipment_type="heat_exchanger",
            manufacturer="Star Refrigeration",
            model="Neatpump",
            capacity=300,
            capacity_unit="kW"
        ),
    ])
    
    return equipment


def create_zones(buildings: List[Building]) -> List[Zone]:
    """Create HVAC zones for buildings."""
    zones = []
    
    # Opera zones
    zones.extend([
        Zone(id="zone_opera_foyer", name="Foyer-sone", description="Main entrance foyer", zone_type="hvac"),
        Zone(id="zone_opera_hall", name="Hovedsal-sone", description="Main concert hall", zone_type="hvac"),
        Zone(id="zone_opera_stage", name="Scene-sone", description="Stage area", zone_type="hvac"),
        Zone(id="zone_opera_backstage", name="Backstage-sone", description="Backstage areas", zone_type="hvac"),
    ])
    
    # Deichman zones
    zones.extend([
        Zone(id="zone_deichman_reading", name="Lesesal-sone", description="Reading room", zone_type="hvac"),
        Zone(id="zone_deichman_archive", name="Arkiv-sone", description="Archive storage (climate controlled)", zone_type="hvac"),
        Zone(id="zone_deichman_public", name="Publikum-sone", description="Public areas", zone_type="hvac"),
    ])
    
    # Barcode zones (office building typical setup)
    for floor in range(1, 6):
        zones.extend([
            Zone(id=f"zone_barcode_office_{floor}", name=f"Kontor-sone Etasje {floor}", zone_type="hvac"),
            Zone(id=f"zone_barcode_meeting_{floor}", name=f"Møterom-sone Etasje {floor}", zone_type="hvac"),
        ])
    
    return zones


def create_sensors(equipment: List[Equipment], zones: List[Zone]) -> List[Sensor]:
    """Create sensors for equipment and zones."""
    sensors = []
    
    # Temperature sensors for zones
    for zone in zones:
        sensors.append(Sensor(
            id=f"sensor_temp_{zone.id}",
            name=f"Temperatur {zone.name}",
            description=f"Zone temperature sensor for {zone.name}",
            sensor_type="temperature",
            unit="°C",
            current_value=21.5  # Typical indoor temp
        ))
        
        sensors.append(Sensor(
            id=f"sensor_co2_{zone.id}",
            name=f"CO2 {zone.name}",
            description=f"CO2 sensor for {zone.name}",
            sensor_type="co2",
            unit="ppm",
            current_value=650
        ))
    
    # Equipment sensors
    for eq in equipment:
        if eq.equipment_type.lower() == "ahu":
            sensors.extend([
                Sensor(
                    id=f"sensor_temp_supply_{eq.id}",
                    name=f"Tilluftstemp {eq.name}",
                    description=f"Supply air temperature for {eq.name}",
                    sensor_type="temperature",
                    unit="°C",
                    current_value=18.0
                ),
                Sensor(
                    id=f"sensor_temp_return_{eq.id}",
                    name=f"Avtrekkstempe {eq.name}",
                    description=f"Return air temperature for {eq.name}",
                    sensor_type="temperature",
                    unit="°C",
                    current_value=22.0
                ),
                Sensor(
                    id=f"sensor_power_{eq.id}",
                    name=f"Effekt {eq.name}",
                    description=f"Power consumption for {eq.name}",
                    sensor_type="power",
                    unit="kW",
                    current_value=45.0
                ),
            ])
        
        elif eq.equipment_type.lower() in ["chiller", "heat_exchanger"]:
            sensors.extend([
                Sensor(
                    id=f"sensor_power_{eq.id}",
                    name=f"Effekt {eq.name}",
                    description=f"Power consumption for {eq.name}",
                    sensor_type="power",
                    unit="kW",
                    current_value=120.0
                ),
                Sensor(
                    id=f"sensor_temp_in_{eq.id}",
                    name=f"Innløpstemp {eq.name}",
                    description=f"Inlet temperature for {eq.name}",
                    sensor_type="temperature",
                    unit="°C",
                    current_value=12.0
                ),
                Sensor(
                    id=f"sensor_temp_out_{eq.id}",
                    name=f"Utløpstemp {eq.name}",
                    description=f"Outlet temperature for {eq.name}",
                    sensor_type="temperature",
                    unit="°C",
                    current_value=7.0
                ),
            ])
    
    return sensors


def create_systems(buildings: List[Building]) -> List[System]:
    """Create building systems."""
    systems = []
    
    for building in buildings:
        bid = building.id.replace("building_", "")
        
        systems.extend([
            System(
                id=f"system_hvac_{bid}",
                name=f"HVAC-system {building.name}",
                description=f"Complete HVAC system for {building.name}",
                system_type="hvac"
            ),
            System(
                id=f"system_electrical_{bid}",
                name=f"Elektrisk anlegg {building.name}",
                description=f"Electrical system for {building.name}",
                system_type="electrical"
            ),
            System(
                id=f"system_lighting_{bid}",
                name=f"Belysningsanlegg {building.name}",
                description=f"Lighting system for {building.name}",
                system_type="lighting"
            ),
        ])
    
    return systems


def create_relationships(
    buildings: List[Building],
    floors: List[Floor],
    meters: List[Meter],
    equipment: List[Equipment],
    zones: List[Zone],
    sensors: List[Sensor],
    systems: List[System]
) -> List[BrickRelationship]:
    """Create all relationships between entities."""
    relationships = []
    
    # Floor -> Building (isPartOf)
    building_floor_map = {
        "opera": "building_opera",
        "deichman": "building_deichman",
        "barcode": "building_barcode_b13",
        "powerhouse": "building_powerhouse",
    }
    
    for floor in floors:
        for key, building_id in building_floor_map.items():
            if key in floor.id:
                relationships.append(BrickRelationship(
                    from_id=floor.id,
                    to_id=building_id,
                    relation_type=BrickRelation.IS_PART_OF
                ))
                break
    
    # Meter -> Building (meters)
    for meter in meters:
        for key, building_id in building_floor_map.items():
            if key in meter.id:
                relationships.append(BrickRelationship(
                    from_id=meter.id,
                    to_id=building_id,
                    relation_type=BrickRelation.METERS
                ))
                break
    
    # Sub-meter relationships
    for meter in meters:
        if "hvac" in meter.id or "lighting" in meter.id:
            # Find main meter
            parts = meter.id.split("_")
            building_key = parts[-1]
            main_meter_id = f"meter_elec_main_{building_key}"
            relationships.append(BrickRelationship(
                from_id=main_meter_id,
                to_id=meter.id,
                relation_type=BrickRelation.HAS_SUB_METER
            ))
    
    # Equipment -> Building (hasLocation)
    equipment_building_map = {
        "opera": "building_opera",
        "deichman": "building_deichman",
        "barcode": "building_barcode_b13",
        "powerhouse": "building_powerhouse",
    }
    
    for eq in equipment:
        for key, building_id in equipment_building_map.items():
            if key in eq.id:
                relationships.append(BrickRelationship(
                    from_id=eq.id,
                    to_id=building_id,
                    relation_type=BrickRelation.HAS_LOCATION
                ))
                break
    
    # Zone -> Building (hasLocation)
    zone_building_map = {
        "opera": "building_opera",
        "deichman": "building_deichman",
        "barcode": "building_barcode_b13",
    }
    
    for zone in zones:
        for key, building_id in zone_building_map.items():
            if key in zone.id:
                relationships.append(BrickRelationship(
                    from_id=zone.id,
                    to_id=building_id,
                    relation_type=BrickRelation.HAS_LOCATION
                ))
                break
    
    # Sensor -> Equipment (isPointOf) and Zone (isPointOf)
    for sensor in sensors:
        # Equipment sensors
        for eq in equipment:
            if eq.id in sensor.id:
                relationships.append(BrickRelationship(
                    from_id=sensor.id,
                    to_id=eq.id,
                    relation_type=BrickRelation.IS_POINT_OF
                ))
                break
        
        # Zone sensors
        for zone in zones:
            if zone.id in sensor.id:
                relationships.append(BrickRelationship(
                    from_id=sensor.id,
                    to_id=zone.id,
                    relation_type=BrickRelation.IS_POINT_OF
                ))
                break
    
    # AHU feeds zones
    ahu_zone_feeds = [
        ("ahu_opera_main", ["zone_opera_foyer", "zone_opera_backstage"]),
        ("ahu_opera_stage", ["zone_opera_hall", "zone_opera_stage"]),
        ("ahu_deichman_main", ["zone_deichman_reading", "zone_deichman_public", "zone_deichman_archive"]),
        ("ahu_barcode_main", [f"zone_barcode_office_{i}" for i in range(1, 6)]),
    ]
    
    for ahu_id, zone_ids in ahu_zone_feeds:
        for zone_id in zone_ids:
            relationships.append(BrickRelationship(
                from_id=ahu_id,
                to_id=zone_id,
                relation_type=BrickRelation.FEEDS
            ))
    
    # System -> Equipment (hasMember)
    for eq in equipment:
        for key, building_id in equipment_building_map.items():
            if key in eq.id:
                system_id = f"system_hvac_{key}"
                relationships.append(BrickRelationship(
                    from_id=system_id,
                    to_id=eq.id,
                    relation_type=BrickRelation.HAS_MEMBER
                ))
                break
    
    # System -> Building (hasLocation)
    for system in systems:
        for key, building_id in equipment_building_map.items():
            if key in system.id:
                relationships.append(BrickRelationship(
                    from_id=system.id,
                    to_id=building_id,
                    relation_type=BrickRelation.HAS_LOCATION
                ))
                break
    
    return relationships


def get_all_seed_data() -> Tuple[List, List[BrickRelationship]]:
    """
    Generate all seed data for the knowledge graph.
    
    Returns:
        Tuple of (list of all entities, list of all relationships)
    """
    buildings = create_buildings()
    floors = create_floors(buildings)
    meters = create_meters(buildings)
    equipment = create_equipment(buildings)
    zones = create_zones(buildings)
    sensors = create_sensors(equipment, zones)
    systems = create_systems(buildings)
    
    all_entities = buildings + floors + meters + equipment + zones + sensors + systems
    
    relationships = create_relationships(
        buildings, floors, meters, equipment, zones, sensors, systems
    )
    
    return all_entities, relationships


if __name__ == "__main__":
    # Print summary of seed data
    entities, relationships = get_all_seed_data()
    
    print("=" * 60)
    print("SEED DATA SUMMARY")
    print("=" * 60)
    
    # Count by type
    type_counts = {}
    for entity in entities:
        class_name = entity.brick_class.value
        type_counts[class_name] = type_counts.get(class_name, 0) + 1
    
    print("\nEntities by type:")
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name}: {count}")
    
    print(f"\nTotal entities: {len(entities)}")
    print(f"Total relationships: {len(relationships)}")
    
    # Relationship counts
    rel_counts = {}
    for rel in relationships:
        rel_type = rel.relation_type.value
        rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1
    
    print("\nRelationships by type:")
    for rel_type, count in sorted(rel_counts.items()):
        print(f"  {rel_type}: {count}")
