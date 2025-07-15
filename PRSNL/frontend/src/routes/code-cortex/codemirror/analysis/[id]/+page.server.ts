import type { PageServerLoad } from './$types';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params, fetch }) => {
  const { id: analysisId } = params;
  
  try {
    // Try to load by slug first (if it looks like a slug), then by ID
    let analysisResponse;
    
    // Check if it looks like a UUID (has dashes and is 36 chars)
    const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(analysisId);
    
    if (isUUID) {
      // Try by ID first
      analysisResponse = await fetch(`/api/codemirror/analysis/${analysisId}`, {
        headers: {
          'X-PRSNL-Integration': 'frontend'
        }
      });
    } else {
      // Try by slug first
      analysisResponse = await fetch(`/api/codemirror/analysis/by-slug/${analysisId}`, {
        headers: {
          'X-PRSNL-Integration': 'frontend'
        }
      });
    }
    
    // If first attempt fails and we tried UUID, try slug
    if (!analysisResponse.ok && isUUID) {
      analysisResponse = await fetch(`/api/codemirror/analysis/by-slug/${analysisId}`, {
        headers: {
          'X-PRSNL-Integration': 'frontend'
        }
      });
    }
    
    // If first attempt fails and we tried slug, try UUID
    if (!analysisResponse.ok && !isUUID) {
      analysisResponse = await fetch(`/api/codemirror/analysis/${analysisId}`, {
        headers: {
          'X-PRSNL-Integration': 'frontend'
        }
      });
    }
    
    if (!analysisResponse.ok) {
      console.error(`Analysis API failed: ${analysisResponse.status} ${analysisResponse.statusText}`);
      throw error(analysisResponse.status, `Analysis not found: ${analysisResponse.statusText}`);
    }
    
    const analysis = await analysisResponse.json();
    
    // Load insights for this analysis
    const insightsResponse = await fetch(`/api/codemirror/insights/${analysis.id}?status=open`, {
      headers: {
        'X-PRSNL-Integration': 'frontend'
      }
    });
    
    let insights = [];
    if (insightsResponse.ok) {
      insights = await insightsResponse.json();
    }
    
    // Parse languages and frameworks from the analysis
    let languages = [];
    let frameworks = [];
    let fileCount = analysis.file_count || 0;
    
    // Parse languages_detected JSON string
    if (analysis.languages_detected) {
      try {
        languages = JSON.parse(analysis.languages_detected);
      } catch (e) {
        languages = [];
      }
    }
    
    // Parse frameworks_detected JSON string
    if (analysis.frameworks_detected) {
      try {
        frameworks = JSON.parse(analysis.frameworks_detected);
      } catch (e) {
        frameworks = [];
      }
    }
    
    return {
      analysis,
      insights,
      analysisId,
      knowledgeContent: analysis.knowledge_content || '',
      languages,
      frameworks,
      fileCount
    };
  } catch (err) {
    console.error('Error loading analysis data:', err);
    
    if (err.status) {
      throw err; // Re-throw SvelteKit errors
    }
    
    throw error(500, 'Failed to load analysis data');
  }
};