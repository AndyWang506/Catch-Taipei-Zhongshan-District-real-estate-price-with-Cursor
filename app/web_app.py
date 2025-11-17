"""
Minimal FastAPI web UI for the DeepSeek + Google Maps chatbot.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .chatbot_with_maps import MapsEnabledChatbot
from fastapi.middleware.cors import CORSMiddleware
import os
from .vertex_client import vertex_predict


app = FastAPI(
    title="DeepSeek Maps Chatbot",
    description="Chatbot that blends DeepSeek responses with Google Maps MCP tools.",
)

# Instantiate a single chatbot instance to reuse across requests.
chatbot = MapsEnabledChatbot()

_recent_predictions: list[dict] = []

# CORS for integrating external frontends (e.g., Lovable)
# For production, replace '*' with your exact Lovable domain(s), e.g.:
# allowed_origins = ["https://your-lovable-site.web.app"]
allowed_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str
    use_maps: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    usage: Dict[str, Any]

class PredictRequest(BaseModel):
    address: str
    building_name: Optional[str] = None
    sq_meters: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = "apartment"
    year_built: Optional[int] = None
    use_maps: bool = True

class PredictResponse(BaseModel):
    normalized_address: str
    lat: float
    lng: float
    monthly_forecast_twd: Dict[str, float]
    current_estimate_twd: float
    next_year_estimate_twd: float
    ci90_twd: Dict[str, float]
    assumptions: Dict[str, Any]
    nearby_context: Optional[Dict[str, Any]] = None
    recent: list[dict]


@app.get("/health")
async def health() -> Dict[str, str]:
    """
    Simple health check endpoint.
    """

    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """
    Serve a minimal HTML interface for chatting.
    """

    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>DeepSeek Maps + Pricing</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
    header { background: #111827; color: white; padding: 1.5rem; }
    header h1 { margin: 0; font-size: 1.8rem; }
    header p { margin: 0.2rem 0 0; opacity: 0.8; }
    main { max-width: 720px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
    nav { display: flex; gap: 1rem; margin-bottom: 1rem; }
    nav button { background: #e5e7eb; color: #111827; border: none; padding: 0.6rem 1rem; border-radius: 8px; cursor: pointer; }
    nav button.active { background: #2563eb; color: white; }
    textarea { width: 100%; min-height: 120px; padding: 1rem; border-radius: 8px; border: 1px solid #d1d5db; font-size: 1rem; resize: vertical; }
    input, select { width: 100%; padding: 0.7rem; border-radius: 8px; border: 1px solid #d1d5db; font-size: 1rem; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
    .controls { margin: 1rem 0; display: flex; align-items: center; gap: 0.5rem; }
    button.primary { background: #2563eb; color: white; border: none; padding: 0.8rem 1.6rem; border-radius: 8px; font-size: 1rem; cursor: pointer; }
    button.secondary { background: #e5e7eb; color: #111827; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; cursor: pointer; }
    button:disabled { background: #9ca3af; cursor: not-allowed; }
    pre { background: #111827; color: #e5e7eb; padding: 1rem; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
    .status { margin-top: 0.5rem; font-size: 0.9rem; color: #6b7280; }
    .card { border: 1px solid #e5e7eb; padding: 1rem; border-radius: 10px; }
    .muted { color: #6b7280; font-size: 0.9rem; }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>
  <header>
    <h1>DeepSeek Maps Chat + Price Predictor</h1>
    <p>Ask location-aware questions, or estimate next-year home prices for Zhongshan District.</p>
  </header>
  <main>
    <nav>
      <button id="tabChat" class="active">Chat</button>
      <button id="tabPredict">Price Prediction</button>
    </nav>

    <section id="panelChat">
      <label for="prompt">Prompt</label>
      <textarea id="prompt" placeholder="Type your question..."></textarea>
      <div class="controls">
        <label><input type="checkbox" id="useMaps" checked /> Use Google Maps tools automatically</label>
      </div>
      <button class="primary" id="sendBtn">Send</button>
      <div class="status" id="status"></div>
      <h3>Response</h3>
      <pre id="response"></pre>
    </section>

    <section id="panelPredict" style="display:none">
      <div class="card">
        <div class="row">
          <div>
            <label>Building name (optional)</label>
            <input id="bName" placeholder="e.g., Taipei 101" />
          </div>
          <div>
            <label>Address</label>
            <input id="addr" placeholder="e.g., Zhongshan District, Taipei, Taiwan" />
          </div>
        </div>
        <div class="row" style="margin-top:0.8rem">
          <div>
            <label>Size (m²)</label>
            <input id="sqm" type="number" min="5" step="1" placeholder="e.g., 40" />
          </div>
          <div>
            <label>Property type</label>
            <select id="ptype">
              <option value="apartment" selected>Apartment</option>
              <option value="condo">Condo</option>
              <option value="house">House</option>
              <option value="studio">Studio</option>
            </select>
          </div>
        </div>
        <div class="row" style="margin-top:0.8rem">
          <div>
            <label>Bedrooms</label>
            <input id="beds" type="number" min="0" step="1" placeholder="e.g., 2" />
          </div>
          <div>
            <label>Bathrooms</label>
            <input id="baths" type="number" min="0" step="1" placeholder="e.g., 1" />
          </div>
        </div>
        <div class="row" style="margin-top:0.8rem">
          <div>
            <label>Year built (optional)</label>
            <input id="yBuilt" type="number" min="1950" max="2100" step="1" placeholder="e.g., 2005" />
          </div>
          <div class="muted" style="display:flex; align-items:flex-end">
            Focus area: Zhongshan District, Taipei, Taiwan
          </div>
        </div>
        <div class="controls">
          <button class="primary" id="predictBtn">Predict next 12 months</button>
          <button class="secondary" id="clearBtn">Clear</button>
          <span id="pStatus" class="status"></span>
        </div>
      </div>

      <div style="margin-top:1rem">
        <canvas id="chart" height="120"></canvas>
      </div>
      <div id="summary" class="card" style="margin-top:1rem"></div>
      <div id="recent" class="card" style="margin-top:1rem"></div>
    </section>
  </main>
  <script>
    // Tabs
    const tabChat = document.getElementById('tabChat');
    const tabPredict = document.getElementById('tabPredict');
    const panelChat = document.getElementById('panelChat');
    const panelPredict = document.getElementById('panelPredict');
    tabChat.addEventListener('click', () => {
      tabChat.classList.add('active'); tabPredict.classList.remove('active');
      panelChat.style.display = ''; panelPredict.style.display = 'none';
    });
    tabPredict.addEventListener('click', () => {
      tabPredict.classList.add('active'); tabChat.classList.remove('active');
      panelPredict.style.display = ''; panelChat.style.display = 'none';
    });

    // Chat
    const promptEl = document.getElementById('prompt');
    const useMapsEl = document.getElementById('useMaps');
    const sendBtn = document.getElementById('sendBtn');
    const responseEl = document.getElementById('response');
    const statusEl = document.getElementById('status');

    async function sendPrompt() {
      const prompt = promptEl.value.trim();
      if (!prompt) {
        statusEl.textContent = 'Please enter a prompt.';
        return;
      }

      sendBtn.disabled = true;
      statusEl.textContent = 'Thinking...';
      responseEl.textContent = '';

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt,
            use_maps: useMapsEl.checked,
          }),
        });

        if (!res.ok) {
          throw new Error(`Request failed with status ${res.status}`);
        }

        const data = await res.json();
        responseEl.textContent = data.answer || '(No answer returned)';
        statusEl.textContent = 'Done.';
      } catch (err) {
        responseEl.textContent = '';
        statusEl.textContent = `Error: ${err.message}`;
      } finally {
        sendBtn.disabled = false;
      }
    }

    sendBtn.addEventListener('click', sendPrompt);
    promptEl.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        sendPrompt();
      }
    });

    // Prediction
    let chart;
    const bName = document.getElementById('bName');
    const addr = document.getElementById('addr');
    const sqm = document.getElementById('sqm');
    const ptype = document.getElementById('ptype');
    const beds = document.getElementById('beds');
    const baths = document.getElementById('baths');
    const yBuilt = document.getElementById('yBuilt');
    const predictBtn = document.getElementById('predictBtn');
    const clearBtn = document.getElementById('clearBtn');
    const pStatus = document.getElementById('pStatus');
    const summary = document.getElementById('summary');
    const recent = document.getElementById('recent');

    function renderChart(series) {
      const labels = Object.keys(series);
      const values = Object.values(series);
      const ctx = document.getElementById('chart').getContext('2d');
      if (chart) chart.destroy();
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Estimated price (TWD)',
            data: values,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37,99,235,0.15)',
            tension: 0.25,
            fill: true,
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: false, ticks: { callback: (v)=> v.toLocaleString() } }
          }
        }
      });
    }

    function renderRecent(items) {
      if (!items || !items.length) {
        recent.innerHTML = '<div class="muted">No recent predictions yet.</div>';
        return;
      }
      const html = items.map(x => {
        return '<div style="margin:.4rem 0"><strong>' + x.normalized_address +
          '</strong> — current ' + x.current_estimate_twd.toLocaleString() + ' TWD, next year ' +
          x.next_year_estimate_twd.toLocaleString() + ' TWD</div>';
      }).join('');
      recent.innerHTML = '<h4>Recent</h4>' + html;
    }

    async function predict() {
      const payload = {
        address: addr.value,
        building_name: bName.value || null,
        sq_meters: sqm.value ? Number(sqm.value) : null,
        bedrooms: beds.value ? Number(beds.value) : null,
        bathrooms: baths.value ? Number(baths.value) : null,
        property_type: ptype.value || 'apartment',
        year_built: yBuilt.value ? Number(yBuilt.value) : null,
        use_maps: true,
      };
      pStatus.textContent = 'Estimating...';
      try {
        const res = await fetch('/api/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('Request failed: ' + res.status);
        const data = await res.json();
        renderChart(data.monthly_forecast_twd);
        renderRecent(data.recent);
        summary.innerHTML = '<h4>Summary</h4>' +
          '<div><strong>Address:</strong> ' + data.normalized_address + '</div>' +
          '<div><strong>Current estimate:</strong> ' + data.current_estimate_twd.toLocaleString() + ' TWD</div>' +
          '<div><strong>Next-year estimate:</strong> ' + data.next_year_estimate_twd.toLocaleString() + ' TWD</div>' +
          '<div class="muted">Assumptions: ' + JSON.stringify(data.assumptions) + '</div>';
        pStatus.textContent = 'Done.';
      } catch (e) {
        pStatus.textContent = 'Error: ' + e.message;
      }
    }

    predictBtn.addEventListener('click', predict);
    clearBtn.addEventListener('click', () => {
      bName.value = ''; addr.value = ''; sqm.value=''; beds.value=''; baths.value=''; yBuilt.value='';
      summary.innerHTML=''; pStatus.textContent=''; renderChart({});
    });
  </script>
</body>
</html>
    """


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Handle chat requests by delegating to the MapsEnabledChatbot.
    """

    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt cannot be empty.")

    try:
        answer, usage = chatbot.send_text(
            prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_maps=request.use_maps,
        )
    except Exception as exc:  # pragma: no cover - surface errors to client
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(answer=answer, usage=usage or {})

@app.post("/api/predict", response_model=PredictResponse)
async def predict_endpoint(request: PredictRequest) -> PredictResponse:
    """
    Very lightweight price prediction for Zhongshan District properties.
    - Geocodes the address via MCP to validate the location and get lat/lng.
    - Uses a simple heuristic to estimate current price and 12-month forecast.
    - Returns a recent-history list for UX continuity.
    """

    addr = request.address.strip()
    if not addr:
        raise HTTPException(status_code=422, detail="Address is required.")

    # 1) Geocode address via MCP
    try:
        geo = chatbot.geocode_address(addr)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {exc}") from exc

    content = geo.get("content")
    text_blob = ""
    if isinstance(content, list) and content:
        text_blob = content[0].get("text", "")
    elif isinstance(content, str):
        text_blob = content
    if not text_blob:
        raise HTTPException(status_code=404, detail="No geocoding results.")

    try:
        data = json.loads(text_blob)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Bad geocode payload.") from exc
    results = data.get("results") or []
    if not results:
        raise HTTPException(status_code=404, detail="Address not found.")
    top = results[0]
    normalized = top.get("formatted_address") or addr
    geometry = top.get("geometry") or {}
    loc = geometry.get("location") or {}
    lat = float(loc.get("lat", 0.0))
    lng = float(loc.get("lng", 0.0))

    # 2) Heuristic pricing (placeholder until model is integrated)
    # Base price per m^2 for Zhongshan (illustrative only; not financial advice)
    base_psm = 280_000.0
    # Adjust by property type
    type_adj = {
        "apartment": 1.0,
        "condo": 1.05,
        "house": 1.15,
        "studio": 0.95,
    }.get((request.property_type or "apartment").lower(), 1.0)
    # Size scaling (smaller units often higher per m^2)
    size = request.sq_meters or 35.0
    size_adj = 1.1 if size < 25 else (1.05 if size < 40 else (1.0 if size < 60 else 0.95))
    # Bedroom/bathroom small adders
    bed_adj = 1.0 + 0.02 * (request.bedrooms or 0)
    bath_adj = 1.0 + 0.015 * (request.bathrooms or 0)
    # Age discount (very rough)
    age_adj = 1.0
    if request.year_built:
        age = max(0, 2025 - request.year_built)
        age_adj = max(0.85, 1.0 - 0.005 * (age // 5))

    psm = base_psm * type_adj * size_adj * bed_adj * bath_adj * age_adj
    current = psm * size
    # Growth assumption next 12 months (5%) with light seasonality
    growth = 0.05
    monthly = {}
    running = current
    for m in range(1, 13):
        seasonal = 1.0 + 0.01 * (0.5 if m in (6,7,8) else (-0.3 if m in (1,2) else 0))
        running = running * (1.0 + growth/12) * seasonal
        monthly[f"Month {m}"] = round(running, 0)
    next_year = list(monthly.values())[-1] if monthly else current
    ci = {"low": round(next_year * 0.9, 0), "high": round(next_year * 1.1, 0)}

    # Try Vertex AI if configured
    try:
        if os.getenv("VERTEX_ENDPOINT_ID") or os.getenv("VERTEX_MODEL_NAME"):
            instances = [{
                "address": normalized,
                "district": "Zhongshan",
                "city": "Taipei",
                "country": "Taiwan",
                "lat": lat,
                "lng": lng,
                "sq_meters": size,
                "bedrooms": request.bedrooms or 0,
                "bathrooms": request.bathrooms or 0,
                "property_type": (request.property_type or "apartment"),
                "year_built": request.year_built or 0,
            }]
            out = vertex_predict(instances, parameters={"horizon_months": 12})
            # Expecting model to return either a series or point estimate(s).
            preds = out.get("predictions") or []
            if preds:
                p = preds[0]
                # Flexible mapping: accept either keys or fallback to heuristic ones.
                monthly_v = p.get("monthly_forecast_twd")
                current_v = p.get("current_estimate_twd")
                next_year_v = p.get("next_year_estimate_twd")
                if isinstance(monthly_v, dict) and current_v and next_year_v:
                    monthly = {k: float(v) for k, v in monthly_v.items()}
                    current = float(current_v)
                    next_year = float(next_year_v)
                    ci = {
                        "low": float(p.get("ci90_low_twd", next_year * 0.9)),
                        "high": float(p.get("ci90_high_twd", next_year * 1.1)),
                    }
    except Exception:
        # Silent fallback to heuristic if Vertex fails
        pass

    # 3) Nearby context (optional): fetch a couple of POIs for color
    nearby_ctx = None
    try:
        nearby = chatbot.maps.search_nearby(location=f"{lat},{lng}", radius=1000, keyword="mall") if chatbot.maps else None
        nearby_ctx = {"raw": nearby}
    except Exception:
        nearby_ctx = None

    record = {
        "normalized_address": normalized,
        "current_estimate_twd": round(current, 0),
        "next_year_estimate_twd": round(next_year, 0),
    }
    _recent_predictions.insert(0, record)
    _recent_predictions[:] = _recent_predictions[:5]

    return PredictResponse(
        normalized_address=normalized,
        lat=lat,
        lng=lng,
        monthly_forecast_twd=monthly,
        current_estimate_twd=round(current, 0),
        next_year_estimate_twd=round(next_year, 0),
        ci90_twd=ci,
        assumptions={
            "base_psm_twd": base_psm,
            "type_adjustment": type_adj,
            "size_adjustment": size_adj,
            "bedrooms": request.bedrooms,
            "bathrooms": request.bathrooms,
            "age_adjustment": age_adj,
            "growth_rate_annual": growth,
        },
        nearby_context=nearby_ctx,
        recent=_recent_predictions,
    )

