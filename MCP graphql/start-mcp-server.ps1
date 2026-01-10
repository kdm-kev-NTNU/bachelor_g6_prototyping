# Start GraphQL MCP Server
# This script starts the MCP server that connects Claude to your GraphQL API

Write-Host "Starting GraphQL MCP Server..." -ForegroundColor Green
Write-Host "Make sure your GraphQL server is running at http://localhost:8000/graphql" -ForegroundColor Yellow
Write-Host ""

# Change to the Apollo MCP directory
Set-Location $PSScriptRoot

# Run mcp-graphql server
npx -y mcp-graphql --endpoint http://localhost:8000/graphql
