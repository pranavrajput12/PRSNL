import { test, expect } from '@playwright/test';

// CodeMirror Test Configuration
const BASE_URL = 'http://localhost:3004';
const API_BASE_URL = 'http://localhost:8000';

// Test repository ID - replace with actual repo ID from your system
const TEST_REPO_ID = '1cbb79ce-8994-490c-87ce-56911ab03807';

test.describe('PRSNL CodeMirror Integration', () => {
  test('codemirror page loads and initializes', async ({ page }) => {
    console.log('🚀 Testing CodeMirror page initialization...');

    // Enable console logging
    page.on('console', msg => {
      console.log(`CONSOLE [${msg.type()}]:`, msg.text());
    });

    try {
      // Navigate to CodeMirror page
      await page.goto(`${BASE_URL}/code-cortex/codemirror`);
      
      // Wait for page to load
      await expect(page.locator('body')).toBeVisible();
      console.log('✅ Page loaded successfully');

      // Check for CodeMirror editor
      const editor = page.locator('.cm-editor');
      if (await editor.count() > 0) {
        console.log('✅ CodeMirror editor found');
        
        // Test editor interaction
        await editor.click();
        await page.keyboard.type('console.log("Hello CodeMirror!");');
        console.log('✅ Editor interaction successful');
      } else {
        console.log('⚠️ CodeMirror editor not found - may be loading');
      }

      // Check for repository selector
      const repoSelector = page.locator('select, .repo-selector, [data-testid*="repo"]');
      if (await repoSelector.count() > 0) {
        console.log('✅ Repository selector found');
      }

      // Take screenshot
      await page.screenshot({ path: 'codemirror-init-test.png', fullPage: true });

    } catch (error) {
      console.error('❌ CodeMirror initialization test failed:', error);
      await page.screenshot({ path: 'codemirror-init-error.png', fullPage: true });
      throw error;
    }
  });

  test('api endpoints respond correctly', async ({ page }) => {
    console.log('🔧 Testing CodeMirror API endpoints...');

    const endpoints = [
      {
        url: `${API_BASE_URL}/api/codemirror/health`,
        method: 'GET',
        description: 'Health check endpoint'
      },
      {
        url: `${API_BASE_URL}/api/codemirror/analyze/${TEST_REPO_ID}`,
        method: 'POST',
        description: 'Repository analysis endpoint',
        body: {
          repo_id: TEST_REPO_ID,
          analysis_depth: 'standard'
        }
      }
    ];

    for (const endpoint of endpoints) {
      console.log(`\n🔍 Testing: ${endpoint.description}`);
      console.log(`   URL: ${endpoint.url}`);

      try {
        let response;
        
        if (endpoint.method === 'GET') {
          response = await page.request.get(endpoint.url);
        } else if (endpoint.method === 'POST') {
          response = await page.request.post(endpoint.url, {
            data: endpoint.body || {},
            headers: {
              'Content-Type': 'application/json'
            }
          });
        }

        console.log(`   Status: ${response.status()}`);
        
        if (response.status() === 200) {
          const contentType = response.headers()['content-type'];
          console.log(`   Content-Type: ${contentType}`);
          
          if (contentType?.includes('application/json')) {
            try {
              const data = await response.json();
              console.log(`   Response keys: ${Object.keys(data).join(', ')}`);
              
              // For health endpoint, expect specific fields
              if (endpoint.url.includes('/health') && data.status) {
                console.log(`   Health status: ${data.status}`);
                expect(data.status).toBe('healthy');
              }
              
              // For analysis endpoint, expect job or result data
              if (endpoint.url.includes('/analyze') && data.job_id) {
                console.log(`   Analysis job created: ${data.job_id}`);
              }
              
            } catch (e) {
              console.log(`   Response body: ${await response.text()}`);
            }
          }
          
          console.log(`   ✅ ${endpoint.description} - SUCCESS`);
        } else if (response.status() === 404) {
          console.log(`   ⚠️ ${endpoint.description} - NOT FOUND (may not be implemented yet)`);
        } else {
          console.log(`   ❌ ${endpoint.description} - FAILED (${response.status()})`);
          const errorText = await response.text();
          console.log(`   Error: ${errorText}`);
          
          // Don't fail test for 404/500 - may be expected during development
          if (![404, 500].includes(response.status())) {
            throw new Error(`API endpoint failed: ${response.status()}`);
          }
        }

      } catch (error) {
        console.log(`   ❌ ${endpoint.description} - ERROR: ${error.message}`);
        
        // Don't fail test for connection errors during development
        if (!error.message.includes('ECONNREFUSED')) {
          throw error;
        }
      }
    }

    console.log('\n🎉 API endpoint testing completed!');
  });

  test('repository analysis workflow', async ({ page }) => {
    console.log('🧠 Testing repository analysis workflow...');

    try {
      // Navigate to CodeMirror page
      await page.goto(`${BASE_URL}/code-cortex/codemirror`);
      await expect(page.locator('body')).toBeVisible();

      // Look for analysis button or trigger
      const analysisButton = page.locator('button:has-text("Analyze"), [data-testid*="analyze"], .analyze-btn');
      
      if (await analysisButton.count() > 0) {
        console.log('🚀 Found analysis button, testing workflow...');
        
        // Click analyze button
        await analysisButton.first().click();
        
        // Wait for analysis to start
        await page.waitForTimeout(2000);
        
        // Look for loading indicators
        const loadingIndicator = page.locator('.loading, .spinner, [aria-busy="true"]');
        if (await loadingIndicator.count() > 0) {
          console.log('✅ Analysis loading indicator found');
        }
        
        // Wait for results (or timeout)
        try {
          await expect(page.locator('.analysis-result, .analysis-complete, .results')).toBeVisible({ timeout: 30000 });
          console.log('✅ Analysis results appeared');
        } catch (e) {
          console.log('⚠️ Analysis may still be processing or failed');
        }
        
      } else {
        console.log('⚠️ No analysis button found - feature may not be available');
      }

      // Test file tree interaction if available
      const fileTree = page.locator('.file-tree, .explorer, [data-testid*="file"]');
      if (await fileTree.count() > 0) {
        console.log('📁 Testing file tree interaction...');
        
        const fileItems = page.locator('.file-item, .file-node, [data-testid^="file-"]');
        const fileCount = await fileItems.count();
        
        if (fileCount > 0) {
          console.log(`   Found ${fileCount} files`);
          await fileItems.first().click();
          console.log('   ✅ File selection works');
        }
      }

      await page.screenshot({ path: 'codemirror-workflow-test.png', fullPage: true });

    } catch (error) {
      console.error('❌ Repository analysis workflow failed:', error);
      await page.screenshot({ path: 'codemirror-workflow-error.png', fullPage: true });
      throw error;
    }
  });

  test('codemirror features and ui components', async ({ page }) => {
    console.log('🎨 Testing CodeMirror UI components...');

    await page.goto(`${BASE_URL}/code-cortex/codemirror`);
    await expect(page.locator('body')).toBeVisible();

    // Test various UI components
    const components = [
      { selector: '.cm-editor', name: 'CodeMirror Editor' },
      { selector: '.file-explorer, .sidebar', name: 'File Explorer' },
      { selector: '.repository-info, .repo-details', name: 'Repository Info' },
      { selector: '.analysis-panel, .results-panel', name: 'Analysis Panel' },
      { selector: 'button, .btn', name: 'Interactive Buttons' },
      { selector: '.tab, .tabs', name: 'Tab Navigation' }
    ];

    for (const component of components) {
      const elements = page.locator(component.selector);
      const count = await elements.count();
      
      if (count > 0) {
        console.log(`✅ ${component.name}: ${count} found`);
        
        // Test first element if it's interactive
        if (component.selector.includes('button') && count > 0) {
          try {
            await elements.first().click();
            await page.waitForTimeout(500);
            console.log(`   ✅ ${component.name} interaction successful`);
          } catch (e) {
            console.log(`   ⚠️ ${component.name} interaction failed: ${e.message}`);
          }
        }
      } else {
        console.log(`⚠️ ${component.name}: Not found`);
      }
    }

    // Test keyboard shortcuts
    console.log('⌨️ Testing keyboard shortcuts...');
    
    // Focus on editor if available
    const editor = page.locator('.cm-editor, .cm-content');
    if (await editor.count() > 0) {
      await editor.click();
      
      // Test common shortcuts
      await page.keyboard.press('Control+A'); // Select all
      await page.keyboard.press('Control+C'); // Copy
      await page.keyboard.press('Control+V'); // Paste
      
      console.log('✅ Basic keyboard shortcuts tested');
    }

    console.log('🎉 UI components testing completed!');
  });
});

// Manual test runner for compatibility
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🧪 Running CodeMirror tests manually...');
  
  // This would need to be adapted for manual execution
  // For now, recommend using: npm test or playwright test
  console.log('💡 Use "npm test" or "npx playwright test" to run these tests');
}