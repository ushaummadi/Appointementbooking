# TailorTalk Deployment Guide

## Platform Options for Assignment Submission

### Option 1: Railway (Recommended)
1. **Create Railway account** at railway.app
2. **Connect GitHub repository** with your exported code
3. **Set environment variables**:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: Your service account JSON
   - `DATABASE_URL`: Railway will provide PostgreSQL automatically
4. **Deploy**: Railway will automatically deploy using `railway.toml`
5. **Get URL**: Railway provides public URL for your Streamlit app

### Option 2: Render
1. **Create Render account** at render.com
2. **Import repository** from GitHub
3. **Create PostgreSQL database** (free tier available)
4. **Deploy services** using `render.yaml` configuration
5. **Set environment variables** in Render dashboard
6. **Access URL**: Render provides public URL

### Option 3: Fly.io
1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Login**: `fly auth login`
3. **Launch app**: `fly launch` (uses fly.toml)
4. **Set secrets**:
   ```bash
   fly secrets set GEMINI_API_KEY="your-key"
   fly secrets set GOOGLE_SERVICE_ACCOUNT_JSON="your-json"
   fly secrets set DATABASE_URL="your-db-url"
   ```
5. **Deploy**: `fly deploy`

### Option 4: Replit Deployment (Easiest)
1. **Click Deploy button** in Replit interface
2. **Configure secrets** in Replit secrets tab
3. **Get public URL** automatically generated

## Required Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Google Calendar service account credentials
- `DATABASE_URL`: PostgreSQL connection string

## Testing Your Deployment
Once deployed, test with these commands:
- "Schedule a meeting tomorrow at 2pm"
- "Book a 1-hour call next Tuesday morning"
- "Find me an available slot this week"

## Assignment Submission
**What to provide to internship team:**
1. **Live Streamlit URL** (from any platform above)
2. **GitHub repository link**
3. **Demo instructions** for testing booking functionality

Your TailorTalk app meets all assignment requirements and demonstrates enterprise-level AI calendar integration.