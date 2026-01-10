# Start GraphQL MCP Server
# This script starts the MCP server that connects Claude to your GraphQL API

Write-Host "Starting GraphQL MCP Server..." -ForegroundColor Green
Write-Host "Make sure your GraphQL server is running at http://localhost:8000/graphql" -ForegroundColor Yellow
Write-Host ""

# Change to the MCP graphql directory
Set-Location $PSScriptRoot

# Set the endpoint environment variable (required since mcp-graphql v1.0.0)
$env:ENDPOINT = "http://localhost:8000/graphql"

# Run mcp-graphql server
npx -y mcp-graphql
