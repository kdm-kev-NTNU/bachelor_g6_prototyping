"""GraphQL schema definition using Strawberry."""
import strawberry
from typing import List, Optional
from database.models import User, Post, Product


@strawberry.type
class UserType:
    """GraphQL User type."""
    id: int
    name: str
    email: str


@strawberry.type
class PostType:
    """GraphQL Post type."""
    id: int
    title: str
    content: str
    author_id: int
    author: Optional["UserType"] = None


@strawberry.type
class ProductType:
    """GraphQL Product type."""
    id: int
    name: str
    price: float
    description: Optional[str] = None


@strawberry.type
class Query:
    """GraphQL Query type."""
    
    @strawberry.field
    async def users(self) -> List[UserType]:
        """Get all users."""
        from database.db import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            return [UserType(id=u.id, name=u.name, email=u.email) for u in users]
    
    @strawberry.field
    async def user(self, id: int) -> Optional[UserType]:
        """Get a user by ID."""
        from database.db import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == id))
            user = result.scalar_one_or_none()
            if user:
                return UserType(id=user.id, name=user.name, email=user.email)
            return None
    
    @strawberry.field
    async def posts(self) -> List[PostType]:
        """Get all posts."""
        from database.db import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Post))
            posts = result.scalars().all()
            return [
                PostType(
                    id=p.id,
                    title=p.title,
                    content=p.content,
                    author_id=p.author_id,
                    author=UserType(id=p.author.id, name=p.author.name, email=p.author.email) if p.author else None
                )
                for p in posts
            ]
    
    @strawberry.field
    async def post(self, id: int) -> Optional[PostType]:
        """Get a post by ID."""
        from database.db import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Post).where(Post.id == id))
            post = result.scalar_one_or_none()
            if post:
                return PostType(
                    id=post.id,
                    title=post.title,
                    content=post.content,
                    author_id=post.author_id,
                    author=UserType(id=post.author.id, name=post.author.name, email=post.author.email) if post.author else None
                )
            return None
    
    @strawberry.field
    async def products(self) -> List[ProductType]:
        """Get all products."""
        from database.db import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Product))
            products = result.scalars().all()
            return [
                ProductType(
                    id=p.id,
                    name=p.name,
                    price=p.price,
                    description=p.description
                )
                for p in products
            ]
    
    @strawberry.field
    async def product(self, id: int) -> Optional[ProductType]:
        """Get a product by ID."""
        from database.db import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Product).where(Product.id == id))
            product = result.scalar_one_or_none()
            if product:
                return ProductType(
                    id=product.id,
                    name=product.name,
                    price=product.price,
                    description=product.description
                )
            return None


@strawberry.type
class Mutation:
    """GraphQL Mutation type."""
    
    @strawberry.mutation
    async def create_user(self, name: str, email: str) -> UserType:
        """Create a new user."""
        from database.db import AsyncSessionLocal
        from database.models import User
        
        async with AsyncSessionLocal() as session:
            user = User(name=name, email=email)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return UserType(id=user.id, name=user.name, email=user.email)
    
    @strawberry.mutation
    async def create_post(self, title: str, content: str, author_id: int) -> PostType:
        """Create a new post."""
        from database.db import AsyncSessionLocal
        from database.models import Post, User
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            # Verify author exists
            result = await session.execute(select(User).where(User.id == author_id))
            author = result.scalar_one_or_none()
            if not author:
                raise ValueError(f"User with id {author_id} not found")
            
            post = Post(title=title, content=content, author_id=author_id)
            session.add(post)
            await session.commit()
            await session.refresh(post)
            
            return PostType(
                id=post.id,
                title=post.title,
                content=post.content,
                author_id=post.author_id,
                author=UserType(id=author.id, name=author.name, email=author.email)
            )


# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
