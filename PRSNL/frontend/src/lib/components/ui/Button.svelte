<script lang="ts">
  import { autoId } from '$lib/actions/autoId';
  
  export let variant: 'primary' | 'secondary' | 'outline' = 'primary';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let disabled = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';

  const variantClasses = {
    primary: 'bg-red-600 text-white hover:bg-red-700',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700',
    outline: 'border border-red-600 text-red-600 hover:bg-red-50',
  };

  const sizeClasses = {
    sm: 'px-3 py-1 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };
</script>

<button
  {type}
  {disabled}
  class="
    font-medium rounded-lg transition-colors duration-200
    {variantClasses[variant]}
    {sizeClasses[size]}
    {disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
    {$$props.class || ''}
  "
  use:autoId={{type: "button", component: "Button", suffix: variant}}
  on:click
>
  <slot />
</button>
