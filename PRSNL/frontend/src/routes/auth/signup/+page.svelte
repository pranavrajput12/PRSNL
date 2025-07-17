<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authActions, isAuthenticated, isLoading, authError } from '$lib/stores/unified-auth';
  import { addNotification } from '$lib/stores/app';
  import Icon from '$lib/components/Icon.svelte';
  import NeuralBackground from '$lib/components/NeuralBackground.svelte';
  import InspirationMessage from '$lib/components/InspirationMessage.svelte';
  import MagneticButton from '$lib/components/MagneticButton.svelte';
  import BreathingCard from '$lib/components/BreathingCard.svelte';

  // Form state
  let formData = {
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    user_type: 'individual' as 'individual' | 'team' | 'enterprise'
  };

  let currentStep = 1;
  let formErrors: Record<string, string> = {};
  let showPassword = false;
  let showConfirmPassword = false;
  let isFormActive = false;

  // Inspirational messages for each step
  const stepMessages = {
    1: [
      "Your journey to amplified intelligence begins",
      "Create your neural interface",
      "Join the cognitive revolution",
      "Your second brain awaits activation"
    ],
    2: [
      "Let's personalize your neural interface",
      "Tell us who's behind the brilliant mind",
      "Every great brain has a name",
      "Identity unlocks infinite possibilities"
    ],
    3: [
      "Choose how your brain will evolve",
      "Select your cognitive enhancement path",
      "Pick your intelligence amplification mode",
      "Your brain, your rules"
    ]
  };

  const successMessages = [
    "Neural pathways initialized...",
    "Preparing your cognitive enhancement...",
    "Welcome to the future of intelligence"
  ];

  // User type options with dynamic descriptions
  const userTypes = [
    {
      value: 'individual',
      title: '👤 Individual',
      description: 'Personal knowledge management and AI assistance',
      features: ['Personal AI assistant', 'Knowledge graphs', 'Smart search', 'Document analysis']
    },
    {
      value: 'team',
      title: '👥 Team',
      description: 'Collaborate with your team on shared knowledge',
      features: ['Team collaboration', 'Shared workspaces', 'Real-time sync', 'Advanced permissions']
    },
    {
      value: 'enterprise',
      title: '🏢 Enterprise',
      description: 'Enterprise-grade security and management features',
      features: ['SSO integration', 'Audit trails', 'Custom integrations', 'Priority support']
    }
  ];

  // Redirect if already authenticated
  $: if ($isAuthenticated) {
    goto('/');
  }

  // Validation functions
  function validateEmail(email: string): string | null {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) return 'Email is required';
    if (!emailRegex.test(email)) return 'Please enter a valid email address';
    return null;
  }

  function validatePassword(password: string): string | null {
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(password)) return 'Password must contain an uppercase letter';
    if (!/[a-z]/.test(password)) return 'Password must contain a lowercase letter';
    if (!/[0-9]/.test(password)) return 'Password must contain a number';
    return null;
  }

  function validateStep1(): boolean {
    formErrors = {};
    
    const emailError = validateEmail(formData.email);
    const passwordError = validatePassword(formData.password);
    
    if (emailError) formErrors.email = emailError;
    if (passwordError) formErrors.password = passwordError;
    
    if (formData.password !== formData.confirmPassword) {
      formErrors.confirmPassword = 'Passwords do not match';
    }
    
    return Object.keys(formErrors).length === 0;
  }

  function validateStep2(): boolean {
    formErrors = {};
    
    if (!formData.first_name.trim()) {
      formErrors.first_name = 'First name is required';
    }
    
    return Object.keys(formErrors).length === 0;
  }

  function nextStep() {
    if (currentStep === 1 && validateStep1()) {
      currentStep = 2;
    } else if (currentStep === 2 && validateStep2()) {
      currentStep = 3;
    }
  }

  function prevStep() {
    if (currentStep > 1) {
      currentStep--;
    }
  }

  async function handleSubmit() {
    if (currentStep < 3) {
      nextStep();
      return;
    }

    // Final validation
    if (!validateStep1() || !validateStep2()) {
      currentStep = 1;
      return;
    }

    try {
      await authActions.signupWithPRSNL({
        email: formData.email,
        password: formData.password,
        firstName: formData.first_name,
        lastName: formData.last_name
      });
      goto('/');
    } catch (error) {
      console.error('Signup failed:', error);
    }
  }

  // Clear errors when inputs change
  $: if (formData.email) delete formErrors.email;
  $: if (formData.password) delete formErrors.password;
  $: if (formData.confirmPassword && formData.password === formData.confirmPassword) delete formErrors.confirmPassword;
  $: if (formData.first_name) delete formErrors.first_name;

  onMount(() => {
    // Clear any previous errors
    authActions.clearError();
  });
</script>

