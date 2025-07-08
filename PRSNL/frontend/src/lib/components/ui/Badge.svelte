<script lang="ts">
  export let variant: 'default' | 'success' | 'warning' | 'error' = 'default';
  export let size: 'sm' | 'md' = 'md';
  
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800'
  };
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm'
  };
</script>

<span 
  class="
    inline-flex items-center font-medium rounded-full
    {variantClasses[variant]}
    {sizeClasses[size]}
    {$$props.class || ''}
  "
>
  <slot />
</span>