"""Initialize the application - setup database and vector store."""
import asyncio
from database.seed import main as seed_db
from vector_db.store import store_schema_in_vector_db


def init():
    """Initialize database and vector store."""
    print("Initializing database...")
    asyncio.run(seed_db())
    
    print("\nInitializing vector database...")
    store_schema_in_vector_db()
    
    print("\n✅ Initialization complete!")
    print("\nNext steps:")
    print("1. Make sure you have set OPENAI_API_KEY in your .env file")
    print("2. Run: python main.py")
    print("3. Visit http://localhost:8000 for the API")


if __name__ == "__main__":
    init()

