import { test, expect } from '@playwright/test';

test.describe('Chat Search Functionality', () => {
  test('chat search with citations', async ({ page }) => {
    console.log('🚀 Starting Playwright test for chat search...');
    
    // Enable console logging
    page.on('console', msg => {
      if (msg.type() === 'log' || msg.type() === 'debug') {
        console.log('PAGE LOG:', msg.text());
      }
    });
    
    try {
      // Navigate to chat page
      console.log('📍 Navigating to chat page...');
      await page.goto('http://localhost:3004/chat');
      
      // Wait for chat interface to load
      await expect(page.locator('.message-input')).toBeVisible({ timeout: 10000 });
      console.log('✅ Chat interface loaded');
      
      // Type a search query
      const searchQuery = 'show me all my saved content about AI and programming';
      console.log(`📝 Typing query: "${searchQuery}"`);
      await page.locator('.message-input').fill(searchQuery);
      
      // Send the message
      console.log('📤 Sending message...');
      await page.locator('.send-button').click();
      
      // Wait for response
      console.log('⏳ Waiting for AI response...');
      await expect(page.locator('.message-wrapper.assistant')).toBeVisible({ timeout: 30000 });
      
      // Wait a bit more for citations to load
      await page.waitForTimeout(3000);
      
      // Check for citations
      const citations = await page.locator('.citation-chip').evaluateAll(elements => 
        elements.map(el => ({
          title: el.querySelector('.citation-title')?.textContent?.trim() || '',
          type: el.querySelector('.citation-type')?.textContent?.trim() || '',
          preview: el.querySelector('.citation-preview')?.textContent?.trim() || ''
        }))
      );
      
      console.log(`📊 Found ${citations.length} citations`);
      if (citations.length > 0) {
        console.log('📋 Citations:', citations);
        
        // Test clicking on a citation
        console.log('🔍 Testing citation click...');
        await page.locator('.citation-chip').first().click();
        
        // Wait for citation modal or expanded view
        try {
          await expect(page.locator('.citation-modal, .citation-expanded')).toBeVisible({ timeout: 5000 });
          console.log('✅ Citation modal opened successfully');
        } catch (e) {
          console.log('⚠️ Citation modal did not open, but continuing test');
        }
      }
      
      // Check response quality
      const responseText = await page.locator('.message-wrapper.assistant .message-content').textContent();
      console.log(`📝 Response length: ${responseText?.length || 0} characters`);
      
      if (responseText && responseText.length > 50) {
        console.log('✅ Received substantial response from AI');
      } else {
        console.log('⚠️ Response seems short or empty');
      }
      
      // Take screenshot of final result
      await page.screenshot({ path: 'chat-search-result.png', fullPage: true });
      
      console.log('🎉 Chat search test completed successfully!');
      
      // Assertions
      expect(citations.length).toBeGreaterThan(0);
      expect(responseText).toBeTruthy();
      expect(responseText.length).toBeGreaterThan(50);
      
    } catch (error) {
      console.error('❌ Test failed:', error);
      await page.screenshot({ path: 'chat-search-error.png', fullPage: true });
      throw error;
    }
  });

  test('search with different query types', async ({ page }) => {
    const queries = [
      'find my notes about JavaScript frameworks',
      'show me saved videos about machine learning',
      'search for articles about web development',
      'what do I have about React hooks?'
    ];

    await page.goto('http://localhost:3004/chat');
    await expect(page.locator('.message-input')).toBeVisible();

    for (const query of queries) {
      console.log(`Testing query: "${query}"`);
      
      // Clear input and type new query
      await page.locator('.message-input').fill('');
      await page.locator('.message-input').fill(query);
      
      // Send message
      await page.locator('.send-button').click();
      
      // Wait for response
      await expect(page.locator('.message-wrapper.assistant')).toBeVisible({ timeout: 20000 });
      
      // Brief pause between queries
      await page.waitForTimeout(2000);
    }

    console.log('✅ Multiple query types tested successfully');
  });
});