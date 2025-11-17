# Deployment Guide for zhongshan-dream-finder.lovable.app

This guide helps you deploy your backend API so your Lovable frontend can connect to it.

## Quick Setup Checklist

- [ ] Deploy backend API to a hosting service
- [ ] Update CORS to allow your Lovable domain
- [ ] Set environment variables on hosting service
- [ ] Update Lovable project with API URL
- [ ] Test the connection

---

## Step 1: Deploy Your Backend API

You need to deploy the backend API somewhere accessible. Here are recommended options:

### Option A: Railway (Recommended - Easiest)

1. **Sign up**: Go to [railway.app](https://railway.app) and sign up
2. **Create new project**: Click "New Project" → "Deploy from GitHub repo"
3. **Connect your repo**: Select your Cursor project repository
4. **Configure**:
   - Root directory: `/Users/tinganwang/.cursor/worktrees/Cursor_project/zkqET`
   - Start command: `python -m uvicorn app.api:app --host 0.0.0.0 --port $PORT`
5. **Set environment variables** in Railway dashboard:
   ```
   DEEPSEEK_API_KEY=your-key
   GOOGLE_MAPS_API_KEY=your-key
   GOOGLE_CLOUD_PROJECT=your-project-id
   VERTEX_LOCATION=us-central1
   VERTEX_ENDPOINT_ID=your-endpoint-id
   GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
   ALLOWED_ORIGINS=https://zhongshan-dream-finder.lovable.app
   ```
6. **Upload service account file**: Add it as a secret file in Railway
7. **Deploy**: Railway will automatically deploy and give you a URL like `https://your-app.railway.app`

### Option B: Render

1. **Sign up**: Go to [render.com](https://render.com)
2. **New Web Service**: Connect your GitHub repo
3. **Settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**: Add all the same variables as Railway
5. **Deploy**: Render gives you a URL like `https://your-app.onrender.com`

### Option C: Fly.io

1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Login**: `fly auth login`
3. **Create app**: `fly launch` in your project directory
4. **Set secrets**: `fly secrets set DEEPSEEK_API_KEY=...` (repeat for all vars)
5. **Deploy**: `fly deploy`

---

## Step 2: Update CORS Configuration

The backend is already configured to allow `https://zhongshan-dream-finder.lovable.app`.

If you need to add more domains, set the `ALLOWED_ORIGINS` environment variable:

```bash
export ALLOWED_ORIGINS="https://zhongshan-dream-finder.lovable.app,https://another-domain.com"
```

---

## Step 3: Update Your Lovable Project

1. **Go to your Lovable project**: https://zhongshan-dream-finder.lovable.app
2. **Add environment variable**:
   - In Lovable settings, add:
     ```
     REACT_APP_API_URL=https://your-deployed-backend.railway.app
     ```
   - Replace with your actual deployed backend URL

3. **Copy integration code**:
   - Copy `lovable-integration-production.js` into your Lovable project
   - Name it `api.js` or `backend.js`
   - The code will automatically use the `REACT_APP_API_URL` environment variable

---

## Step 4: Start MCP Server (Separate Service)

The Google Maps MCP server needs to run separately. You have two options:

### Option A: Run Locally (Development Only)

Keep the MCP server running on your local machine:
```bash
./start_mcp.sh
```

**Note**: This only works for local development. For production, you need Option B.

### Option B: Deploy MCP Server (Production)

The MCP server is a Node.js app. You can deploy it to:
- **Railway**: Create a separate service for the MCP server
- **Render**: Create a separate web service
- **Fly.io**: Create a separate app

Then update your backend's `MCP_SERVER_URL` environment variable to point to the deployed MCP server.

---

## Step 5: Test Everything

1. **Test backend health**:
   ```bash
   curl https://your-deployed-backend.railway.app/health
   ```

2. **Test from Lovable**:
   - Open your Lovable site
   - Try the chat feature
   - Try the price prediction feature
   - Check browser console for any errors

---

## Environment Variables Summary

### Backend API (Railway/Render/Fly.io)

```bash
# Required
DEEPSEEK_API_KEY=your-deepseek-key
GOOGLE_MAPS_API_KEY=your-google-maps-key

# Optional (for Vertex AI)
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_LOCATION=us-central1
VERTEX_ENDPOINT_ID=your-endpoint-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# CORS
ALLOWED_ORIGINS=https://zhongshan-dream-finder.lovable.app

# MCP Server URL (if MCP is deployed separately)
MCP_SERVER_URL=https://your-mcp-server.railway.app
```

### Lovable Frontend

```bash
REACT_APP_API_URL=https://your-deployed-backend.railway.app
```

---

## Troubleshooting

**"CORS error" in browser**
- Check that `ALLOWED_ORIGINS` includes `https://zhongshan-dream-finder.lovable.app`
- Make sure there are no typos in the domain

**"Failed to fetch"**
- Check that your backend is deployed and running
- Verify the `REACT_APP_API_URL` in Lovable matches your backend URL
- Check backend logs for errors

**"MCP server connection failed"**
- Make sure MCP server is running (locally or deployed)
- Check `MCP_SERVER_URL` environment variable
- Verify Google Maps API key is set

**"Vertex AI not working"**
- The API will automatically fall back to heuristic pricing
- Check that all Vertex AI env vars are set correctly
- Verify service account JSON file is uploaded correctly

---

## Quick Deploy Script

Save this as `deploy.sh`:

```bash
#!/bin/bash
# Quick deployment checklist

echo "🚀 Deployment Checklist for zhongshan-dream-finder.lovable.app"
echo ""
echo "1. Backend API deployed? (Railway/Render/Fly.io)"
echo "2. Environment variables set?"
echo "3. CORS configured for https://zhongshan-dream-finder.lovable.app?"
echo "4. Lovable REACT_APP_API_URL set?"
echo "5. MCP server running (local or deployed)?"
echo ""
echo "Test your deployment:"
echo "curl https://your-backend-url/health"
```

---

## Support

If you run into issues:
1. Check backend logs (Railway/Render dashboard)
2. Check browser console for errors
3. Test API endpoints directly with `curl`
4. Verify all environment variables are set correctly

Your backend is already configured for your Lovable domain! Just deploy it and set the API URL in Lovable. 🎉