<svelte:head>
  <title>Sign Up - PRSNL</title>
  <meta name="description" content="Create your PRSNL account and unlock AI-powered knowledge management" />
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4 relative overflow-hidden">
  <!-- Animated Neural Network Background -->
  <NeuralBackground 
    particleCount={120}
    connectionDistance={150}
    mouseInfluence={true}
    colorScheme={{
      particles: '#8b5cf6',
      connections: '#ec4899',
      mouseGlow: '#10b981'
    }}
  />
  
  <!-- Gradient Overlay for depth -->
  <div class="absolute inset-0 bg-gradient-to-t from-slate-900/50 via-transparent to-purple-900/30 pointer-events-none"></div>
  
  <!-- Inspirational Messages -->
  {#if !$isLoading}
    <InspirationMessage 
      messages={stepMessages[currentStep]}
      position="top"
      size="medium"
      interval={5000}
    />
  {:else}
    <InspirationMessage 
      messages={successMessages}
      position="top"
      size="medium"
      interval={3000}
    />
  {/if}

  <div class="w-full max-w-md relative">
    <!-- Header with enhanced animation -->
    <div class="text-center mb-8 animate-fade-in">
      <div class="inline-flex items-center space-x-2 mb-4 group">
        <div class="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center transform transition-all duration-300 group-hover:scale-110 group-hover:rotate-12">
          <Icon name="brain" class="w-6 h-6 text-white" />
        </div>
        <span class="text-2xl font-bold text-white bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">PRSNL</span>
      </div>
      <h1 class="text-3xl font-bold text-white mb-2 animate-slide-up">Create your account</h1>
      <p class="text-slate-300 animate-slide-up-delayed">Join the future of AI-powered knowledge management</p>
    </div>

    <!-- Animated Progress Bar -->
    <div class="mb-8 animate-fade-in">
      <div class="flex items-center justify-between mb-2">
        {#each [1, 2, 3] as step}
          <div class="flex items-center">
            <div class="w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all duration-300 transform {
              currentStep >= step 
                ? 'bg-purple-500 border-purple-500 text-white scale-110' 
                : 'border-slate-600 text-slate-400 scale-100'
            } step-indicator">
              {#if currentStep > step}
                <Icon name="check" class="w-4 h-4" />
              {:else}
                <span class="text-sm font-medium">{step}</span>
              {/if}
            </div>
            {#if step < 3}
              <div class="relative w-12 h-0.5 mx-2 bg-slate-600 overflow-hidden">
                <div class="absolute inset-0 bg-purple-500 transition-transform duration-300 {currentStep > step ? 'translate-x-0' : '-translate-x-full'}"></div>
              </div>
            {/if}
          </div>
        {/each}
      </div>
      <div class="flex justify-between text-xs text-slate-400">
        <span>Account</span>
        <span>Profile</span>
        <span>Preferences</span>
      </div>
    </div>

    <!-- Form Card with breathing effect -->
    <BreathingCard 
      glowColor={isFormActive ? '#10b981' : '#8b5cf6'} 
      breathingScale={0.02} 
      breathingDuration={4}
      interactive={true}
    >
      <div on:focusin={() => isFormActive = true} on:focusout={() => isFormActive = false}>
      <form on:submit|preventDefault={handleSubmit} class="space-y-6">
        <!-- Step 1: Account Details -->
        {#if currentStep === 1}
          <div class="space-y-4 animate-slide-in">
            <h2 class="text-xl font-semibold text-white mb-4">Account Details</h2>
            
            <!-- Email -->
            <div>
              <label for="email" class="block text-sm font-medium text-slate-200 mb-2">Email Address</label>
              <div class="relative">
                <input
                  type="email"
                  id="email"
                  bind:value={formData.email}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
                  placeholder="you@example.com"
                  autocomplete="email"
                />
                <Icon name="mail" class="absolute right-3 top-3.5 w-5 h-5 text-slate-400" />
              </div>
              {#if formErrors.email}
                <p class="text-red-400 text-sm mt-1">{formErrors.email}</p>
              {/if}
            </div>

            <!-- Password -->
            <div>
              <label for="password" class="block text-sm font-medium text-slate-200 mb-2">Password</label>
              <div class="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  bind:value={formData.password}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 pr-12"
                  placeholder="Create a strong password"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  on:click={() => showPassword = !showPassword}
                  class="absolute right-3 top-3.5 text-slate-400 hover:text-white transition-colors"
                >
                  <Icon name={showPassword ? 'eye-off' : 'eye'} class="w-5 h-5" />
                </button>
              </div>
              {#if formErrors.password}
                <p class="text-red-400 text-sm mt-1">{formErrors.password}</p>
              {/if}
              {#if formData.password}
                <div class="mt-2 space-y-1">
                  <div class="flex items-center space-x-2 text-xs">
                    <div class="w-2 h-2 rounded-full {formData.password.length >= 8 ? 'bg-green-500' : 'bg-slate-500'}"></div>
                    <span class="text-slate-300">At least 8 characters</span>
                  </div>
                  <div class="flex items-center space-x-2 text-xs">
                    <div class="w-2 h-2 rounded-full {/[A-Z]/.test(formData.password) && /[a-z]/.test(formData.password) ? 'bg-green-500' : 'bg-slate-500'}"></div>
                    <span class="text-slate-300">Upper & lowercase letters</span>
                  </div>
                  <div class="flex items-center space-x-2 text-xs">
                    <div class="w-2 h-2 rounded-full {/[0-9]/.test(formData.password) ? 'bg-green-500' : 'bg-slate-500'}"></div>
                    <span class="text-slate-300">At least one number</span>
                  </div>
                </div>
              {/if}
            </div>

            <!-- Confirm Password -->
            <div>
              <label for="confirmPassword" class="block text-sm font-medium text-slate-200 mb-2">Confirm Password</label>
              <div class="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  bind:value={formData.confirmPassword}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 pr-12"
                  placeholder="Confirm your password"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  on:click={() => showConfirmPassword = !showConfirmPassword}
                  class="absolute right-3 top-3.5 text-slate-400 hover:text-white transition-colors"
                >
                  <Icon name={showConfirmPassword ? 'eye-off' : 'eye'} class="w-5 h-5" />
                </button>
              </div>
              {#if formErrors.confirmPassword}
                <p class="text-red-400 text-sm mt-1">{formErrors.confirmPassword}</p>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Step 2: Profile Information -->
        {#if currentStep === 2}
          <div class="space-y-4 animate-slide-in">
            <h2 class="text-xl font-semibold text-white mb-4">Tell us about yourself</h2>
            
            <div class="grid grid-cols-2 gap-4">
              <!-- First Name -->
              <div>
                <label for="firstName" class="block text-sm font-medium text-slate-200 mb-2">First Name</label>
                <input
                  type="text"
                  id="firstName"
                  bind:value={formData.first_name}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
                  placeholder="John"
                  autocomplete="given-name"
                />
                {#if formErrors.first_name}
                  <p class="text-red-400 text-sm mt-1">{formErrors.first_name}</p>
                {/if}
              </div>

              <!-- Last Name -->
              <div>
                <label for="lastName" class="block text-sm font-medium text-slate-200 mb-2">Last Name</label>
                <input
                  type="text"
                  id="lastName"
                  bind:value={formData.last_name}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
                  placeholder="Doe"
                  autocomplete="family-name"
                />
              </div>
            </div>
          </div>
        {/if}

        <!-- Step 3: User Type Selection -->
        {#if currentStep === 3}
          <div class="space-y-4 animate-slide-in">
            <h2 class="text-xl font-semibold text-white mb-4">Choose your plan</h2>
            
            <div class="space-y-3">
              {#each userTypes as type}
                <label class="block">
                  <input
                    type="radio"
                    bind:group={formData.user_type}
                    value={type.value}
                    class="sr-only"
                  />
                  <div class="cursor-pointer p-4 border-2 rounded-lg transition-all duration-200 transform hover:scale-[1.02] {
                    formData.user_type === type.value
                      ? 'border-purple-500 bg-purple-500/20 shadow-lg shadow-purple-500/25 scale-[1.02]'
                      : 'border-white/20 hover:border-white/40 bg-white/5 hover:bg-white/10'
                  }">
                    <div class="flex items-start space-x-3">
                      <div class="flex-shrink-0 mt-1">
                        <div class="w-4 h-4 rounded-full border-2 {
                          formData.user_type === type.value
                            ? 'border-purple-500 bg-purple-500'
                            : 'border-slate-400'
                        } flex items-center justify-center">
                          {#if formData.user_type === type.value}
                            <div class="w-2 h-2 rounded-full bg-white"></div>
                          {/if}
                        </div>
                      </div>
                      <div class="flex-1">
                        <h3 class="text-lg font-medium text-white">{type.title}</h3>
                        <p class="text-slate-300 text-sm mb-2">{type.description}</p>
                        <div class="flex flex-wrap gap-2">
                          {#each type.features as feature}
                            <span class="px-2 py-1 bg-white/10 rounded-full text-xs text-slate-300">{feature}</span>
                          {/each}
                        </div>
                      </div>
                    </div>
                  </div>
                </label>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Error Display -->
        {#if $authError}
          <div class="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
            <div class="flex items-center space-x-2">
              <Icon name="alert-circle" class="w-5 h-5 text-red-400" />
              <p class="text-red-400 text-sm">{$authError}</p>
            </div>
          </div>
        {/if}

        <!-- Navigation Buttons -->
        <div class="flex items-center justify-between pt-4">
          {#if currentStep > 1}
            <MagneticButton
              type="button"
              variant="ghost"
              size="medium"
              icon="arrow-left"
              iconPosition="left"
              on:click={prevStep}
            >
              Back
            </MagneticButton>
          {:else}
            <div></div>
          {/if}

          <MagneticButton
            type="submit"
            variant="primary"
            disabled={$isLoading}
            loading={$isLoading}
            size="medium"
            icon={currentStep < 3 ? 'arrow-right' : 'user-plus'}
          >
            {#if $isLoading}
              Creating account...
            {:else if currentStep < 3}
              Continue
            {:else}
              Create Account
            {/if}
          </MagneticButton>
        </div>
      </form>
      </div>
    </BreathingCard>

    <!-- Social Signup Options -->
    <div class="mt-8">
      <div class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-white/20"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-slate-900 text-slate-400">Or sign up with</span>
        </div>
      </div>
      
      <div class="mt-6 space-y-3">
        <button 
          on:click={() => authActions.loginWithGoogle()}
          disabled={$isLoading}
          class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-white/10 text-sm font-medium text-white hover:bg-white/20 transition-colors disabled:opacity-50"
        >
          <Icon name="chrome" class="w-5 h-5" />
          <span class="ml-2">Continue with Google</span>
        </button>
        
        <button 
          on:click={() => authActions.loginWithGitHub()}
          disabled={$isLoading}
          class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-white/10 text-sm font-medium text-white hover:bg-white/20 transition-colors disabled:opacity-50"
        >
          <Icon name="github" class="w-5 h-5" />
          <span class="ml-2">Continue with GitHub</span>
        </button>
        
        <button 
          on:click={() => authActions.loginWithMicrosoft()}
          disabled={$isLoading}
          class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-white/10 text-sm font-medium text-white hover:bg-white/20 transition-colors disabled:opacity-50"
        >
          <Icon name="windows" class="w-5 h-5" />
          <span class="ml-2">Continue with Microsoft</span>
        </button>
      </div>
      
      <div class="mt-4 text-center">
        <p class="text-xs text-slate-400">
          <Icon name="shield-check" class="w-3 h-3 inline mr-1" />
          Secure enterprise SSO via Keycloak
        </p>
      </div>
    </div>

    <!-- Login Link -->
    <div class="text-center mt-6">
      <p class="text-slate-300">
        Already have an account? 
        <a href="/auth/login" class="text-purple-400 hover:text-purple-300 font-medium transition-colors duration-200">
          Sign in
        </a>
      </p>
    </div>
  </div>
</div>

<style>
  /* Custom scrollbar for the page */
  :global(html) {
    scrollbar-width: thin;
    scrollbar-color: rgba(139, 92, 246, 0.5) transparent;
  }

  :global(html::-webkit-scrollbar) {
    width: 6px;
  }

  :global(html::-webkit-scrollbar-track) {
    background: transparent;
  }

  :global(html::-webkit-scrollbar-thumb) {
    background: rgba(139, 92, 246, 0.5);
    border-radius: 3px;
  }

  :global(html::-webkit-scrollbar-thumb:hover) {
    background: rgba(139, 92, 246, 0.7);
  }

  /* Animations */
  :global(.animate-fade-in) {
    animation: fadeIn 0.8s ease-out;
  }

  :global(.animate-slide-up) {
    animation: slideUp 0.6s ease-out;
  }

  :global(.animate-slide-up-delayed) {
    animation: slideUp 0.6s ease-out 0.2s both;
  }

  :global(.animate-slide-in) {
    animation: slideIn 0.5s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  /* Step indicator pulse animation */
  .step-indicator {
    animation: pulse 2s ease-in-out infinite;
  }

  .step-indicator:not(.bg-purple-500) {
    animation: none;
  }

  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
      box-shadow: 0 0 0 0 rgba(139, 92, 246, 0);
    }
    50% {
      transform: scale(1.1);
      box-shadow: 0 0 0 8px rgba(139, 92, 246, 0.2);
    }
  }

  /* Input focus effects */
  :global(input:focus) {
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }

  /* Password strength indicators animation */
  :global(.w-2.h-2.rounded-full) {
    transition: all 0.3s ease;
  }

  :global(.bg-green-500) {
    animation: checkmark 0.3s ease-out;
  }

  @keyframes checkmark {
    from {
      transform: scale(0);
    }
    to {
      transform: scale(1);
    }
  }

  /* Reduce motion for accessibility */
  @media (prefers-reduced-motion: reduce) {
    :global(.animate-fade-in),
    :global(.animate-slide-up),
    :global(.animate-slide-up-delayed),
    :global(.animate-slide-in) {
      animation: none;
    }
    
    .step-indicator {
      animation: none;
    }
  }
</style>