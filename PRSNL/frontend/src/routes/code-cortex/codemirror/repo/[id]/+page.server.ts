import type { PageServerLoad } from './$types';
import { error, redirect } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params, fetch, url }) => {
  const { id: repoId } = params;
  
  try {
    // Try to load by slug first, then by ID
    let repoResponse = await fetch(`/api/github/repos/by-slug/${repoId}`, {
      headers: {
        'X-PRSNL-Integration': 'frontend'
      }
    });
    
    // If slug lookup fails, try by ID
    if (!repoResponse.ok) {
      repoResponse = await fetch(`/api/github/repos/${repoId}`, {
        headers: {
          'X-PRSNL-Integration': 'frontend'
        }
      });
    }
    
    // Load CodeMirror analyses using the same logic
    let analysesResponse = await fetch(`/api/codemirror/repo/by-slug/${repoId}/analyses`, {
      headers: {
        'X-PRSNL-Integration': 'frontend'
      }
    });
    
    // If slug lookup fails, try by repo ID
    if (!analysesResponse.ok) {
      analysesResponse = await fetch(`/api/codemirror/analyses/${repoId}`, {
        headers: {
          'X-PRSNL-Integration': 'frontend'
        }
      });
    }
    
    let repository = null;
    let analyses = [];
    
    if (repoResponse.ok) {
      repository = await repoResponse.json();
    }
    
    if (analysesResponse.ok) {
      analyses = await analysesResponse.json();
    }
    
    // If we can't get repository info from GitHub API but have analyses,
    // get repo name from first analysis
    if (!repository && analyses.length > 0 && analyses[0].repository_name) {
      repository = {
        id: repoId,
        name: analyses[0].repository_name,
        description: 'Repository from CodeMirror analysis'
      };
    }
    
    // If we still don't have repository info, this repo might not exist
    if (!repository && analyses.length === 0) {
      throw error(404, 'Repository not found');
    }
    
    return {
      repository,
      analyses,
      repoId
    };
  } catch (err) {
    console.error('Error loading repository data:', err);
    
    // If it's a 404, let it pass through
    if (err.status === 404) {
      throw err;
    }
    
    // For other errors, return empty data and let client handle
    return {
      repository: null,
      analyses: [],
      repoId,
      loadError: err.message || 'Failed to load repository data'
    };
  }
};