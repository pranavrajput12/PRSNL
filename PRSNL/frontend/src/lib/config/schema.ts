import { z } from 'zod';

/**
 * Frontend Configuration Schema using Zod
 * Provides runtime validation and type safety for configuration
 */

// API Configuration Schema
export const ApiConfigSchema = z.object({
  baseUrl: z.string().url('API base URL must be a valid URL').default('http://localhost:8000'),
  wsUrl: z.string().url('WebSocket URL must be a valid URL').default('ws://localhost:8000'),
  timeout: z.number().positive().default(30000),
  retries: z.number().int().min(0).max(5).default(3),
});

// Voice Settings Schema
export const VoiceConfigSchema = z.object({
  ttsModel: z.enum(['chatterbox', 'edge-tts']).default('chatterbox'),
  emotion: z.enum(['neutral', 'happy', 'sad', 'angry', 'excited', 'calm', 'friendly']).default('friendly'),
  speed: z.number().min(0.5).max(2.0).default(1.0),
  pitch: z.number().int().min(-50).max(50).default(0),
  language: z.string().default('en'),
});

// App Configuration Schema  
export const AppConfigSchema = z.object({
  theme: z.enum(['dark', 'light', 'auto']).default('dark'),
  debugMode: z.boolean().default(false),
  telemetryEnabled: z.boolean().default(true),
  autoSave: z.boolean().default(true),
  notifications: z.boolean().default(true),
});

// Complete Configuration Schema
export const ConfigSchema = z.object({
  api: ApiConfigSchema,
  voice: VoiceConfigSchema,
  app: AppConfigSchema,
});

// Export types
export type ApiConfig = z.infer<typeof ApiConfigSchema>;
export type VoiceConfig = z.infer<typeof VoiceConfigSchema>;
export type AppConfig = z.infer<typeof AppConfigSchema>;
export type Config = z.infer<typeof ConfigSchema>;

// Default configuration
export const DEFAULT_CONFIG: Config = {
  api: {
    baseUrl: 'http://localhost:8000',
    wsUrl: 'ws://localhost:8000', 
    timeout: 30000,
    retries: 3,
  },
  voice: {
    ttsModel: 'chatterbox',
    emotion: 'friendly',
    speed: 1.0,
    pitch: 0,
    language: 'en',
  },
  app: {
    theme: 'dark',
    debugMode: false,
    telemetryEnabled: true,
    autoSave: true,
    notifications: true,
  },
};