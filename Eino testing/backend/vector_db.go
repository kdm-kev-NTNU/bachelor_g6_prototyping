package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os/exec"
	"path/filepath"
)

var collectionName = "energy_advice_docs"

// ChromaDB embedded client via Python
type chromaClient struct {
	dbPath string
}

func newChromaClient() *chromaClient {
	dbPath := getChromaPath()
	// Convert to absolute path
	absPath, err := filepath.Abs(dbPath)
	if err != nil {
		log.Printf("Warning: Could not get absolute path for ChromaDB: %v", err)
		absPath = dbPath
	}
	return &chromaClient{
		dbPath: absPath,
	}
}

func (c *chromaClient) init(ctx context.Context) error {
	scriptPath := filepath.Join(".", "vector_db.py")
	if _, err := filepath.Abs(scriptPath); err != nil {
		// Try relative to backend directory
		scriptPath = "vector_db.py"
	}

	cmd := exec.CommandContext(ctx, "python", scriptPath, "init", c.dbPath, collectionName)
	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return fmt.Errorf("failed to initialize ChromaDB: %s (exit code: %d)", string(exitErr.Stderr), exitErr.ExitCode())
		}
		return fmt.Errorf("failed to initialize ChromaDB: %w", err)
	}

	var result struct {
		Status     string `json:"status"`
		Created    bool   `json:"created"`
		Collection string `json:"collection"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return fmt.Errorf("failed to parse init response: %w", err)
	}

	if result.Created {
		log.Printf("Created collection: %s", collectionName)
	} else {
		log.Printf("Using existing collection: %s", collectionName)
	}

	return nil
}

func (c *chromaClient) add(ctx context.Context, ids []string, embeddings [][]float32, metadatas []map[string]interface{}, documents []string) error {
	scriptPath := "vector_db.py"

	// Convert float32 to float64 for JSON
	embeddingsFloat64 := make([][]float64, len(embeddings))
	for i, emb := range embeddings {
		embeddingsFloat64[i] = make([]float64, len(emb))
		for j, val := range emb {
			embeddingsFloat64[i][j] = float64(val)
		}
	}

	payload := map[string]interface{}{
		"ids":        ids,
		"embeddings": embeddingsFloat64,
		"metadatas":  metadatas,
		"documents":  documents,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	cmd := exec.CommandContext(ctx, "python", scriptPath, "add", c.dbPath, collectionName)
	cmd.Stdin = bytes.NewReader(jsonData)

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return fmt.Errorf("python script failed: %s (exit code: %d)", string(exitErr.Stderr), exitErr.ExitCode())
		}
		return fmt.Errorf("failed to add documents: %w", err)
	}

	var result struct {
		Status string `json:"status"`
		Count  int    `json:"count"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return fmt.Errorf("failed to parse add response: %w", err)
	}

	return nil
}

func (c *chromaClient) query(ctx context.Context, queryEmbeddings [][]float32, nResults int) (*chromaQueryResponse, error) {
	scriptPath := "vector_db.py"

	// Convert float32 to float64 for JSON
	embeddingsFloat64 := make([][]float64, len(queryEmbeddings))
	for i, emb := range queryEmbeddings {
		embeddingsFloat64[i] = make([]float64, len(emb))
		for j, val := range emb {
			embeddingsFloat64[i][j] = float64(val)
		}
	}

	payload := map[string]interface{}{
		"query_embeddings": embeddingsFloat64,
		"n_results":        nResults,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	cmd := exec.CommandContext(ctx, "python", scriptPath, "query", c.dbPath, collectionName)
	cmd.Stdin = bytes.NewReader(jsonData)

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("python script failed: %s (exit code: %d)", string(exitErr.Stderr), exitErr.ExitCode())
		}
		return nil, fmt.Errorf("failed to query: %w", err)
	}

	var result chromaQueryResponse
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("failed to parse query response: %w", err)
	}

	return &result, nil
}

