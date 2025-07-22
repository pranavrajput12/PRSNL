import puppeteer from 'puppeteer';

(async () => {
  console.log('🚀 Starting Puppeteer test for chat search...');
  
  const browser = await puppeteer.launch({
    headless: false, // Show browser for debugging
    defaultViewport: { width: 1280, height: 800 }
  });
  
  const page = await browser.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'log' || msg.type() === 'debug') {
      console.log('PAGE LOG:', msg.text());
    }
  });
  
  try {
    // Navigate to chat page
    console.log('📍 Navigating to chat page...');
    await page.goto('http://localhost:3004/chat', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    // Wait for chat interface to load
    await page.waitForSelector('.message-input', { timeout: 10000 });
    console.log('✅ Chat interface loaded');
    
    // Type a search query
    const searchQuery = 'show me all my saved content about AI and programming';
    console.log(`📝 Typing query: "${searchQuery}"`);
    await page.type('.message-input', searchQuery);
    
    // Send the message
    console.log('📤 Sending message...');
    await page.click('.send-button');
    
    // Wait for response
    console.log('⏳ Waiting for AI response...');
    await page.waitForSelector('.message-wrapper.assistant', { timeout: 30000 });
    
    // Wait a bit more for citations to load
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Check for citations
    const citations = await page.$$eval('.citation-chip', elements => 
      elements.map(el => ({
        title: el.textContent.trim(),
        onclick: el.getAttribute('onclick')
      }))
    );
    
    console.log(`\n📊 RESULTS SUMMARY:`);
    console.log(`Found ${citations.length} citations`);
    
    if (citations.length > 0) {
      console.log('\n📚 Citations found:');
      citations.forEach((citation, index) => {
        console.log(`  ${index + 1}. ${citation.title}`);
      });
      
      // Click on first citation to test navigation
      if (citations.length > 0) {
        console.log('\n🖱️ Clicking on first citation...');
        await page.click('.citation-chip');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const currentUrl = page.url();
        console.log(`📍 Navigated to: ${currentUrl}`);
        
        // Check if it's the correct template
        if (currentUrl.includes('/items/')) {
          console.log('✅ Correctly navigated to timeline template');
        } else if (currentUrl.includes('/videos/')) {
          console.log('✅ Correctly navigated to Visual Cortex');
        } else if (currentUrl.includes('/code-cortex/')) {
          console.log('✅ Correctly navigated to Code Cortex');
        } else if (currentUrl.includes('/conversations/')) {
          console.log('✅ Correctly navigated to Conversations');
        } else {
          console.log('❌ Navigation went to unexpected URL');
        }
      }
    } else {
      console.log('❌ No citations found in response!');
    }
    
    // Take a screenshot
    await page.screenshot({ 
      path: 'chat_search_results.png',
      fullPage: true 
    });
    console.log('\n📸 Screenshot saved as chat_search_results.png');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    await page.screenshot({ path: 'error_screenshot.png' });
  }
  
  console.log('\n✨ Test complete! Browser will close in 5 seconds...');
  await new Promise(resolve => setTimeout(resolve, 5000));
  await browser.close();
})();