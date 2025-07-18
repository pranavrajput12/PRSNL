import { writable, derived } from 'svelte/store';
import { page } from '$app/stores';

export interface FloatingChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface FloatingChatState {
  isOpen: boolean;
  messages: FloatingChatMessage[];
  isLoading: boolean;
  position: 'bottom-right' | 'bottom-left';
  size: 'compact' | 'expanded';
}

// Initialize floating chat state
const initialState: FloatingChatState = {
  isOpen: false,
  messages: [],
  isLoading: false,
  position: 'bottom-right',
  size: 'compact'
};

// Create the store
export const floatingChatStore = writable<FloatingChatState>(initialState);

// Helper functions
export const floatingChatActions = {
  toggle: () => {
    floatingChatStore.update(state => ({ ...state, isOpen: !state.isOpen }));
  },
  
  open: () => {
    floatingChatStore.update(state => ({ ...state, isOpen: true }));
  },
  
  close: () => {
    floatingChatStore.update(state => ({ ...state, isOpen: false }));
  },
  
  addMessage: (message: Omit<FloatingChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: FloatingChatMessage = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date()
    };
    
    floatingChatStore.update(state => ({
      ...state,
      messages: [...state.messages, newMessage]
    }));
    
    return newMessage;
  },
  
  setLoading: (isLoading: boolean) => {
    floatingChatStore.update(state => ({ ...state, isLoading }));
  },
  
  clearMessages: () => {
    floatingChatStore.update(state => ({ ...state, messages: [] }));
  },
  
  setPosition: (position: 'bottom-right' | 'bottom-left') => {
    floatingChatStore.update(state => ({ ...state, position }));
  },
  
  setSize: (size: 'compact' | 'expanded') => {
    floatingChatStore.update(state => ({ ...state, size }));
  }
};

// Determine page type based on current route
export function getPageType(pathname: string): string {
  if (pathname === '/') return 'dashboard';
  if (pathname.startsWith('/items/')) return 'item-detail';
  if (pathname === '/timeline') return 'timeline';
  if (pathname === '/capture') return 'capture';
  if (pathname.startsWith('/code-cortex')) return 'code-cortex';
  if (pathname === '/development') return 'development';
  if (pathname === '/chat') return 'chat';
  return 'unknown';
}

// Get page-specific quick actions
export function getQuickActions(pageType: string): string[] {
  const actions: Record<string, string[]> = {
    'dashboard': [
      'Summarize my recent activity',
      'What did I save today?',
      'Show trending topics',
      'Find duplicates'
    ],
    'item-detail': [
      'Summarize this',
      'Find similar items',
      'Extract key points',
      'Generate tags'
    ],
    'timeline': [
      'What happened this week?',
      'Show productivity insights',
      'Find patterns',
      'Weekly summary'
    ],
    'code-cortex': [
      'Explain this code',
      'Find security issues',
      'Suggest improvements',
      'Generate documentation'
    ],
    'development': [
      'Debug this error',
      'Best practices for...',
      'Generate boilerplate',
      'Explain architecture'
    ]
  };
  
  return actions[pageType] || ['How can I help?'];
}