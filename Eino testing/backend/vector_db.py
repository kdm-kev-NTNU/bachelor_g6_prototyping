"""
ChromaDB embedded client for Go backend
Uses existing chroma_db directory directly without requiring a server
"""
import sys
import json
import chromadb
from chromadb.config import Settings

def init_client(db_path):
    """Initialize ChromaDB client with existing database"""
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(anonymized_telemetry=False)
    )
    return client

def get_or_create_collection(client, collection_name):
    """Get existing collection or create if it doesn't exist"""
    try:
        collection = client.get_collection(name=collection_name)
        return collection, False  # False = already existed
    except:
        collection = client.create_collection(name=collection_name)
        return collection, True  # True = just created

def add_documents(collection, ids, embeddings, metadatas, documents):
    """Add documents to collection"""
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )

def query_collection(collection, query_embeddings, n_results):
    """Query collection and return results"""
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results
    )
    return {
        "ids": results["ids"],
        "documents": results["documents"],
        "metadatas": results["metadatas"],
        "distances": results["distances"]
    }

if __name__ == "__main__":
    command = sys.argv[1]
    db_path = sys.argv[2]
    collection_name = sys.argv[3]
    
    client = init_client(db_path)
    collection, created = get_or_create_collection(client, collection_name)
    
    if command == "init":
        print(json.dumps({"status": "ok", "created": created, "collection": collection_name}))
    
    elif command == "add":
        # Read JSON from stdin
        data = json.loads(sys.stdin.read())
        add_documents(
            collection,
            data["ids"],
            data["embeddings"],
            data["metadatas"],
            data["documents"]
        )
        print(json.dumps({"status": "ok", "count": len(data["ids"])}))
    
    elif command == "query":
        # Read JSON from stdin
        data = json.loads(sys.stdin.read())
        results = query_collection(
            collection,
            data["query_embeddings"],
            data["n_results"]
        )
        print(json.dumps(results))
    
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}), file=sys.stderr)
        sys.exit(1)
