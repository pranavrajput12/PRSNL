<script lang="ts" type="module">
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let color: string = 'text-red-600';

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };
</script>

<div class="inline-flex items-center justify-center">
  <div
    class="
      animate-spin rounded-full border-2 border-gray-300
      {sizeClasses[size]}
      {color}
    "
    style="border-top-color: currentColor"
  />
</div>

<style>
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>
