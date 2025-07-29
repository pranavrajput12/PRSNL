<!--
  Content Type Indicator Component
  
  Displays a visual indicator for content types with icon and color coding.
-->

<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';
  
  export let type: string;
  export let label: string;
  export let color: string = '#6B7280';
  export let icon: string = 'file';
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let variant: 'filled' | 'outlined' | 'subtle' = 'subtle';
  
  $: sizeClasses = {
    small: 'indicator-small',
    medium: 'indicator-medium', 
    large: 'indicator-large'
  };
  
  $: variantClasses = {
    filled: 'indicator-filled',
    outlined: 'indicator-outlined',
    subtle: 'indicator-subtle'
  };
</script>

<div 
  class="content-type-indicator {sizeClasses[size]} {variantClasses[variant]}"
  style="--indicator-color: {color}"
  title="{label} content"
>
  <Icon name={icon} size={size === 'large' ? 'medium' : 'small'} />
  <span class="indicator-label">{label}</span>
</div>

<style>
  .content-type-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    border-radius: 20px;
    font-weight: 500;
    white-space: nowrap;
    transition: all 0.2s;
  }
  
  /* Size variations */
  .indicator-small {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    gap: 0.25rem;
  }
  
  .indicator-medium {
    padding: 0.375rem 0.75rem;
    font-size: 0.875rem;
    gap: 0.5rem;
  }
  
  .indicator-large {
    padding: 0.5rem 1rem;
    font-size: 1rem;
    gap: 0.75rem;
  }
  
  /* Variant styles */
  .indicator-filled {
    background: var(--indicator-color);
    color: white;
  }
  
  .indicator-outlined {
    background: transparent;
    border: 1px solid var(--indicator-color);
    color: var(--indicator-color);
  }
  
  .indicator-subtle {
    background: color-mix(in srgb, var(--indicator-color) 15%, transparent);
    color: var(--indicator-color);
    border: 1px solid color-mix(in srgb, var(--indicator-color) 30%, transparent);
  }
  
  /* Fallback for browsers that don't support color-mix */
  @supports not (color: color-mix(in srgb, red, blue)) {
    .indicator-subtle {
      background: rgba(107, 114, 128, 0.15);
      border: 1px solid rgba(107, 114, 128, 0.3);
    }
  }
  
  .indicator-label {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }
  
  /* Hover effects */
  .indicator-filled:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
  }
  
  .indicator-outlined:hover,
  .indicator-subtle:hover {
    background: color-mix(in srgb, var(--indicator-color) 25%, transparent);
    transform: translateY(-1px);
  }
  
  /* Fallback hover for browsers that don't support color-mix */
  @supports not (color: color-mix(in srgb, red, blue)) {
    .indicator-outlined:hover,
    .indicator-subtle:hover {
      background: rgba(107, 114, 128, 0.25);
    }
  }
  
  /* Responsive adjustments */
  @media (max-width: 768px) {
    .indicator-large {
      padding: 0.375rem 0.75rem;
      font-size: 0.875rem;
      gap: 0.5rem;
    }
    
    .indicator-medium {
      padding: 0.25rem 0.5rem;
      font-size: 0.75rem;
      gap: 0.25rem;
    }
  }
</style>