/**
 * Job Persistence Store for CodeMirror
 *
 * Manages real-time job progress tracking and WebSocket communication
 */

import { writable } from 'svelte/store';

interface Job {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  stage: string;
  message?: string;
  created_at: string;
  updated_at: string;
}

interface JobPersistenceStore {
  jobs: Map<string, Job>;
  isConnected: boolean;
}

function createJobPersistenceStore() {
  const { subscribe, set, update } = writable<JobPersistenceStore>({
    jobs: new Map(),
    isConnected: false,
  });

  let ws: WebSocket | null = null;

  return {
    subscribe,

    // Initialize WebSocket connection
    connect: () => {
      if (ws?.readyState === WebSocket.OPEN) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/jobs`;

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        update((store) => ({ ...store, isConnected: true }));
      };

      ws.onmessage = (event) => {
        try {
          const jobUpdate = JSON.parse(event.data);
          update((store) => {
            const newJobs = new Map(store.jobs);
            newJobs.set(jobUpdate.job_id, jobUpdate);
            return { ...store, jobs: newJobs };
          });
        } catch (error) {
          console.error('Failed to parse job update:', error);
        }
      };

      ws.onclose = () => {
        update((store) => ({ ...store, isConnected: false }));
        // Reconnect after 3 seconds
        setTimeout(() => createJobPersistenceStore().connect(), 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    },

    // Monitor specific job
    monitorJob: (jobId: string) => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'monitor', job_id: jobId }));
      }
    },

    // Get job by ID
    getJob: (jobId: string): Job | undefined => {
      let currentJob: Job | undefined;
      update((store) => {
        currentJob = store.jobs.get(jobId);
        return store;
      });
      return currentJob;
    },

    // Disconnect WebSocket
    disconnect: () => {
      if (ws) {
        ws.close();
        ws = null;
      }
      update((store) => ({ ...store, isConnected: false }));
    },
  };
}

export const jobPersistenceStore = createJobPersistenceStore();
