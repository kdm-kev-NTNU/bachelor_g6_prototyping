"""
Generate fictional building data for testing.
"""

from typing import List, Dict, Any
import random
from dataclasses import dataclass


@dataclass
class Building:
    """Represents a fictional building with energy data."""
    id: str
    name: str
    age: int  # years
    size_m2: float  # square meters
    construction_type: str  # "wood", "concrete", "brick", "mixed"
    building_type: str  # "residential", "commercial", "public"
    current_energy_kwh: float  # kWh per year
    expected_energy_kwh: float  # Expected kWh per year based on building details
    details: Dict[str, Any]  # Additional building details


def calculate_expected_energy(age: int, size_m2: float, construction_type: str, 
                              building_type: str) -> float:
    """
    Calculate expected energy usage based on building characteristics.
    Returns kWh per year.
    """
    # Base energy per m2 per year (kWh/m2/year)
    base_energy = {
        "residential": 150,
        "commercial": 200,
        "public": 180
    }
    
    # Age factor (older buildings use more energy)
    age_factor = 1.0 + (age / 100) * 0.5  # Up to 50% more for very old buildings
    
    # Construction type factor
    construction_factor = {
        "wood": 0.9,
        "concrete": 1.1,
        "brick": 1.0,
        "mixed": 1.05
    }
    
    base = base_energy.get(building_type, 150)
    factor = age_factor * construction_factor.get(construction_type, 1.0)
    
    return size_m2 * base * factor


def generate_buildings(count: int = 10) -> List[Building]:
    """Generate fictional building data."""
    buildings = []
    
    building_names = [
        "Gamlehuset i sentrum",
        "Moderne leilighetskompleks",
        "Skolebygget fra 1970",
        "Kontorbygg i glass",
        "Villa fra 1950",
        "Barnehage i tre",
        "Sykehjem i betong",
        "Butikkbygg fra 1980",
        "Kulturhus i mur",
        "Boligblokk fra 1960"
    ]
    
    construction_types = ["wood", "concrete", "brick", "mixed"]
    building_types = ["residential", "commercial", "public"]
    
    for i in range(count):
        name = building_names[i % len(building_names)]
        age = random.randint(10, 80)
        size = random.uniform(200, 2000)
        construction = random.choice(construction_types)
        btype = random.choice(building_types)
        
        expected = calculate_expected_energy(age, size, construction, btype)
        
        # Make some buildings use "too much" energy (20-50% more than expected)
        if random.random() < 0.6:  # 60% use too much energy
            current = expected * random.uniform(1.2, 1.5)
        else:
            current = expected * random.uniform(0.8, 1.1)
        
        building = Building(
            id=f"building_{i+1}",
            name=name,
            age=age,
            size_m2=round(size, 1),
            construction_type=construction,
            building_type=btype,
            current_energy_kwh=round(current, 0),
            expected_energy_kwh=round(expected, 0),
            details={
                "insulation": random.choice(["poor", "moderate", "good"]),
                "windows": random.choice(["single", "double", "triple"]),
                "heating_system": random.choice(["electric", "district", "oil", "heat_pump"]),
                "ventilation": random.choice(["natural", "mechanical", "balanced"]),
                "roof_type": random.choice(["flat", "pitched", "green"]),
                "orientation": random.choice(["north", "south", "east", "west", "mixed"])
            }
        )
        buildings.append(building)
    
    return buildings


def get_building_dict(building: Building) -> Dict[str, Any]:
    """Convert Building to dictionary."""
    return {
        "id": building.id,
        "name": building.name,
        "age": building.age,
        "size_m2": building.size_m2,
        "construction_type": building.construction_type,
        "building_type": building.building_type,
        "current_energy_kwh": building.current_energy_kwh,
        "expected_energy_kwh": building.expected_energy_kwh,
        "energy_excess_percent": round(
            ((building.current_energy_kwh - building.expected_energy_kwh) / building.expected_energy_kwh) * 100,
            1
        ),
        "details": building.details
    }


def format_building_for_prompt(building: Building) -> str:
    """Format building data for LLM prompt."""
    return f"""Bygningsdata:
- Navn: {building.name}
- Alder: {building.age} år
- Størrelse: {building.size_m2} m²
- Konstruksjonstype: {building.construction_type}
- Bygningstype: {building.building_type}
- Nåværende energibruk: {building.current_energy_kwh:.0f} kWh/år
- Forventet energibruk: {building.expected_energy_kwh:.0f} kWh/år
- Overskridelse: {((building.current_energy_kwh - building.expected_energy_kwh) / building.expected_energy_kwh * 100):.1f}%

Detaljer:
- Isolasjon: {building.details['insulation']}
- Vinduer: {building.details['windows']}
- Oppvarmingssystem: {building.details['heating_system']}
- Ventilasjon: {building.details['ventilation']}
- Taktype: {building.details['roof_type']}
- Orientering: {building.details['orientation']}"""


if __name__ == "__main__":
    # Test generation
    buildings = generate_buildings(5)
    for b in buildings:
        print(f"\n{b.name}:")
        print(f"  Nåværende: {b.current_energy_kwh:.0f} kWh/år")
        print(f"  Forventet: {b.expected_energy_kwh:.0f} kWh/år")
        print(f"  Overskridelse: {((b.current_energy_kwh - b.expected_energy_kwh) / b.expected_energy_kwh * 100):.1f}%")
