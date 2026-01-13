package main

import (
	"context"
	"fmt"
	"strings"

	"github.com/cloudwego/eino-ext/components/model/openai"
	"github.com/cloudwego/eino/schema"
)

type Advisor struct {
	chatModel *openai.ChatModel
}

func NewAdvisor() (*Advisor, error) {
	ctx := context.Background()

	chatModel, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
		APIKey: getOpenAIKey(),
		Model:  AdvisorModel,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create chat model: %w", err)
	}

	return &Advisor{
		chatModel: chatModel,
	}, nil
}

func (a *Advisor) GenerateAdvice(building *Building, query string, retrievedDocs []RetrievedDoc) (string, []Citation, error) {
	ctx := context.Background()

	// Build query if not provided
	if query == "" {
		query = fmt.Sprintf(
			"Gi råd om energieffektivisering for en %d år gammel bygning på %.1f m² av type %s som bruker %.0f kWh/år, mens forventet bruk er %.0f kWh/år.",
			building.Age,
			building.SizeM2,
			building.ConstructionType,
			building.CurrentEnergyKwh,
			building.ExpectedEnergyKwh,
		)
	}

	// Format context from retrieved documents
	contextParts := []string{}
	for _, doc := range retrievedDocs {
		contextParts = append(contextParts, fmt.Sprintf("%s\n%s", doc.Citation, doc.Source))
	}
	context := strings.Join(contextParts, "\n\n---\n\n")

	// Format building data
	buildingText := formatBuildingForPrompt(building)

	// Build user prompt
	userPrompt := fmt.Sprintf(`%s

Relevante dokumenter:
%s

Basert på bygningsdataene og dokumentasjonen over, gi konkrete råd om energieffektivisering.
Husk å:
- Referere eksplisitt til bygningsdataene
- Sitere kildene du bruker
- Bruke rådgivende tone (foreslå, ikke instruer)
- Skille mellom fakta og antagelser
- Anerkjenne usikkerheter og begrensninger`, buildingText, context)

	// Create messages
	messages := []*schema.Message{
		{
			Role:    schema.System,
			Content: AdvisorSystemPrompt,
		},
		{
			Role:    schema.User,
			Content: userPrompt,
		},
	}

	// Generate advice
	result, err := a.chatModel.Generate(ctx, messages)
	if err != nil {
		return "", nil, fmt.Errorf("failed to generate advice: %w", err)
	}

	// Extract citations
	citations := extractCitations(result.Content, retrievedDocs)

	return result.Content, citations, nil
}

func formatBuildingForPrompt(building *Building) string {
	excessPercent := ((building.CurrentEnergyKwh - building.ExpectedEnergyKwh) / building.ExpectedEnergyKwh) * 100

	return fmt.Sprintf(`Bygningsdata:
- Navn: %s
- Alder: %d år
- Størrelse: %.1f m²
- Konstruksjonstype: %s
- Bygningstype: %s
- Nåværende energibruk: %.0f kWh/år
- Forventet energibruk: %.0f kWh/år
- Overskridelse: %.1f%%

Detaljer:
- Isolasjon: %s
- Vinduer: %s
- Oppvarmingssystem: %s
- Ventilasjon: %s
- Taktype: %s
- Orientering: %s`,
		building.Name,
		building.Age,
		building.SizeM2,
		building.ConstructionType,
		building.BuildingType,
		building.CurrentEnergyKwh,
		building.ExpectedEnergyKwh,
		excessPercent,
		building.Details["insulation"],
		building.Details["windows"],
		building.Details["heating_system"],
		building.Details["ventilation"],
		building.Details["roof_type"],
		building.Details["orientation"],
	)
}

func extractCitations(adviceText string, retrievedDocs []RetrievedDoc) []Citation {
	citations := []Citation{}

	for _, doc := range retrievedDocs {
		if strings.Contains(adviceText, doc.Citation) {
			citations = append(citations, Citation{
				Citation: doc.Citation,
				Source:   doc.Source,
				Page:     doc.Page,
			})
		}
	}

	return citations
}
