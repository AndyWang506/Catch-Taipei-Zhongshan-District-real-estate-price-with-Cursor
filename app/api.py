"""
Backend API for DeepSeek LLM + Google Maps MCP + Vertex AI integration.
This is a pure REST API backend - no web UI. Use with your Lovable frontend.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .chatbot_with_maps import MapsEnabledChatbot
from .vertex_client import vertex_predict

app = FastAPI(
    title="DeepSeek Maps + Vertex AI API",
    description="Backend API: DeepSeek LLM with Google Maps MCP tools and Vertex AI price predictions.",
    version="1.0.0",
)

# Instantiate chatbot instance (reused across requests)
chatbot = MapsEnabledChatbot()

# In-memory recent predictions (in production, use a database)
_recent_predictions: list[dict] = []

# CORS configuration - allow your Lovable frontend
# Set ALLOWED_ORIGINS env var for production, e.g.:
# export ALLOWED_ORIGINS="https://your-lovable-site.web.app,https://your-domain.com"
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "https://zhongshan-dream-finder.lovable.app")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")] if allowed_origins_str != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    prompt: str
    use_maps: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[float] = None


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


# API Endpoints
@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "DeepSeek Maps + Vertex AI API"}


@app.get("/")
async def root() -> Dict[str, str]:
    """API root - returns API info."""
    return {
        "name": "DeepSeek Maps + Vertex AI API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "predict": "/api/predict",
            "docs": "/docs",
        },
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint: DeepSeek LLM with optional Google Maps integration.
    
    - Uses DeepSeek to generate responses
    - Automatically calls Google Maps MCP tools when location queries are detected
    - Returns the LLM's answer with usage statistics
    """
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt cannot be empty.")

    try:
        answer, usage = chatbot.send_text(
            prompt,
            temperature=request.temperature,
            max_tokens=int(request.max_tokens) if request.max_tokens else None,
            use_maps=request.use_maps,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(answer=answer, usage=usage or {})


@app.post("/api/predict", response_model=PredictResponse)
async def predict_endpoint(request: PredictRequest) -> PredictResponse:
    """
    Price prediction endpoint: Uses Vertex AI model (if configured) or heuristic fallback.
    
    - Geocodes address via Google Maps MCP
    - Calls Vertex AI model for predictions (if VERTEX_ENDPOINT_ID or VERTEX_MODEL_NAME is set)
    - Falls back to heuristic pricing if Vertex AI is not available
    - Returns 12-month forecast, current/next-year estimates, and confidence intervals
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

    # 2) Heuristic pricing (fallback if Vertex AI not available)
    base_psm = 280_000.0
    type_adj = {
        "apartment": 1.0,
        "condo": 1.05,
        "house": 1.15,
        "studio": 0.95,
    }.get((request.property_type or "apartment").lower(), 1.0)
    size = request.sq_meters or 35.0
    size_adj = 1.1 if size < 25 else (1.05 if size < 40 else (1.0 if size < 60 else 0.95))
    bed_adj = 1.0 + 0.02 * (request.bedrooms or 0)
    bath_adj = 1.0 + 0.015 * (request.bathrooms or 0)
    age_adj = 1.0
    if request.year_built:
        age = max(0, 2025 - request.year_built)
        age_adj = max(0.85, 1.0 - 0.005 * (age // 5))

    psm = base_psm * type_adj * size_adj * bed_adj * bath_adj * age_adj
    current = psm * size
    growth = 0.05
    monthly = {}
    running = current
    for m in range(1, 13):
        seasonal = 1.0 + 0.01 * (0.5 if m in (6, 7, 8) else (-0.3 if m in (1, 2) else 0))
        running = running * (1.0 + growth / 12) * seasonal
        monthly[f"Month {m}"] = round(running, 0)
    next_year = list(monthly.values())[-1] if monthly else current
    ci = {"low": round(next_year * 0.9, 0), "high": round(next_year * 1.1, 0)}

    # 3) Try Vertex AI if configured
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
            preds = out.get("predictions") or []
            if preds:
                p = preds[0]
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

    # 4) Nearby context (optional)
    nearby_ctx = None
    try:
        if chatbot.maps:
            nearby = chatbot.maps.search_nearby(location=f"{lat},{lng}", radius=1000, keyword="mall")
            nearby_ctx = {"raw": nearby}
    except Exception:
        nearby_ctx = None

    # 5) Store in recent history
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
            "using_vertex_ai": bool(os.getenv("VERTEX_ENDPOINT_ID") or os.getenv("VERTEX_MODEL_NAME")),
        },
        nearby_context=nearby_ctx,
        recent=_recent_predictions,
    )

