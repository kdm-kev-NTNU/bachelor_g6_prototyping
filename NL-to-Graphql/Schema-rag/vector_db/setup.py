"""Initialize Chroma vector database."""
import chromadb
from chromadb.config import Settings
import os
from pathlib import Path


def get_chroma_client():
    """Get or create Chroma client."""
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    Path(chroma_path).mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=chroma_path,
        settings=Settings(anonymized_telemetry=False)
    )
    
    return client


def get_collection(name: str = "graphql_schema"):
    """Get or create a Chroma collection."""
    client = get_chroma_client()
    
    try:
        collection = client.get_collection(name=name)
    except:
        collection = client.create_collection(name=name)
    
    return collection

