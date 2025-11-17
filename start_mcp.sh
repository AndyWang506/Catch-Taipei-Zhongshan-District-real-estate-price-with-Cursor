#!/bin/bash
# Start Google Maps MCP Server

# Load nvm (needed for mcp-google-map command)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Load environment variables from .zshrc if they're there
source ~/.zshrc 2>/dev/null || true

# Start the MCP server
echo "🚀 Starting Google Maps MCP Server..."
echo "📍 Server will run on http://localhost:3000"
echo ""

mcp-google-map --port 3000 --apikey "${GOOGLE_MAPS_API_KEY}"

