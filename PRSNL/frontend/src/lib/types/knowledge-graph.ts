/**
 * Knowledge Graph Types
 * 
 * Type definitions for the knowledge graph visualization system
 */

export interface GraphNode {
  id: string;
  title: string;
  type: string;
  summary?: string;
  tags?: string[];
  importance?: number;
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
  
  // Additional metadata
  createdAt?: string;
  updatedAt?: string;
  url?: string;
  category?: string;
  status?: string;
}

export interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  relationship: string;
  strength: number;
  weight?: number;
  
  // Additional metadata
  createdAt?: string;
  description?: string;
  automatic?: boolean;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata: {
    totalNodes: number;
    totalEdges: number;
    nodeTypes: Record<string, number>;
    relationshipTypes: Record<string, number>;
    lastUpdated: string;
  };
}

export interface GraphFilters {
  contentType?: string;
  category?: string;
  minStrength?: number;
  maxNodes?: number;
  depth?: number;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface GraphLayout {
  algorithm: 'force' | 'hierarchical' | 'circular';
  options: {
    linkDistance?: number;
    chargeStrength?: number;
    centerForce?: number;
    collision?: boolean;
    collisionRadius?: number;
  };
}

export interface GraphVisualizationConfig {
  width: number;
  height: number;
  layout: GraphLayout;
  colors: {
    nodes: Record<string, string>;
    edges: Record<string, string>;
    background: string;
  };
  showLabels: boolean;
  labelThreshold: number;
  zoomEnabled: boolean;
  dragEnabled: boolean;
}

// D3-specific interfaces for force simulation
export interface D3Node extends GraphNode {
  x: number;
  y: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  index?: number;
}

export interface D3Edge extends GraphEdge {
  source: D3Node;
  target: D3Node;
  index?: number;
}

// Event types for graph interactions
export interface GraphNodeEvent {
  type: 'click' | 'hover' | 'drag';
  node: GraphNode;
  event: MouseEvent;
}

export interface GraphEdgeEvent {
  type: 'click' | 'hover';
  edge: GraphEdge;
  event: MouseEvent;
}

// Knowledge graph relationship types
export type RelationshipType = 
  | 'extends'
  | 'related'
  | 'prerequisite'
  | 'contradicts'
  | 'implements'
  | 'references'
  | 'part_of'
  | 'alternative'
  | 'duplicate'
  | 'similar'
  | 'follows'
  | 'builds_on'
  | 'explains'
  | 'example_of';

// Content type mappings for nodes
export type ContentType = 
  | 'article'
  | 'video'
  | 'code'
  | 'recipe'
  | 'bookmark'
  | 'document'
  | 'repository'
  | 'conversation'
  | 'screenshot'
  | 'note'
  | 'item';

// Export utility types
export type NodeId = string;
export type EdgeId = string;
export type GraphId = string;