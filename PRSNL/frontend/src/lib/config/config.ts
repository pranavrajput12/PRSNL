import { browser } from '$app/environment';
import { ConfigSchema, DEFAULT_CONFIG, type Config } from './schema';
import type { ZodError } from 'zod';

/**
 * Configuration Service with Zod Validation
 * Provides centralized, type-safe configuration management
 */

class ConfigurationService {
  private config: Config = DEFAULT_CONFIG;
  private initialized = false;

  /**
   * Initialize configuration from environment variables and user settings
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Load base configuration from environment
      const envConfig = this.loadFromEnvironment();
      
      // Load user settings from localStorage (browser only)
      const userConfig = browser ? this.loadFromStorage() : {};
      
      // Merge configurations (env < default < user)
      const mergedConfig = this.mergeConfigs(DEFAULT_CONFIG, envConfig, userConfig);
      
      // Validate the complete configuration
      const validationResult = ConfigSchema.safeParse(mergedConfig);
      
      if (!validationResult.success) {
        console.error('❌ Configuration validation failed:', validationResult.error);
        this.handleValidationError(validationResult.error);
        // Fall back to default config
        this.config = DEFAULT_CONFIG;
      } else {
        this.config = validationResult.data;
        console.log('✅ Configuration loaded and validated successfully');
      }
      
      this.initialized = true;
    } catch (error) {
      console.error('❌ Failed to initialize configuration:', error);
      this.config = DEFAULT_CONFIG;
      this.initialized = true;
    }
  }

  /**
   * Get current configuration
   */
  getConfig(): Config {
    if (!this.initialized) {
      console.warn('⚠️ Configuration not initialized, using defaults');
      return DEFAULT_CONFIG;
    }
    return this.config;
  }

  /**
   * Get API configuration
   */
  getApiConfig() {
    return this.getConfig().api;
  }

  /**
   * Get voice configuration
   */
  getVoiceConfig() {
    return this.getConfig().voice;
  }

  /**
   * Get app configuration
   */
  getAppConfig() {
    return this.getConfig().app;
  }

  /**
   * Update user configuration and persist to storage
   */
  async updateConfig(updates: Partial<Config>): Promise<boolean> {
    try {
      const updatedConfig = this.mergeConfigs(this.config, updates);
      
      // Validate updated configuration
      const validationResult = ConfigSchema.safeParse(updatedConfig);
      
      if (!validationResult.success) {
        console.error('❌ Configuration update validation failed:', validationResult.error);
        return false;
      }
      
      this.config = validationResult.data;
      
      // Persist user overrides to localStorage
      if (browser) {
        this.saveToStorage(updates);
      }
      
      console.log('✅ Configuration updated successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to update configuration:', error);
      return false;
    }
  }

  /**
   * Load configuration from environment variables
   */
  private loadFromEnvironment(): Partial<Config> {
    const envConfig: Partial<Config> = {};

    // API configuration from environment
    if (import.meta.env.PUBLIC_API_URL) {
      envConfig.api = {
        ...envConfig.api,
        baseUrl: import.meta.env.PUBLIC_API_URL,
      };
    }

    if (import.meta.env.PUBLIC_WS_URL) {
      envConfig.api = {
        ...envConfig.api,
        wsUrl: import.meta.env.PUBLIC_WS_URL,
      };
    }

    // Debug mode from environment
    if (import.meta.env.DEV) {
      envConfig.app = {
        ...envConfig.app,
        debugMode: true,
      };
    }

    return envConfig;
  }

  /**
   * Load user configuration from localStorage
   */
  private loadFromStorage(): Partial<Config> {
    try {
      const stored = localStorage.getItem('prsnl-config');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.warn('⚠️ Failed to load configuration from storage:', error);
    }
    return {};
  }

  /**
   * Save user configuration to localStorage
   */
  private saveToStorage(config: Partial<Config>): void {
    try {
      const existing = this.loadFromStorage();
      const merged = this.mergeConfigs(existing, config);
      localStorage.setItem('prsnl-config', JSON.stringify(merged));
    } catch (error) {
      console.warn('⚠️ Failed to save configuration to storage:', error);
    }
  }

  /**
   * Deep merge configuration objects
   */
  private mergeConfigs(...configs: Partial<Config>[]): Config {
    return configs.reduce((acc, config) => {
      return {
        api: { ...acc.api, ...config.api },
        voice: { ...acc.voice, ...config.voice },
        app: { ...acc.app, ...config.app },
      };
    }, DEFAULT_CONFIG);
  }

  /**
   * Handle configuration validation errors
   */
  private handleValidationError(error: ZodError): void {
    console.group('❌ Configuration Validation Errors:');
    error.errors.forEach((err) => {
      console.error(`- ${err.path.join('.')}: ${err.message}`);
    });
    console.groupEnd();
  }

  /**
   * Get configuration validation status
   */
  async validateCurrentConfig(): Promise<{ valid: boolean; errors?: ZodError }> {
    const result = ConfigSchema.safeParse(this.config);
    return {
      valid: result.success,
      errors: result.success ? undefined : result.error,
    };
  }

  /**
   * Reset configuration to defaults
   */
  async resetToDefaults(): Promise<void> {
    this.config = DEFAULT_CONFIG;
    if (browser) {
      localStorage.removeItem('prsnl-config');
    }
    console.log('✅ Configuration reset to defaults');
  }
}

// Export singleton instance
export const configService = new ConfigurationService();

// Export convenience functions
export const getConfig = () => configService.getConfig();
export const getApiConfig = () => configService.getApiConfig();
export const getVoiceConfig = () => configService.getVoiceConfig();
export const getAppConfig = () => configService.getAppConfig();