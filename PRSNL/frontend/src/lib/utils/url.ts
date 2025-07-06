/**
 * URL utility functions for PRSNL
 * Helps with URL validation, detection, and processing
 */

/**
 * Detects if a URL is from Instagram
 * @param url The URL to check
 * @returns boolean indicating if the URL is from Instagram
 */
export function isInstagramUrl(url: string): boolean {
  if (!url) return false;
  
  try {
    const urlObj = new URL(url);
    return urlObj.hostname === 'instagram.com' || 
           urlObj.hostname === 'www.instagram.com' ||
           urlObj.hostname.endsWith('.instagram.com');
  } catch (e) {
    return false;
  }
}

/**
 * Detects if a URL is likely to be a video URL
 * @param url The URL to check
 * @returns boolean indicating if the URL is likely a video
 */
export function isVideoUrl(url: string): boolean {
  if (!url) return false;
  
  // Check for Instagram video patterns
  if (isInstagramUrl(url)) {
    return url.includes('/reel/') || 
           url.includes('/tv/') || 
           url.includes('/p/');  // Instagram posts can be videos too
  }
  
  // Check for YouTube
  if (isYouTubeUrl(url)) {
    return true;
  }
  
  // Check for Twitter videos
  if (isTwitterUrl(url)) {
    return url.includes('/video/');
  }
  
  // Check for TikTok
  if (isTikTokUrl(url)) {
    return true;
  }
  
  return false;
}

/**
 * Detects if a URL is from YouTube
 * @param url The URL to check
 * @returns boolean indicating if the URL is from YouTube
 */
export function isYouTubeUrl(url: string): boolean {
  if (!url) return false;
  
  try {
    const urlObj = new URL(url);
    return urlObj.hostname === 'youtube.com' || 
           urlObj.hostname === 'www.youtube.com' ||
           urlObj.hostname === 'youtu.be';
  } catch (e) {
    return false;
  }
}

/**
 * Detects if a URL is from Twitter
 * @param url The URL to check
 * @returns boolean indicating if the URL is from Twitter
 */
export function isTwitterUrl(url: string): boolean {
  if (!url) return false;
  
  try {
    const urlObj = new URL(url);
    return urlObj.hostname === 'twitter.com' || 
           urlObj.hostname === 'www.twitter.com' ||
           urlObj.hostname === 'x.com' ||
           urlObj.hostname === 'www.x.com';
  } catch (e) {
    return false;
  }
}

/**
 * Detects if a URL is from TikTok
 * @param url The URL to check
 * @returns boolean indicating if the URL is from TikTok
 */
export function isTikTokUrl(url: string): boolean {
  if (!url) return false;
  
  try {
    const urlObj = new URL(url);
    return urlObj.hostname === 'tiktok.com' || 
           urlObj.hostname === 'www.tiktok.com' ||
           urlObj.hostname.endsWith('.tiktok.com');
  } catch (e) {
    return false;
  }
}

/**
 * Gets the platform name from a URL
 * @param url The URL to check
 * @returns The platform name or null if not recognized
 */
export function getVideoPlatform(url: string): string | null {
  if (!url) return null;
  
  if (isInstagramUrl(url)) return 'Instagram';
  if (isYouTubeUrl(url)) return 'YouTube';
  if (isTwitterUrl(url)) return 'Twitter';
  if (isTikTokUrl(url)) return 'TikTok';
  
  return null;
}

/**
 * Estimates download time based on platform and network speed
 * @param url The URL to check
 * @param networkSpeedMbps Network speed in Mbps (default: 5)
 * @returns Estimated download time in seconds
 */
export function estimateDownloadTime(url: string, networkSpeedMbps: number = 5): number {
  if (!isVideoUrl(url)) return 0;
  
  // Average video sizes by platform in MB
  const avgSizes: Record<string, number> = {
    'Instagram': 15,
    'YouTube': 30,
    'Twitter': 10,
    'TikTok': 12
  };
  
  const platform = getVideoPlatform(url);
  if (!platform || !avgSizes[platform]) return 0;
  
  // Convert Mbps to MBps (divide by 8) and calculate time in seconds
  const speedMBps = networkSpeedMbps / 8;
  const estimatedTimeSeconds = avgSizes[platform] / speedMBps;
  
  return Math.round(estimatedTimeSeconds);
}

/**
 * Formats seconds into a human-readable time string
 * @param seconds Number of seconds
 * @returns Formatted time string (e.g., "2m 30s")
 */
export function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  
  if (remainingSeconds === 0) {
    return `${minutes}m`;
  }
  
  return `${minutes}m ${remainingSeconds}s`;
}
