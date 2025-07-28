import type { PageServerLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { getItemRoute } from '$lib/config/templateMapping';

export const load: PageServerLoad = async ({ params, fetch }) => {
  // Fetch the item to determine its type
  try {
    const response = await fetch(`/api/items/${params.id}`);
    if (!response.ok) {
      // If item not found, continue with generic template
      return {};
    }
    
    const item = await response.json();
    
    // Get the appropriate route based on item type
    const targetRoute = getItemRoute(params.id, item.type || 'default');
    
    // If it's not the generic route, redirect to the specific template
    if (targetRoute !== `/item/${params.id}`) {
      throw redirect(307, targetRoute);
    }
    
    // Otherwise, continue with the current page
    return {
      item
    };
  } catch (error) {
    // If it's a redirect, throw it
    if (error instanceof Response && error.status >= 300 && error.status < 400) {
      throw error;
    }
    
    // For other errors, continue with generic template
    console.error('Error determining item type:', error);
    return {};
  }
};