# Start GraphQL MCP Server for Energy Data
# Connects Claude/Cursor to FalkorDB energy data via GraphQL

param(
    [switch]$StartGraphQL,
    [switch]$McpOnly
)

$GraphQLEndpoint = "http://localhost:4000/graphql"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Energy Data MCP Server" -ForegroundColor Cyan
Write-Host "  FalkorDB -> GraphQL -> MCP -> AI" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# Start GraphQL server if requested
if ($StartGraphQL) {
    Write-Host "[1/2] Starting GraphQL Server..." -ForegroundColor Yellow
    Start-Process -NoNewWindow -FilePath "python" -ArgumentList "graphql_server.py"
    Write-Host "     Waiting for server to start..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
}

# Check if GraphQL server is running
try {
    $response = Invoke-WebRequest -Uri "$GraphQLEndpoint" -Method Post -ContentType "application/json" -Body '{"query": "{ __typename }"}' -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] GraphQL server is running at $GraphQLEndpoint" -ForegroundColor Green
} catch {
    Write-Host "[!] GraphQL server not responding at $GraphQLEndpoint" -ForegroundColor Red
    Write-Host ""
    Write-Host "Start the GraphQL server first:" -ForegroundColor Yellow
    Write-Host "  python graphql_server.py" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use: .\start-mcp-server.ps1 -StartGraphQL" -ForegroundColor Yellow
    exit 1
}

if (-not $McpOnly) {
    Write-Host ""
    Write-Host "[2/2] Starting MCP Server..." -ForegroundColor Yellow
}

# Set environment and run MCP
$env:ENDPOINT = $GraphQLEndpoint
npx -y mcp-graphql
