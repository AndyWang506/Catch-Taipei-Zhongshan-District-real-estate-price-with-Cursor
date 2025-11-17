/**
 * Production-ready integration for zhongshan-dream-finder.lovable.app
 * Copy this into your Lovable project
 */

// ============================================
// CONFIGURATION
// ============================================
// Set this in your Lovable project's environment variables
// For local dev: http://localhost:8000
// For production: your deployed backend URL (e.g., https://your-api.railway.app)
const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (process.env.NODE_ENV === 'production' 
    ? 'https://your-backend-api.com'  // TODO: Replace with your actual deployed backend URL
    : 'http://localhost:8000');

// ============================================
// API FUNCTIONS
// ============================================

/**
 * Send a chat message to DeepSeek LLM with Google Maps integration
 */
export async function sendChat(prompt, useMaps = true) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: prompt.trim(),
        use_maps: useMaps,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    return {
      answer: data.answer,
      usage: data.usage,
    };
  } catch (error) {
    console.error('Chat API error:', error);
    throw error;
  }
}

/**
 * Get price prediction for a property
 */
export async function getPricePrediction(params) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        address: params.address,
        building_name: params.buildingName || null,
        sq_meters: params.sqMeters || null,
        bedrooms: params.bedrooms || null,
        bathrooms: params.bathrooms || null,
        property_type: params.propertyType || 'apartment',
        year_built: params.yearBuilt || null,
        use_maps: true,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    return {
      address: data.normalized_address,
      location: {
        lat: data.lat,
        lng: data.lng,
      },
      currentPrice: data.current_estimate_twd,
      nextYearPrice: data.next_year_estimate_twd,
      monthlyForecast: data.monthly_forecast_twd,
      confidenceInterval: data.ci90_twd,
      assumptions: data.assumptions,
      nearbyContext: data.nearby_context,
      recentPredictions: data.recent,
    };
  } catch (error) {
    console.error('Prediction API error:', error);
    throw error;
  }
}

/**
 * Check if the API is running
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    return data.status === 'ok';
  } catch (error) {
    return false;
  }
}

// ============================================
// REACT HOOKS
// ============================================

import { useState } from 'react';

/**
 * React hook for chat functionality
 */
export function useChat() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  const sendMessage = async (prompt, useMaps = true) => {
    setLoading(true);
    setError(null);
    try {
      const result = await sendChat(prompt, useMaps);
      setResponse(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clear = () => {
    setResponse(null);
    setError(null);
  };

  return { sendMessage, loading, error, response, clear };
}

/**
 * React hook for price predictions
 */
export function usePricePrediction() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [prediction, setPrediction] = useState(null);

  const predict = async (params) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getPricePrediction(params);
      setPrediction(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clear = () => {
    setPrediction(null);
    setError(null);
  };

  return { predict, loading, error, prediction, clear };
}

