package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os/exec"
	"path/filepath"
	"strings"
)

type DocumentChunk struct {
	Text     string
	Metadata map[string]interface{}
}

func processPDFDirectory(pdfDir string) ([]DocumentChunk, error) {
	chunks := []DocumentChunk{}

	// Find all PDF files
	pdfFiles, err := filepath.Glob(filepath.Join(pdfDir, "*.pdf"))
	if err != nil {
		return nil, fmt.Errorf("failed to find PDF files: %w", err)
	}

	if len(pdfFiles) == 0 {
		log.Println("No PDF files found in", pdfDir)
		return chunks, nil
	}

	log.Printf("Found %d PDF files", len(pdfFiles))

	for _, pdfPath := range pdfFiles {
		fileName := filepath.Base(pdfPath)
		log.Printf("Processing %s...", fileName)

		// Use Python pdfplumber for PDF extraction (more reliable)
		// This calls a Python script that uses pdfplumber
		text, err := extractPDFTextWithPython(pdfPath)
		if err != nil {
			log.Printf("Warning: failed to extract text from %s: %v", fileName, err)
			continue
		}

		if strings.TrimSpace(text) == "" {
			log.Printf("Warning: no text extracted from %s", fileName)
			continue
		}

		// Chunk the text
		textChunks := chunkText(text, ChunkSize, ChunkOverlap)

		// Create chunk entries
		for i, chunkText := range textChunks {
			chunks = append(chunks, DocumentChunk{
				Text: chunkText,
				Metadata: map[string]interface{}{
					"source_file":  fileName,
					"chunk_index":  i,
					"total_chunks": len(textChunks),
					"doc_type":     "energy_advice",
				},
			})
		}

		log.Printf("Processed %s: %d chunks", fileName, len(textChunks))
	}

	log.Printf("Total: %d chunks from %d PDFs", len(chunks), len(pdfFiles))
	return chunks, nil
}

func chunkText(text string, chunkSize, overlap int) []string {
	if text == "" {
		return []string{}
	}

	// Split by paragraphs
	paragraphs := strings.Split(text, "\n\n")
	var chunks []string
	currentChunk := ""
	currentLength := 0

	for _, para := range paragraphs {
		para = strings.TrimSpace(para)
		if para == "" {
			continue
		}

		paraLength := len(strings.Fields(para)) // Approximate token count

		if currentLength+paraLength > chunkSize && currentChunk != "" {
			chunks = append(chunks, currentChunk)

			// Keep overlap
			if overlap > 0 && len(chunks) > 0 {
				words := strings.Fields(currentChunk)
				if len(words) > overlap {
					currentChunk = strings.Join(words[len(words)-overlap:], " ")
					currentLength = overlap
				} else {
					currentChunk = ""
					currentLength = 0
				}
			} else {
				currentChunk = ""
				currentLength = 0
			}
		}

		if currentChunk != "" {
			currentChunk += "\n\n"
		}
		currentChunk += para
		currentLength += paraLength
	}

	if currentChunk != "" {
		chunks = append(chunks, currentChunk)
	}

	return chunks
}

// extractPDFTextWithPython uses Python pdfplumber to extract text
func extractPDFTextWithPython(pdfPath string) (string, error) {
	// Create a temporary Python script
	pythonScript := `
import sys
import pdfplumber
import json

pdf_path = sys.argv[1]
text_parts = []

try:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_parts.append(page_text)
    print(json.dumps({"text": "\n\n".join(text_parts)}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
`

	// Execute Python script
	cmd := exec.Command("python", "-c", pythonScript, pdfPath)
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("python execution failed: %w", err)
	}

	// Parse JSON output
	var result struct {
		Text  string `json:"text"`
		Error string `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return "", fmt.Errorf("failed to parse python output: %w", err)
	}

	if result.Error != "" {
		return "", fmt.Errorf("python error: %s", result.Error)
	}

	return result.Text, nil
}
