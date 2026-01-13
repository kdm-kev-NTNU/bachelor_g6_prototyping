package main

// Building represents a fictional building with energy data
type Building struct {
	ID                string            `json:"id"`
	Name              string            `json:"name"`
	Age               int               `json:"age"`
	SizeM2            float64           `json:"size_m2"`
	ConstructionType  string            `json:"construction_type"`
	BuildingType      string            `json:"building_type"`
	CurrentEnergyKwh  float64           `json:"current_energy_kwh"`
	ExpectedEnergyKwh float64           `json:"expected_energy_kwh"`
	Details           map[string]string `json:"details"`
}

// AdviceRequest for generating advice
type AdviceRequest struct {
	BuildingID string `json:"building_id" binding:"required"`
	Query      string `json:"query,omitempty"`
}

// AdviceResponse contains generated advice
type AdviceResponse struct {
	Advice        string                 `json:"advice"`
	Citations     []Citation             `json:"citations"`
	RetrievedDocs []RetrievedDoc         `json:"retrieved_docs"`
	Metadata      map[string]interface{} `json:"metadata"`
	Building      Building               `json:"building"`
}

// Citation in advice text
type Citation struct {
	Citation string `json:"citation"`
	Source   string `json:"source"`
	Page     string `json:"page"`
}

// RetrievedDoc from vector database
type RetrievedDoc struct {
	Source   string `json:"source"`
	Page     string `json:"page"`
	Citation string `json:"citation"`
}

// JudgeRequest for evaluating advice
type JudgeRequest struct {
	Advice       string    `json:"advice" binding:"required"`
	BuildingData *Building `json:"building_data,omitempty"`
}

// JudgeResponse contains evaluation scores
type JudgeResponse struct {
	DataReferencing            int    `json:"data_referencing"`
	InternalConsistency        int    `json:"internal_consistency"`
	FactVsAssumption           int    `json:"fact_vs_assumption"`
	UncertaintyAcknowledgement int    `json:"uncertainty_acknowledgement"`
	AdvisoryTone               int    `json:"advisory_tone"`
	TotalScore                 int    `json:"total_score"`
	Comment                    string `json:"comment"`
}

// EvaluateRequest for full pipeline
type EvaluateRequest struct {
	BuildingID string `json:"building_id" binding:"required"`
	Query      string `json:"query,omitempty"`
}

// EvaluateResponse contains advice and evaluation
type EvaluateResponse struct {
	Building   Building               `json:"building"`
	Advice     string                 `json:"advice"`
	Citations  []Citation             `json:"citations"`
	Evaluation JudgeResponse          `json:"evaluation"`
	Metadata   map[string]interface{} `json:"metadata"`
}
