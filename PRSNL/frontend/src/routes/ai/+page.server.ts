import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, fetch }) => {
  // If the user isn't authenticated, redirect to login
  if (!locals.user) {
    throw redirect(302, '/login');
  }
  
  // We'll load data client-side via the API for better user experience
  // This is just a placeholder for server-side authorization checks
  
  return {
    user: locals.user
  };
};
