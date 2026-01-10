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

---

## Quick Start Guide

### Prerequisites

Before you begin, make sure you have:

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 8+ | `npm --version` |

---

## Step 1: Start the GraphQL Server

The GraphQL server must be running before Claude can connect to it.

### Option A: Using the main.py script

```powershell
# Navigate to the Schema-rag folder
cd C:\Users\kevin\Documents\GitHub\NL-to-Graphql\Schema-rag

# Activate virtual environment (if using one)
# .\.venv\Scripts\Activate.ps1

# Start the server
python main.py
```

### Option B: Using uvicorn directly

```powershell
cd C:\Users\kevin\Documents\GitHub\NL-to-Graphql\Schema-rag

# Start with auto-reload (for development)
uvicorn api.routes:app --reload --host 0.0.0.0 --port 8000
```

### Verify GraphQL Server is Running

Open your browser and go to: **http://localhost:8000/graphql**

You should see the GraphQL Playground interface. Try this query:

```graphql
{
  users {
    id
    name
    email
  }
}
```

Or test from terminal (PowerShell):

```powershell
$body = '{"query": "{ users { id name email } }"}'
Invoke-RestMethod -Uri "http://localhost:8000/graphql" -Method Post -ContentType "application/json" -Body $body
```

---

## Step 2: Configure Claude Desktop for MCP

### Find the Configuration File

The Claude Desktop config file is located at:

```
Windows: %APPDATA%\Claude\claude_desktop_config.json
macOS:   ~/Library/Application Support/Claude/claude_desktop_config.json
Linux:   ~/.config/Claude/claude_desktop_config.json
```

### Edit the Configuration

Open the file and add this configuration:

```json
{
  "mcpServers": {
    "graphql-api": {
      "command": "cmd.exe",
      "args": ["/c", "npx", "-y", "mcp-graphql"],
      "env": {
        "ENDPOINT": "http://localhost:8000/graphql"
      }
    }
  }
}
```

> **Note:** The `mcp-graphql` package uses environment variables (not command-line arguments) since version 1.0.0.

### Quick Edit via PowerShell

```powershell
# Open the config file in your default editor
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

---

## Step 3: Restart Claude Desktop

**Important:** You must fully quit Claude Desktop, not just close the window!

### Windows
1. Right-click the Claude icon in the **system tray** (near the clock)
2. Select **"Quit"** or **"Exit"**
3. Open Claude Desktop again

### Verify MCP Server is Running

1. Open Claude Desktop
2. Go to **Settings** (gear icon)
3. Click **Developer** in the left menu
4. Under **Local MCP servers**, you should see **"graphql-api"** with status **"running"**

---

## Step 4: Test the Integration

In Claude Desktop, try these prompts:

```
"What MCP tools do you have available?"
```

```
"Show me all users in the database"
```

```
"Get all products"
```

```
"Create a new user named Test User with email test@example.com"
```

---

## Running Both Servers Together

### Option 1: Two Terminal Windows

**Terminal 1 - GraphQL Server:**
```powershell
cd C:\Users\kevin\Documents\GitHub\NL-to-Graphql\Schema-rag
python main.py
```

**Terminal 2 - Test MCP manually (optional):**
```powershell
$env:ENDPOINT = "http://localhost:8000/graphql"
npx -y mcp-graphql
```

### Option 2: Using the PowerShell Script

```powershell
cd "C:\Users\kevin\Documents\GitHub\NL-to-Graphql\MCP graphql"
.\start-mcp-server.ps1
```

### Option 3: Background Process (GraphQL Server)

```powershell
# Start GraphQL server in background
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "main.py" -WorkingDirectory "C:\Users\kevin\Documents\GitHub\NL-to-Graphql\Schema-rag"

# Check if it's running
Invoke-RestMethod -Uri "http://localhost:8000/graphql" -Method Post -ContentType "application/json" -Body '{"query": "{ __typename }"}'
```

---

## Troubleshooting

### GraphQL Server Issues

| Problem | Solution |
|---------|----------|
| Port 8000 already in use | `netstat -ano \| findstr :8000` then kill the process |
| Module not found | `pip install -r requirements.txt` in Schema-rag folder |
| Database errors | Delete `app.db` and run `python init.py` to recreate |

### MCP Server Issues

| Problem | Solution |
|---------|----------|
| graphql-api not showing in Claude | Fully quit and restart Claude Desktop |
| Server shows "error" status | Check Claude logs at `%APPDATA%\Claude\logs\mcp.log` |
| npx command not found | Install Node.js 18+ and restart terminal |

### Check Claude Desktop Logs

```powershell
# View MCP logs
Get-Content "$env:APPDATA\Claude\logs\mcp.log" -Tail 50

# View server-specific logs
Get-Content "$env:APPDATA\Claude\logs\mcp-server-graphql-api.log" -Tail 50
```

### Test GraphQL Endpoint Directly

```powershell
# Simple query test
$response = Invoke-RestMethod -Uri "http://localhost:8000/graphql" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"query": "{ users { id name email } }"}'

$response.data | ConvertTo-Json
```

---

## Files in This Folder

| File | Description |
|------|-------------|
| `start-mcp-server.ps1` | PowerShell script to start MCP server manually |
| `README.md` | This documentation |

> **Note:** `mcp-graphql` does automatic schema introspection, so no pre-defined operation files are needed.

---

## Example Conversations with Claude

Once everything is set up, you can have natural conversations like:

> **You:** "Show me all users in the database"
> 
> **Claude:** *Uses the GraphQL MCP tool to query users*
> "Here are the users in your database:
> 1. Alice Johnson (alice@example.com)
> 2. Bob Smith (bob@example.com)
> ..."

> **You:** "Create a blog post titled 'Hello World' by user 1"
> 
> **Claude:** *Uses the createPost mutation*
> "I've created a new post with the title 'Hello World' by Alice Johnson."

---

## References

- [mcp-graphql on npm](https://www.npmjs.com/package/mcp-graphql)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Server Build Guide](https://modelcontextprotocol.io/docs/develop/build-server)
- [Apollo MCP Server Documentation](https://www.apollographql.com/docs/apollo-mcp-server)
- [Strawberry GraphQL](https://strawberry.rocks/)