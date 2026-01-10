"""Seed the database with sample data."""
import sys
from pathlib import Path

# Legg til prosjektets rot-mappe i Python-stien
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import text
from database.db import engine, Base
from database.models import User, Post, Product


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_data():
    """Seed database with sample data."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from database.db import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        
        if count > 0:
            print("Database already seeded. Skipping...")
            return
        
        # Create users
        users = [
            User(name="Alice Johnson", email="alice@example.com"),
            User(name="Bob Smith", email="bob@example.com"),
            User(name="Charlie Brown", email="charlie@example.com"),
            User(name="Diana Prince", email="diana@example.com"),
        ]
        
        session.add_all(users)
        await session.flush()  # Get IDs
        
        # Create posts
        posts = [
            Post(title="Getting Started with GraphQL", content="GraphQL is a powerful query language for APIs...", author_id=users[0].id),
            Post(title="RAG Systems Explained", content="Retrieval-Augmented Generation combines retrieval and generation...", author_id=users[0].id),
            Post(title="Vector Databases", content="Vector databases are essential for semantic search...", author_id=users[1].id),
            Post(title="Python Best Practices", content="Here are some best practices for Python development...", author_id=users[2].id),
            Post(title="FastAPI Tutorial", content="FastAPI is a modern web framework for building APIs...", author_id=users[3].id),
        ]
        
        session.add_all(posts)
        
        # Create products
        products = [
            Product(name="Laptop", price=999.99, description="High-performance laptop for developers"),
            Product(name="Keyboard", price=79.99, description="Mechanical keyboard with RGB lighting"),
            Product(name="Mouse", price=49.99, description="Wireless ergonomic mouse"),
            Product(name="Monitor", price=299.99, description="27-inch 4K monitor"),
            Product(name="Headphones", price=149.99, description="Noise-cancelling headphones"),
        ]
        
        session.add_all(products)
        
        await session.commit()
        print("Database seeded successfully!")


async def main():
    """Main function to initialize and seed database."""
    await init_db()
    await seed_data()


if __name__ == "__main__":
    asyncio.run(main())

