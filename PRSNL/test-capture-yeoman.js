const { chromium } = require('playwright');

async function testYeomanCapture() {
  console.log('🚀 Testing capture with yeoman.io/learning/');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500,
  });
  
  const page = await browser.newPage();
  
  // Track console logs
  const logs = { errors: [], warnings: [], info: [] };
  page.on('console', msg => {
    if (msg.type() === 'error') logs.errors.push(msg.text());
    else if (msg.type() === 'warning') logs.warnings.push(msg.text());
    else logs.info.push(msg.text());
  });
  
  // Track API calls
  const apiCalls = [];
  page.on('request', req => {
    if (req.url().includes('/api/')) {
      apiCalls.push({
        method: req.method(),
        url: req.url(),
        postData: req.postData()
      });
    }
  });
  
  const apiResponses = [];
  page.on('response', resp => {
    if (resp.url().includes('/api/')) {
      apiResponses.push({
        url: resp.url(),
        status: resp.status()
      });
    }
  });
  
  try {
    // Login
    await page.goto('http://localhost:3004/auth/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'testpassword123');
    await page.click('button:has-text("Sign In")');
    await page.waitForURL(url => !url.includes('/auth/login'), { timeout: 10000 });
    console.log('✅ Login successful');
    
    // Navigate to capture
    await page.click('a[href="/capture"]');
    await page.waitForSelector('.terminal-input.primary-input', { timeout: 10000 });
    console.log('✅ Capture page loaded');
    
    // Enter URL
    await page.fill('.terminal-input.primary-input', 'https://yeoman.io/learning/');
    console.log('✅ URL entered');
    
    // Wait for AI suggestions
    await page.waitForTimeout(3000);
    
    // Check detected content type
    const typeElement = await page.locator('.content-type-badge, .detected-type').first();
    if (await typeElement.isVisible()) {
      const detectedType = await typeElement.textContent();
      console.log(`📊 Detected content type: ${detectedType}`);
    }
    
    // Submit
    await page.click('.execute-button');
    
    // Wait for response
    const response = await page.waitForResponse(resp => 
      resp.url().includes('/api/capture'), 
      { timeout: 30000 }
    );
    
    console.log(`📥 Capture response: ${response.status()}`);
    
    if (response.ok()) {
      const data = await response.json();
      console.log('✅ Capture successful!');
      console.log('Item ID:', data.id);
      console.log('Title:', data.title);
      console.log('Type:', data.item_type);
    } else {
      const error = await response.text();
      console.log('❌ Capture failed:', error);
    }
    
    // Check terminal output
    const terminalLines = await page.locator('.terminal-line').allTextContents();
    console.log('\n📟 Terminal output:');
    terminalLines.slice(-5).forEach(line => console.log(`  > ${line}`));
    
    // Analysis
    console.log('\n📊 Test Analysis:');
    console.log(`Total API calls: ${apiCalls.length}`);
    console.log(`Console errors: ${logs.errors.length}`);
    console.log(`Console warnings: ${logs.warnings.length}`);
    
    // Show API calls
    console.log('\n🔍 API Calls:');
    apiCalls.forEach((call, i) => {
      const resp = apiResponses.find(r => r.url === call.url);
      console.log(`${i+1}. ${call.method} ${call.url.replace('http://localhost:3004', '')} -> ${resp?.status || 'pending'}`);
    });
    
    // Show errors
    if (logs.errors.length > 0) {
      console.log('\n❌ Errors found:');
      logs.errors.forEach(err => console.log(`  - ${err}`));
    }
    
  } catch (error) {
    console.error('Test failed:', error.message);
    await page.screenshot({ path: 'yeoman-test-error.png' });
  } finally {
    await browser.close();
  }
}

testYeomanCapture().catch(console.error);