"""Store GraphQL schema information in Chroma vector database."""
import sys
from pathlib import Path

# Legg til prosjektets rot-mappe i Python-stien
sys.path.insert(0, str(Path(__file__).parent.parent))

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


def store_schema_in_vector_db():
    """Store GraphQL schema documentation in vector database."""
    collection = get_collection()
    
    # GraphQL schema documentation chunks
    schema_docs = [
        {
            "id": "query_users",
            "text": "Query: users - Returns a list of all users. Each user has id, name, and email fields.",
            "metadata": {"type": "query", "operation": "users", "returns": "List[UserType]"}
        },
        {
            "id": "query_user",
            "text": "Query: user(id: Int!) - Returns a single user by ID. Takes id as integer parameter. Returns UserType with id, name, and email.",
            "metadata": {"type": "query", "operation": "user", "parameters": "id: Int!", "returns": "UserType"}
        },
        {
            "id": "query_posts",
            "text": "Query: posts - Returns a list of all posts. Each post has id, title, content, author_id, and author (UserType) fields.",
            "metadata": {"type": "query", "operation": "posts", "returns": "List[PostType]"}
        },
        {
            "id": "query_post",
            "text": "Query: post(id: Int!) - Returns a single post by ID. Takes id as integer parameter. Returns PostType with id, title, content, author_id, and author.",
            "metadata": {"type": "query", "operation": "post", "parameters": "id: Int!", "returns": "PostType"}
        },
        {
            "id": "query_products",
            "text": "Query: products - Returns a list of all products. Each product has id, name, price, and description fields.",
            "metadata": {"type": "query", "operation": "products", "returns": "List[ProductType]"}
        },
        {
            "id": "query_product",
            "text": "Query: product(id: Int!) - Returns a single product by ID. Takes id as integer parameter. Returns ProductType with id, name, price, and description.",
            "metadata": {"type": "query", "operation": "product", "parameters": "id: Int!", "returns": "ProductType"}
        },
        {
            "id": "mutation_create_user",
            "text": "Mutation: createUser(name: String!, email: String!) - Creates a new user. Takes name and email as required string parameters. Returns the created UserType.",
            "metadata": {"type": "mutation", "operation": "createUser", "parameters": "name: String!, email: String!", "returns": "UserType"}
        },
        {
            "id": "mutation_create_post",
            "text": "Mutation: createPost(title: String!, content: String!, authorId: Int!) - Creates a new post. Takes title and content as required strings, and authorId as required integer. Returns the created PostType with all fields including author.",
            "metadata": {"type": "mutation", "operation": "createPost", "parameters": "title: String!, content: String!, authorId: Int!", "returns": "PostType"}
        },
        {
            "id": "type_user",
            "text": "Type: UserType - Represents a user with fields: id (Int), name (String), email (String).",
            "metadata": {"type": "type", "name": "UserType", "fields": "id, name, email"}
        },
        {
            "id": "type_post",
            "text": "Type: PostType - Represents a post with fields: id (Int), title (String), content (String), authorId (Int, exposed as authorId in GraphQL), author (UserType, optional).",
            "metadata": {"type": "type", "name": "PostType", "fields": "id, title, content, authorId, author"}
        },
        {
            "id": "type_product",
            "text": "Type: ProductType - Represents a product with fields: id (Int), name (String), price (Float), description (String, optional).",
            "metadata": {"type": "type", "name": "ProductType", "fields": "id, name, price, description"}
        },
    ]
    
    # Generate embeddings and store
    texts = [doc["text"] for doc in schema_docs]
    ids = [doc["id"] for doc in schema_docs]
    metadatas = [doc["metadata"] for doc in schema_docs]
    
    # Get embeddings
    embeddings = [get_embedding(text) for text in texts]
    
    # Store in Chroma
    collection.add(
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Stored {len(schema_docs)} schema documents in vector database")


if __name__ == "__main__":
    store_schema_in_vector_db()

