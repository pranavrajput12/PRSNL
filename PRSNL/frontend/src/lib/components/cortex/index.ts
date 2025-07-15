// Cortex UI Components
// Shared template components for Code Cortex pages

export { default as CortexPageHeader } from './CortexPageHeader.svelte';
export { default as CortexTabNavigation } from './CortexTabNavigation.svelte';
export { default as CortexContentLayout } from './CortexContentLayout.svelte';
export { default as CortexCard } from './CortexCard.svelte';
export { default as CortexEmptyState } from './CortexEmptyState.svelte';
export { default as CortexLoadingState } from './CortexLoadingState.svelte';

// Type definitions for component props
export interface CortexTab {
  id: string;
  label: string;
  icon?: string;
  count?: number;
  disabled?: boolean;
}

export interface CortexStat {
  label: string;
  value: string | number;
}

export interface CortexAction {
  label: string;
  icon?: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

export interface CortexTag {
  label: string;
  color?: string;
}

export interface CortexCardAction {
  label: string;
  icon?: string;
  onClick: () => void;
}
