import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 3002,
    proxy: {
      '/api': {
        target: process.env.PUBLIC_API_URL || 'http://localhost:8000',
        changeOrigin: true
      },
      '/media': {
        target: process.env.PUBLIC_API_URL || 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: process.env.PUBLIC_API_URL || 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
  }
});