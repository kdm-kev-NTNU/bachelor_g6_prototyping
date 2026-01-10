"""
Brick Ontology Seed Data for FalkorDB

Creates a connected knowledge graph with brick_Building as root.
All nodes have a valid semantic path to the Building.

Traversal: Building → System → Equipment → Point → Timeseries
"""

from typing import List, Tuple, Dict, Any


def generate_cypher_statements() -> List[str]:
    """
    Generate Cypher statements for seeding the graph.
    Returns list of Cypher CREATE/MATCH statements.
    """
    statements = []
    
    # ========================================================================
    # ROOT: Building
    # ========================================================================
    statements.append("""
    CREATE (b:brick_Building {
        id: 'building_opera',
        name: 'Operahuset',
        description: 'Oslo Opera House',
        address: 'Kirsten Flagstads Plass 1, Oslo',
        area_sqm: 38500,
        year_built: 2008,
        energy_class: 'B'
    })
    """)
    
    # ========================================================================
    # FLOORS: Building -[hasPart]-> Floor
    # ========================================================================
    for level in range(1, 4):
        statements.append(f"""
        MATCH (b:brick_Building {{id: 'building_opera'}})
        CREATE (f:brick_Floor {{
            id: 'floor_opera_{level}',
            name: 'Etasje {level}',
            level: {level}
        }})
        CREATE (b)-[:brick_hasPart]->(f)
        """)
    
    # ========================================================================
    # HVAC ZONES: Floor -[hasPart]-> HVAC_Zone
    # ========================================================================
    zones = [
        ('zone_foyer', 'Foyer', 1),
        ('zone_hall', 'Hovedsal', 2),
        ('zone_backstage', 'Backstage', 3),
    ]
    
    for zone_id, zone_name, floor_level in zones:
        statements.append(f"""
        MATCH (f:brick_Floor {{id: 'floor_opera_{floor_level}'}})
        CREATE (z:brick_HVAC_Zone {{
            id: '{zone_id}',
            name: '{zone_name}'
        }})
        CREATE (f)-[:brick_hasPart]->(z)
        """)
    
    # ========================================================================
    # SYSTEMS: Building -[hasPart]-> System
    # ========================================================================
    systems = [
        ('system_hvac', 'brick_HVAC_System', 'HVAC System'),
        ('system_electrical', 'brick_Electrical_System', 'Elektrisk System'),
        ('system_lighting', 'brick_Lighting_System', 'Belysningssystem'),
    ]
    
    for sys_id, sys_label, sys_name in systems:
        statements.append(f"""
        MATCH (b:brick_Building {{id: 'building_opera'}})
        CREATE (s:{sys_label} {{
            id: '{sys_id}',
            name: '{sys_name}'
        }})
        CREATE (b)-[:brick_hasPart]->(s)
        """)
    
    # ========================================================================
    # EQUIPMENT: System -[hasMember]-> Equipment
    # ========================================================================
    
    # AHU in HVAC System
    statements.append("""
    MATCH (s:brick_HVAC_System {id: 'system_hvac'})
    CREATE (ahu:brick_Air_Handling_Unit {
        id: 'ahu_main',
        name: 'Hovedaggregat AHU-01',
        manufacturer: 'Swegon',
        model: 'Gold RX',
        capacity: 50000,
        capacity_unit: 'm3/h'
    })
    CREATE (s)-[:brick_hasMember]->(ahu)
    """)
    
    # Chiller in HVAC System
    statements.append("""
    MATCH (s:brick_HVAC_System {id: 'system_hvac'})
    CREATE (ch:brick_Chiller {
        id: 'chiller_main',
        name: 'Kjølemaskin CH-01',
        manufacturer: 'Carrier',
        model: 'AquaEdge 23XRV',
        capacity: 2000,
        capacity_unit: 'kW'
    })
    CREATE (s)-[:brick_hasMember]->(ch)
    """)
    
    # Pump in HVAC System
    statements.append("""
    MATCH (s:brick_HVAC_System {id: 'system_hvac'})
    CREATE (p:brick_Pump {
        id: 'pump_chw',
        name: 'Kjølevannspumpe P-01',
        manufacturer: 'Grundfos',
        capacity: 75,
        capacity_unit: 'kW'
    })
    CREATE (s)-[:brick_hasMember]->(p)
    """)
    
    # ========================================================================
    # EQUIPMENT FEEDS ZONES: AHU -[feeds]-> Zone
    # ========================================================================
    for zone_id in ['zone_foyer', 'zone_hall', 'zone_backstage']:
        statements.append(f"""
        MATCH (ahu:brick_Air_Handling_Unit {{id: 'ahu_main'}})
        MATCH (z:brick_HVAC_Zone {{id: '{zone_id}'}})
        CREATE (ahu)-[:brick_feeds]->(z)
        """)
    
    # ========================================================================
    # METERS: Building -[isMeteredBy]-> Meter
    # ========================================================================
    meters = [
        ('meter_elec_main', 'brick_Electrical_Meter', 'Hovedmåler Elektrisitet', 'kWh'),
        ('meter_thermal', 'brick_Thermal_Energy_Meter', 'Varmemåler', 'kWh'),
        ('meter_water', 'brick_Water_Meter', 'Vannmåler', 'm3'),
    ]
    
    for meter_id, meter_label, meter_name, unit in meters:
        statements.append(f"""
        MATCH (b:brick_Building {{id: 'building_opera'}})
        CREATE (m:{meter_label} {{
            id: '{meter_id}',
            name: '{meter_name}',
            unit: '{unit}'
        }})
        CREATE (b)-[:brick_isMeteredBy]->(m)
        """)
    
    # ========================================================================
    # POINTS (SENSORS): Equipment/Zone -[hasPoint]-> Sensor
    # ========================================================================
    
    # AHU sensors
    ahu_sensors = [
        ('sensor_ahu_supply_temp', 'brick_Temperature_Sensor', 'Tilluftstemp AHU-01', 'degC'),
        ('sensor_ahu_return_temp', 'brick_Temperature_Sensor', 'Avtrekkstemp AHU-01', 'degC'),
        ('sensor_ahu_power', 'brick_Power_Sensor', 'Effekt AHU-01', 'kW'),
    ]
    
    for sensor_id, sensor_label, sensor_name, unit in ahu_sensors:
        statements.append(f"""
        MATCH (ahu:brick_Air_Handling_Unit {{id: 'ahu_main'}})
        CREATE (s:{sensor_label} {{
            id: '{sensor_id}',
            name: '{sensor_name}',
            unit: '{unit}'
        }})
        CREATE (ahu)-[:brick_hasPoint]->(s)
        """)
    
    # Chiller sensors
    chiller_sensors = [
        ('sensor_chiller_power', 'brick_Power_Sensor', 'Effekt Kjølemaskin', 'kW'),
        ('sensor_chiller_supply_temp', 'brick_Temperature_Sensor', 'Turtemp Kjølevann', 'degC'),
        ('sensor_chiller_return_temp', 'brick_Temperature_Sensor', 'Returtemp Kjølevann', 'degC'),
    ]
    
    for sensor_id, sensor_label, sensor_name, unit in chiller_sensors:
        statements.append(f"""
        MATCH (ch:brick_Chiller {{id: 'chiller_main'}})
        CREATE (s:{sensor_label} {{
            id: '{sensor_id}',
            name: '{sensor_name}',
            unit: '{unit}'
        }})
        CREATE (ch)-[:brick_hasPoint]->(s)
        """)
    
    # Meter sensors
    statements.append("""
    MATCH (m:brick_Electrical_Meter {id: 'meter_elec_main'})
    CREATE (s:brick_Energy_Sensor {
        id: 'sensor_energy_main',
        name: 'Akkumulert Energi',
        unit: 'kWh'
    })
    CREATE (m)-[:brick_hasPoint]->(s)
    """)
    
    statements.append("""
    MATCH (m:brick_Electrical_Meter {id: 'meter_elec_main'})
    CREATE (s:brick_Power_Sensor {
        id: 'sensor_power_main',
        name: 'Momentan Effekt',
        unit: 'kW'
    })
    CREATE (m)-[:brick_hasPoint]->(s)
    """)
    
    # Zone sensors
    zone_sensors = [
        ('zone_foyer', 'sensor_temp_foyer', 'Temperatur Foyer'),
        ('zone_hall', 'sensor_temp_hall', 'Temperatur Hovedsal'),
        ('zone_backstage', 'sensor_temp_backstage', 'Temperatur Backstage'),
    ]
    
    for zone_id, sensor_id, sensor_name in zone_sensors:
        statements.append(f"""
        MATCH (z:brick_HVAC_Zone {{id: '{zone_id}'}})
        CREATE (s:brick_Temperature_Sensor {{
            id: '{sensor_id}',
            name: '{sensor_name}',
            unit: 'degC'
        }})
        CREATE (z)-[:brick_hasPoint]->(s)
        """)
    
    # CO2 sensors in zones
    for zone_id in ['zone_foyer', 'zone_hall']:
        statements.append(f"""
        MATCH (z:brick_HVAC_Zone {{id: '{zone_id}'}})
        CREATE (s:brick_CO2_Sensor {{
            id: 'sensor_co2_{zone_id}',
            name: 'CO2 {zone_id.replace('zone_', '').title()}',
            unit: 'ppm'
        }})
        CREATE (z)-[:brick_hasPoint]->(s)
        """)
    
    # ========================================================================
    # TIMESERIES: Sensor -[hasTimeseries]-> Timeseries
    # ========================================================================
    
    # Connect key sensors to timeseries
    timeseries_sensors = [
        'sensor_ahu_supply_temp',
        'sensor_ahu_power',
        'sensor_chiller_power',
        'sensor_energy_main',
        'sensor_power_main',
        'sensor_temp_foyer',
        'sensor_temp_hall',
    ]
    
    for sensor_id in timeseries_sensors:
        ts_id = sensor_id.replace('sensor_', 'ts_')
        statements.append(f"""
        MATCH (s {{id: '{sensor_id}'}})
        CREATE (ts:brick_Timeseries {{
            id: '{ts_id}',
            external_id: 'piscada.{ts_id}',
            resolution: 'PT15M'
        }})
        CREATE (s)-[:brick_hasTimeseries]->(ts)
        """)
    
    return statements


def get_seed_summary() -> Dict[str, Any]:
    """Get summary of seed data for verification."""
    return {
        "root": "brick_Building (Operahuset)",
        "floors": 3,
        "zones": 3,
        "systems": 3,
        "equipment": 3,
        "meters": 3,
        "sensors": 14,
        "timeseries": 7,
        "traversal_paths": [
            "Building → Floor → Zone → Sensor → Timeseries",
            "Building → System → Equipment → Sensor → Timeseries",
            "Building → Meter → Sensor → Timeseries",
        ]
    }


if __name__ == "__main__":
    # Print summary
    summary = get_seed_summary()
    print("SEED DATA SUMMARY")
    print("=" * 40)
    print(f"Root: {summary['root']}")
    print(f"Floors: {summary['floors']}")
    print(f"Zones: {summary['zones']}")
    print(f"Systems: {summary['systems']}")
    print(f"Equipment: {summary['equipment']}")
    print(f"Meters: {summary['meters']}")
    print(f"Sensors: {summary['sensors']}")
    print(f"Timeseries: {summary['timeseries']}")
    print("\nTraversal paths:")
    for path in summary['traversal_paths']:
        print(f"  {path}")
