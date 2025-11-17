# Lovable Frontend Integration Guide

This guide shows you exactly how to connect your Lovable frontend to the Cursor backend API.

## Quick Setup (3 Steps)

### Step 1: Copy the Integration File

Copy `lovable-integration.js` into your Lovable project. You can:
- Create a new file in your Lovable project called `api.js` or `backend.js`
- Paste the contents of `lovable-integration.js` into it

### Step 2: Set Your API URL

In your Lovable project, set the environment variable:

```javascript
// In your Lovable project settings or .env file
REACT_APP_API_URL=http://localhost:8000
```

Or if deploying to production:
```javascript
REACT_APP_API_URL=https://your-backend-api.com
```

### Step 3: Use the Functions in Your Components

Import and use the functions in any Lovable component:

```javascript
import { sendChat, getPricePrediction } from './api'; // or wherever you saved it
```

---

## Example Components

### Chat Component

```javascript
import React, { useState } from 'react';
import { useChat } from './api';

export default function ChatComponent() {
  const { sendMessage, loading, error, response } = useChat();
  const [input, setInput] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    await sendMessage(input);
    setInput(''); // Clear input after sending
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Ask About Locations</h2>
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Find coffee shops near Taipei..."
          style={{ width: '300px', padding: '10px' }}
        />
        <button 
          type="submit" 
          disabled={loading}
          style={{ padding: '10px 20px', marginLeft: '10px' }}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>

      {error && (
        <div style={{ color: 'red', marginTop: '10px' }}>
          Error: {error}
        </div>
      )}

      {response && (
        <div style={{ marginTop: '20px', padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
          <strong>Response:</strong>
          <p>{response.answer}</p>
        </div>
      )}
    </div>
  );
}
```

### Price Prediction Component

```javascript
import React, { useState } from 'react';
import { usePricePrediction } from './api';

export default function PricePredictionComponent() {
  const { predict, loading, error, prediction } = usePricePrediction();
  const [formData, setFormData] = useState({
    address: 'Zhongshan District, Taipei, Taiwan',
    sqMeters: '40',
    bedrooms: '2',
    bathrooms: '1',
    propertyType: 'apartment',
  });

  const handlePredict = async () => {
    await predict({
      address: formData.address,
      sqMeters: parseFloat(formData.sqMeters),
      bedrooms: parseInt(formData.bedrooms),
      bathrooms: parseInt(formData.bathrooms),
      propertyType: formData.propertyType,
    });
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Property Price Prediction</h2>

      <div style={{ marginBottom: '15px' }}>
        <label>Address:</label>
        <input
          type="text"
          value={formData.address}
          onChange={(e) => setFormData({...formData, address: e.target.value})}
          style={{ width: '100%', padding: '8px', marginTop: '5px' }}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
        <div>
          <label>Size (m²):</label>
          <input
            type="number"
            value={formData.sqMeters}
            onChange={(e) => setFormData({...formData, sqMeters: e.target.value})}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        <div>
          <label>Bedrooms:</label>
          <input
            type="number"
            value={formData.bedrooms}
            onChange={(e) => setFormData({...formData, bedrooms: e.target.value})}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        <div>
          <label>Bathrooms:</label>
          <input
            type="number"
            value={formData.bathrooms}
            onChange={(e) => setFormData({...formData, bathrooms: e.target.value})}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        <div>
          <label>Property Type:</label>
          <select
            value={formData.propertyType}
            onChange={(e) => setFormData({...formData, propertyType: e.target.value})}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          >
            <option value="apartment">Apartment</option>
            <option value="condo">Condo</option>
            <option value="house">House</option>
            <option value="studio">Studio</option>
          </select>
        </div>
      </div>

      <button
        onClick={handlePredict}
        disabled={loading}
        style={{ padding: '12px 24px', fontSize: '16px', cursor: loading ? 'not-allowed' : 'pointer' }}
      >
        {loading ? 'Predicting...' : 'Get Price Prediction'}
      </button>

      {error && (
        <div style={{ color: 'red', marginTop: '15px' }}>
          Error: {error}
        </div>
      )}

      {prediction && (
        <div style={{ marginTop: '30px', padding: '20px', background: '#f9f9f9', borderRadius: '8px' }}>
          <h3>Prediction Results</h3>
          <p><strong>Address:</strong> {prediction.address}</p>
          <p><strong>Current Estimate:</strong> {prediction.currentPrice.toLocaleString()} TWD</p>
          <p><strong>Next Year Estimate:</strong> {prediction.nextYearPrice.toLocaleString()} TWD</p>
          <p><strong>Confidence Interval:</strong> {prediction.confidenceInterval.low.toLocaleString()} - {prediction.confidenceInterval.high.toLocaleString()} TWD</p>

          <h4 style={{ marginTop: '20px' }}>12-Month Forecast</h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#e5e5e5' }}>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Month</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Price (TWD)</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(prediction.monthlyForecast).map(([month, price]) => (
                  <tr key={month}>
                    <td style={{ padding: '8px' }}>{month}</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>{price.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## What You Get

✅ **Ready-to-use functions** - Just import and call  
✅ **React hooks** - Built-in state management  
✅ **Error handling** - Automatic error catching  
✅ **TypeScript-ready** - Easy to add types if needed  
✅ **Production-ready** - Works with deployed backends  

---

## Testing

1. Make sure your backend is running:
   ```bash
   # Terminal 1
   ./start_mcp.sh
   
   # Terminal 2
   ./start_web.sh
   ```

2. Test in your Lovable component:
   ```javascript
   import { checkHealth } from './api';
   
   // Check if API is running
   const isHealthy = await checkHealth();
   console.log('API is running:', isHealthy);
   ```

---

## Troubleshooting

**"Network error" or "Failed to fetch"**
- Make sure the backend is running on `http://localhost:8000`
- Check that CORS is enabled (it is by default)

**"Address not found"**
- Make sure the MCP server is running
- Check that `GOOGLE_MAPS_API_KEY` is set

**"Vertex AI not working"**
- The API will fall back to heuristic pricing automatically
- Check that Vertex AI env vars are set if you want real predictions

---

That's it! Your Lovable frontend is now connected to your Cursor backend. 🎉

