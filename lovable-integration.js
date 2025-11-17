/**
 * Ready-to-use integration code for your Lovable frontend
 * Copy this into your Lovable project
 */

// ============================================
// CONFIGURATION
// ============================================
// For production, this should be your deployed backend URL
// For local development, use http://localhost:8000
const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (window.location.hostname === 'zhongshan-dream-finder.lovable.app' 
    ? 'https://your-backend-api.com'  // TODO: Replace with your deployed backend URL
    : 'http://localhost:8000');

// ============================================
// API FUNCTIONS
// ============================================

/**
 * Send a chat message to DeepSeek LLM with Google Maps integration
 * @param {string} prompt - User's question/prompt
 * @param {boolean} useMaps - Whether to use Google Maps tools (default: true)
 * @returns {Promise<{answer: string, usage: object}>}
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
      const error = await response.json();
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
 * @param {object} params - Prediction parameters
 * @param {string} params.address - Property address (required)
 * @param {string} [params.buildingName] - Optional building name
 * @param {number} [params.sqMeters] - Size in square meters
 * @param {number} [params.bedrooms] - Number of bedrooms
 * @param {number} [params.bathrooms] - Number of bathrooms
 * @param {string} [params.propertyType] - Type: "apartment", "condo", "house", "studio"
 * @param {number} [params.yearBuilt] - Year the property was built
 * @returns {Promise<object>} Prediction results with forecast, estimates, etc.
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
      const error = await response.json();
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
      monthlyForecast: data.monthly_forecast_twd, // Object with "Month 1", "Month 2", etc.
      confidenceInterval: data.ci90_twd, // { low, high }
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
 * @returns {Promise<boolean>}
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
// REACT HOOKS (for Lovable React components)
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

  return { sendMessage, loading, error, response };
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

  return { predict, loading, error, prediction };
}

// ============================================
// EXAMPLE USAGE IN LOVABLE COMPONENTS
// ============================================

/*
// Example 1: Simple Chat Component
import { useChat } from './lovable-integration';

function ChatComponent() {
  const { sendMessage, loading, error, response } = useChat();
  const [input, setInput] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    await sendMessage(input);
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input 
          value={input} 
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about locations..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
      {error && <div style={{color: 'red'}}>{error}</div>}
      {response && <div>{response.answer}</div>}
    </div>
  );
}

// Example 2: Price Prediction Component
import { usePricePrediction } from './lovable-integration';
import { Line } from 'react-chartjs-2'; // or your chart library

function PricePredictionComponent() {
  const { predict, loading, error, prediction } = usePricePrediction();
  const [formData, setFormData] = useState({
    address: '',
    sqMeters: '',
    bedrooms: '',
    bathrooms: '',
  });

  const handlePredict = async () => {
    await predict({
      address: formData.address,
      sqMeters: parseFloat(formData.sqMeters),
      bedrooms: parseInt(formData.bedrooms),
      bathrooms: parseInt(formData.bathrooms),
      propertyType: 'apartment',
    });
  };

  return (
    <div>
      <input
        placeholder="Address"
        value={formData.address}
        onChange={(e) => setFormData({...formData, address: e.target.value})}
      />
      <input
        type="number"
        placeholder="Size (m²)"
        value={formData.sqMeters}
        onChange={(e) => setFormData({...formData, sqMeters: e.target.value})}
      />
      <button onClick={handlePredict} disabled={loading}>
        {loading ? 'Predicting...' : 'Get Prediction'}
      </button>
      
      {error && <div style={{color: 'red'}}>{error}</div>}
      
      {prediction && (
        <div>
          <h3>{prediction.address}</h3>
          <p>Current: {prediction.currentPrice.toLocaleString()} TWD</p>
          <p>Next Year: {prediction.nextYearPrice.toLocaleString()} TWD</p>
          
          {/* Chart */}
          <Line
            data={{
              labels: Object.keys(prediction.monthlyForecast),
              datasets: [{
                label: 'Price Forecast (TWD)',
                data: Object.values(prediction.monthlyForecast),
                borderColor: 'rgb(75, 192, 192)',
              }]
            }}
          />
        </div>
      )}
    </div>
  );
}
*/

