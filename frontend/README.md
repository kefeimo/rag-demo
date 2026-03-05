# FastAPI RAG - Frontend

React + Vite frontend for the FastAPI RAG system with beautiful UI and real-time backend status.

## 🚀 Quick Start

### Prerequisites

- **Node.js 20+**: Use nvm (recommended) or install Node.js 20+ directly
- **nvm** (optional but recommended): [Install nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Setup & Run

```bash
# Navigate to project root first
cd /path/to/ai-engineer-coding-exercise

# Install and use Node 20 (reads .nvmrc from parent directory)
nvm install
nvm use

# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
# Open http://localhost:5173
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── QueryInput.jsx    # Query input with submit button
│   │   ├── ResponseDisplay.jsx  # Answer and sources display
│   │   ├── SourceCard.jsx    # Individual source with confidence badge
│   │   └── ErrorDisplay.jsx  # Error message component
│   ├── utils/
│   │   └── api.js            # API client (axios)
│   ├── App.jsx               # Main app component
│   ├── main.jsx              # Entry point
│   └── index.css             # Global styles with Tailwind
├── public/                   # Static assets
├── package.json              # Dependencies
├── tailwind.config.js        # Tailwind CSS configuration
├── postcss.config.js         # PostCSS configuration
└── vite.config.js            # Vite configuration
```

## 🎨 Features

### UI Components
- ✅ **Query Input**: Textarea with character count, loading state, keyboard shortcuts
- ✅ **Response Display**: Formatted answer with confidence score
- ✅ **Source Cards**: Color-coded confidence badges (High/Medium/Low)
- ✅ **Error Display**: User-friendly error messages with dismiss
- ✅ **Backend Status**: Real-time connection indicator (green/red dot)
- ✅ **Example Questions**: Quick-start buttons for common queries

### UX Features
- ✅ Beautiful gradient background
- ✅ Responsive design (mobile-friendly)
- ✅ Loading spinner with "Searching..." text
- ✅ Auto-disable submit during loading
- ✅ Welcome screen with example questions
- ✅ Proper error handling and user feedback

## 🔌 API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

### API Endpoints Used

```javascript
// Health check (called on mount)
GET /health

// Submit query
POST /api/v1/query
{
  "query": "What is FastAPI?",
  "top_k": 3
}
```

### Configuration

Configure API base URL via environment variable:

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
```

## 🛠️ Development

### Available Scripts

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Tech Stack

- **React 19**: UI framework with hooks
- **Vite 7**: Fast build tool and dev server
- **Tailwind CSS 4**: Utility-first CSS framework
- **axios**: Promise-based HTTP client
- **ESLint**: Code linting

## 🐳 Docker Deployment

Build and run with Docker:

```bash
# Build image
docker build -t rag-frontend .

# Run container
docker run -p 5173:5173 rag-frontend

# Or use docker-compose (from project root)
docker-compose up frontend
```

## 🧪 Testing

### Manual Testing Checklist

- [ ] Backend status indicator shows "Connected" when backend is running
- [ ] Backend status indicator shows "Disconnected" when backend is offline
- [ ] Can submit query and receive response
- [ ] Loading spinner shows during query processing
- [ ] Sources display with correct confidence badges
- [ ] Error message appears when backend is offline
- [ ] Example question buttons work
- [ ] Responsive on mobile (test at 375px width)
- [ ] Submit button disabled when query is empty

### Test Queries

Try these queries to test the system:

1. **Simple**: "What is FastAPI?"
2. **Procedural**: "How do I create a path parameter?"
3. **Complex**: "What are FastAPI's main features?"

Expected: Each query should return answer with 3 sources and confidence >65%

## 🔧 Troubleshooting

### Issue: "Unsupported engine" warning

```
npm warn EBADENGINE required: { node: '^20.19.0 || >=22.12.0' }
```

**Solution**: This is a benign warning. Node 20.17.0+ works fine despite the warning.

### Issue: Port 5173 already in use

```bash
# Find and kill process
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 5174
```

### Issue: Backend not connecting

1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in backend `.env`:
   ```
   CORS_ORIGINS=http://localhost:5173,http://localhost:5174
   ```
3. Check browser console for CORS errors

### Issue: Tailwind CSS not working

Ensure `tailwind.config.js` content paths are correct:

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  // ...
}
```

## 📚 Documentation

- **[Project README](../README.md)** - Main project documentation
- **[Backend README](../backend/README.md)** - Backend API documentation
- **[Docker Guide](../DOCKER.md)** - Docker deployment
- **[Setup Guide](./SETUP.md)** - Detailed setup instructions

## 🎯 Future Enhancements

Potential improvements for production:

- [ ] Add query history (localStorage)
- [ ] Implement dark mode toggle
- [ ] Add copy-to-clipboard for answers
- [ ] Add export conversation feature
- [ ] Implement typing indicators
- [ ] Add message timestamps
- [ ] Add pagination for sources
- [ ] Add keyboard shortcuts (Ctrl+K to focus input)
- [ ] Add accessibility improvements (ARIA labels)

---

**Status:** Stage 1B Complete ✅  
**Version:** 1.0.0  
**Last Updated:** March 4, 2026
