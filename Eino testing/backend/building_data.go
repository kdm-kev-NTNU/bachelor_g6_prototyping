package main

import (
	"fmt"
	"math/rand"
	"time"
)

func init() {
	rand.Seed(time.Now().UnixNano())
}

func calculateExpectedEnergy(age int, sizeM2 float64, constructionType, buildingType string) float64 {
	baseEnergy := map[string]float64{
		"residential": 150,
		"commercial":  200,
		"public":      180,
	}

	ageFactor := 1.0 + (float64(age)/100.0)*0.5

	constructionFactor := map[string]float64{
		"wood":     0.9,
		"concrete": 1.1,
		"brick":    1.0,
		"mixed":    1.05,
	}

	base := baseEnergy[buildingType]
	if base == 0 {
		base = 150
	}

	factor := ageFactor * constructionFactor[constructionType]
	if factor == 0 {
		factor = 1.0
	}

	return sizeM2 * base * factor
}

func generateBuildings(count int) []Building {
	buildings := []Building{}

	buildingNames := []string{
		"Gamlehuset i sentrum",
		"Moderne leilighetskompleks",
		"Skolebygget fra 1970",
		"Kontorbygg i glass",
		"Villa fra 1950",
		"Barnehage i tre",
		"Sykehjem i betong",
		"Butikkbygg fra 1980",
		"Kulturhus i mur",
		"Boligblokk fra 1960",
	}

	constructionTypes := []string{"wood", "concrete", "brick", "mixed"}
	buildingTypes := []string{"residential", "commercial", "public"}

	for i := 0; i < count; i++ {
		name := buildingNames[i%len(buildingNames)]
		age := rand.Intn(70) + 10
		size := rand.Float64()*1800 + 200
		construction := constructionTypes[rand.Intn(len(constructionTypes))]
		btype := buildingTypes[rand.Intn(len(buildingTypes))]

		expected := calculateExpectedEnergy(age, size, construction, btype)

		var current float64
		if rand.Float64() < 0.6 {
			current = expected * (rand.Float64()*0.3 + 1.2)
		} else {
			current = expected * (rand.Float64()*0.3 + 0.8)
		}

		building := Building{
			ID:                fmt.Sprintf("building_%d", i+1),
			Name:              name,
			Age:               age,
			SizeM2:            size,
			ConstructionType:  construction,
			BuildingType:      btype,
			CurrentEnergyKwh:  current,
			ExpectedEnergyKwh: expected,
			Details: map[string]string{
				"insulation":      []string{"poor", "moderate", "good"}[rand.Intn(3)],
				"windows":         []string{"single", "double", "triple"}[rand.Intn(3)],
				"heating_system":  []string{"electric", "district", "oil", "heat_pump"}[rand.Intn(4)],
				"ventilation":     []string{"natural", "mechanical", "balanced"}[rand.Intn(3)],
				"roof_type":       []string{"flat", "pitched", "green"}[rand.Intn(3)],
				"orientation":     []string{"north", "south", "east", "west", "mixed"}[rand.Intn(5)],
			},
		}
		buildings = append(buildings, building)
	}

	return buildings
}
