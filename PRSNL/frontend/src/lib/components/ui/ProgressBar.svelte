<script lang="ts">
  export let value: number = 0;
  export let max: number = 100;
  export let color: string = 'bg-red-600';
  export let height: string = 'h-2';
  
  $: percentage = Math.min(100, Math.max(0, (value / max) * 100));
</script>

<div class="w-full bg-gray-200 rounded-full {height} overflow-hidden">
  <div 
    class="{color} {height} rounded-full transition-all duration-300"
    style="width: {percentage}%"
  />
</div>