type chromaQueryResponse struct {
	Ids       [][]string                 `json:"ids"`
	Documents [][]string                 `json:"documents"`
	Metadatas [][]map[string]interface{} `json:"metadatas"`
	Distances [][]float64                `json:"distances"`
}

var chromaCli *chromaClient

func initChromaDB() error {
	chromaCli = newChromaClient()
	ctx := context.Background()

	if err := chromaCli.init(ctx); err != nil {
		log.Printf("Warning: Failed to initialize ChromaDB: %v", err)
		return err
	}

	return nil
}

func storeChunksInVectorDB(chunks []DocumentChunk) error {
	if chromaCli == nil {
		if err := initChromaDB(); err != nil {
			return err
		}
	}

	ctx := context.Background()

	// Generate embeddings using OpenAI API directly
	texts := make([]string, len(chunks))
	for i, chunk := range chunks {
		texts[i] = chunk.Text
	}

	embeddings, err := getEmbeddings(ctx, texts)
	if err != nil {
		return fmt.Errorf("failed to generate embeddings: %w", err)
	}

	// Prepare data for Chroma
	ids := make([]string, len(chunks))
	metadatas := make([]map[string]interface{}, len(chunks))
	embeddingsFloat := make([][]float32, len(embeddings))

	for i, chunk := range chunks {
		ids[i] = fmt.Sprintf("%s_chunk_%d", chunk.Metadata["source_file"], chunk.Metadata["chunk_index"])
		metadatas[i] = chunk.Metadata

		// Convert []float64 to []float32
		embeddingsFloat[i] = make([]float32, len(embeddings[i]))
		for j, val := range embeddings[i] {
			embeddingsFloat[i][j] = float32(val)
		}
	}

	// Store in Chroma
	if err := chromaCli.add(ctx, ids, embeddingsFloat, metadatas, texts); err != nil {
		return fmt.Errorf("failed to store in Chroma: %w", err)
	}

	log.Printf("Stored %d chunks in vector database", len(chunks))
	return nil
}

func retrieveDocuments(query string, topK int) ([]RetrievedDoc, error) {
	if chromaCli == nil {
		if err := initChromaDB(); err != nil {
			// Return empty results if ChromaDB not available
			log.Println("ChromaDB not available, returning empty results")
			return []RetrievedDoc{}, nil
		}
	}

	ctx := context.Background()

	// Generate query embedding using OpenAI API directly
	embeddings, err := getEmbeddings(ctx, []string{query})
	if err != nil {
		return nil, fmt.Errorf("failed to generate query embedding: %w", err)
	}

	// Convert to float32
	queryEmbedding := make([][]float32, 1)
	queryEmbedding[0] = make([]float32, len(embeddings[0]))
	for i, val := range embeddings[0] {
		queryEmbedding[0][i] = float32(val)
	}

	// Query Chroma
	results, err := chromaCli.query(ctx, queryEmbedding, topK)
	if err != nil {
		return nil, fmt.Errorf("failed to query Chroma: %w", err)
	}

	// Convert to RetrievedDoc format
	retrievedDocs := []RetrievedDoc{}
	if len(results.Documents) > 0 && len(results.Documents[0]) > 0 {
		for i := range results.Documents[0] {
			source := "Ukjent kilde"
			page := "?"

			if len(results.Metadatas) > 0 && len(results.Metadatas[0]) > i {
				if meta := results.Metadatas[0][i]; meta != nil {
					if src, ok := meta["source_file"].(string); ok {
						source = src
					}
					if pg, ok := meta["page"].(string); ok {
						page = pg
					}
				}
			}

			retrievedDocs = append(retrievedDocs, RetrievedDoc{
				Source:   source,
				Page:     page,
				Citation: fmt.Sprintf("[Kilde: %s, side %s]", source, page),
			})
		}
	}

	return retrievedDocs, nil
}
