package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/cloudwego/eino-ext/components/model/openai"
	"github.com/cloudwego/eino/schema"
)

type Judge struct {
	chatModel *openai.ChatModel
}

func NewJudge() (*Judge, error) {
	ctx := context.Background()

	chatModel, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
		APIKey: getOpenAIKey(),
		Model:  JudgeModel,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create chat model: %w", err)
	}

	return &Judge{
		chatModel: chatModel,
	}, nil
}

func (j *Judge) Evaluate(adviceText string, building *Building) (*JudgeResponse, error) {
	ctx := context.Background()

	// Build evaluation prompt
	evaluationPrompt := buildEvaluationPrompt(adviceText, building)

	// Create messages
	messages := []*schema.Message{
		{
			Role:    schema.System,
			Content: JudgeSystemPrompt,
		},
		{
			Role:    schema.User,
			Content: evaluationPrompt,
		},
	}

	// Generate evaluation
	result, err := j.chatModel.Generate(ctx, messages)
	if err != nil {
		return nil, fmt.Errorf("failed to generate evaluation: %w", err)
	}

	// Parse JSON response
	var evaluation JudgeResponse
	if err := json.Unmarshal([]byte(result.Content), &evaluation); err != nil {
		return nil, fmt.Errorf("failed to parse evaluation JSON: %w", err)
	}

	// Ensure total_score matches sum
	calculatedTotal := evaluation.DataReferencing +
		evaluation.InternalConsistency +
		evaluation.FactVsAssumption +
		evaluation.UncertaintyAcknowledgement +
		evaluation.AdvisoryTone

	if evaluation.TotalScore != calculatedTotal {
		evaluation.TotalScore = calculatedTotal
	}

	return &evaluation, nil
}

func buildEvaluationPrompt(adviceText string, building *Building) string {
	prompt := fmt.Sprintf(`Evaluér følgende råd basert på den faste rubrikken:

RUBRIKK:
%s

RÅDET SOM SKAL EVALUERES:
%s`, JudgeRubric, adviceText)

	if building != nil {
		prompt += fmt.Sprintf(`

KONTEKST (bygningsdata som rådet skulle referere til):
- Alder: %d år
- Størrelse: %.1f m²
- Konstruksjonstype: %s
- Nåværende energibruk: %.0f kWh/år
- Forventet energibruk: %.0f kWh/år`,
			building.Age,
			building.SizeM2,
			building.ConstructionType,
			building.CurrentEnergyKwh,
			building.ExpectedEnergyKwh,
		)
	}

	prompt += `

HUSK: Du evaluerer KUN struktur, tydelighet og sporbarhet. IKKE om rådet er faglig korrekt.
Returner JSON med poeng for hvert kriterium (0-2) og total score (0-10).`

	return prompt
}
