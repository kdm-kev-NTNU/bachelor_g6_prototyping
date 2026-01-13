"""
Hybrid retrieval strategy combining semantic search and keyword/metadata filtering.
"""

from typing import List, Dict, Any, Optional
from vector_db import get_collection, get_embedding
from config import TOP_K_SEMANTIC, TOP_K_KEYWORD, TOP_K_FINAL


def semantic_search(query: str, collection, top_k: int = TOP_K_SEMANTIC) -> List[Dict[str, Any]]:
    """
    Perform semantic search using vector similarity.
    
    Args:
        query: Search query
        collection: Chroma collection
        top_k: Number of results to return
    
    Returns:
        List of relevant documents with scores
    """
    # Get query embedding
    query_embedding = get_embedding(query)
    
    # Search in collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    # Format results
    retrieved_docs = []
    if results["documents"] and len(results["documents"][0]) > 0:
        for i, doc in enumerate(results["documents"][0]):
            retrieved_docs.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
                "score": 1.0 - (results["distances"][0][i] if results["distances"] else 1.0)  # Convert distance to similarity
            })
    
    return retrieved_docs


def keyword_filter(query: str, collection, top_k: int = TOP_K_KEYWORD) -> List[Dict[str, Any]]:
    """
    Filter documents by keywords and metadata.
    
    Args:
        query: Search query
        collection: Chroma collection
        top_k: Number of results to return
    
    Returns:
        List of relevant documents
    """
    # Extract keywords from query (simple approach)
    query_lower = query.lower()
    keywords = [word for word in query_lower.split() if len(word) > 3]
    
    # Get all documents (or use where clause if Chroma supports it)
    # For now, we'll use semantic search but with keyword boosting
    results = collection.get()
    
    if not results["documents"]:
        return []
    
    scored_docs = []
    for i, doc in enumerate(results["documents"]):
        doc_lower = doc.lower()
        metadata = results["metadatas"][i] if results["metadatas"] else {}
        
        # Count keyword matches
        keyword_score = sum(1 for keyword in keywords if keyword in doc_lower)
        
        # Boost score based on metadata matches
        metadata_score = 0
        if "doc_type" in metadata and "energi" in query_lower:
            metadata_score += 1
        
        total_score = keyword_score + metadata_score * 0.5
        
        if total_score > 0:
            scored_docs.append({
                "text": doc,
                "metadata": metadata,
                "score": total_score / max(len(keywords), 1)  # Normalize
            })
    
    # Sort by score and return top_k
    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    return scored_docs[:top_k]


def hybrid_retrieve(query: str, building_data: Optional[Dict[str, Any]] = None,
                    top_k: int = TOP_K_FINAL) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval combining semantic search and keyword filtering.
    
    Args:
        query: Search query
        building_data: Optional building data for context-aware retrieval
        top_k: Final number of results to return
    
    Returns:
        List of relevant document chunks with citations
    """
    collection = get_collection()
    
    # Enhance query with building context if available
    enhanced_query = query
    if building_data:
        building_context = f"""
        Bygning: {building_data.get('age', '')} år gammel, 
        {building_data.get('size_m2', '')} m², 
        {building_data.get('construction_type', '')}, 
        energibruk: {building_data.get('current_energy_kwh', '')} kWh/år
        """
        enhanced_query = f"{query} {building_context}"
    
    # Semantic search
    semantic_results = semantic_search(enhanced_query, collection, top_k=TOP_K_SEMANTIC)
    
    # Keyword filtering
    keyword_results = keyword_filter(query, collection, top_k=TOP_K_KEYWORD)
    
    # Combine and deduplicate
    seen_texts = set()
    combined_results = []
    
    # Add semantic results first (higher priority)
    for doc in semantic_results:
        text_hash = hash(doc["text"][:100])  # Use first 100 chars as hash
        if text_hash not in seen_texts:
            doc["retrieval_method"] = "semantic"
            combined_results.append(doc)
            seen_texts.add(text_hash)
    
    # Add keyword results (if not already included)
    for doc in keyword_results:
        text_hash = hash(doc["text"][:100])
        if text_hash not in seen_texts:
            doc["retrieval_method"] = "keyword"
            combined_results.append(doc)
            seen_texts.add(text_hash)
    
    # Re-score combined results
    # Semantic results get base score, keyword results get adjusted score
    for doc in combined_results:
        if doc["retrieval_method"] == "semantic":
            # Keep semantic score
            pass
        else:
            # Boost keyword score to be comparable
            doc["score"] = doc.get("score", 0) * 0.7  # Slightly lower weight
    
    # Sort by score and return top_k
    combined_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Format with citations
    formatted_results = []
    for doc in combined_results[:top_k]:
        source = doc["metadata"].get("source_file", "Ukjent kilde")
        page = doc["metadata"].get("page", "?")
        
        formatted_results.append({
            "text": doc["text"],
            "citation": f"[Kilde: {source}, side {page}]",
            "source": source,
            "page": page,
            "metadata": doc["metadata"],
            "score": doc.get("score", 0),
            "retrieval_method": doc.get("retrieval_method", "unknown")
        })
    
    return formatted_results


def format_context_for_prompt(retrieved_docs: List[Dict[str, Any]]) -> str:
    """
    Format retrieved documents as context for LLM prompt.
    
    Args:
        retrieved_docs: List of retrieved document chunks
    
    Returns:
        Formatted context string
    """
    if not retrieved_docs:
        return "Ingen relevante dokumenter funnet."
    
    context_parts = []
    for i, doc in enumerate(retrieved_docs, 1):
        citation = doc.get("citation", f"[Kilde {i}]")
        text = doc["text"]
        context_parts.append(f"{citation}\n{text}\n")
    
    return "\n---\n\n".join(context_parts)


if __name__ == "__main__":
    # Test retrieval
    query = "Hvordan redusere energibruk i gamle bygninger?"
    results = hybrid_retrieve(query)
    
    print(f"Fant {len(results)} relevante dokumenter:")
    for i, doc in enumerate(results, 1):
        print(f"\n{i}. {doc['citation']}")
        print(f"   Score: {doc['score']:.3f}")
        print(f"   Metode: {doc['retrieval_method']}")
        print(f"   Tekst: {doc['text'][:200]}...")
