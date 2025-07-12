import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const routes = [
  { path: '/', name: 'Home' },
  { path: '/insights', name: 'Insights' }, 
  { path: '/videos', name: 'Videos' },
  { path: '/timeline', name: 'Timeline' },
  { path: '/settings', name: 'Settings' },
  { path: '/import', name: 'Import' },
  { path: '/capture', name: 'Capture' },
  { path: '/chat', name: 'Chat' },
  { path: '/ai', name: 'AI' },
  { path: '/code-cortex', name: 'Code Cortex' }
];

// Test modern permalink structure - using actual existing routes
const cortexEntries = [
  { path: '/code-cortex/docs', name: 'Code Docs' },
  { path: '/code-cortex/links', name: 'Code Links' },
  { path: '/code-cortex/projects', name: 'Code Projects' },
  { path: '/code-cortex/synapses', name: 'Code Synapses' },
  // Test new modern routes
  { path: '/thoughts', name: 'Thoughts List' },
  { path: '/videos/1', name: 'Video Entry 1' },
  // Test redirect from old routes
  { path: '/items', name: 'Items Redirect Test' },
  { path: '/item', name: 'Item Redirect Test' }
];

// Create screenshots directory
const screenshotsDir = './test-screenshots';
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir);
}

// Create test results directory
const resultsDir = './test-results';
if (!fs.existsSync(resultsDir)) {
  fs.mkdirSync(resultsDir);
}

console.log('🧪 Starting comprehensive test suite...');

