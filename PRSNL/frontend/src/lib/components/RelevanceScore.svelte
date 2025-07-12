<script lang="ts">
  // Props
  export let score: number;
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let showLabel: boolean = true;

  // Computed values
  $: percentage = Math.round(score * 100);
  $: colorClass = getColorClass(percentage);

  // Helper to get color class based on score
  function getColorClass(value: number): string {
    if (value >= 85) return 'high';
    if (value >= 60) return 'medium';
    if (value >= 40) return 'moderate';
    return 'low';
  }
</script>

<div class="relevance-score {size}" title="Relevance score: {percentage}%">
  {#if showLabel}
    <span class="label">Match</span>
  {/if}
  <div
    class="score-indicator {colorClass}"
    role="meter"
    aria-valuenow={percentage}
    aria-valuemin="0"
    aria-valuemax="100"
  >
    <span class="percentage">{percentage}%</span>
  </div>
</div>

<style>
  .relevance-score {
    display: flex;
    align-items: center;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .relevance-score.small {
    font-size: 0.7rem;
  }

  .relevance-score.large {
    font-size: 0.9rem;
  }

  .label {
    margin-right: 0.5rem;
  }

  .score-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.25rem 0.5rem;
    border-radius: 1rem;
    font-weight: 500;
    line-height: 1;
  }

  .small .score-indicator {
    padding: 0.2rem 0.4rem;
  }

  .large .score-indicator {
    padding: 0.3rem 0.6rem;
  }

  .score-indicator.high {
    background-color: rgba(var(--success-rgb), 0.15);
    color: var(--success);
  }

  .score-indicator.medium {
    background-color: rgba(var(--accent-rgb), 0.15);
    color: var(--accent);
  }

  .score-indicator.moderate {
    background-color: rgba(var(--warning-rgb), 0.15);
    color: var(--warning);
  }

  .score-indicator.low {
    background-color: rgba(var(--error-rgb), 0.15);
    color: var(--error);
  }
</style>
