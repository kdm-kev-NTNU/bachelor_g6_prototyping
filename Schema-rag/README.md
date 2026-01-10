# RAG-Enhanced GraphQL Query Generation System

A system that converts natural language queries to GraphQL queries using Retrieval-Augmented Generation (RAG). The system uses a vector database (Chroma) to store GraphQL schema information and OpenAI for embeddings and query generation.

## Features

- **GraphQL Server**: FastAPI with Strawberry GraphQL
- **SQLite Database**: Stores fictional data (Users, Posts, Products)
- **Vector Database**: ChromaDB for semantic search of schema information
- **RAG System**: Retrieves relevant schema info and generates GraphQL queries
- **Natural Language to GraphQL**: Convert plain English to GraphQL queries

## Architecture

```
User Query (NL) → Embedding → Vector DB Search → RAG Engine → GPT → GraphQL Query → GraphQL Server → SQLite → Response
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Initialize Database

```bash
python database/seed.py
```

This will:
- Create the SQLite database
- Create all tables
- Seed with sample data

### 4. Initialize Vector Database

```bash
python vector_db/store.py
```

This will:
- Create Chroma collection
- Store GraphQL schema documentation
- Generate embeddings for schema information

### 5. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn api.routes:app --reload
```

The server will start on `http://localhost:8000`

## API Endpoints

### GraphQL Endpoint

- **URL**: `http://localhost:8000/graphql`
- **Method**: POST
- **Content-Type**: application/json

Example:
```json
{
  "query": "{ users { id name email } }"
}
```

### Natural Language to GraphQL

- **URL**: `http://localhost:8000/nl-to-graphql`
- **Method**: POST
- **Content-Type**: application/json

Example:
```json
{
  "query": "Get all users with their names and emails"
}
```

Response:
```json
{
  "graphql_query": "{ users { name email } }",
  "result": {
    "users": [
      {"name": "Alice Johnson", "email": "alice@example.com"},
      ...
    ]
  }
}
```

### Health Check

- **URL**: `http://localhost:8000/health`
- **Method**: GET

## GraphQL Schema

### Queries

- `users`: Get all users
- `user(id: Int!)`: Get user by ID
- `posts`: Get all posts
- `post(id: Int!)`: Get post by ID
- `products`: Get all products
- `product(id: Int!)`: Get product by ID

### Mutations

- `createUser(name: String!, email: String!)`: Create a new user
- `createPost(title: String!, content: String!, authorId: Int!)`: Create a new post

### Types

- **UserType**: id, name, email
- **PostType**: id, title, content, authorId, author
- **ProductType**: id, name, price, description

## Example Queries

### Natural Language Examples

1. "Get all users"
2. "Show me all products with their prices"
3. "Find the user with id 1"
4. "Get all posts with their authors"
5. "Create a new user named John Doe with email john@example.com"

### Direct GraphQL Examples

```graphql
# Get all users
{
  users {
    id
    name
    email
  }
}

# Get a specific post with author
{
  post(id: 1) {
    title
    content
    author {
      name
      email
    }
  }
}

# Get all products
{
  products {
    id
    name
    price
  }
}
```

## Project Structure

```
NL-to-Graphql/
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models
│   ├── seed.py            # Seed data script
│   └── db.py              # Database connection
├── graphql/
│   ├── __init__.py
│   └── schema.py          # GraphQL schema definition
├── vector_db/
│   ├── __init__.py
│   ├── setup.py           # Chroma initialization
│   └── store.py           # Store schema in vector DB
├── rag/
│   ├── __init__.py
│   ├── retriever.py       # Retrieve from vector DB
│   └── generator.py       # Generate GraphQL from NL
├── api/
│   ├── __init__.py
│   └── routes.py          # API endpoints
├── main.py                # Application entry point
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

1. **User Query**: User provides a natural language query
2. **Embedding**: Query is embedded using OpenAI embeddings
3. **Retrieval**: Vector database (Chroma) is searched for relevant schema information
4. **Context Building**: Retrieved schema info is combined with the user query
5. **Generation**: GPT-4 generates a GraphQL query based on the context
6. **Execution**: Generated query is executed against the GraphQL server
7. **Response**: Results are returned to the user

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection (for OpenAI API calls)

## License

MIT

