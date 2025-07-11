// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
  namespace App {
    interface Error {
      message: string;
      code?: string;
      status?: number;
    }

    interface Locals {
      user?: {
        id: string;
        email?: string;
      };
      apiKey?: string;
    }

    interface PageData {
      title?: string;
      description?: string;
    }

    interface PageState {
      search?: {
        query: string;
        filters: Record<string, string>;
      };
    }

    // interface Platform {}
  }

  // Add support for environment variables
  interface ImportMetaEnv {
    readonly PUBLIC_API_URL: string;
    readonly PUBLIC_WS_URL: string;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

export {};
