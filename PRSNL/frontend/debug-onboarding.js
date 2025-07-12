// Debug script to investigate onboarding popup issue
// Run this in browser console on the timeline page

console.log('=== ONBOARDING DEBUG ===');

// Check if onboarding container exists in DOM
const onboardingContainer = document.querySelector('.onboarding-container');
console.log('Onboarding container found:', !!onboardingContainer);

if (onboardingContainer) {
  console.log('Container element:', onboardingContainer);
  console.log('Container innerHTML:', onboardingContainer.innerHTML);
  console.log('Container parent:', onboardingContainer.parentElement);
  console.log('Container siblings:', onboardingContainer.parentElement?.children);
  
  // Check if it's inside the main content area
  const mainContent = document.querySelector('.main-content');
  console.log('Is inside main content:', mainContent?.contains(onboardingContainer));
  
  // Check if it's in the layout
  const appLayout = document.querySelector('.app-layout');
  console.log('Is inside app layout:', appLayout?.contains(onboardingContainer));
  
  // Check for any Svelte component markers
  console.log('Component data attributes:', Array.from(onboardingContainer.attributes).filter(attr => attr.name.startsWith('data-')));
}

// Check for any onboarding overlay
const onboardingOverlay = document.querySelector('.onboarding-overlay');
console.log('Onboarding overlay found:', !!onboardingOverlay);

if (onboardingOverlay) {
  console.log('Overlay parent:', onboardingOverlay.parentElement);
  console.log('Overlay innerHTML:', onboardingOverlay.innerHTML);
}

// Check current route
console.log('Current pathname:', window.location.pathname);
console.log('Page title:', document.title);

// Check for any Svelte stores or state
if (window.__SVELTE__ && window.__SVELTE__.length > 0) {
  console.log('Svelte components found:', window.__SVELTE__.length);
}

console.log('=== END DEBUG ===');
