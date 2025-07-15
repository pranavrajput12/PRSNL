<script>
  import Button from '$lib/components/ui/button/button.svelte';
  import AnimatedButton from '$lib/components/AnimatedButton.svelte';
</script>

<div class="min-h-screen p-8 space-y-8">
  <h1 class="text-3xl font-bold text-white">shadcn-svelte Integration Test</h1>
  
  <div class="space-y-4">
    <h2 class="text-xl text-white">New shadcn-svelte Components</h2>
    <div class="flex gap-4">
      <Button>Default Button</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
    </div>
  </div>
  
  <div class="space-y-4">
    <h2 class="text-xl text-white">Existing PRSNL Components (Should Work Unchanged)</h2>
    <div class="flex gap-4">
      <AnimatedButton>Existing Animated Button</AnimatedButton>
    </div>
  </div>
  
  <div class="bg-green-500/20 border border-green-500 p-4 rounded-lg">
    <p class="text-green-200">
      ✅ If you can see this page with both button types working, the migration is successful!
    </p>
  </div>
</div>

<style>
  /* Existing custom styles should still work */
  :global(body) {
    background: var(--bg-primary);
  }
</style>