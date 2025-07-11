import { writable, derived } from 'svelte/store';
import type {
  InsightsResponse,
  TopicCluster,
  ContentTrendPoint,
  KnowledgeGraphData,
  TopContentItem,
} from '$lib/types/api';
import { getInsights } from '$lib/api';

// Define types for the store
type InsightsState = {
  data: InsightsResponse | null;
  isLoading: boolean;
  error: Error | null;
  timeRange: string;
  selectedCluster: string | null;
  exportFormat: 'pdf' | 'csv' | 'json' | null;
  exportInProgress: boolean;
};

// Create the initial state
const initialState: InsightsState = {
  data: null,
  isLoading: false,
  error: null,
  timeRange: 'week',
  selectedCluster: null,
  exportFormat: null,
  exportInProgress: false,
};

// Create the writable store
function createInsightsStore() {
  const { subscribe, set, update } = writable<InsightsState>(initialState);

  // Load insights data for a specific time range
  async function loadInsights(timeRange: string) {
    update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const response = await getInsights({ timeRange });
      update((state) => ({
        ...state,
        data: response,
        isLoading: false,
        timeRange,
      }));
      return response;
    } catch (error) {
      update((state) => ({
        ...state,
        error: error as Error,
        isLoading: false,
      }));
      throw error;
    }
  }

  // Set selected cluster
  function setSelectedCluster(clusterId: string | null) {
    update((state) => ({ ...state, selectedCluster: clusterId }));
  }

  // Reset the store to initial state
  function reset() {
    set(initialState);
  }

  // Export insights data in the specified format
  async function exportInsights(format: 'pdf' | 'csv' | 'json') {
    update((state) => ({ ...state, exportFormat: format, exportInProgress: true }));

    try {
      // This would normally call a backend API for generating exports
      // For now, we'll simulate the export process
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const data = await getFormattedData(format);
      downloadData(data, `insights-export-${new Date().toISOString().split('T')[0]}.${format}`);

      update((state) => ({ ...state, exportInProgress: false, exportFormat: null }));
    } catch (error) {
      update((state) => ({
        ...state,
        error: error as Error,
        exportInProgress: false,
        exportFormat: null,
      }));
      throw error;
    }
  }

  // Helper function to get formatted data for export
  async function getFormattedData(format: string) {
    let result: string = '';
    let state: InsightsState;

    // Get current state from the store
    subscribe((s) => {
      state = s;
    })();

    if (!state.data) {
      throw new Error('No insights data available to export');
    }

    switch (format) {
      case 'json':
        result = JSON.stringify(state.data, null, 2);
        break;
      case 'csv':
        // Create CSV format for trend data
        const headers = 'Date,Articles,Videos,Notes,Bookmarks,Total\n';
        const rows = state.data.contentTrends
          ?.map((point) => {
            const total = point.articles + point.videos + point.notes + point.bookmarks;
            return `${point.date},${point.articles},${point.videos},${point.notes},${point.bookmarks},${total}`;
          })
          .join('\n');
        result = headers + rows;
        break;
      case 'pdf':
        // In a real implementation, this would generate a PDF
        // For now, we'll return a placeholder text representation
        result = JSON.stringify(state.data, null, 2);
        break;
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }

    return result;
  }

  // Helper function to download data
  function downloadData(data: string, filename: string) {
    // In a browser environment, this would create a download
    // For development purposes, we'll log the data
    console.log(`Downloading ${filename} with data:`, data.substring(0, 100) + '...');

    // In a real implementation, we would use:
    const blob = new Blob([data], { type: getMimeType(filename) });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // Helper function to get mime type
  function getMimeType(filename: string): string {
    if (filename.endsWith('.json')) return 'application/json';
    if (filename.endsWith('.csv')) return 'text/csv';
    if (filename.endsWith('.pdf')) return 'application/pdf';
    return 'text/plain';
  }

  return {
    subscribe,
    loadInsights,
    setSelectedCluster,
    reset,
    exportInsights,
  };
}

// Create and export the store
export const insights = createInsightsStore();

// Create derived stores for specific pieces of data
export const topicClusters = derived(insights, ($insights) => $insights.data?.topicClusters || []);

export const contentTrends = derived(insights, ($insights) => $insights.data?.contentTrends || []);

export const knowledgeGraph = derived(
  insights,
  ($insights) => $insights.data?.knowledgeGraph || { nodes: [], links: [] }
);

export const topContent = derived(insights, ($insights) => $insights.data?.topContent || []);

export const isLoading = derived(insights, ($insights) => $insights.isLoading);

export const error = derived(insights, ($insights) => $insights.error);

export const selectedCluster = derived(insights, ($insights) => $insights.selectedCluster);

export const timeRange = derived(insights, ($insights) => $insights.timeRange);

export const exportInProgress = derived(insights, ($insights) => $insights.exportInProgress);
