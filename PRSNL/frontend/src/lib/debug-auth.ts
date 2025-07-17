/**
 * Authentication debugging utilities
 */

export interface AuthDebugLog {
  timestamp: string;
  event: string;
  details: any;
  url?: string;
  error?: string;
}

class AuthDebugger {
  private logs: AuthDebugLog[] = [];
  private maxLogs = 100;

  log(event: string, details: any, error?: string) {
    const entry: AuthDebugLog = {
      timestamp: new Date().toISOString(),
      event,
      details,
      url: window.location.href,
      error
    };

    this.logs.unshift(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.pop();
    }

    // Always log to console in development
    if (import.meta.env.DEV) {
      console.log(`🔐 AUTH DEBUG [${event}]:`, details, error ? `Error: ${error}` : '');
    }

    // Store in localStorage for persistence
    try {
      localStorage.setItem('auth-debug-logs', JSON.stringify(this.logs.slice(0, 50)));
    } catch (e) {
      console.warn('Failed to save auth debug logs:', e);
    }
  }

  getLogs(): AuthDebugLog[] {
    return [...this.logs];
  }

  clearLogs() {
    this.logs = [];
    localStorage.removeItem('auth-debug-logs');
  }

  // Load logs from localStorage on page refresh
  loadStoredLogs() {
    try {
      const stored = localStorage.getItem('auth-debug-logs');
      if (stored) {
        this.logs = JSON.parse(stored);
      }
    } catch (e) {
      console.warn('Failed to load stored auth debug logs:', e);
    }
  }

  // Export logs for debugging
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
}

export const authDebugger = new AuthDebugger();

// Load stored logs on initialization
if (typeof window !== 'undefined') {
  authDebugger.loadStoredLogs();
}

// Add global debug function
if (typeof window !== 'undefined') {
  (window as any).debugAuth = {
    logs: () => authDebugger.getLogs(),
    export: () => authDebugger.exportLogs(),
    clear: () => authDebugger.clearLogs()
  };
}