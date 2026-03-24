# POLE NL-to-Cypher Frontend

React 18 + TypeScript + Vite frontend for the POLE Natural Language to Cypher QA System.

## Features

- **Natural Language Query Interface**: Ask questions in plain English
- **Real-time Query Processing**: Displays generated Cypher queries and execution results
- **Graph Visualization**: Interactive network visualization using vis-network
- **Example Questions**: Quick-start with pre-defined example queries
- **Auto-Retry Logic**: Displays retry attempts and execution metadata
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000`

## Installation

```bash
# Install dependencies
npm install

# Or with yarn
yarn install
```

## Development

```bash
# Start development server (http://localhost:3000)
npm run dev

# Or with yarn
yarn dev
```

The dev server includes proxy configuration to forward `/api` requests to the backend at `http://localhost:8000`.

## Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── QueryPanel.tsx          # Question input and examples
│   │   ├── QueryPanel.css
│   │   ├── ResponsePanel.tsx       # Answer and results display
│   │   ├── ResponsePanel.css
│   │   ├── GraphVisualization.tsx  # Interactive graph viewer
│   │   └── GraphVisualization.css
│   ├── services/
│   │   └── api.ts                  # API client with TypeScript types
│   ├── App.tsx                     # Main application component
│   ├── App.css
│   ├── main.tsx                    # Entry point
│   └── index.css                   # Global styles
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## Components

### QueryPanel
- Text input for natural language questions
- Submit button with loading state
- Example questions for quick selection
- Error handling and display

### ResponsePanel
- Natural language answer display
- Collapsible Cypher query viewer with copy button
- Results table (collapsible)
- Execution metadata (attempts, time)

### GraphVisualization
- Interactive graph using vis-network
- Node coloring by label type
- Zoom, pan, and select interactions
- Toggle visibility
- Displays node and edge counts

## API Endpoints

The frontend expects the following API endpoints:

- `POST /api/ask` - Submit natural language query
- `GET /api/schema` - Get Neo4j schema information
- `GET /api/examples` - Get example questions
- `GET /api/health` - Check system health

## Configuration

### API Base URL

Edit `src/services/api.ts` to change the API base URL:

```typescript
const API_BASE_URL = '/api'; // Change this if needed
```

### Vite Proxy

Edit `vite.config.ts` to change the backend proxy target:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000', // Change this
      changeOrigin: true,
    },
  },
}
```

## Customization

### Graph Colors

Edit `src/components/GraphVisualization.tsx` to customize node colors:

```typescript
groups: {
  Person: { color: { background: '#FF6B6B', border: '#C92A2A' } },
  Crime: { color: { background: '#845EC2', border: '#5F3B8C' } },
  // ... add more
}
```

### Theme

The app supports light and dark mode based on system preferences. Customize colors in CSS files.

## Troubleshooting

### CORS Issues
If you encounter CORS errors, ensure the backend has proper CORS configuration:

```python
# In FastAPI backend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Graph Not Rendering
- Check browser console for errors
- Ensure results contain Neo4j node/relationship objects
- Verify vis-network is properly installed

### API Connection Failed
- Verify backend is running on port 8000
- Check Vite proxy configuration
- Inspect network tab in browser DevTools

## License

Part of the Investigraph POLE NL-to-Cypher QA System.
