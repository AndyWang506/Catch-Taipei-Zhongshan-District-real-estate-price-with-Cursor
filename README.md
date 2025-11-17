# DeepSeek Multimodal Chatbot

This project shows how to build a Python chatbot that can reason over both text and images using the DeepSeek LLM API. It ships with a simple CLI example plus helper classes for managing prompts, multimodal payloads, and conversation state.

## 1. Prerequisites

- Python 3.10+
- A DeepSeek API key with access to the `deepseek-chat` (multimodal) model
- `pip install -r requirements.txt` *(see below)*

## 2. Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Export your DeepSeek credentials:

   ```bash
   export DEEPSEEK_API_KEY="Your_API_KEYS"
   # Optional overrides:
   # export DEEPSEEK_BASE_URL="https://api.deepseek.com"
   # export DEEPSEEK_CHAT_PATH="/chat/completions"
   ```

3. Run the sample CLI:

   ```bash
   python -m app.main "Summarize this sunset photo" --image ./examples/sunset.jpg --pretty
   ```

## 2.5. Google Maps Integration (Optional)

This project includes integration with the [Google Maps MCP server](https://github.com/cablate/mcp-google-map) for location-based queries.

### Setup Google Maps MCP Server

1. **Install Node.js** (if not already installed):
   ```bash
   # Check if Node.js is installed
   node --version
   ```

2. **Install the MCP Google Map server globally**:
   ```bash
   npm install -g @cablate/mcp-google-map
   ```

3. **Get a Google Maps API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project or select an existing one
   - Enable the following APIs:
     - Maps JavaScript API
     - Places API (New)
     - Geocoding API
     - Directions API
     - Distance Matrix API
     - Elevation API
   - Create credentials (API Key)
   - Restrict the API key for security (optional but recommended)

4. **Start the MCP server** (in a separate terminal):
   ```bash
   # Method 1: With API key as argument
   mcp-google-map --port 3000 --apikey "YOUR_GOOGLE_MAPS_API_KEY"
   
   # Method 2: With environment variable
   export GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"
   mcp-google-map --port 3000
   ```

5. **Configure environment variables** (optional):
   ```bash
   export MCP_SERVER_URL="http://localhost:3000"  # Default
   export GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"  # Optional, can be passed via header
   ```

### Using the Maps-Enabled Chatbot

```python
from app.chatbot_with_maps import MapsEnabledChatbot

# Initialize the maps-enabled chatbot
chatbot = MapsEnabledChatbot()

# Example 1: Search for nearby places
result = chatbot.search_nearby_places(
    location="San Francisco, CA",
    keyword="coffee",
    radius=2000,
)

# Example 2: Get directions
directions = chatbot.get_directions(
    origin="San Francisco, CA",
    destination="Los Angeles, CA",
    mode="driving",  # or "walking", "bicycling", "transit"
)

# Example 3: Chat with automatic maps integration
response, usage = chatbot.send_text(
    "Find coffee shops near San Francisco",
    use_maps=True,
)

# Example 4: Geocode an address
geocode_result = chatbot.geocode_address("1600 Amphitheatre Parkway, Mountain View, CA")

# Example 5: Calculate distance
distance = chatbot.get_distance(
    origins=["San Francisco, CA"],
    destinations=["Los Angeles, CA"],
    mode="driving",
)
```

### Available Google Maps Features

- **Search Nearby**: Find places near a location with filters (keyword, rating, type, etc.)
- **Place Details**: Get detailed information about a specific place
- **Geocoding**: Convert addresses to coordinates
- **Reverse Geocoding**: Convert coordinates to addresses
- **Directions**: Get turn-by-turn navigation directions
- **Distance Matrix**: Calculate distances and travel times between multiple locations
- **Elevation**: Get elevation data for locations

See `app/maps_example.py` for more examples.

## 2.6. Backend API Server

This project provides a **pure backend API** (no web UI) that integrates:
- **DeepSeek LLM** for natural language responses
- **Google Maps MCP** for location services  
- **Google Vertex AI** for price predictions

**Configured for**: https://zhongshan-dream-finder.lovable.app

Use this API with your **Lovable frontend** or any other client.

### Quick Start

1. **Start the MCP server** (Terminal 1):
   ```bash
   ./start_mcp.sh
   # Or manually:
   export GOOGLE_MAPS_API_KEY="your-key"
   mcp-google-map --port 3000
   ```

2. **Start the API server** (Terminal 2):
   ```bash
   ./start_web.sh
   # Or manually:
   export DEEPSEEK_API_KEY="your-key"
   python -m uvicorn app.api:app --reload --port 8000
   ```

3. **Test the API**:
   ```bash
   # Health check
   curl http://localhost:8000/health

   # Chat endpoint
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Find coffee shops near San Francisco", "use_maps": true}'

   # Price prediction
   curl -X POST http://localhost:8000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"address": "Zhongshan District, Taipei, Taiwan", "sq_meters": 40}'
   ```

4. **View API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### API Endpoints

- **GET** `/health` - Health check
- **POST** `/api/chat` - DeepSeek LLM + Google Maps integration
- **POST** `/api/predict` - Price prediction (Vertex AI or heuristic fallback)

See `API_DOCS.md` for complete API documentation and integration examples.

## 3. Project Structure

- `app/config.py` – loads and validates environment variables.
- `app/deepseek_client.py` – converts text + images into the JSON payload expected by DeepSeek and issues HTTP requests.
- `app/chatbot.py` – maintains conversation history and offers convenience methods for text-only or multimodal turns.
- `app/main.py` – minimal CLI wrapper so you can try the chatbot locally.
- `app/mcp_client.py` – client for communicating with the Google Maps MCP server.
- `app/chatbot_with_maps.py` – enhanced chatbot with Google Maps integration.
- `app/maps_example.py` – example usage of the maps-enabled chatbot.
- `app/api.py` – FastAPI backend API (pure REST, no UI) for DeepSeek + Maps + Vertex AI.
- `app/vertex_client.py` – Client wrapper for Google Vertex AI predictions.

## 2.7. Vertex AI Integration (Optional)

You can swap the price heuristic for your trained Vertex AI model with zero code changes in your frontend.

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables (server terminal):
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export VERTEX_LOCATION="us-central1"         # or your region
   # choose ONE:
   export VERTEX_ENDPOINT_ID="xxxxxxxxxxxx"     # deployed Endpoint ID
   # OR
   export VERTEX_MODEL_NAME="projects/xxx/locations/yyy/models/zzz"

   # Vertex credentials
   export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/service-account.json"
   ```
3. Start servers:
   ```bash
   # MCP server (Google Maps)
   export GOOGLE_MAPS_API_KEY="..."
   mcp-google-map --port 3000

   # Backend API (DeepSeek key also required)
   export DEEPSEEK_API_KEY="..."
   python -m uvicorn app.api:app --reload --port 8000
   ```
4. Behavior:
   - If `VERTEX_ENDPOINT_ID` or `VERTEX_MODEL_NAME` is set, `/api/predict` will call Vertex AI.
   - Otherwise it falls back to a heuristic forecast so the app still works.

## 4. Multi-Agent Orchestration

To extend the chatbot with specialised multi-agent behaviour:

- **Planner Agent**: interprets the user’s high-level goal and decomposes it into steps. Uses the chatbot to gather missing info.
- **Specialist Agents**: each agent owns a type of task (e.g. `Vision Analyst`, `Researcher`, `Coder`) and receives sub-prompts from the planner. They call the chatbot with task-specific system prompts.
- **Controller / Orchestrator**: manages the workflow, decides which agent should act next, and aggregates their outputs into a final reply.

You can build this controller with frameworks like Haystack Agents, LangGraph, or a custom Python loop. A sketch using plain Python:

```python
from app.chatbot import DeepSeekChatbot

planner = DeepSeekChatbot(system_prompt="You plan and assign tasks to specialists.")
vision = DeepSeekChatbot(system_prompt="You describe and interpret images in detail.")
researcher = DeepSeekChatbot(system_prompt="You fetch and summarise background knowledge.")

def solve(task, images=None):
    plan, _ = planner.send_text(f"Task: {task}\nReturn numbered steps.")
    steps = plan.splitlines()
    results = []
    for step in steps:
        if "image" in step.lower():
            result, _ = vision.send_with_images(step, image_paths=images or [])
        else:
            result, _ = researcher.send_text(step)
        results.append(result)
    final_answer, _ = planner.send_text(
        f"Task: {task}\nSteps:\n{plan}\nResults:\n" + "\n".join(results)
    )
    return final_answer
```

Key ideas:

- **Shared context**: pass summaries between agents so they stay aligned without sharing the full token history.
- **Guard rails**: add system prompts that constrain each agent’s behaviour; enforce validation on their outputs.
- **Tool use**: agents can call external tools (search, code exec) before reporting back, letting you automate complex tasks.

## 5. Extending the Chatbot

- Build a REST API (e.g. FastAPI) that wraps `DeepSeekChatbot`.
- Add streaming responses by switching to the DeepSeek streaming endpoint.
- Persist conversation history in a database or vector store for long-term memory.
- Integrate voice and camera inputs to capture multimodal prompts dynamically.

## 6. Requirements File

Create `requirements.txt` with:

```
requests>=2.32.3
python-dotenv>=1.0.1
```

(`python-dotenv` is optional but handy if you prefer loading secrets from a `.env` file.)

## 7. Troubleshooting

- `MissingAPIKeyError`: ensure `DEEPSEEK_API_KEY` is exported in your shell or stored via `.env`.
- 401/403 errors: verify the key has permission for the model you selected.
- 415 or 422 errors: confirm images are readable files, and their MIME types are supported (`jpeg`, `png`, `webp`, etc.).
- **MCP Server Connection Issues**: 
  - Ensure the MCP server is running on the configured port (default: 3000)
  - Check that `MCP_SERVER_URL` matches the server's address
  - Verify the Google Maps API key is valid and has the required APIs enabled
  - Check server logs for detailed error messages
- **Google Maps API Errors**: 
  - Ensure Places API (New) is enabled in Google Cloud Console
  - Verify API key restrictions allow requests from your IP/domain
  - Check API quotas and billing status

Happy building!


