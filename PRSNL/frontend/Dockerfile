# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with network timeout
RUN npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm ci --loglevel verbose

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy everything needed for production
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.svelte-kit ./.svelte-kit
COPY --from=builder /app/vite.config.ts ./
COPY --from=builder /app/svelte.config.js ./
COPY --from=builder /app/src ./src

# Expose port
EXPOSE 3002

# Set environment variables
ENV PORT=3002
ENV HOST=0.0.0.0
ENV NODE_ENV=production
ENV PUBLIC_API_URL=http://backend:8000

# For development/preview mode
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3002"]