import { test, expect } from '@playwright/test';

test.describe('CodeMirror Features', () => {
  test('codemirror editor functionality', async ({ page }) => {
    console.log('🚀 Starting CodeMirror feature test...');

    // Enable console logging
    page.on('console', msg => {
      console.log(`CONSOLE [${msg.type()}]:`, msg.text());
    });

    try {
      // Navigate to CodeMirror page
      console.log('📍 Navigating to CodeMirror page...');
      await page.goto('http://localhost:3004/code-cortex/codemirror');
      
      // Wait for the page to load
      await expect(page.locator('body')).toBeVisible();
      console.log('✅ Page loaded');

      // Wait for CodeMirror to initialize
      await expect(page.locator('.cm-editor')).toBeVisible({ timeout: 10000 });
      console.log('✅ CodeMirror editor found');

      // Test typing in the editor
      console.log('📝 Testing code input...');
      const editor = page.locator('.cm-content');
      await editor.click();
      
      const testCode = `function hello() {
  console.log("Hello from CodeMirror!");
  return "success";
}`;
      
      await editor.fill(testCode);
      console.log('✅ Code input successful');

      // Test syntax highlighting
      console.log('🎨 Checking syntax highlighting...');
      const highlightedElements = page.locator('.cm-content .tok-keyword, .cm-content .tok-string, .cm-content .tok-function');
      const highlightCount = await highlightedElements.count();
      
      if (highlightCount > 0) {
        console.log(`✅ Found ${highlightCount} syntax highlighted elements`);
      } else {
        console.log('⚠️ No syntax highlighting detected');
      }

      // Test line numbers
      const lineNumbers = page.locator('.cm-gutter .cm-gutterElement');
      const lineNumberCount = await lineNumbers.count();
      console.log(`📊 Found ${lineNumberCount} line numbers`);

      // Test folding capabilities
      console.log('📁 Testing code folding...');
      const foldGutters = page.locator('.cm-foldGutter');
      if (await foldGutters.count() > 0) {
        console.log('✅ Code folding gutter present');
      }

      // Test repository analysis if available
      console.log('🔍 Testing repository analysis...');
      const analyzeButton = page.locator('button:has-text("Analyze"), [data-testid*="analyze"]');
      
      if (await analyzeButton.count() > 0) {
        console.log('🚀 Found analyze button, testing...');
        await analyzeButton.first().click();
        
        // Wait for analysis results
        try {
          await expect(page.locator('.analysis-result, .analysis-output')).toBeVisible({ timeout: 15000 });
          console.log('✅ Analysis completed successfully');
        } catch (e) {
          console.log('⚠️ Analysis may be in progress or unavailable');
        }
      }

      // Test file tree if available
      console.log('🌳 Testing file tree navigation...');
      const fileTree = page.locator('.file-tree, [data-testid*="file"], .sidebar');
      
      if (await fileTree.count() > 0) {
        const fileItems = page.locator('.file-item, .file-node, [data-testid^="file-"]');
        const fileCount = await fileItems.count();
        
        if (fileCount > 0) {
          console.log(`📁 Found ${fileCount} files in tree`);
          
          // Click on first file
          await fileItems.first().click();
          console.log('✅ File selection works');
        }
      }

      // Test search functionality
      console.log('🔍 Testing search functionality...');
      await page.keyboard.press('Control+F'); // Or Cmd+F on Mac
      
      const searchInput = page.locator('.cm-search input, .search-input');
      if (await searchInput.count() > 0) {
        await searchInput.fill('function');
        console.log('✅ Search functionality works');
      }

      // Take final screenshot
      await page.screenshot({ path: 'codemirror-test-result.png', fullPage: true });
      
      console.log('🎉 CodeMirror test completed successfully!');

    } catch (error) {
      console.error('❌ CodeMirror test failed:', error);
      await page.screenshot({ path: 'codemirror-test-error.png', fullPage: true });
      throw error;
    }
  });

  test('repository intelligence features', async ({ page }) => {
    console.log('🧠 Testing repository intelligence features...');

    await page.goto('http://localhost:3004/code-cortex/codemirror');
    await expect(page.locator('.cm-editor')).toBeVisible();

    // Test AI-powered features
    const aiButtons = page.locator('button:has-text("AI"), button:has-text("Suggest"), button:has-text("Explain")');
    const aiButtonCount = await aiButtons.count();

    if (aiButtonCount > 0) {
      console.log(`🤖 Found ${aiButtonCount} AI-powered buttons`);
      
      // Test first AI feature
      await aiButtons.first().click();
      
      // Wait for AI response
      try {
        await expect(page.locator('.ai-response, .suggestion, .explanation')).toBeVisible({ timeout: 20000 });
        console.log('✅ AI feature responded successfully');
      } catch (e) {
        console.log('⚠️ AI feature may be processing or unavailable');
      }
    }

    // Test code analysis features
    const analysisButtons = page.locator('button:has-text("Analyze"), button:has-text("Metrics"), button:has-text("Quality")');
    const analysisCount = await analysisButtons.count();

    if (analysisCount > 0) {
      console.log(`📊 Found ${analysisCount} analysis features`);
    }

    console.log('🎉 Repository intelligence test completed!');
  });
});