(async () => {
  try {
  const browser = await puppeteer.launch({ 
    headless: false,
    defaultViewport: { width: 1920, height: 1080 },
    args: ['--start-maximized']
  });
  
  const page = await browser.newPage();
  const testResults = [];
  
  // Listen to console events
  const consoleMessages = [];
  page.on('console', msg => {
    const message = `[${msg.type()}] ${msg.text()}`;
    consoleMessages.push(message);
    console.log(message);
  });
  
  // Listen to network events
  const networkErrors = [];
  page.on('response', response => {
    if (response.status() >= 400) {
      const error = `${response.status()} ${response.statusText()} - ${response.url()}`;
      networkErrors.push(error);
      console.log(`[NETWORK ERROR] ${error}`);
    }
  });
  
  // Test main routes
  console.log('🧪 Testing Main Routes\n');
  for (const route of routes) {
    console.log(`\n=== Testing ${route.name}: ${route.path} ===`);
    
    const routeResult = {
      name: route.name,
      path: route.path,
      url: '',
      status: 'failed',
      consoleMessages: [],
      networkErrors: [],
      screenshot: '',
      loadTime: 0
    };
    
    try {
      const startTime = Date.now();
      const fullUrl = `http://localhost:3004${route.path}`;
      
      await page.goto(fullUrl, { 
        waitUntil: 'networkidle2',
        timeout: 15000 
      });
      
      const loadTime = Date.now() - startTime;
      routeResult.loadTime = loadTime;
      routeResult.url = await page.url();
      routeResult.status = 'success';
      
      console.log(`✅ Page loaded successfully in ${loadTime}ms`);
      console.log(`📍 Final URL: ${routeResult.url}`);
      
      // Wait for any dynamic content
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Take screenshot
      const screenshotPath = path.join(screenshotsDir, `${route.name.toLowerCase().replace(/\s+/g, '-')}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });
      routeResult.screenshot = screenshotPath;
      console.log(`📸 Screenshot saved: ${screenshotPath}`);
      
      // Test page interactions
      console.log('🔍 Testing page interactions...');
      
      // Try to find and click common interactive elements
      try {
        const buttons = await page.$$('button');
        console.log(`Found ${buttons.length} button(s)`);
        
        const links = await page.$$('a[href]');
        console.log(`Found ${links.length} link(s)`);
        
        const forms = await page.$$('form');
        console.log(`Found ${forms.length} form(s)`);
        
        // Test specific functionality based on page
        if (route.path === '/chat') {
          console.log('🔍 Testing chat functionality...');
          const messageInput = await page.$('input[type="text"], textarea');
          if (messageInput) {
            console.log('✅ Found message input');
          }
        }
        
        if (route.path === '/capture') {
          console.log('🔍 Testing capture functionality...');
          const fileInput = await page.$('input[type="file"]');
          if (fileInput) {
            console.log('✅ Found file input');
          }
        }
        
        if (route.path === '/videos' || route.path === '/timeline') {
          console.log('🔍 Testing content listing...');
          const items = await page.$$('[data-testid="content-item"], .content-item, .timeline-item');
          console.log(`Found ${items.length} content item(s)`);
        }
      } catch (interactionError) {
        console.log(`⚠️ Interaction test error: ${interactionError.message}`);
      }
      
    } catch (error) {
      console.log(`❌ Failed to load: ${error.message}`);
      routeResult.status = 'failed';
    }
    
    // Capture console messages for this route
    routeResult.consoleMessages = [...consoleMessages];
    routeResult.networkErrors = [...networkErrors];
    
    // Clear arrays for next route
    consoleMessages.length = 0;
    networkErrors.length = 0;
    
    testResults.push(routeResult);
  }
  
  // Test cortex entries
  console.log('\n\n🎯 Testing Cortex Entries\n');
  for (const entry of cortexEntries) {
    console.log(`\n=== Testing ${entry.name}: ${entry.path} ===`);
    
    const entryResult = {
      name: entry.name,
      path: entry.path,
      url: '',
      status: 'failed',
      consoleMessages: [],
      networkErrors: [],
      screenshot: '',
      loadTime: 0,
      content: {}
    };
    
    try {
      const startTime = Date.now();
      const fullUrl = `http://localhost:3004${entry.path}`;
      
      await page.goto(fullUrl, { 
        waitUntil: 'networkidle2',
        timeout: 15000 
      });
      
      const loadTime = Date.now() - startTime;
      entryResult.loadTime = loadTime;
      entryResult.url = await page.url();
      entryResult.status = 'success';
      
      console.log(`✅ Entry loaded successfully in ${loadTime}ms`);
      console.log(`📍 Final URL: ${entryResult.url}`);
      
      // Wait for content to load
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Extract content information
      try {
        const title = await page.$eval('h1, .title, [data-testid="title"]', el => el.textContent).catch(() => 'No title found');
        entryResult.content.title = title;
        console.log(`📋 Title: ${title}`);
        
        // Check for video elements
        if (entry.path.includes('/videos/')) {
          const video = await page.$('video');
          if (video) {
            const videoSrc = await video.evaluate(el => el.src || el.getAttribute('src'));
            entryResult.content.videoSrc = videoSrc;
            console.log(`🎥 Video source: ${videoSrc}`);
          }
        }
        
        // Check for code elements  
        if (entry.path.includes('/code-cortex/')) {
          const codeBlocks = await page.$$('pre, code, .code-block');
          entryResult.content.codeBlocks = codeBlocks.length;
          console.log(`💻 Found ${codeBlocks.length} code block(s)`);
        }
        
        // Check for article content
        if (entry.path.includes('/item/')) {
          const content = await page.$('.content, .article-content, [data-testid="content"]');
          if (content) {
            const contentText = await content.evaluate(el => el.textContent.substring(0, 100));
            entryResult.content.preview = contentText;
            console.log(`📄 Content preview: ${contentText}...`);
            
            // Test AI insights if available
            const aiInsights = await page.$('.ai-insights, [data-testid="ai-insights"]');
            if (aiInsights) {
              console.log('🤖 AI insights found');
              entryResult.content.hasAIInsights = true;
            }
          }
        }
        
      } catch (contentError) {
        console.log(`⚠️ Content extraction error: ${contentError.message}`);
      }
      
      // Take screenshot
      const screenshotPath = path.join(screenshotsDir, `${entry.name.toLowerCase().replace(/\s+/g, '-')}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });
      entryResult.screenshot = screenshotPath;
      console.log(`📸 Screenshot saved: ${screenshotPath}`);
      
    } catch (error) {
      console.log(`❌ Failed to load entry: ${error.message}`);
      entryResult.status = 'failed';
    }
    
    // Capture console messages for this entry
    entryResult.consoleMessages = [...consoleMessages];
    entryResult.networkErrors = [...networkErrors];
    
    // Clear arrays for next entry
    consoleMessages.length = 0;
    networkErrors.length = 0;
    
    testResults.push(entryResult);
  }
  
  // Save test results
  const resultsPath = path.join(resultsDir, `test-results-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  fs.writeFileSync(resultsPath, JSON.stringify(testResults, null, 2));
  console.log(`\n📊 Test results saved: ${resultsPath}`);
  
  // Generate summary report
  const summary = {
    total: testResults.length,
    successful: testResults.filter(r => r.status === 'success').length,
    failed: testResults.filter(r => r.status === 'failed').length,
    avgLoadTime: testResults.filter(r => r.status === 'success').reduce((sum, r) => sum + r.loadTime, 0) / testResults.filter(r => r.status === 'success').length || 0,
    totalConsoleErrors: testResults.reduce((sum, r) => sum + r.consoleMessages.filter(m => m.includes('[error]')).length, 0),
    totalNetworkErrors: testResults.reduce((sum, r) => sum + r.networkErrors.length, 0)
  };
  
  console.log('\n📈 Test Summary:');
  console.log(`✅ Successful: ${summary.successful}/${summary.total}`);
  console.log(`❌ Failed: ${summary.failed}/${summary.total}`);
  console.log(`⏱️ Average Load Time: ${Math.round(summary.avgLoadTime)}ms`);
  console.log(`🚨 Console Errors: ${summary.totalConsoleErrors}`);
  console.log(`🌐 Network Errors: ${summary.totalNetworkErrors}`);
  
  console.log('\n🎉 All testing completed!');
  await browser.close();
  
  } catch (mainError) {
    console.error('❌ Main test error:', mainError.message);
    console.error('Stack:', mainError.stack);
    process.exit(1);
  }
})();
