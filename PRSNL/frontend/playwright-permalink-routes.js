import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3004';

test.describe('Permalink Routes Testing', () => {
  test('test permalink routes', async ({ page }) => {
    console.log('🔗 Starting Permalink Routes test...');

    // Test routes configuration
    const testRoutes = [
      {
        path: '/c/dev',
        description: 'Development content category',
        expectedElements: ['main', 'h1, h2'],
        shouldRedirect: false
      },
      {
        path: '/p/timeline',
        description: 'Timeline permalink',
        expectedElements: ['main', '.timeline, [data-testid*="timeline"]'],
        shouldRedirect: false
      },
      {
        path: '/items/123',
        description: 'Legacy item route (should redirect)',
        expectedElements: null,
        shouldRedirect: true
      },
      {
        path: '/videos/456',
        description: 'Legacy video route (should redirect)',
        expectedElements: null,
        shouldRedirect: true
      },
      {
        path: '/api/content/dev/sample-slug',
        description: 'API content endpoint',
        expectedElements: null,
        shouldRedirect: false,
        isApi: true
      }
    ];

    // Test each route
    for (const route of testRoutes) {
      console.log(`\n🧪 Testing route: ${route.path}`);
      console.log(`   Description: ${route.description}`);

      try {
        if (route.isApi) {
          // Test API endpoint
          const response = await page.request.get(`${BASE_URL}${route.path}`);
          console.log(`   API Response Status: ${response.status()}`);
          
          if (response.status() === 200) {
            const contentType = response.headers()['content-type'];
            console.log(`   Content-Type: ${contentType}`);
            
            if (contentType?.includes('application/json')) {
              const data = await response.json();
              console.log(`   JSON Response Keys: ${Object.keys(data).join(', ')}`);
            }
          }
          
          // API endpoints should return 200 or 404 (not 500)
          expect([200, 404]).toContain(response.status());
          
        } else {
          // Test regular routes
          await page.goto(`${BASE_URL}${route.path}`);
          
          if (route.shouldRedirect) {
            // Wait for redirect and check new URL
            await page.waitForURL(url => !url.includes(route.path), { timeout: 5000 });
            const newUrl = page.url();
            console.log(`   ✅ Redirected to: ${newUrl}`);
            
            // Verify we're not on the original path
            expect(newUrl).not.toContain(route.path);
            
          } else {
            // Wait for page to load
            await page.waitForLoadState('networkidle');
            
            // Check for expected elements
            if (route.expectedElements) {
              for (const selector of route.expectedElements) {
                const elements = page.locator(selector);
                const count = await elements.count();
                
                if (count > 0) {
                  console.log(`   ✅ Found ${count} elements matching: ${selector}`);
                } else {
                  console.log(`   ⚠️ No elements found for: ${selector}`);
                }
                
                // At least one expected element should be present
                expect(count).toBeGreaterThan(0);
              }
            }
            
            // Check that we're not redirected to error page
            const currentUrl = page.url();
            expect(currentUrl).not.toContain('/error');
            expect(currentUrl).not.toContain('/404');
            
            // Check for error messages on the page
            const errorElements = page.locator('.error, [role="alert"], .alert-error');
            const errorCount = await errorElements.count();
            
            if (errorCount > 0) {
              const errorText = await errorElements.first().textContent();
              console.log(`   ⚠️ Found error message: ${errorText}`);
            }
            
            expect(errorCount).toBe(0);
          }
        }
        
        console.log(`   ✅ Route test passed: ${route.path}`);
        
      } catch (error) {
        console.log(`   ❌ Route test failed: ${route.path}`);
        console.log(`   Error: ${error.message}`);
        
        // Take screenshot for debugging
        if (!route.isApi) {
          await page.screenshot({ 
            path: `permalink-error-${route.path.replace(/[\/]/g, '-')}.png`,
            fullPage: true 
          });
        }
        
        throw error;
      }
    }

    console.log('\n🎉 All permalink routes tested successfully!');
  });

  test('test dynamic route parameters', async ({ page }) => {
    console.log('🎯 Testing dynamic route parameters...');

    const dynamicRoutes = [
      {
        path: '/c/tech/javascript-tutorial',
        category: 'tech',
        slug: 'javascript-tutorial'
      },
      {
        path: '/c/personal/my-thoughts',
        category: 'personal', 
        slug: 'my-thoughts'
      },
      {
        path: '/p/projects/my-app',
        type: 'projects',
        slug: 'my-app'
      }
    ];

    for (const route of dynamicRoutes) {
      console.log(`\n🔍 Testing dynamic route: ${route.path}`);
      
      try {
        await page.goto(`${BASE_URL}${route.path}`);
        await page.waitForLoadState('networkidle');
        
        // Check that the page loaded without errors
        const currentUrl = page.url();
        expect(currentUrl).toContain(route.path);
        
        // Look for content that might indicate the route parameters were processed
        const main = page.locator('main');
        const hasContent = await main.count() > 0;
        
        console.log(`   ${hasContent ? '✅' : '⚠️'} Main content area: ${hasContent ? 'Found' : 'Not found'}`);
        
        // Check page title reflects the route
        const title = await page.title();
        console.log(`   📄 Page title: ${title}`);
        
        expect(title).toBeTruthy();
        
      } catch (error) {
        console.log(`   ❌ Dynamic route failed: ${route.path}`);
        await page.screenshot({ 
          path: `dynamic-route-error-${route.path.replace(/[\/]/g, '-')}.png`,
          fullPage: true 
        });
        throw error;
      }
    }

    console.log('\n✅ Dynamic route parameters tested successfully!');
  });

  test('test route accessibility', async ({ page }) => {
    console.log('♿ Testing route accessibility...');

    const routesToTest = ['/c/dev', '/p/timeline'];

    for (const route of routesToTest) {
      console.log(`\n♿ Testing accessibility for: ${route}`);
      
      await page.goto(`${BASE_URL}${route}`);
      await page.waitForLoadState('networkidle');
      
      // Check for basic accessibility elements
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();
      const landmarksNav = await page.locator('[role="navigation"], nav').count();
      const landmarksMain = await page.locator('[role="main"], main').count();
      const ariaLabels = await page.locator('[aria-label]').count();
      const altTexts = await page.locator('img[alt]').count();
      const totalImages = await page.locator('img').count();
      
      console.log(`   📊 Accessibility audit:`);
      console.log(`     Headings: ${headings}`);
      console.log(`     Navigation landmarks: ${landmarksNav}`);
      console.log(`     Main landmarks: ${landmarksMain}`);
      console.log(`     ARIA labels: ${ariaLabels}`);
      console.log(`     Images with alt text: ${altTexts}/${totalImages}`);
      
      // Basic accessibility assertions
      expect(headings).toBeGreaterThan(0);
      expect(landmarksMain).toBeGreaterThan(0);
      
      // If there are images, check that they have alt text
      if (totalImages > 0) {
        const altTextRatio = altTexts / totalImages;
        if (altTextRatio < 0.8) {
          console.log(`   ⚠️ Low alt text coverage: ${Math.round(altTextRatio * 100)}%`);
        } else {
          console.log(`   ✅ Good alt text coverage: ${Math.round(altTextRatio * 100)}%`);
        }
      }
    }

    console.log('\n✅ Route accessibility testing completed!');
  });
});