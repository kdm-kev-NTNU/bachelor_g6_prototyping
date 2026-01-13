"""
Chroma vector database setup and management for energy advice documents.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

from config import CHROMA_COLLECTION_NAME, CHROMA_PATH, EMBEDDING_MODEL
from eino_client import create_eino_client

load_dotenv()


def get_chroma_client():
    """Get or create Chroma client."""
    chroma_path = Path(CHROMA_PATH)
    chroma_path.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=Settings(anonymized_telemetry=False)
    )
    
    return client


def get_collection(name: str = CHROMA_COLLECTION_NAME):
    """Get or create a Chroma collection."""
    client = get_chroma_client()
    
    try:
        collection = client.get_collection(name=name)
        print(f"[INFO] Bruker eksisterende collection: {name}")
    except:
        collection = client.create_collection(
            name=name,
            metadata={"description": "Energy advice documents"}
        )
        print(f"[INFO] Opprettet ny collection: {name}")
    
    return collection


def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """Get embedding for text using Eino platform."""
    client = create_eino_client()
    
    response = client.embeddings.create(
        model=model,
        input=text
    )
    
    return response.data[0].embedding


def store_chunks_in_vector_db(chunks: List[Dict[str, Any]], 
                              collection_name: str = CHROMA_COLLECTION_NAME):
    """
    Store document chunks in Chroma vector database.
    
    Args:
        chunks: List of chunk dictionaries with 'text' and 'metadata'
        collection_name: Name of Chroma collection
    """
    if not chunks:
        print("[WARN] Ingen chunks å lagre")
        return
    
    collection = get_collection(collection_name)
    
    # Check if collection already has data
    existing_count = collection.count()
    if existing_count > 0:
        print(f"[INFO] Collection har allerede {existing_count} dokumenter")
        response = input("Vil du legge til nye dokumenter? (j/n): ")
        if response.lower() != 'j':
            print("[INFO] Avbrutt")
            return
    
    print(f"[INFO] Lagrer {len(chunks)} chunks i vector database...")
    
    # Prepare data for Chroma
    ids = []
    documents = []
    metadatas = []
    embeddings = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{chunk['metadata']['source_file']}_chunk_{chunk['metadata']['chunk_index']}"
        ids.append(chunk_id)
        documents.append(chunk['text'])
        
        # Prepare metadata (Chroma requires string values)
        metadata = {}
        for key, value in chunk['metadata'].items():
            if isinstance(value, (str, int, float)):
                metadata[key] = str(value)
            elif isinstance(value, bool):
                metadata[key] = str(value).lower()
            elif value is None:
                metadata[key] = ""
            else:
                metadata[key] = str(value)
        
        metadatas.append(metadata)
        
        # Get embedding
        try:
            embedding = get_embedding(chunk['text'])
            embeddings.append(embedding)
        except Exception as e:
            print(f"[ERROR] Feil ved embedding for chunk {i}: {e}")
            # Skip this chunk
            ids.pop()
            documents.pop()
            metadatas.pop()
            continue
        
        if (i + 1) % 10 == 0:
            print(f"[INFO] Prosesserer chunk {i + 1}/{len(chunks)}...")
    
    # Store in Chroma
    if ids:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        print(f"[OK] Lagret {len(ids)} chunks i vector database")
    else:
        print("[ERROR] Ingen chunks å lagre")


def initialize_vector_db(pdf_dir: str = "pdf", force_reload: bool = False):
    """
    Initialize vector database by processing PDFs and storing chunks.
    
    Args:
        pdf_dir: Directory containing PDF files
        force_reload: If True, reload even if collection has data
    """
    from pdf_processor import process_pdf_directory
    
    collection = get_collection()
    
    if not force_reload:
        count = collection.count()
        if count > 0:
            print(f"[INFO] Vector database har allerede {count} dokumenter")
            print("[INFO] Bruk force_reload=True for å laste på nytt")
            return
    
    # Process PDFs
    chunks = process_pdf_directory(pdf_dir)
    
    if chunks:
        # Store in vector database
        store_chunks_in_vector_db(chunks)
    else:
        print("[WARN] Ingen chunks å lagre")


if __name__ == "__main__":
    # Initialize vector database
    print("Initialiserer vector database...")
    initialize_vector_db(force_reload=False)
