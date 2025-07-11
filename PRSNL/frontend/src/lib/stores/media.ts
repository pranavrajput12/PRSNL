/**
 * PRSNL Media Store
 * Manages media state and performance optimizations for videos
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';

// Types
export interface MediaSettings {
  preloadStrategy: 'none' | 'metadata' | 'auto';
  maxConcurrentVideos: number;
  thumbnailQuality: 'low' | 'medium' | 'high';
  enableProgressiveLoading: boolean;
  autoplayInViewport: boolean;
  networkSavingMode: boolean;
  logPerformanceMetrics: boolean;
}

export interface PerformanceMetrics {
  loadTimes: Record<string, number>;
  playbackStats: Record<
    string,
    {
      bufferingEvents: number;
      playbackStartTime: number;
      totalBufferingTime: number;
    }
  >;
  memoryUsage: number[];
  timestamps: number[];
}

// Default settings
const DEFAULT_SETTINGS: MediaSettings = {
  preloadStrategy: 'metadata',
  maxConcurrentVideos: 3,
  thumbnailQuality: 'medium',
  enableProgressiveLoading: true,
  autoplayInViewport: false,
  networkSavingMode: false,
  logPerformanceMetrics: true,
};

// Load settings from localStorage if available
function loadMediaSettings(): MediaSettings {
  if (browser) {
    const saved = localStorage.getItem('prsnl-media-settings');
    if (saved) {
      try {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(saved) };
      } catch (e) {
        console.error('Failed to parse media settings:', e);
      }
    }
  }
  return DEFAULT_SETTINGS;
}

// Create stores
export const mediaSettings = writable<MediaSettings>(loadMediaSettings());
export const activeVideoIds = writable<Set<string>>(new Set());
export const visibleVideoIds = writable<Set<string>>(new Set());
export const performanceMetrics = writable<PerformanceMetrics>({
  loadTimes: {},
  playbackStats: {},
  memoryUsage: [],
  timestamps: [],
});

// Save settings to localStorage when they change
if (browser) {
  mediaSettings.subscribe((value) => {
    localStorage.setItem('prsnl-media-settings', JSON.stringify(value));
  });
}

// Derived store for current preload strategy
export const preloadStrategy = derived(mediaSettings, ($settings) => $settings.preloadStrategy);

// Derived store to determine if we should load a video based on active count
export const canLoadMoreVideos = derived(
  [activeVideoIds, mediaSettings],
  ([$activeVideoIds, $mediaSettings]) => {
    return $activeVideoIds.size < $mediaSettings.maxConcurrentVideos;
  }
);

// Helper functions for media settings
export function updateMediaSetting<K extends keyof MediaSettings>(key: K, value: MediaSettings[K]) {
  mediaSettings.update((settings) => ({ ...settings, [key]: value }));
}

export function toggleNetworkSavingMode() {
  mediaSettings.update((settings) => {
    const networkSavingMode = !settings.networkSavingMode;
    return {
      ...settings,
      networkSavingMode,
      preloadStrategy: networkSavingMode ? 'none' : 'metadata',
      maxConcurrentVideos: networkSavingMode ? 1 : 3,
      thumbnailQuality: networkSavingMode ? 'low' : 'medium',
    };
  });
}

// Video tracking functions
export function registerVideoView(videoId: string) {
  visibleVideoIds.update((ids) => {
    const newIds = new Set(ids);
    newIds.add(videoId);
    return newIds;
  });
}

export function unregisterVideoView(videoId: string) {
  visibleVideoIds.update((ids) => {
    const newIds = new Set(ids);
    newIds.delete(videoId);
    return newIds;
  });
}

export function activateVideo(videoId: string) {
  const $mediaSettings = get(mediaSettings);
  const $activeVideoIds = get(activeVideoIds);

  // If we've reached max concurrent videos and network saving is on,
  // deactivate the oldest video
  if (
    $activeVideoIds.size >= $mediaSettings.maxConcurrentVideos &&
    $mediaSettings.networkSavingMode
  ) {
    const oldestId = Array.from($activeVideoIds)[0];
    deactivateVideo(oldestId);
  }

  activeVideoIds.update((ids) => {
    const newIds = new Set(ids);
    newIds.add(videoId);
    return newIds;
  });
}

export function deactivateVideo(videoId: string) {
  activeVideoIds.update((ids) => {
    const newIds = new Set(ids);
    newIds.delete(videoId);
    return newIds;
  });
}

// Performance monitoring functions
export function recordLoadTime(videoId: string, loadTimeMs: number) {
  if (!get(mediaSettings).logPerformanceMetrics) return;

  performanceMetrics.update((metrics) => {
    return {
      ...metrics,
      loadTimes: {
        ...metrics.loadTimes,
        [videoId]: loadTimeMs,
      },
    };
  });
}

export function recordBufferingEvent(videoId: string) {
  if (!get(mediaSettings).logPerformanceMetrics) return;

  performanceMetrics.update((metrics) => {
    const videoStats = metrics.playbackStats[videoId] || {
      bufferingEvents: 0,
      playbackStartTime: Date.now(),
      totalBufferingTime: 0,
    };

    return {
      ...metrics,
      playbackStats: {
        ...metrics.playbackStats,
        [videoId]: {
          ...videoStats,
          bufferingEvents: videoStats.bufferingEvents + 1,
        },
      },
    };
  });
}

export function recordMemoryUsage() {
  if (!get(mediaSettings).logPerformanceMetrics || !browser) return;

  // Use performance API to get memory info if available
  const memory = (performance as any).memory?.usedJSHeapSize;

  if (memory) {
    performanceMetrics.update((metrics) => {
      return {
        ...metrics,
        memoryUsage: [...metrics.memoryUsage, memory],
        timestamps: [...metrics.timestamps, Date.now()],
      };
    });
  }
}

// Start periodic memory usage monitoring
if (browser && get(mediaSettings).logPerformanceMetrics) {
  const memoryMonitoringInterval = setInterval(recordMemoryUsage, 30000); // Every 30 seconds

  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    clearInterval(memoryMonitoringInterval);
  });
}

// Get performance report
export function getPerformanceReport(): string {
  const metrics = get(performanceMetrics);
  const settings = get(mediaSettings);

  const avgLoadTime =
    Object.values(metrics.loadTimes).reduce((sum, time) => sum + time, 0) /
    (Object.values(metrics.loadTimes).length || 1);

  const totalBufferingEvents = Object.values(metrics.playbackStats).reduce(
    (sum, stat) => sum + stat.bufferingEvents,
    0
  );

  return `
Performance Report:
------------------
Average video load time: ${avgLoadTime.toFixed(2)}ms
Total buffering events: ${totalBufferingEvents}
Active videos: ${get(activeVideoIds).size}
Visible videos: ${get(visibleVideoIds).size}
Preload strategy: ${settings.preloadStrategy}
Network saving mode: ${settings.networkSavingMode ? 'On' : 'Off'}
Max concurrent videos: ${settings.maxConcurrentVideos}
  `;
}
