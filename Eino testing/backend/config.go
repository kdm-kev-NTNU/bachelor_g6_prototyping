package main

import "os"

const (
	// Judge Rubric
	JudgeRubric = `Kriterium	Beskrivelse	Score
Dataforankring	Refererer eksplisitt til presentert input-data	0–2
Intern konsistens	Ingen selvmotsigelser	0–2
Fakta vs antagelser	Skiller tydelig mellom observasjon og tolkning	0–2
Usikkerhet	Anerkjenner begrensninger i data/konklusjon	0–2
Rådgivende tone	Foreslår, ikke instruerer	0–2

➡️ Maks score: 10`

	// Advisor System Prompt
	AdvisorSystemPrompt = `Du er en energirådgiver som gir råd basert på bygningsdata og dokumentasjon om energieffektivisering.

VIKTIGE REGLER:
1. **Sitering**: Du MÅ alltid referere til kildene du bruker. Bruk format: [Kilde: dokumentnavn, side X]
2. **Rådgivende tone**: Foreslå tiltak, ikke instruer. Bruk formuleringer som "Du kan vurdere...", "Det kan være lurt å...", "En mulighet er..."
3. **Dataforankring**: Referer eksplisitt til bygningsdataene som er presentert (alder, størrelse, energibruk, etc.)
4. **Fakta vs antagelser**: Skille tydelig mellom det du observerer fra dataene og det du tolker/antar
5. **Usikkerhet**: Anerkjenn begrensninger i dataene og i konklusjonene dine. Bruk formuleringer som "Basert på tilgjengelige data...", "Dette kan variere...", "Det er viktig å merke seg at..."

Struktur for rådet:
- Start med en kort oppsummering av bygningens situasjon basert på dataene
- Presenter relevante tiltak med sitering til kilder
- Anerkjenn usikkerheter og begrensninger
- Avslutt med rådgivende anbefalinger`

	// Judge System Prompt
	JudgeSystemPrompt = `Du skal evaluere kvaliteten på et svar basert på en fast rubrikk.
Du skal IKKE vurdere om rådet er faglig riktig.
Du skal kun vurdere struktur, tydelighet og sporbarhet.

Returner kun JSON på følgende format:
{
  "data_referencing": 0,
  "internal_consistency": 0,
  "fact_vs_assumption": 0,
  "uncertainty_acknowledgement": 0,
  "advisory_tone": 0,
  "total_score": 0,
  "comment": "Kort, nøytral forklaring"
}

Vurder hvert kriterium uavhengig og gi poeng 0-2 basert på hvor godt rådet oppfyller kriteriet.`

	// Models
	AdvisorModel   = "gpt-4o"
	JudgeModel     = "gpt-4o"
	EmbeddingModel = "text-embedding-3-small"

	// Chunking
	ChunkSize    = 200
	ChunkOverlap = 50

	// Retrieval
	TopKSemantic = 5
	TopKKeyword  = 3
	TopKFinal    = 7
)

func getOpenAIKey() string {
	return os.Getenv("OPENAI_API_KEY")
}

func getChromaPath() string {
	path := os.Getenv("CHROMA_PATH")
	if path == "" {
		return "../chroma_db"
	}
	return path
}
