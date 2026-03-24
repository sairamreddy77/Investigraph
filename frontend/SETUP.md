# Frontend Setup Guide

Quick setup guide for the POLE NL-to-Cypher Frontend.

## Quick Start

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

## Verify Installation

After running `npm install`, you should see these key packages:
- ✅ React 18.2.0
- ✅ TypeScript 5.2.2
- ✅ Vite 5.0.8
- ✅ vis-network 9.1.9

## Backend Requirements

The frontend expects the backend API to be running at:
```
http://localhost:8000
```

Make sure these endpoints are available:
- `POST /api/ask` - Submit queries
- `GET /api/health` - Health check
- `GET /api/examples` - Get example questions
- `GET /api/schema` - Get Neo4j schema

## Development Workflow

1. **Start Backend** (in separate terminal):
   ```bash
   cd ../
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access Application**:
   Open browser to `http://localhost:3000`

## Testing the Application

1. **Check System Status**: Look for green indicators in the header
   - Neo4j: Connected
   - LLM: Available

2. **Try an Example Query**: Click any example question button

3. **Custom Query**: Type a question like:
   - "How many crimes are recorded?"
   - "Who is involved in drug crimes?"
   - "Which officer investigated the most crimes?"

4. **Verify Response Components**:
   - ✅ Natural language answer displayed
   - ✅ Generated Cypher query (expandable)
   - ✅ Results table (expandable)
   - ✅ Graph visualization (if applicable)

## Build for Production

```bash
# Create optimized production build
npm run build

# Output will be in dist/ directory
# Serve with any static file server
npm run preview
```

## Troubleshooting

### Port 3000 Already in Use
```bash
# Change port in vite.config.ts
server: {
  port: 3001,  // Use different port
  ...
}
```

### Backend Connection Issues
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check Vite proxy config in `vite.config.ts`
3. Check browser console for CORS errors

### Dependencies Not Installing
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors
```bash
# Ensure TypeScript is installed
npm install -D typescript

# Check tsconfig.json is present
```

## Next Steps

- Customize theme colors in CSS files
- Add more example questions
- Customize graph visualization node colors
- Add authentication if needed
- Deploy to production server

## Support

For issues or questions, check:
- Browser console for errors
- Network tab for API call failures
- Backend logs for API errors
