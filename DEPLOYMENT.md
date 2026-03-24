# Deployment Guide - Investigraph POLE NL-to-Cypher QA System

> Comprehensive deployment instructions for local development, Docker, and cloud platforms.

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Platform Deployment](#cloud-platform-deployment)
   - [Heroku](#heroku)
   - [Render](#render)
   - [Railway](#railway)
   - [Vercel (Frontend) + Railway (Backend)](#vercel-frontend--railway-backend)
4. [Environment Variables](#environment-variables)
5. [Production Best Practices](#production-best-practices)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Neo4j Database (local or cloud)
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Activate (Unix/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your credentials
# Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
# Required: At least one LLM API key (GROQ_API_KEY, OPENAI_API_KEY, etc.)

# Run development server
uvicorn app.main:app --reload --port 8000

# Test backend is running
curl http://localhost:8000/api/health
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Frontend will be available at http://localhost:3000
```

### Verify Installation

1. Open `http://localhost:3000` in browser
2. Try example question: "How many crimes are recorded?"
3. Verify:
   - Natural language answer appears
   - Cypher query is displayed
   - Results table shows data
   - Graph visualization renders (if applicable)

---

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Option 1: Docker Compose (Recommended)

The `docker-compose.yml` file orchestrates both backend and frontend services.

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

**Access the application:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Option 2: Individual Docker Containers

**Backend:**

```bash
cd backend

# Build image
docker build -t investigraph-backend .

# Run container
docker run -d \
  --name investigraph-backend \
  -p 8000:8000 \
  --env-file .env \
  investigraph-backend

# View logs
docker logs -f investigraph-backend
```

**Frontend:**

```bash
cd frontend

# Build image
docker build -t investigraph-frontend .

# Run container
docker run -d \
  --name investigraph-frontend \
  -p 3000:3000 \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  investigraph-frontend

# View logs
docker logs -f investigraph-frontend
```

### Docker Environment Variables

Create `.env` file for backend container:

```env
# Neo4j
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=pole

# LLM Provider
GROQ_API_KEY=gsk_xxxxx

# Optional
LOG_LEVEL=INFO
```

### Docker Compose Environment Variables

Edit `docker-compose.yml` or create `.env` in root directory:

```env
# Backend environment
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=pole
GROQ_API_KEY=gsk_xxxxx

# Frontend environment
VITE_API_BASE_URL=/api
```

---

## Cloud Platform Deployment

### Heroku

Heroku supports both Python (backend) and Node.js (frontend) applications.

#### Backend Deployment

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create Heroku app
cd backend
heroku create investigraph-backend

# Add Python buildpack
heroku buildpacks:set heroku/python

# Set environment variables
heroku config:set NEO4J_URI="neo4j+s://xxxxx.databases.neo4j.io"
heroku config:set NEO4J_USERNAME="neo4j"
heroku config:set NEO4J_PASSWORD="your_password"
heroku config:set NEO4J_DATABASE="pole"
heroku config:set GROQ_API_KEY="gsk_xxxxx"

# Create Procfile
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku master

# View logs
heroku logs --tail

# Open app
heroku open
```

#### Frontend Deployment

```bash
cd frontend

# Create Heroku app
heroku create investigraph-frontend

# Add Node.js buildpack
heroku buildpacks:set heroku/nodejs

# Set backend API URL
heroku config:set VITE_API_BASE_URL="https://investigraph-backend.herokuapp.com"

# Create static.json for serving
cat > static.json <<EOF
{
  "root": "dist",
  "clean_urls": true,
  "routes": {
    "/**": "index.html"
  },
  "proxies": {
    "/api/": {
      "origin": "https://investigraph-backend.herokuapp.com"
    }
  }
}
EOF

# Update package.json scripts
# Ensure "build" script exists: "vite build"
# Add "start" script: "serve -s dist -l $PORT"

# Install serve
npm install --save serve

# Deploy
git add .
git commit -m "Deploy frontend to Heroku"
git push heroku master

# Open app
heroku open
```

---

### Render

Render provides zero-config deployments for both services.

#### Backend Deployment

1. **Connect Repository:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub/GitLab repository
   - Select `backend` directory as root

2. **Configure Service:**
   - **Name**: `investigraph-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free or Starter

3. **Environment Variables:**
   Add in Render dashboard:
   ```
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   NEO4J_DATABASE=pole
   GROQ_API_KEY=gsk_xxxxx
   ```

4. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Access at: `https://investigraph-backend.onrender.com`

#### Frontend Deployment

1. **Connect Repository:**
   - Click "New +" → "Static Site"
   - Select `frontend` directory as root

2. **Configure Service:**
   - **Name**: `investigraph-frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

3. **Environment Variables:**
   ```
   VITE_API_BASE_URL=https://investigraph-backend.onrender.com
   ```

4. **Deploy:**
   - Click "Create Static Site"
   - Access at: `https://investigraph-frontend.onrender.com`

---

### Railway

Railway offers simple deployment with automatic HTTPS and environment management.

#### Backend Deployment

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Initialize:**
   ```bash
   cd backend
   railway login
   railway init
   ```

3. **Configure Service:**
   ```bash
   # Set start command
   railway run --service backend

   # Add environment variables
   railway variables set NEO4J_URI="neo4j+s://xxxxx.databases.neo4j.io"
   railway variables set NEO4J_USERNAME="neo4j"
   railway variables set NEO4J_PASSWORD="your_password"
   railway variables set NEO4J_DATABASE="pole"
   railway variables set GROQ_API_KEY="gsk_xxxxx"
   ```

4. **Create Railway.json:**
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

5. **Deploy:**
   ```bash
   railway up
   ```

6. **Get URL:**
   ```bash
   railway domain
   # Or set custom domain in Railway dashboard
   ```

#### Frontend Deployment

1. **Initialize Frontend:**
   ```bash
   cd frontend
   railway init
   ```

2. **Configure:**
   ```bash
   railway variables set VITE_API_BASE_URL="https://your-backend.railway.app"
   ```

3. **Create Railway.json:**
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "npm run preview -- --host 0.0.0.0 --port $PORT"
     }
   }
   ```

4. **Deploy:**
   ```bash
   railway up
   ```

---

### Vercel (Frontend) + Railway (Backend)

Recommended setup for optimal performance: static frontend on Vercel, backend on Railway.

#### Backend on Railway

Follow [Railway Backend Deployment](#backend-deployment-2) above.

#### Frontend on Vercel

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Configure Project:**
   ```bash
   cd frontend
   vercel login
   ```

3. **Create vercel.json:**
   ```json
   {
     "buildCommand": "npm run build",
     "outputDirectory": "dist",
     "framework": "vite",
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://your-backend.railway.app/api/:path*"
       }
     ]
   }
   ```

4. **Deploy:**
   ```bash
   vercel
   ```

5. **Set Environment Variables:**
   ```bash
   vercel env add VITE_API_BASE_URL
   # Enter: /api (uses Vercel proxy)
   ```

6. **Deploy to Production:**
   ```bash
   vercel --prod
   ```

---

## Environment Variables

### Backend Environment Variables

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `NEO4J_URI` | Yes | - | Neo4j connection URI | `neo4j+s://xxx.databases.neo4j.io` |
| `NEO4J_USERNAME` | Yes | - | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Yes | - | Neo4j password | `your_secure_password` |
| `NEO4J_DATABASE` | No | `neo4j` | Database name | `pole` |
| `GROQ_API_KEY` | No* | - | Groq API key | `gsk_xxxxx` |
| `OPENAI_API_KEY` | No* | - | OpenAI API key | `sk-xxxxx` |
| `ANTHROPIC_API_KEY` | No* | - | Anthropic API key | `sk-ant-xxxxx` |
| `GOOGLE_API_KEY` | No* | - | Google API key | `AIzaSyxxxxx` |
| `LOG_LEVEL` | No | `INFO` | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `PORT` | No | `8000` | Server port | Auto-set by cloud platforms |

*At least one LLM API key is required

### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | No | `/api` | Backend API base URL |

**Note**: Frontend environment variables must be prefixed with `VITE_` to be accessible in the application.

---

## Production Best Practices

### Security

1. **Use HTTPS**: Always deploy with SSL/TLS certificates
2. **Environment Variables**: Never commit `.env` files to version control
3. **API Keys**: Rotate keys regularly, use different keys for dev/prod
4. **CORS**: Configure allowed origins in `app/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
5. **Rate Limiting**: Add rate limiting for API endpoints
6. **Input Validation**: Already handled by Pydantic models

### Performance

1. **Use Production LLM**: Claude Sonnet 4 or GPT-4o for best accuracy
2. **Neo4j Indexes**: Create indexes on frequently queried properties:
   ```cypher
   CREATE INDEX person_name FOR (p:Person) ON (p.name, p.surname);
   CREATE INDEX crime_type FOR (c:Crime) ON (c.type);
   CREATE INDEX location_postcode FOR (l:Location) ON (l.postcode);
   ```
3. **Connection Pooling**: Configure in `app/database.py`:
   ```python
   driver = GraphDatabase.driver(
       uri,
       auth=(username, password),
       max_connection_pool_size=50,
       connection_acquisition_timeout=30.0
   )
   ```
4. **Caching**: Consider Redis for caching frequent queries
5. **CDN**: Use CDN for frontend static assets (Vercel includes this)

### Scaling

1. **Horizontal Scaling (Backend):**
   - Use Gunicorn with multiple workers:
     ```bash
     gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
     ```
   - Update Dockerfile CMD or Procfile

2. **Load Balancing:**
   - Most cloud platforms provide this automatically
   - For custom deployments, use NGINX or Traefik

3. **Database:**
   - Use managed Neo4j cluster (Neo4j Aura)
   - Enable read replicas for high-traffic scenarios

4. **Monitoring:**
   - Set up health check endpoints (already at `/api/health`)
   - Use platform monitoring (Render, Railway, Heroku dashboards)
   - Consider DataDog, New Relic, or Sentry for APM

### Logging

Configure structured logging in production:

```python
# app/main.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

---

## Monitoring and Logging

### Health Checks

**Endpoint**: `GET /api/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "llm_provider": "groq",
  "schema_loaded": true,
  "examples_loaded": true,
  "examples_count": 24
}
```

**Use for:**
- Load balancer health checks
- Uptime monitoring (UptimeRobot, Pingdom)
- Container orchestration health probes

### Application Logging

**View Logs:**

**Heroku:**
```bash
heroku logs --tail --app investigraph-backend
```

**Render:**
- Dashboard → Service → Logs tab

**Railway:**
```bash
railway logs
```

**Docker:**
```bash
docker logs -f investigraph-backend
```

### Key Metrics to Monitor

1. **Response Time**: Average time for `/api/ask` requests
2. **Error Rate**: 4xx/5xx response codes
3. **LLM Calls**: Number of successful/failed LLM invocations
4. **Retry Rate**: Percentage of queries requiring retries
5. **Database Connection**: Neo4j connection pool status

### Setting Up Alerts

Configure alerts for:
- Health check failures
- High error rates (>5%)
- Slow response times (>10s average)
- Database connection failures

---

## Troubleshooting

### Common Deployment Issues

#### "Module not found" errors

**Solution:**
```bash
# Ensure requirements.txt is complete
pip freeze > requirements.txt

# For frontend
npm install
```

#### "Port already in use"

**Solution:**
```bash
# Change port in start command
uvicorn app.main:app --port 8001

# Or kill process on port 8000
# Unix/macOS:
lsof -ti:8000 | xargs kill -9
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### "Neo4j connection timeout"

**Checklist:**
- [ ] Verify `NEO4J_URI` format: `neo4j+s://xxx.databases.neo4j.io`
- [ ] Check credentials are correct
- [ ] Ensure database is online (check Neo4j Aura dashboard)
- [ ] Verify firewall/IP allowlist settings
- [ ] Test connection from deployment server

#### "LLM API errors"

**Checklist:**
- [ ] Verify API key is set correctly
- [ ] Check API key permissions/quotas
- [ ] Test API key directly:
  ```bash
  # Groq
  curl https://api.groq.com/openai/v1/models \
    -H "Authorization: Bearer $GROQ_API_KEY"

  # OpenAI
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY"
  ```
- [ ] Check rate limits haven't been exceeded
- [ ] Verify billing/credits are active

#### "CORS errors" in frontend

**Solution:**

Update `backend/app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### "Static files not loading" (Frontend)

**Solution:**

Verify build output:
```bash
cd frontend
npm run build
ls -la dist/  # Should contain index.html, assets/, etc.
```

Update serving configuration for your platform.

### Platform-Specific Issues

#### Heroku

**Issue**: Application sleeps on free tier
**Solution**: Upgrade to Hobby dyno or use external uptime monitor

**Issue**: Slug size too large (>500MB)
**Solution**:
- Add `.slugignore` file
- Remove unused dependencies
- Use Docker deployment instead

#### Render

**Issue**: Free tier spins down after inactivity
**Solution**: Upgrade to Starter plan or use external keep-alive service

**Issue**: Build timeouts
**Solution**: Increase build timeout in service settings

#### Railway

**Issue**: Deployment fails silently
**Solution**: Check Railway logs, verify `railway.json` configuration

#### Vercel

**Issue**: API routes not working
**Solution**: Ensure `vercel.json` has correct proxy rewrites

---

## Rollback Procedures

### Heroku

```bash
# List releases
heroku releases

# Rollback to previous version
heroku rollback v42
```

### Render

- Dashboard → Service → "Manual Deploy" → Select previous commit

### Railway

```bash
# List deployments
railway status

# Rollback
railway rollback <deployment-id>
```

### Docker

```bash
# Stop current container
docker stop investigraph-backend

# Remove current container
docker rm investigraph-backend

# Run previous image version
docker run -d --name investigraph-backend investigraph-backend:previous-tag
```

---

## Backup and Recovery

### Neo4j Database

**Backup:**
```cypher
// Export to CSV
CALL apoc.export.csv.all('backup.csv', {})

// Or use Neo4j Aura automated backups
```

**Restore:**
- Use Neo4j Aura restore feature
- Or re-import CSV data

### Application State

The application is stateless - all data is in Neo4j and configuration is in environment variables.

To restore:
1. Redeploy application
2. Set environment variables
3. Connect to existing Neo4j database

---

## Cost Optimization

### Free Tier Options

- **Hosting**: Render (free with limitations), Railway ($5 credit/month)
- **LLM**: Groq (free tier with generous limits)
- **Neo4j**: Neo4j Aura Free (persistent instance)
- **Frontend**: Vercel (free for personal projects)

### Paid Tier Recommendations

**Minimal Production ($20-30/month):**
- Backend: Railway Starter ($5-10/month)
- Frontend: Vercel Pro ($20/month) or Render ($7/month)
- Neo4j: Aura Professional ($65/month) or self-hosted
- LLM: Groq (pay-as-you-go) or Gemini Flash (very cheap)

**Recommended Production ($100-150/month):**
- Backend: Render Standard ($25/month) or Railway Pro
- Frontend: Vercel Pro ($20/month)
- Neo4j: Aura Professional ($65/month)
- LLM: OpenAI GPT-4o or Claude Sonnet 4 (pay-as-you-go, ~$20-40/month)
- Monitoring: DataDog free tier or Sentry ($26/month)

---

## Support and Resources

- **Neo4j Aura**: https://console.neo4j.io/
- **Heroku**: https://devcenter.heroku.com/
- **Render**: https://render.com/docs
- **Railway**: https://docs.railway.app/
- **Vercel**: https://vercel.com/docs

For deployment issues, check:
1. Platform status pages
2. Application logs
3. Health check endpoint
4. `backend/tests/manual_test_checklist.md` for verification steps
