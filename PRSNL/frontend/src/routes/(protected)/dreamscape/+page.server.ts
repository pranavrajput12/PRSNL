import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, cookies }) => {
  // Pre-load any server-side data needed for the Dreamscape dashboard
  // This could include initial persona data, user preferences, etc.
  
  try {
    // For now, we'll let the client-side handle the API calls
    // This can be enhanced later for SSR optimization
    return {
      title: 'Dreamscape - Personal Intelligence Dashboard',
      description: 'Your AI-powered personal intelligence system that learns from your behavior and preferences'
    };
  } catch (error) {
    console.error('Error loading Dreamscape data:', error);
    return {
      title: 'Dreamscape - Personal Intelligence Dashboard',
      description: 'Your AI-powered personal intelligence system that learns from your behavior and preferences',
      error: 'Failed to load initial data'
    };
  }
};