import { test, expect } from '@playwright/test';

test('homepage has title', async ({ page }) => {
  await page.goto('/');
  
  // Expects the page to have title containing "PRSNL"
  await expect(page).toHaveTitle(/PRSNL/);
});

test('console error monitoring', async ({ page }) => {
  const consoleMessages: string[] = [];
  const consoleErrors: string[] = [];
  
  // Listen to console events
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
    consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
  });
  
  // Navigate to the page
  await page.goto('/');
  
  // Wait for the page to fully load
  await page.waitForLoadState('networkidle');
  
  // Check for console errors
  if (consoleErrors.length > 0) {
    console.log('Console errors detected:', consoleErrors);
  }
  
  // Assert no console errors
  expect(consoleErrors).toHaveLength(0);
});