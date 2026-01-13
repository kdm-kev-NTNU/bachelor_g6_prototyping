package main

import (
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
)

func healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":           "running",
		"version":          "1.0.0",
		"vector_db_ready":  false, // TODO: check ChromaDB status
		"advisor_available": true,
		"judge_available":   true,
	})
}

func listBuildings(c *gin.Context) {
	buildings := generateBuildings(10)
	c.JSON(http.StatusOK, buildings)
}

func getBuilding(c *gin.Context) {
	id := c.Param("id")
	buildings := generateBuildings(10)
	
	for _, b := range buildings {
		if b.ID == id {
			c.JSON(http.StatusOK, b)
			return
		}
	}
	
	c.JSON(http.StatusNotFound, gin.H{"error": "Bygning ikke funnet"})
}

func generateAdvice(c *gin.Context) {
	var req AdviceRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	buildings := generateBuildings(10)
	var building *Building
	for _, b := range buildings {
		if b.ID == req.BuildingID {
			building = &b
			break
		}
	}

	if building == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Bygning ikke funnet"})
		return
	}

	// Initialize advisor
	advisor, err := NewAdvisor()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to create advisor: %v", err)})
		return
	}

	// Retrieve relevant documents
	query := req.Query
	if query == "" {
		query = fmt.Sprintf("energieffektivisering %s år gammel bygning %s", building.ConstructionType, building.BuildingType)
	}

	retrievedDocs, err := retrieveDocuments(query, TopKFinal)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to retrieve documents: %v", err)})
		return
	}

	// Generate advice
	advice, citations, err := advisor.GenerateAdvice(building, req.Query, retrievedDocs)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to generate advice: %v", err)})
		return
	}

	c.JSON(http.StatusOK, AdviceResponse{
		Advice:       advice,
		Citations:    citations,
		RetrievedDocs: retrievedDocs,
		Metadata: map[string]interface{}{
			"model":       AdvisorModel,
			"num_sources": len(retrievedDocs),
		},
		Building: *building,
	})
}

func evaluateAdvice(c *gin.Context) {
	var req JudgeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Initialize judge
	judge, err := NewJudge()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to create judge: %v", err)})
		return
	}

	// Evaluate advice
	evaluation, err := judge.Evaluate(req.Advice, req.BuildingData)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to evaluate: %v", err)})
		return
	}

	c.JSON(http.StatusOK, evaluation)
}

func fullEvaluation(c *gin.Context) {
	var req EvaluateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	buildings := generateBuildings(10)
	var building *Building
	for _, b := range buildings {
		if b.ID == req.BuildingID {
			building = &b
			break
		}
	}

	if building == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Bygning ikke funnet"})
		return
	}

	// Initialize advisor
	advisor, err := NewAdvisor()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to create advisor: %v", err)})
		return
	}

	// Retrieve documents
	query := req.Query
	if query == "" {
		query = fmt.Sprintf("energieffektivisering %s år gammel bygning %s", building.ConstructionType, building.BuildingType)
	}

	retrievedDocs, err := retrieveDocuments(query, TopKFinal)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to retrieve documents: %v", err)})
		return
	}

	// Generate advice
	advice, citations, err := advisor.GenerateAdvice(building, req.Query, retrievedDocs)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to generate advice: %v", err)})
		return
	}

	// Initialize judge
	judge, err := NewJudge()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to create judge: %v", err)})
		return
	}

	// Evaluate advice
	evaluation, err := judge.Evaluate(advice, building)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to evaluate: %v", err)})
		return
	}

	c.JSON(http.StatusOK, EvaluateResponse{
		Building:   *building,
		Advice:     advice,
		Citations:  citations,
		Evaluation: *evaluation,
		Metadata: map[string]interface{}{
			"model":       AdvisorModel,
			"num_sources": len(retrievedDocs),
		},
	})
}

func initializeDatabase(c *gin.Context) {
	pdfDir := "../pdf"
	
	// Process PDFs
	chunks, err := processPDFDirectory(pdfDir)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to process PDFs: %v", err)})
		return
	}

	if len(chunks) == 0 {
		c.JSON(http.StatusOK, gin.H{
			"status":           "success",
			"documents_stored": 0,
			"message":          "Ingen chunks å lagre",
		})
		return
	}

	// Store in vector database
	if err := storeChunksInVectorDB(chunks); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to store in vector DB: %v", err)})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":           "success",
		"documents_stored": len(chunks),
		"message":          fmt.Sprintf("Lagret %d chunks i vector database", len(chunks)),
	})
}
