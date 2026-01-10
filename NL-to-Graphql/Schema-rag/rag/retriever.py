"""Retrieve relevant schema information from vector database."""
from vector_db.setup import get_collection
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding(text: str) -> list:
    """Get embedding for text using OpenAI."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def retrieve_schema_info(query: str, n_results: int = 5) -> list:
    """
    Retrieve relevant schema information based on natural language query.
    
    Args:
        query: Natural language query
        n_results: Number of results to retrieve
        
    Returns:
        List of relevant schema documents with metadata
    """
    collection = get_collection()
    
    # Get query embedding
    query_embedding = get_embedding(query)
    
    # Search in vector database
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    # Format results
    retrieved_docs = []
    if results["documents"] and len(results["documents"][0]) > 0:
        for i, doc in enumerate(results["documents"][0]):
            retrieved_docs.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None
            })
    
    return retrieved_docs

