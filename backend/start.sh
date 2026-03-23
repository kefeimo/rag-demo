#!/bin/bash
# Startup script for App Runner deployment
# Copies baked data to runtime directory if empty

set -e

echo "🚀 Starting RAG backend..."

# Check if runtime data directory is empty (App Runner ephemeral storage)
if [ ! -f "/app/data/chroma_db/chroma.sqlite3" ]; then
    echo "📦 Runtime data directory empty - copying baked data..."

    # Copy ChromaDB data
    if [ -d "/app/data_baked/chroma_db" ]; then
        echo "  → Copying ChromaDB..."
        cp -r /app/data_baked/chroma_db/* /app/data/chroma_db/
        echo "  ✓ ChromaDB copied ($(du -sh /app/data/chroma_db | cut -f1))"
    fi

    # Copy documents
    if [ -d "/app/data_baked/documents" ]; then
        echo "  → Copying documents..."
        cp -r /app/data_baked/documents/* /app/data/documents/
        echo "  ✓ Documents copied ($(du -sh /app/data/documents | cut -f1))"
    fi

    echo "✓ Data initialization complete"
else
    echo "✓ Runtime data already exists - using existing data"
fi

echo "🚀 Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
