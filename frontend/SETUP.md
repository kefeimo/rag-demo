# FastAPI RAG - Frontend

React + Vite frontend for the FastAPI RAG system.

## Prerequisites

- **Node.js 20+**: Use nvm (recommended) or install Node.js 20+ directly
- **nvm** (optional but recommended): [Install nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

## Setup

### Option 1: Using nvm (Recommended)

```bash
# Install nvm if you don't have it
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install and use Node 20 (automatically reads .nvmrc from parent directory)
cd /path/to/ai-engineer-coding-exercise
nvm install
nvm use

# Install dependencies
cd frontend
npm install
```

### Option 2: Using existing Node.js 20+

If you already have Node.js 20 or higher installed:

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
# Open http://localhost:5173
```

## Build for Production

```bash
npm run build
npm run preview  # Preview production build locally
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # React components (to be created)
│   ├── utils/          # API client utilities (to be created)
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles with Tailwind
├── public/             # Static assets
├── .nvmrc              # Node version specification (20)
├── package.json        # Dependencies
├── tailwind.config.js  # Tailwind CSS configuration
└── vite.config.js      # Vite configuration
```

## Tech Stack

- **React 19**: UI framework
- **Vite 7**: Build tool and dev server
- **Tailwind CSS 4**: Utility-first CSS framework  
- **axios**: HTTP client for API calls

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

Endpoints used:
- `GET /health` - Health check
- `POST /api/v1/query` - Submit RAG queries
- `POST /api/v1/ingest` - Ingest documents (optional)

## Troubleshooting

**Issue: "Unsupported engine" warning**
```
npm warn EBADENGINE required: { node: '^20.19.0 || >=22.12.0' }
```
This is a benign warning. Node 20.17.0+ works fine despite the warning.

**Issue: Node version not found**
```bash
# Make sure you're in the project root when running nvm use
cd /path/to/ai-engineer-coding-exercise
nvm use
```

**Issue: Port 5173 already in use**
```bash
# Kill the existing process
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 5174
```

## Next Steps

1. Create query interface components
2. Build API integration layer
3. Add source display with confidence badges
4. Implement error handling
5. Test with backend integration
