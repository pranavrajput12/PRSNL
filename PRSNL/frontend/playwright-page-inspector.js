import { test, expect } from '@playwright/test';

test.describe('Page Inspector', () => {
  test('page inspector functionality', async ({ page }) => {
    console.log('🔍 Starting Page Inspector test...');

    // Enable comprehensive console logging
    page.on('console', msg => {
      console.log(`CONSOLE [${msg.type()}]:`, msg.text());
    });

    // Track network requests
    page.on('request', request => {
      console.log(`REQUEST: ${request.method()} ${request.url()}`);
    });

    page.on('response', response => {
      console.log(`RESPONSE: ${response.status()} ${response.url()}`);
    });

    try {
      // Navigate to main page
      console.log('📍 Navigating to main page...');
      await page.goto('http://localhost:3004');
      
      // Wait for page to fully load
      await page.waitForLoadState('networkidle');
      console.log('✅ Page loaded completely');

      // Inspect page structure
      console.log('🏗️ Inspecting page structure...');
      
      // Check for main layout elements
      const header = page.locator('header, [role="banner"]');
      const main = page.locator('main, [role="main"]');
      const nav = page.locator('nav, [role="navigation"]');
      
      const hasHeader = await header.count() > 0;
      const hasMain = await main.count() > 0;
      const hasNav = await nav.count() > 0;
      
      console.log(`📊 Layout structure: Header(${hasHeader}) Main(${hasMain}) Nav(${hasNav})`);

      // Check for accessibility attributes
      console.log('♿ Checking accessibility...');
      const ariaLabels = await page.locator('[aria-label]').count();
      const ariaDescriptions = await page.locator('[aria-describedby]').count();
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();
      
      console.log(`♿ Accessibility: ARIA labels(${ariaLabels}) Descriptions(${ariaDescriptions}) Headings(${headings})`);

      // Check for interactive elements
      console.log('🖱️ Inspecting interactive elements...');
      const buttons = await page.locator('button').count();
      const links = await page.locator('a').count();
      const inputs = await page.locator('input, textarea, select').count();
      
      console.log(`🖱️ Interactive: Buttons(${buttons}) Links(${links}) Inputs(${inputs})`);

      // Check for loading states
      console.log('⏳ Checking for loading indicators...');
      const loadingElements = page.locator('.loading, [aria-busy="true"], .spinner, .skeleton');
      const loadingCount = await loadingElements.count();
      
      if (loadingCount > 0) {
        console.log(`⚠️ Found ${loadingCount} loading indicators - page may still be loading`);
      } else {
        console.log('✅ No loading indicators found - page appears fully loaded');
      }

      // Check for error states
      console.log('❌ Checking for error indicators...');
      const errorElements = page.locator('.error, [role="alert"], .alert-error, .text-red-500');
      const errorCount = await errorElements.count();
      
      if (errorCount > 0) {
        console.log(`⚠️ Found ${errorCount} error indicators`);
        const errorText = await errorElements.first().textContent();
        console.log(`Error message: ${errorText}`);
      } else {
        console.log('✅ No error indicators found');
      }

      // Check for performance issues
      console.log('⚡ Performance inspection...');
      const images = await page.locator('img').count();
      const scripts = await page.locator('script').count();
      const stylesheets = await page.locator('link[rel="stylesheet"]').count();
      
      console.log(`⚡ Resources: Images(${images}) Scripts(${scripts}) Stylesheets(${stylesheets})`);

      // Check for modern web features
      console.log('🚀 Checking modern web features...');
      const hasServiceWorker = await page.evaluate(() => 'serviceWorker' in navigator);
      const hasWebWorkers = await page.evaluate(() => 'Worker' in window);
      const hasLocalStorage = await page.evaluate(() => 'localStorage' in window);
      
      console.log(`🚀 Features: ServiceWorker(${hasServiceWorker}) WebWorkers(${hasWebWorkers}) LocalStorage(${hasLocalStorage})`);

      // Test responsive design
      console.log('📱 Testing responsive design...');
      await page.setViewportSize({ width: 375, height: 667 }); // Mobile
      await page.waitForTimeout(1000);
      
      const mobileNav = page.locator('.mobile-nav, .hamburger, [data-testid*="mobile"]');
      const hasMobileNav = await mobileNav.count() > 0;
      console.log(`📱 Mobile navigation: ${hasMobileNav ? 'Present' : 'Not found'}`);
      
      // Reset to desktop
      await page.setViewportSize({ width: 1280, height: 800 });

      // Take comprehensive screenshots
      await page.screenshot({ path: 'page-inspector-desktop.png', fullPage: true });
      
      await page.setViewportSize({ width: 375, height: 667 });
      await page.screenshot({ path: 'page-inspector-mobile.png', fullPage: true });
      
      console.log('🎉 Page inspection completed successfully!');

      // Assertions
      expect(hasMain).toBeTruthy();
      expect(headings).toBeGreaterThan(0);
      expect(buttons + links).toBeGreaterThan(0);
      expect(errorCount).toBe(0);

    } catch (error) {
      console.error('❌ Page inspector failed:', error);
      await page.screenshot({ path: 'page-inspector-error.png', fullPage: true });
      throw error;
    }
  });

  test('page performance metrics', async ({ page }) => {
    console.log('⚡ Testing page performance...');

    await page.goto('http://localhost:3004');
    
    // Measure page load performance
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        domInteractive: navigation.domInteractive - navigation.navigationStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
      };
    });

    console.log('📊 Performance Metrics:');
    console.log(`  DOM Content Loaded: ${performanceMetrics.domContentLoaded}ms`);
    console.log(`  Load Complete: ${performanceMetrics.loadComplete}ms`);
    console.log(`  DOM Interactive: ${performanceMetrics.domInteractive}ms`);
    console.log(`  First Paint: ${performanceMetrics.firstPaint}ms`);
    console.log(`  First Contentful Paint: ${performanceMetrics.firstContentfulPaint}ms`);

    // Check for reasonable performance
    expect(performanceMetrics.domInteractive).toBeLessThan(5000);
    expect(performanceMetrics.firstContentfulPaint).toBeLessThan(3000);

    console.log('✅ Performance metrics within acceptable ranges');
  });
});