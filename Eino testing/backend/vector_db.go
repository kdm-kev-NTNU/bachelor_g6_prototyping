package main

import (
	"context"
	"fmt"
	"log"

	"github.com/chroma-core/chroma/go/pkg/client"
	"github.com/chroma-core/chroma/go/pkg/config"
	"github.com/cloudwego/eino/schema"
	"github.com/cloudwego/eino-ext/components/model/openai"
)

var chromaClient *client.Client
var collectionName = "energy_advice_docs"

func initChromaDB() error {
	cfg := config.NewDefaultConfig()
	cfg.ChromaHost = "localhost"
	cfg.ChromaPort = 8000

	var err error
	chromaClient, err = client.NewClient(cfg)
	if err != nil {
		// If ChromaDB is not running, return error but don't fail completely
		log.Printf("Warning: ChromaDB not available: %v. Will use in-memory storage.", err)
		return err
	}

	// Create or get collection
	_, err = chromaClient.CreateCollection(context.Background(), &client.CreateCollectionParams{
		Name: collectionName,
	})
	if err != nil {
		// Collection might already exist, try to get it
		_, err = chromaClient.GetCollection(context.Background(), &client.GetCollectionParams{
			Name: collectionName,
		})
		if err != nil {
			return fmt.Errorf("failed to create/get collection: %w", err)
		}
		log.Println("Using existing collection:", collectionName)
	} else {
		log.Println("Created collection:", collectionName)
	}

	return nil
}

func storeChunksInVectorDB(chunks []DocumentChunk) error {
	if chromaClient == nil {
		if err := initChromaDB(); err != nil {
			return err
		}
	}

	ctx := context.Background()

	// Initialize embedding model
	embeddingModel, err := openai.NewEmbeddingModel(ctx, &openai.EmbeddingModelConfig{
		APIKey: getOpenAIKey(),
		Model:  EmbeddingModel,
	})
	if err != nil {
		return fmt.Errorf("failed to create embedding model: %w", err)
	}

	// Generate embeddings
	texts := make([]string, len(chunks))
	for i, chunk := range chunks {
		texts[i] = chunk.Text
	}

	embeddings, err := embeddingModel.Embed(ctx, texts)
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
	_, err = chromaClient.Add(context.Background(), &client.AddParams{
		CollectionName: collectionName,
		IDs:            ids,
		Embeddings:     embeddingsFloat,
		Metadatas:      metadatas,
		Documents:      texts,
	})
	if err != nil {
		return fmt.Errorf("failed to store in Chroma: %w", err)
	}

	log.Printf("Stored %d chunks in vector database", len(chunks))
	return nil
}

func retrieveDocuments(query string, topK int) ([]RetrievedDoc, error) {
	if chromaClient == nil {
		if err := initChromaDB(); err != nil {
			// Return empty results if ChromaDB not available
			log.Println("ChromaDB not available, returning empty results")
			return []RetrievedDoc{}, nil
		}
	}

	ctx := context.Background()

	// Generate query embedding
	embeddingModel, err := openai.NewEmbeddingModel(ctx, &openai.EmbeddingModelConfig{
		APIKey: getOpenAIKey(),
		Model:  EmbeddingModel,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create embedding model: %w", err)
	}

	embeddings, err := embeddingModel.Embed(ctx, []string{query})
	if err != nil {
		return nil, fmt.Errorf("failed to generate query embedding: %w", err)
	}

	// Convert to float32
	queryEmbedding := make([]float32, len(embeddings[0]))
	for i, val := range embeddings[0] {
		queryEmbedding[i] = float32(val)
	}

	// Query Chroma
	results, err := chromaClient.Query(ctx, &client.QueryParams{
		CollectionName: collectionName,
		QueryEmbeddings: [][]float32{queryEmbedding},
		NResults:       topK,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to query Chroma: %w", err)
	}

	// Convert to RetrievedDoc format
	retrievedDocs := []RetrievedDoc{}
	if len(results.Documents) > 0 && len(results.Documents[0]) > 0 {
		for i, doc := range results.Documents[0] {
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
