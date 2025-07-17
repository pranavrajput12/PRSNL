<script lang="ts">
  import { onMount } from 'svelte';
  import { currentUser as user, authActions, isLoading, authError } from '$lib/stores/unified-auth';
  import { addNotification } from '$lib/stores/app';
  import Icon from '$lib/components/Icon.svelte';
  import { profileApi } from '$lib/api';

  // Form state
  let profileData = {
    first_name: '',
    last_name: '',
    name: '',
    email: '',
    user_type: 'individual' as 'individual' | 'team' | 'enterprise'
  };

  let passwordData = {
    current_password: '',
    new_password: '',
    confirm_password: ''
  };

  let userStats = {
    total_items: 0,
    total_tags: 0,
    items_this_month: 0,
    last_capture: null as string | null
  };

  let formErrors: Record<string, string> = {};
  let activeTab: 'profile' | 'password' | 'account' = 'profile';
  let showCurrentPassword = false;
  let showNewPassword = false;
  let showConfirmPassword = false;
  let isUpdatingProfile = false;
  let isUpdatingPassword = false;
  let isLoadingProfile = true;
  let isLoadingStats = true;

  // User type options
  const userTypes = [
    {
      value: 'individual',
      title: '👤 Individual',
      description: 'Personal knowledge management and AI assistance'
    },
    {
      value: 'team',
      title: '👥 Team',
      description: 'Collaborate with your team on shared knowledge'
    },
    {
      value: 'enterprise',
      title: '🏢 Enterprise',
      description: 'Enterprise-grade security and management features'
    }
  ];

  // Load user data on mount
  onMount(async () => {
    await loadProfileData();
    await loadUserStats();
  });

  async function loadProfileData() {
    try {
      isLoadingProfile = true;
      const profile = await profileApi.getProfile();
      profileData = {
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        name: profile.name || '',
        email: profile.email,
        user_type: profile.user_type as any
      };
    } catch (error) {
      console.error('Failed to load profile:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load profile data'
      });
    } finally {
      isLoadingProfile = false;
    }
  }

  async function loadUserStats() {
    try {
      isLoadingStats = true;
      const stats = await profileApi.getStats();
      userStats = stats;
    } catch (error) {
      console.error('Failed to load user stats:', error);
      // Don't show error notification for stats as it's not critical
    } finally {
      isLoadingStats = false;
    }
  }

  // Validation functions
  function validateProfile(): boolean {
    formErrors = {};
    
    if (!profileData.first_name.trim()) {
      formErrors.first_name = 'First name is required';
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!profileData.email) {
      formErrors.email = 'Email is required';
    } else if (!emailRegex.test(profileData.email)) {
      formErrors.email = 'Please enter a valid email address';
    }
    
    return Object.keys(formErrors).length === 0;
  }

  function validatePassword(): boolean {
    formErrors = {};
    
    if (!passwordData.current_password) {
      formErrors.current_password = 'Current password is required';
    }
    
    if (!passwordData.new_password) {
      formErrors.new_password = 'New password is required';
    } else if (passwordData.new_password.length < 8) {
      formErrors.new_password = 'Password must be at least 8 characters';
    } else if (!/[A-Z]/.test(passwordData.new_password)) {
      formErrors.new_password = 'Password must contain an uppercase letter';
    } else if (!/[a-z]/.test(passwordData.new_password)) {
      formErrors.new_password = 'Password must contain a lowercase letter';
    } else if (!/[0-9]/.test(passwordData.new_password)) {
      formErrors.new_password = 'Password must contain a number';
    }
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      formErrors.confirm_password = 'Passwords do not match';
    }
    
    return Object.keys(formErrors).length === 0;
  }

  async function updateProfile() {
    if (!validateProfile()) return;

    isUpdatingProfile = true;
    
    try {
      // Build update data, only including changed fields
      const updateData: any = {};
      if (profileData.first_name.trim()) updateData.first_name = profileData.first_name.trim();
      if (profileData.last_name.trim()) updateData.last_name = profileData.last_name.trim();
      if (profileData.name.trim()) updateData.name = profileData.name.trim();
      
      await profileApi.updateProfile(updateData);
      
      addNotification({
        type: 'success',
        message: 'Profile updated successfully!'
      });
      
      // Refresh user data
      await authActions.getCurrentUser();
      await loadProfileData();
    } catch (error) {
      console.error('Profile update error:', error);
      addNotification({
        type: 'error',
        message: 'Failed to update profile. Please try again.'
      });
    } finally {
      isUpdatingProfile = false;
    }
  }

  async function updatePassword() {
    if (!validatePassword()) return;

    isUpdatingPassword = true;
    
    try {
      await profileApi.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      
      addNotification({
        type: 'success',
        message: 'Password updated successfully!'
      });
      
      // Clear password form
      passwordData = {
        current_password: '',
        new_password: '',
        confirm_password: ''
      };
    } catch (error) {
      console.error('Password update error:', error);
      let errorMessage = 'Failed to update password. Please try again.';
      
      // Handle specific error cases
      if (error instanceof Error) {
        if (error.message.includes('Current password is incorrect')) {
          errorMessage = 'Current password is incorrect.';
          formErrors.current_password = 'Current password is incorrect';
        } else if (error.message.includes('password')) {
          errorMessage = error.message;
        }
      }
      
      addNotification({
        type: 'error',
        message: errorMessage
      });
    } finally {
      isUpdatingPassword = false;
    }
  }

  async function resendVerification() {
    const success = await authActions.resendVerification();
    if (success) {
      addNotification({
        type: 'success',
        message: 'Verification email sent!'
      });
    }
  }

  async function deleteAccount() {
    const confirmed = confirm(
      'Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently lost.'
    );
    
    if (!confirmed) return;

    const doubleConfirmed = confirm(
      'This will permanently delete all your captured content, notes, and account data. Are you absolutely sure?'
    );
    
    if (!doubleConfirmed) return;

    try {
      await profileApi.deleteAccount();
      
      addNotification({
        type: 'success',
        message: 'Account deleted successfully. You will be redirected to the homepage.'
      });
      
      // Logout and redirect
      await authActions.logout();
      
      // Redirect to home page
      if (typeof window !== 'undefined') {
        window.location.href = '/';
      }
    } catch (error) {
      console.error('Account deletion error:', error);
      addNotification({
        type: 'error',
        message: 'Failed to delete account. Please try again or contact support.'
      });
    }
  }

  // Clear errors when inputs change
  $: if (profileData.first_name) delete formErrors.first_name;
  $: if (profileData.email) delete formErrors.email;
  $: if (passwordData.current_password) delete formErrors.current_password;
  $: if (passwordData.new_password) delete formErrors.new_password;
  $: if (passwordData.confirm_password && passwordData.new_password === passwordData.confirm_password) delete formErrors.confirm_password;
