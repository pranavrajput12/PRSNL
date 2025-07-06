# Frontend Setup Guide

## Why Frontend is Not in Docker

The frontend runs separately from Docker for development purposes to enable:
- Hot Module Replacement (HMR) for instant updates
- Better debugging experience
- Faster development workflow

## How to Run

1. **Start Docker services** (backend, database, ollama):
   ```bash
   docker-compose up -d
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm install  # Only needed first time
   npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:3002
   - Backend API: http://localhost:8000
   - Ollama: http://localhost:11434

## Port Configuration

The frontend is configured to run on port 3002 to avoid conflicts with other common development servers.

The Vite proxy is configured to forward API requests from `/api` to the backend at `http://localhost:8000`.

## Troubleshooting

If you see a 500 error:
1. Make sure all Docker services are running: `docker-compose ps`
2. Check that the backend is accessible: `curl http://localhost:8000/api/timeline`
3. Restart the frontend: Kill any process on port 3002 and run `npm run dev` again

## Configuration Files

- `vite.config.ts`: Contains port and proxy settings
- `svelte.config.js`: Contains TypeScript preprocessing configuration
- `src/lib/api.ts`: API client uses relative URLs (`/api`) for proxy support