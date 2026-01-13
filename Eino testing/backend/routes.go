package main

import (
	"github.com/gin-gonic/gin"
)

func setupRoutes(r *gin.Engine) {
	api := r.Group("/api/v1")

	// Health check
	api.GET("/health", healthCheck)

	// Buildings
	api.GET("/buildings", listBuildings)
	api.GET("/buildings/:id", getBuilding)

	// Advice generation
	api.POST("/advice", generateAdvice)

	// Judge evaluation
	api.POST("/judge", evaluateAdvice)

	// Full pipeline
	api.POST("/evaluate", fullEvaluation)

	// Vector DB management
	api.POST("/initialize-db", initializeDatabase)

	// Serve static files (UI)
	r.Static("/ui", "../ui")
	r.GET("/", func(c *gin.Context) {
		c.File("../ui/index.html")
	})
}
