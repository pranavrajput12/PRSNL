/**
 * API type definitions for PRSNL frontend
 */

// Enums matching backend
export enum ItemStatus {
  PENDING = 'pending',
  COMPLETED = 'completed',
  FAILED = 'failed',
  BOOKMARK = 'bookmark'
}

export enum ItemType {
  ARTICLE = 'article',
  VIDEO = 'video',
  NOTE = 'note',
  BOOKMARK = 'bookmark',
  IMAGE = 'image'
}

// Base types
export interface Tag {
  id: string;
  name: string;
  count?: number;
  created_at?: string;
}

export interface AIAnalysis {
  title: string;
  summary: string;
  tags: string[];
  key_points?: string[];
  questions?: string[];
  entities?: {
    Prerequisites?: string[];
    Tools?: string[];
    Skills?: string[];
  };
  sentiment?: string;
  reading_time?: number;
  score?: number;
}

export interface VideoMetadata {
  width: number;
  height: number;
  duration: number;
  fps?: number;
  codec?: string;
  bitrate?: number;
  view_count?: number;
  like_count?: number;
  channel?: string;
}

export interface ItemMetadata {
  ai_analysis?: AIAnalysis;
  video_metadata?: VideoMetadata;
  processing_progress?: {
    status: string;
    percent: number;
    message?: string;
  };
  [key: string]: any; // For additional metadata
}

// Item type
export interface Item {
  id: string;
  url?: string;
  title: string;
  content?: string;
  summary?: string;
  item_type: ItemType;
  status: ItemStatus;
  created_at: string;
  updated_at?: string;
  accessed_at?: string;
  access_count: number;
  tags: string[];
  file_path?: string;
  thumbnail_url?: string;
  duration?: number;
  platform?: string;
  transcription?: string;
  metadata?: ItemMetadata;
}

// API Request types
export interface CaptureRequest {
  url?: string;
  content?: string;
  title?: string;
  highlight?: string;
  tags?: string[];
  type?: 'page' | 'selection';
  enable_summarization?: boolean;
  content_type?: string;
  uploaded_files?: File[];
  // Development-specific fields
  programming_language?: string;
  project_category?: string;
  difficulty_level?: number;
  is_career_related?: boolean;
  is_video?: boolean;
  video_platform?: string | null;
  video_quality?: string;
}

export interface SearchRequest {
  query: string;
  tags?: string[];
  limit?: number;
  offset?: number;
}

export interface UpdateItemRequest {
  title?: string;
  summary?: string;
  tags?: string[];
}

// API Response types
export interface CaptureResponse {
  id: string;
  status: ItemStatus;
  message: string;
}

export interface SearchResult {
  id: string;
  title: string;
  url?: string;
  snippet: string;
  tags: string[];
  created_at: string;
  score?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  took_ms: number;
}

export interface TimelineItem {
  id: string;
  title: string;
  url?: string;
  snippet: string;
  summary?: string;
  type?: string;
  thumbnail_url?: string;
  duration?: number;
  platform?: string;
  file_path?: string;
  tags: string[];
  created_at: string;
  createdAt?: string; // Alternative field name
  updatedAt?: string;
  status?: string;
}

export interface TimelineResponse {
  items: TimelineItem[];
  hasMore: boolean;
  nextCursor?: string | null;
}

export interface TagsResponse {
  tags: Tag[];
  total: number;
}

export interface StorageStats {
  total_items: number;
  total_size_mb: number;
  breakdown: {
    video: { count: number; size_mb: number };
    article: { count: number; size_mb: number };
    note: { count: number; size_mb: number };
  };
}

// Error response
export interface APIError {
  error: string;
  message: string;
  detail?: string;
  retry_after?: number;
}

// Pagination
export interface PaginationParams {
  offset?: number;
  limit?: number;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'progress' | 'update' | 'notification' | 'error';
  data: any;
  item_id?: string;
  timestamp?: string;
}

// AI Insights Dashboard types
export interface TopicCluster {
  id: string;
  name: string;
  count: number;
  group: string;
  importance: number;
}

export interface ContentTrendPoint {
  date: string;
  articles: number;
  videos: number;
  notes: number;
  bookmarks: number;
}

export interface KnowledgeGraphNode {
  id: string;
  name: string;
  type: string; // Dynamic type
  cluster?: string;
  importance?: number;
  connections?: number;
  date?: string;
  url?: string;
  // D3 simulation properties
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  index?: number;
}

export interface KnowledgeGraphLink {
  source: string | KnowledgeGraphNode;
  target: string | KnowledgeGraphNode;
  value?: number;
  type?: string;
}

export interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  links: KnowledgeGraphLink[];
}

export interface TagAnalysis {
  name: string;
  weight: number;
  hue: number;
  count: number;
}

export interface InsightsResponse {
  topicClusters: TopicCluster[];
  contentTrends: ContentTrendPoint[];
  knowledgeGraph: KnowledgeGraph;
  topContent: Item[];
  tagAnalysis: TagAnalysis[];
}