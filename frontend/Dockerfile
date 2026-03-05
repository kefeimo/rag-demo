# Frontend Dockerfile for React + Vite
FROM node:20-slim as build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install curl for health checks and serve to run the built app
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g serve

# Copy built assets from build stage
COPY --from=build /app/dist /app/dist

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5173 || exit 1

# Run the application
CMD ["serve", "-s", "dist", "-l", "5173"]
