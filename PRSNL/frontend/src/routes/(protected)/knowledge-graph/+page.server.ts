import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
  // The knowledge graph page loads data dynamically via API calls
  // No need to pre-load data here
  
  return {
    title: 'Knowledge Graph | PRSNL',
    description: 'Explore semantic connections between your content'
  };
};