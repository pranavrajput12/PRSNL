<script lang="ts" type="module">
  export let name = '';
  export let size: 'small' | 'medium' | 'large' | string | number = 'medium';
  export let color = 'currentColor';
  export let strokeWidth = 2;
  
  // Add support for class prop
  let className = '';
  export { className as class };

  const sizeMap: Record<string, number> = {
    small: 16,
    medium: 20,
    large: 24,
  };

  $: width = typeof size === 'number' ? size : (sizeMap[size] || 20);
  $: height = typeof size === 'number' ? size : (sizeMap[size] || 20);
</script>

{#if name === 'capture'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round"
    class={className}
  >
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
{:else if name === 'search'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <circle cx="11" cy="11" r="8" />
    <path d="m21 21-4.35-4.35" />
  </svg>
{:else if name === 'timeline'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
{:else if name === 'plus'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
{:else if name === 'close'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
{:else if name === 'check'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polyline points="20 6 9 17 4 12" />
  </svg>
{:else if name === 'alert'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
{:else if name === 'info'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="16" x2="12" y2="12" />
    <line x1="12" y1="8" x2="12.01" y2="8" />
  </svg>
{:else if name === 'tag'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="m20.59 13.41-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
    <line x1="7" y1="7" x2="7.01" y2="7" />
  </svg>
{:else if name === 'link'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
  </svg>
{:else if name === 'calendar'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </svg>
{:else if name === 'filter'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </svg>
{:else if name === 'sparkles'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path
      d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"
    />
    <path d="M5 3v4" />
    <path d="M19 17v4" />
    <path d="M3 5h4" />
    <path d="M17 19h4" />
  </svg>
{:else if name === 'prsnl-logo'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <!-- Neural Network Core -->
    <circle cx="12" cy="12" r="4" fill={color} opacity="0.1" />
    <circle cx="12" cy="12" r="2" fill={color} opacity="0.3" />

    <!-- Neural Connections -->
    <path
      d="M12 4c-2.5 0-4.5 2-4.5 4.5S9.5 13 12 13s4.5-2 4.5-4.5S14.5 4 12 4z"
      fill={color}
      opacity="0.15"
    />
    <path
      d="M12 11c-2.5 0-4.5 2-4.5 4.5S9.5 20 12 20s4.5-2 4.5-4.5S14.5 11 12 11z"
      fill={color}
      opacity="0.15"
    />

    <!-- Synaptic Nodes -->
    <circle cx="8" cy="8" r="1.5" fill={color} />
    <circle cx="16" cy="8" r="1.5" fill={color} />
    <circle cx="8" cy="16" r="1.5" fill={color} />
    <circle cx="16" cy="16" r="1.5" fill={color} />
    <circle cx="4" cy="12" r="1" fill={color} opacity="0.7" />
    <circle cx="20" cy="12" r="1" fill={color} opacity="0.7" />
    <circle cx="12" cy="4" r="1" fill={color} opacity="0.7" />
    <circle cx="12" cy="20" r="1" fill={color} opacity="0.7" />

    <!-- Neural Pathways -->
    <path d="M8 8L12 10L16 8" stroke={color} stroke-width="1" opacity="0.6" />
    <path d="M8 16L12 14L16 16" stroke={color} stroke-width="1" opacity="0.6" />
    <path d="M8 8L10 12L8 16" stroke={color} stroke-width="1" opacity="0.6" />
    <path d="M16 8L14 12L16 16" stroke={color} stroke-width="1" opacity="0.6" />

    <!-- P-R-S-N-L Letter Integration -->
    <path d="M6 6L9 9" stroke={color} stroke-width="2" opacity="0.8" />
    <path d="M15 9L18 6" stroke={color} stroke-width="2" opacity="0.8" />
    <path d="M6 18L9 15" stroke={color} stroke-width="2" opacity="0.8" />
    <path d="M15 15L18 18" stroke={color} stroke-width="2" opacity="0.8" />
  </svg>
{:else if name === 'arrow-right'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </svg>
{:else if name === 'external-link'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </svg>
{:else if name === 'video'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
    <polygon points="10 8 16 12 10 16 10 8" />
  </svg>
{:else if name === 'home'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline points="9 22 9 12 15 12 15 22" />
  </svg>
{:else if name === 'brain'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" />
    <rect x="3" y="14" width="7" height="7" />
    <line x1="9" y1="9" x2="9" y2="15" />
    <line x1="15" y1="9" x2="15" y2="15" />
    <line x1="9" y1="15" x2="15" y2="15" />
    <line x1="9" y1="9" x2="15" y2="9" />
  </svg>
{:else if name === 'ingest'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M12 2L8 8h8l-4-6z" />
    <path d="M8 8v4c0 2.21 1.79 4 4 4s4-1.79 4-4V8" />
    <path d="M6 16h12" />
    <path d="M8 20h8" />
    <circle cx="12" cy="12" r="1" />
  </svg>
{:else if name === 'thought-stream'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M4 12h16" />
    <path d="M4 6h16" />
    <path d="M4 18h16" />
    <circle cx="6" cy="6" r="2" />
    <circle cx="12" cy="12" r="2" />
    <circle cx="18" cy="18" r="2" />
  </svg>
{:else if name === 'cognitive-map'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <circle cx="12" cy="12" r="3" />
    <circle cx="6" cy="6" r="2" />
    <circle cx="18" cy="6" r="2" />
    <circle cx="6" cy="18" r="2" />
    <circle cx="18" cy="18" r="2" />
    <line x1="8" y1="7" x2="10" y2="10" />
    <line x1="16" y1="7" x2="14" y2="10" />
    <line x1="8" y1="17" x2="10" y2="14" />
    <line x1="16" y1="17" x2="14" y2="14" />
    <line x1="9" y1="12" x2="15" y2="12" />
  </svg>
{:else if name === 'mind-palace'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M3 21h18" />
    <path d="M5 21V7l8-6 8 6v14" />
    <path d="M9 9h6" />
    <path d="M9 12h6" />
    <path d="M9 15h6" />
    <rect x="8" y="18" width="2" height="3" />
    <rect x="14" y="18" width="2" height="3" />
    <polygon points="12 1 5 7 19 7" />
  </svg>
{:else if name === 'visual-cortex'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
{:else if name === 'knowledge-sync'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M23 4v6h-6" />
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    <path d="M1 20v-6h6" />
    <path d="M3.51 9a9 9 0 0 1 2.12-9.36L1 14" />
  </svg>
{:else if name === 'message-circle'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path
      d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"
    />
  </svg>
{:else if name === 'upload'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
{:else if name === 'clock'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
{:else if name === 'docs'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
{:else if name === 'navigation'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polygon points="3 11 22 2 13 21 11 13 3 11" />
  </svg>
{:else if name === 'settings'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <circle cx="12" cy="12" r="3" />
    <path
      d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
    />
  </svg>
{:else if name === 'chevron-right'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polyline points="9 18 15 12 9 6" />
  </svg>
{:else if name === 'chevron-left'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polyline points="15 18 9 12 15 6" />
  </svg>
{:else if name === 'code'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polyline points="16 18 22 12 16 6" />
    <polyline points="8 6 2 12 8 18" />
  </svg>
{:else if name === 'book'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
  </svg>
{:else if name === 'play'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polygon points="5 3 19 12 5 21 5 3" />
  </svg>
{:else if name === 'lightbulb'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M9 21h6" />
    <path d="M12 17h.01" />
    <path d="M12 3a6 6 0 0 1 6 6c0 2-1 3-2 4h-8c-1-1-2-2-2-4a6 6 0 0 1 6-6z" />
  </svg>
{:else if name === 'inbox'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
    <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
  </svg>
{:else if name === 'loader'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <line x1="12" y1="2" x2="12" y2="6" />
    <line x1="12" y1="18" x2="12" y2="22" />
    <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
    <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
    <line x1="2" y1="12" x2="6" y2="12" />
    <line x1="18" y1="12" x2="22" y2="12" />
    <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
    <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
  </svg>
{:else if name === 'alert-circle'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
{:else if name === 'arrow-left'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <line x1="19" y1="12" x2="5" y2="12" />
    <polyline points="12 19 5 12 12 5" />
  </svg>
{:else if name === 'file-text'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
{:else if name === 'layout'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
    <line x1="3" y1="9" x2="21" y2="9" />
    <line x1="9" y1="21" x2="9" y2="9" />
  </svg>
{:else if name === 'more-vertical'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <circle cx="12" cy="12" r="1" />
    <circle cx="12" cy="5" r="1" />
    <circle cx="12" cy="19" r="1" />
  </svg>
{:else if name === 'bookmark'}
  <svg
    {width}
    {height}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    stroke-width={strokeWidth}
    stroke-linecap="round"
    stroke-linejoin="round" class={className}
  >
    <path d="m19 21-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />
  </svg>
{/if}

<style>
  svg {
    display: inline-block;
    vertical-align: middle;
    transition: all var(--transition-fast);
  }
</style>
