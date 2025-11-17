# Google Maps MCP Integration Setup Guide

This guide will help you set up the Google Maps MCP server integration with your DeepSeek chatbot.

## Quick Start

### 1. Prerequisites

- Node.js (v14 or higher) - [Download here](https://nodejs.org/)
- Python 3.10+ (already installed for this project)
- Google Cloud account with billing enabled

### 2. Install MCP Google Map Server

```bash
# Install globally
npm install -g @cablate/mcp-google-map

# Verify installation
mcp-google-map --help
```

### 3. Get Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Places API (New)** - Required for place searches
   - **Geocoding API** - For address/coordinate conversion
   - **Directions API** - For navigation directions
   - **Distance Matrix API** - For distance calculations
   - **Elevation API** - For elevation data (optional)
   - **Maps JavaScript API** - May be required for some features

4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key
   - (Recommended) Restrict the API key to only the APIs you need

### 4. Start the MCP Server

Open a new terminal window and run:

```bash
# Option 1: Pass API key as argument
mcp-google-map --port 3000 --apikey "YOUR_GOOGLE_MAPS_API_KEY"

# Option 2: Use environment variable
export GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"
mcp-google-map --port 3000
```

You should see output like:
```
🚀 MCP Google Map Server starting...
✅ Server running on http://localhost:3000
```

**Keep this terminal open** - the server needs to stay running.

### 5. Configure Your Python Project

Set environment variables (optional, defaults work for localhost):

```bash
# In your .env file or export in terminal
export MCP_SERVER_URL="http://localhost:3000"  # Default
export GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"  # Optional if passed to server
```

### 6. Test the Integration

```python
from app.chatbot_with_maps import MapsEnabledChatbot

# Initialize chatbot
chatbot = MapsEnabledChatbot()

# Test search
result = chatbot.search_nearby_places(
    location="San Francisco, CA",
    keyword="coffee",
    radius=2000
)
print(result)
```

## Usage Examples

### Basic Search

```python
from app.chatbot_with_maps import MapsEnabledChatbot

chatbot = MapsEnabledChatbot()

# Search for nearby places
results = chatbot.search_nearby_places(
    location="New York, NY",
    keyword="restaurant",
    radius=1000,
    min_rating=4.0,
    open_now=True
)
```

### Get Directions

```python
directions = chatbot.get_directions(
    origin="San Francisco, CA",
    destination="Los Angeles, CA",
    mode="driving"  # or "walking", "bicycling", "transit"
)
```

### Geocode Address

```python
# Convert address to coordinates
coords = chatbot.geocode_address("1600 Amphitheatre Parkway, Mountain View, CA")

# Convert coordinates to address
address = chatbot.maps.reverse_geocode(37.4219983, -122.084)
```

### Calculate Distance

```python
distance = chatbot.get_distance(
    origins=["San Francisco, CA"],
    destinations=["Los Angeles, CA", "San Diego, CA"],
    mode="driving"
)
```

### Chat with Automatic Maps

```python
# The chatbot will automatically detect location queries
response, usage = chatbot.send_text(
    "Find coffee shops near Times Square",
    use_maps=True
)
```

## Troubleshooting

### MCP Server Won't Start

- Check if port 3000 is already in use: `lsof -i :3000`
- Try a different port: `mcp-google-map --port 3001`
- Update `MCP_SERVER_URL` environment variable accordingly

### Connection Errors

- Verify the MCP server is running: `curl http://localhost:3000/mcp`
- Check firewall settings
- Ensure `MCP_SERVER_URL` matches the server address

### API Errors

- **403 Forbidden**: Enable Places API (New) in Google Cloud Console
- **400 Bad Request**: Check API key is valid
- **Quota Exceeded**: Check your Google Cloud billing and quotas

### Python Import Errors

- Ensure you're in the project directory
- Activate your virtual environment
- Install dependencies: `pip install -r requirements.txt`

## Advanced Configuration

### Custom MCP Server URL

If running the MCP server on a different machine or port:

```python
from app.chatbot_with_maps import MapsEnabledChatbot
from app.config import MCPSettings

settings = MCPSettings(
    url="http://your-server:3000",
    api_key="your-api-key"  # Optional if passed to server
)
chatbot = MapsEnabledChatbot(mcp_settings=settings)
```

### Disable Maps Features

```python
# Initialize without maps
chatbot = MapsEnabledChatbot(enable_maps=False)

# Or use the base chatbot
from app.chatbot import DeepSeekChatbot
chatbot = DeepSeekChatbot()
```

## Next Steps

- See `app/maps_example.py` for more examples
- Check the [MCP Google Map repository](https://github.com/cablate/mcp-google-map) for updates
- Explore the full API in `app/mcp_client.py`

