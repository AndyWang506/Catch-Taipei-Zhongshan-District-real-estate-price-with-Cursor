# API Documentation

This is a pure backend API that integrates:
- **DeepSeek LLM** for natural language responses
- **Google Maps MCP** for location services
- **Google Vertex AI** for price predictions

Use this API with your Lovable frontend.

## Base URL

- **Local development**: `http://localhost:8000`
- **Production**: Your deployed backend URL

## Authentication

No authentication required for local development. For production, add API keys or JWT tokens as needed.

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "service": "DeepSeek Maps + Vertex AI API"
}
```

---

### 2. Chat (DeepSeek + Maps)

**POST** `/api/chat`

Send a natural language prompt. The API will:
- Use DeepSeek LLM to generate a response
- Automatically call Google Maps tools when location queries are detected
- Return the answer with usage statistics

**Request Body:**
```json
{
  "prompt": "Find coffee shops near San Francisco",
  "use_maps": true,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "answer": "Here are some coffee shops near San Francisco...",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 120,
    "total_tokens": 135
  }
}
```

**Example (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'Find malls near Taipei',
    use_maps: true
  })
});
const data = await response.json();
console.log(data.answer);
```

---

### 3. Price Prediction (Vertex AI)

**POST** `/api/predict`

Predict property prices for the next 12 months. Uses Vertex AI model if configured, otherwise falls back to heuristic pricing.

**Request Body:**
```json
{
  "address": "Zhongshan District, Taipei, Taiwan",
  "building_name": "Optional building name",
  "sq_meters": 40,
  "bedrooms": 2,
  "bathrooms": 1,
  "property_type": "apartment",
  "year_built": 2005,
  "use_maps": true
}
```

**Response:**
```json
{
  "normalized_address": "Zhongshan District, Taipei City, Taiwan",
  "lat": 25.0522,
  "lng": 121.5200,
  "monthly_forecast_twd": {
    "Month 1": 11200000,
    "Month 2": 11250000,
    ...
    "Month 12": 11760000
  },
  "current_estimate_twd": 11200000,
  "next_year_estimate_twd": 11760000,
  "ci90_twd": {
    "low": 10584000,
    "high": 12936000
  },
  "assumptions": {
    "base_psm_twd": 280000,
    "type_adjustment": 1.0,
    "size_adjustment": 1.05,
    "bedrooms": 2,
    "bathrooms": 1,
    "age_adjustment": 0.96,
    "growth_rate_annual": 0.05,
    "using_vertex_ai": true
  },
  "nearby_context": {
    "raw": { ... }
  },
  "recent": [
    {
      "normalized_address": "...",
      "current_estimate_twd": 11200000,
      "next_year_estimate_twd": 11760000
    }
  ]
}
```

**Example (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/api/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: 'Zhongshan District, Taipei, Taiwan',
    sq_meters: 40,
    bedrooms: 2,
    bathrooms: 1,
    property_type: 'apartment'
  })
});
const data = await response.json();

// Display chart
const labels = Object.keys(data.monthly_forecast_twd);
const values = Object.values(data.monthly_forecast_twd);
// Use Chart.js or your preferred charting library
```

---

## CORS Configuration

For production, set the `ALLOWED_ORIGINS` environment variable:

```bash
export ALLOWED_ORIGINS="https://your-lovable-site.web.app,https://your-domain.com"
```

This restricts API access to your frontend domains only.

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Server Error

Error response format:
```json
{
  "detail": "Error message here"
}
```

---

## Interactive API Docs

FastAPI automatically generates interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Visit these URLs to explore and test the API endpoints directly in your browser.

---

## Integration with Lovable

1. **Set your backend URL** in your Lovable project:
   ```javascript
   const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
   ```

2. **Call the endpoints** from your frontend:
   ```javascript
   // Chat
   const chatResponse = await fetch(`${API_BASE_URL}/api/chat`, {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ prompt: userInput, use_maps: true })
   });

   // Predict
   const predictResponse = await fetch(`${API_BASE_URL}/api/predict`, {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify(predictionFormData)
   });
   ```

3. **Handle responses** and display in your UI (charts, tables, etc.)

---

## Environment Variables

Required for the backend to work:

```bash
# DeepSeek
export DEEPSEEK_API_KEY="your-deepseek-key"

# Google Maps MCP (set when starting MCP server)
export GOOGLE_MAPS_API_KEY="your-google-maps-key"

# Vertex AI (optional - for price predictions)
export GOOGLE_CLOUD_PROJECT="your-project-id"
export VERTEX_LOCATION="us-central1"
export VERTEX_ENDPOINT_ID="your-endpoint-id"  # or VERTEX_MODEL_NAME
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# CORS (for production)
export ALLOWED_ORIGINS="https://your-frontend-domain.com"
```