</script>

<svelte:head>
  <title>Profile - PRSNL</title>
  <meta name="description" content="Manage your PRSNL profile and account settings" />
</svelte:head>

<div class="min-h-screen p-6">
  <div class="max-w-4xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
          {#if $user}
            <span class="text-white font-bold text-lg">
              {$user.firstName ? $user.firstName.charAt(0).toUpperCase() : $user.email.charAt(0).toUpperCase()}
            </span>
          {:else}
            <Icon name="user" class="w-7 h-7 text-white" />
          {/if}
        </div>
        <div>
          <h1 class="text-3xl font-bold text-white">My Profile</h1>
          <p class="text-slate-300">Manage your account information and security</p>
        </div>
      </div>
      
      {#if $user && !$user.isEmailVerified}
        <div class="bg-amber-500/20 border border-amber-500/30 rounded-lg p-4 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <Icon name="alert-triangle" class="w-5 h-5 text-amber-400" />
            <div>
              <p class="text-amber-400 font-medium">Email verification required</p>
              <p class="text-amber-300 text-sm">Please verify your email to access all features</p>
            </div>
          </div>
          <button
            on:click={resendVerification}
            disabled={$isLoading}
            class="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            {$isLoading ? 'Sending...' : 'Resend Email'}
          </button>
        </div>
      {/if}
    </div>

    <!-- Tabs -->
    <div class="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-2 mb-6 shadow-xl">
      <div class="grid grid-cols-3 gap-2">
        <button
          type="button"
          on:click={() => activeTab = 'profile'}
          class="relative px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 {
            activeTab === 'profile'
              ? 'bg-white/20 text-white shadow-lg'
              : 'text-slate-300 hover:text-white'
          }"
        >
          <Icon name="user" class="w-4 h-4 inline mr-2" />
          Profile Info
        </button>
        <button
          type="button"
          on:click={() => activeTab = 'password'}
          class="relative px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 {
            activeTab === 'password'
              ? 'bg-white/20 text-white shadow-lg'
              : 'text-slate-300 hover:text-white'
          }"
        >
          <Icon name="lock" class="w-4 h-4 inline mr-2" />
          Security
        </button>
        <button
          type="button"
          on:click={() => activeTab = 'account'}
          class="relative px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 {
            activeTab === 'account'
              ? 'bg-white/20 text-white shadow-lg'
              : 'text-slate-300 hover:text-white'
          }"
        >
          <Icon name="settings" class="w-4 h-4 inline mr-2" />
          Account
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 shadow-2xl">
      <!-- Profile Tab -->
      {#if activeTab === 'profile'}
        <div class="space-y-6">
          <h2 class="text-xl font-semibold text-white">Profile Information</h2>

          <form on:submit|preventDefault={updateProfile} class="space-y-6">
            <!-- Display Name -->
            <div>
              <label for="displayName" class="block text-sm font-medium text-slate-200 mb-2">Display Name</label>
              <input
                type="text"
                id="displayName"
                bind:value={profileData.name}
                class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
                placeholder="Your display name"
              />
              <p class="text-slate-400 text-xs mt-1">This is how your name appears throughout the application</p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <!-- First Name -->
              <div>
                <label for="firstName" class="block text-sm font-medium text-slate-200 mb-2">First Name</label>
                <input
                  type="text"
                  id="firstName"
                  bind:value={profileData.first_name}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
                  placeholder="John"
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
                  bind:value={profileData.last_name}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
                  placeholder="Doe"
                />
              </div>
            </div>

            <!-- Email -->
            <div>
              <label for="email" class="block text-sm font-medium text-slate-200 mb-2">Email Address</label>
              <div class="relative">
                <input
                  type="email"
                  id="email"
                  bind:value={profileData.email}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
                  placeholder="you@example.com"
                />
                <Icon name="mail" class="absolute right-3 top-3.5 w-5 h-5 text-slate-400" />
              </div>
              {#if formErrors.email}
                <p class="text-red-400 text-sm mt-1">{formErrors.email}</p>
              {/if}
            </div>

            <!-- User Type -->
            <div>
              <label class="block text-sm font-medium text-slate-200 mb-4">Account Type</label>
              <div class="space-y-3">
                {#each userTypes as type}
                  <label class="block">
                    <input
                      type="radio"
                      bind:group={profileData.user_type}
                      value={type.value}
                      class="sr-only"
                    />
                    <div class="cursor-pointer p-4 border-2 rounded-lg transition-all duration-200 {
                      profileData.user_type === type.value
                        ? 'border-purple-500 bg-purple-500/20 shadow-lg shadow-purple-500/25'
                        : 'border-white/20 hover:border-white/40 bg-white/5'
                    }">
                      <div class="flex items-start space-x-3">
                        <div class="flex-shrink-0 mt-1">
                          <div class="w-4 h-4 rounded-full border-2 {
                            profileData.user_type === type.value
                              ? 'border-purple-500 bg-purple-500'
                              : 'border-slate-400'
                          } flex items-center justify-center">
                            {#if profileData.user_type === type.value}
                              <div class="w-2 h-2 rounded-full bg-white"></div>
                            {/if}
                          </div>
                        </div>
                        <div class="flex-1">
                          <h3 class="text-lg font-medium text-white">{type.title}</h3>
                          <p class="text-slate-300 text-sm">{type.description}</p>
                        </div>
                      </div>
                    </div>
                  </label>
                {/each}
              </div>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              disabled={isUpdatingProfile}
              class="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {#if isUpdatingProfile}
                <Icon name="loader-2" class="w-4 h-4 animate-spin" />
                <span>Updating...</span>
              {:else}
                <Icon name="save" class="w-4 h-4" />
                <span>Save Changes</span>
              {/if}
            </button>
          </form>
        </div>

      <!-- Password Tab -->
      {:else if activeTab === 'password'}
        <div class="space-y-6">
          <h2 class="text-xl font-semibold text-white">Security Settings</h2>

          <form on:submit|preventDefault={updatePassword} class="space-y-6">
            <!-- Current Password -->
            <div>
              <label for="currentPassword" class="block text-sm font-medium text-slate-200 mb-2">Current Password</label>
              <div class="relative">
                <input
                  type={showCurrentPassword ? 'text' : 'password'}
                  id="currentPassword"
                  bind:value={passwordData.current_password}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 pr-12"
                  placeholder="Enter your current password"
                />
                <button
                  type="button"
                  on:click={() => showCurrentPassword = !showCurrentPassword}
                  class="absolute right-3 top-3.5 text-slate-400 hover:text-white transition-colors"
                >
                  <Icon name={showCurrentPassword ? 'eye-off' : 'eye'} class="w-5 h-5" />
                </button>
              </div>
              {#if formErrors.current_password}
                <p class="text-red-400 text-sm mt-1">{formErrors.current_password}</p>
              {/if}
            </div>

            <!-- New Password -->
            <div>
              <label for="newPassword" class="block text-sm font-medium text-slate-200 mb-2">New Password</label>
              <div class="relative">
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  id="newPassword"
                  bind:value={passwordData.new_password}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 pr-12"
                  placeholder="Enter your new password"
                />
                <button
                  type="button"
                  on:click={() => showNewPassword = !showNewPassword}
                  class="absolute right-3 top-3.5 text-slate-400 hover:text-white transition-colors"
                >
                  <Icon name={showNewPassword ? 'eye-off' : 'eye'} class="w-5 h-5" />
                </button>
              </div>
              {#if formErrors.new_password}
                <p class="text-red-400 text-sm mt-1">{formErrors.new_password}</p>
              {/if}
              {#if passwordData.new_password}
                <div class="mt-2 space-y-1">
                  <div class="flex items-center space-x-2 text-xs">
                    <div class="w-2 h-2 rounded-full {passwordData.new_password.length >= 8 ? 'bg-green-500' : 'bg-slate-500'}"></div>
                    <span class="text-slate-300">At least 8 characters</span>
                  </div>
                  <div class="flex items-center space-x-2 text-xs">
                    <div class="w-2 h-2 rounded-full {/[A-Z]/.test(passwordData.new_password) && /[a-z]/.test(passwordData.new_password) ? 'bg-green-500' : 'bg-slate-500'}"></div>
                    <span class="text-slate-300">Upper & lowercase letters</span>
                  </div>
                  <div class="flex items-center space-x-2 text-xs">
                    <div class="w-2 h-2 rounded-full {/[0-9]/.test(passwordData.new_password) ? 'bg-green-500' : 'bg-slate-500'}"></div>
                    <span class="text-slate-300">At least one number</span>
                  </div>
                </div>
              {/if}
            </div>

            <!-- Confirm Password -->
            <div>
              <label for="confirmPassword" class="block text-sm font-medium text-slate-200 mb-2">Confirm New Password</label>
              <div class="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  bind:value={passwordData.confirm_password}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 pr-12"
                  placeholder="Confirm your new password"
                />
                <button
                  type="button"
                  on:click={() => showConfirmPassword = !showConfirmPassword}
                  class="absolute right-3 top-3.5 text-slate-400 hover:text-white transition-colors"
                >
                  <Icon name={showConfirmPassword ? 'eye-off' : 'eye'} class="w-5 h-5" />
                </button>
              </div>
              {#if formErrors.confirm_password}
                <p class="text-red-400 text-sm mt-1">{formErrors.confirm_password}</p>
              {/if}
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              disabled={isUpdatingPassword}
              class="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {#if isUpdatingPassword}
                <Icon name="loader-2" class="w-4 h-4 animate-spin" />
                <span>Updating...</span>
              {:else}
                <Icon name="shield" class="w-4 h-4" />
                <span>Update Password</span>
              {/if}
            </button>
          </form>
        </div>

      <!-- Account Tab -->
      {:else if activeTab === 'account'}
        <div class="space-y-6">
          <h2 class="text-xl font-semibold text-white">Account Management</h2>
          
          <!-- Account Info -->
          <div class="bg-white/5 border border-white/10 rounded-lg p-6">
            <h3 class="text-lg font-medium text-white mb-4">Account Information</h3>
            <div class="space-y-3 text-sm">
              <div class="flex justify-between">
                <span class="text-slate-300">Account created:</span>
                <span class="text-white">{'Unknown'}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-300">Last login:</span>
                <span class="text-white">{'Unknown'}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-300">Email verified:</span>
                <span class="text-white flex items-center gap-2">
                  {#if $user?.isEmailVerified}
                    <Icon name="check-circle" class="w-4 h-4 text-green-500" />
                    Yes
                  {:else}
                    <Icon name="x-circle" class="w-4 h-4 text-red-500" />
                    No
                  {/if}
                </span>
              </div>
            </div>
          </div>

          <!-- User Statistics -->
          <div class="bg-white/5 border border-white/10 rounded-lg p-6">
            <h3 class="text-lg font-medium text-white mb-4">Your Data</h3>
            {#if isLoadingStats}
              <div class="flex items-center justify-center py-8">
                <Icon name="loader-2" class="w-6 h-6 animate-spin text-purple-400" />
                <span class="ml-2 text-slate-300">Loading statistics...</span>
              </div>
            {:else}
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div class="text-center p-4 bg-white/5 rounded-lg">
                  <div class="text-2xl font-bold text-purple-400">{userStats.total_items}</div>
                  <div class="text-slate-300">Total Items</div>
                </div>
                <div class="text-center p-4 bg-white/5 rounded-lg">
                  <div class="text-2xl font-bold text-pink-400">{userStats.total_tags}</div>
                  <div class="text-slate-300">Total Tags</div>
                </div>
                <div class="text-center p-4 bg-white/5 rounded-lg">
                  <div class="text-2xl font-bold text-green-400">{userStats.items_this_month}</div>
                  <div class="text-slate-300">This Month</div>
                </div>
                <div class="text-center p-4 bg-white/5 rounded-lg">
                  <div class="text-xs font-medium text-blue-400">
                    {userStats.last_capture ? new Date(userStats.last_capture).toLocaleDateString() : 'Never'}
                  </div>
                  <div class="text-slate-300">Last Capture</div>
                </div>
              </div>
            {/if}
          </div>

          <!-- Danger Zone -->
          <div class="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
            <h3 class="text-lg font-medium text-white mb-2 flex items-center gap-2">
              <Icon name="alert-triangle" class="w-5 h-5 text-red-400" />
              Danger Zone
            </h3>
            <p class="text-slate-300 text-sm mb-4">
              Once you delete your account, there is no going back. Please be certain.
            </p>
            <button
              on:click={deleteAccount}
              class="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-all duration-200 flex items-center gap-2"
            >
              <Icon name="trash-2" class="w-4 h-4" />
              Delete Account
            </button>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>