# GraphQL MCP Server Setup

This folder contains the configuration for connecting your GraphQL API to AI applications like Claude Desktop via the Model Context Protocol (MCP).

## Architecture

```
┌─────────────────┐     MCP Protocol     ┌─────────────────────┐
│  Claude Desktop │ ◄──────────────────► │   mcp-graphql       │
└─────────────────┘                      └──────────┬──────────┘
                                                    │
                                           GraphQL Queries
                                                    │
                                                    ▼
                                         ┌─────────────────────┐
                                         │ Strawberry GraphQL  │
                                         │   (localhost:8000)  │
                                         └──────────┬──────────┘
                                                    │
                                                    ▼
                                         ┌─────────────────────┐
                                         │   SQLite Database   │
                                         └─────────────────────┘
```

## How It Works

The `mcp-graphql` package automatically introspects your GraphQL schema and exposes all queries and mutations as MCP tools. This means Claude can:

1. **Discover** all available operations via schema introspection
2. **Execute** any GraphQL query or mutation
3. **Pass parameters** dynamically based on the operation arguments

## Available GraphQL Operations

Your Strawberry GraphQL server exposes these operations:

### Queries
- **users** - Get all users from the database
- **user(id)** - Get a specific user by ID
- **posts** - Get all posts with author information
- **post(id)** - Get a specific post by ID
- **products** - Get all products from the database
- **product(id)** - Get a specific product by ID

### Mutations
- **createUser(name, email)** - Create a new user
- **createPost(title, content, authorId)** - Create a new post

## Setup Instructions

### Prerequisites

1. Node.js v18 or later
2. GraphQL server running at `http://localhost:8000/graphql`

### Step 1: Start the GraphQL Server

```bash
cd ../Schema-rag
python main.py
```

### Step 2: Configure Claude Desktop

The Claude Desktop configuration has been set up at:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Configuration content:
```json
{
  "mcpServers": {
    "graphql-api": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-graphql",
        "--endpoint",
        "http://localhost:8000/graphql"
      ]
    }
  }
}
```

### Step 3: Restart Claude Desktop

After configuring, restart Claude Desktop to load the MCP server.

### Step 4: Verify Setup

In Claude Desktop, ask:
> "What MCP tools do you have available?"

Claude should list the GraphQL operations as available tools.

## Example Usage in Claude

Once configured, you can interact with your GraphQL API naturally:

- "Show me all users in the database"
- "Get the product with ID 1"
- "Create a new user named John Doe with email john@example.com"
- "List all posts with their authors"
- "What products do you have available?"

## Testing Manually

You can test the MCP server manually:

```bash
# Test the GraphQL endpoint directly
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { id name email } }"}'
```

## Troubleshooting

### Claude can't see the tools
1. Make sure Claude Desktop is restarted after configuration
2. Verify the GraphQL server is running at `http://localhost:8000/graphql`
3. Check that Node.js v18+ is installed

### GraphQL errors
1. Check that your Strawberry GraphQL server is running
2. Test the GraphQL endpoint directly: `http://localhost:8000/graphql`
3. Open GraphQL Playground at `http://localhost:8000/graphql` in your browser

### MCP server won't start
1. Try running `npx -y mcp-graphql --endpoint http://localhost:8000/graphql` manually
2. Check for npm/node errors in the console

## Files in This Folder

| File | Description |
|------|-------------|
| `mcp-config.yaml` | Example configuration (for reference) |
| `operations/` | Pre-defined GraphQL operations (for reference) |
| `start-mcp-server.ps1` | PowerShell script to start manually |
| `README.md` | This documentation |

## References

- [mcp-graphql on npm](https://www.npmjs.com/package/mcp-graphql)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Apollo MCP Server Documentation](https://www.apollographql.com/docs/apollo-mcp-server)
