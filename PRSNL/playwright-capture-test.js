const { chromium } = require('playwright');

// ANSI color codes for better terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
};

// Helper function for formatted logging
function log(message, type = 'info') {
  const timestamp = new Date().toISOString();
  const typeColors = {
    info: colors.cyan,
    success: colors.green,
    error: colors.red,
    warning: colors.yellow,
    step: colors.magenta,
    api: colors.blue,
  };
  
  const color = typeColors[type] || colors.white;
  console.log(`${color}[${timestamp}] ${message}${colors.reset}`);
}

// Main test function
async function testCaptureFeature() {
  log('🚀 Starting Capture Feature Test', 'step');
  log(`URL to capture: https://yeoman.io/learning/`, 'info');
  
  const browser = await chromium.launch({
    headless: false, // Set to true for CI/CD
    slowMo: 500, // Slow down for visibility
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });
  
  const page = await context.newPage();
  
  // Set up console monitoring
  const consoleLogs = [];
  page.on('console', msg => {
    const logEntry = {
      type: msg.type(),
      text: msg.text(),
      timestamp: new Date().toISOString(),
    };
    consoleLogs.push(logEntry);
    
    // Log to our console with appropriate color
    if (msg.type() === 'error') {
      log(`🔴 Browser Console Error: ${msg.text()}`, 'error');
    } else if (msg.type() === 'warning') {
      log(`🟡 Browser Console Warning: ${msg.text()}`, 'warning');
    } else {
      log(`🟢 Browser Console: ${msg.text()}`, 'info');
    }
  });
  
  // Monitor network requests
  const apiCalls = [];
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      log(`📤 API Request: ${request.method()} ${request.url()}`, 'api');
      apiCalls.push({
        method: request.method(),
        url: request.url(),
        headers: request.headers(),
        postData: request.postData(),
      });
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      log(`📥 API Response: ${response.status()} ${response.url()}`, 'api');
    }
  });
  
  try {
    // Step 0: Login first
    log('📍 Step 0: Logging in', 'step');
    await page.goto('http://localhost:3004/auth/login', {
      waitUntil: 'networkidle',
    });
    
    // Wait for login form
    await page.waitForSelector('input[type="email"], input[name="email"]', { timeout: 10000 });
    log('✅ Login page loaded', 'success');
    
    // Fill login credentials
    await page.fill('input[type="email"], input[name="email"]', 'test@example.com');
    await page.fill('input[type="password"], input[name="password"]', 'testpassword123');
    log('✅ Credentials entered', 'success');
    
    // Submit login form - match the actual button text "Sign In"
    const loginButton = await page.locator('button:has-text("Sign In"), button[type="submit"]').first();
    
    // Ensure button is visible
    await loginButton.waitFor({ state: 'visible', timeout: 5000 });
    log('✅ Sign In button found', 'success');
    
    // Click login button (force click due to magnetic-button animation)
    await loginButton.click({ force: true });
    log('🔄 Sign In button clicked', 'info');
    
    // Wait for either navigation or error
    await page.waitForTimeout(2000); // Give time for any error messages
    
    // Check for error messages first
    const errorMessage = await page.locator('.error-message, .alert-error, [role="alert"]').first();
    if (await errorMessage.isVisible()) {
      const errorText = await errorMessage.textContent();
      log(`⚠️ Login error message: ${errorText}`, 'warning');
    }
    
    // Wait for navigation
    try {
      await page.waitForURL(url => typeof url === 'string' && !url.includes('/auth/login'), { timeout: 15000 });
      log('✅ Navigation successful', 'success');
    } catch (e) {
      // Check if we're still on login page
      const currentUrl = page.url();
      if (currentUrl.includes('/auth/login')) {
        // We're still on login page, login failed
        throw new Error('Login failed - still on login page. Check credentials or authentication system.');
      }
      // If we're not on login page, we navigated somewhere else
      log('✅ Login successful (navigated to: ' + currentUrl + ')', 'success');
    }
    
    // Wait for page to stabilize
    await page.waitForLoadState('networkidle');
    
    log('✅ Login successful', 'success');
    
    // Step 1: Navigate to capture page
    log('📍 Step 1: Navigating to capture page', 'step');
    
    // Try clicking the Capture link in the navigation
    const captureLink = await page.locator('a[href="/capture"]').first();
    if (await captureLink.isVisible()) {
      await captureLink.click();
      await page.waitForLoadState('networkidle');
      log('✅ Navigated to capture page via navigation link', 'success');
    } else {
      // Fallback to direct navigation
      await page.goto('http://localhost:3004/capture', {
        waitUntil: 'networkidle',
      });
    }
    
    // Wait for page to fully load
    await page.waitForTimeout(3000);
    
    // Wait for page to be fully loaded - wait for terminal interface
    try {
      await page.waitForSelector('.terminal-input.primary-input, .processing-steps', { timeout: 15000 });
    } catch (e) {
      log('⚠️ Terminal interface not found, trying alternative selectors', 'warning');
      await page.waitForSelector('.dynamic-capture-input, .terminal-container', { timeout: 10000 });
    }
    
    log('✅ Capture page loaded successfully', 'success');
    
    // Take a screenshot to see the current state
    await page.screenshot({ path: 'capture-page-loaded.png' });
    log('📸 Screenshot of loaded page saved', 'info');
    
    // Check page title
    const pageTitle = await page.title();
    log(`Page title: ${pageTitle}`, 'info');
    
    // Step 2: Check initial terminal state
    log('📍 Step 2: Checking initial terminal state', 'step');
    const terminalLines = await page.locator('.terminal-line').allTextContents();
    log(`Terminal lines found: ${terminalLines.length}`, 'info');
    terminalLines.forEach((line, index) => {
      log(`  Terminal[${index}]: ${line}`, 'dim');
    });
    
    // Step 3: Input URL
    log('📍 Step 3: Entering URL', 'step');
    const urlInput = await page.locator('.terminal-input.primary-input').first();
    if (!await urlInput.isVisible()) {
      // Try alternative selector
      const altInput = await page.locator('input[placeholder*="URL"]').first();
      if (await altInput.isVisible()) {
        await altInput.click();
        await altInput.fill('https://yeoman.io/learning/');
      } else {
        throw new Error('URL input field not found or not visible');
      }
    } else {
      await urlInput.click();
      await urlInput.fill('https://yeoman.io/learning/');
    }
    log('✅ URL entered successfully', 'success');
    
    // Wait for any URL validation or type detection
    await page.waitForTimeout(2000);
    
    // Check if content type was detected
    const contentTypeElement = await page.locator('.content-type-selector, [data-testid="content-type"]').first();
    if (await contentTypeElement.isVisible()) {
      const detectedType = await contentTypeElement.textContent();
      log(`🔍 Detected content type: ${detectedType}`, 'info');
    }
    
    // Step 4: Check step progression
    log('📍 Step 4: Monitoring step progression', 'step');
    for (let i = 1; i <= 4; i++) {
      const stepIndicator = await page.locator(`.step-indicator`).nth(i - 1);
      if (await stepIndicator.isVisible()) {
        const stepStatus = await stepIndicator.evaluate(el => {
          if (el.querySelector('.step-number')) return 'pending';
          if (el.querySelector('svg')) return 'completed';
          return 'unknown';
        });
        log(`  Step ${i} status: ${stepStatus}`, 'info');
      }
    }
    
    // Step 5: Submit the form
    log('📍 Step 5: Submitting capture form', 'step');
    
    // Look for submit button - the execute button in terminal interface
    const submitButton = await page.locator('.execute-button, button[type="submit"]').first();
    if (!await submitButton.isVisible()) {
      throw new Error('Submit button not found');
    }
    
    // Click submit and wait for response
    const [captureResponse] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/capture'), { timeout: 30000 }),
      submitButton.click(),
    ]);
    
    log(`📥 Capture API Response: ${captureResponse.status()}`, 'api');
    
    if (captureResponse.ok()) {
      const responseData = await captureResponse.json();
      log('✅ Capture successful!', 'success');
      log(`Response data: ${JSON.stringify(responseData, null, 2)}`, 'info');
    } else {
      const errorText = await captureResponse.text();
      log(`❌ Capture failed: ${errorText}`, 'error');
    }
    
    // Step 6: Check for success notification
    log('📍 Step 6: Checking for success notification', 'step');
    const notification = await page.locator('.notification, .toast, [role="alert"]').first();
    if (await notification.isVisible()) {
      const notificationText = await notification.textContent();
      log(`📢 Notification: ${notificationText}`, 'info');
    }
    
    // Step 7: Check final terminal output
    log('📍 Step 7: Final terminal output', 'step');
    const finalTerminalLines = await page.locator('.terminal-line').allTextContents();
    log(`Final terminal lines: ${finalTerminalLines.length}`, 'info');
    
    // Show new terminal lines
    if (finalTerminalLines.length > terminalLines.length) {
      log('New terminal output:', 'info');
      for (let i = terminalLines.length; i < finalTerminalLines.length; i++) {
        log(`  > ${finalTerminalLines[i]}`, 'dim');
      }
    }
    
    // Wait a bit to see the final state
    await page.waitForTimeout(3000);
    
    // Summary
    log('📊 Test Summary', 'step');
    log(`Total console logs: ${consoleLogs.length}`, 'info');
    log(`Total API calls: ${apiCalls.length}`, 'info');
    log(`Errors encountered: ${consoleLogs.filter(l => l.type === 'error').length}`, 
        consoleLogs.some(l => l.type === 'error') ? 'error' : 'info');
    
    // Print all API calls for debugging
    if (apiCalls.length > 0) {
      log('API Calls Detail:', 'info');
      apiCalls.forEach((call, index) => {
        log(`  Call ${index + 1}: ${call.method} ${call.url}`, 'api');
        if (call.postData) {
          log(`    Body: ${call.postData.substring(0, 200)}...`, 'dim');
        }
      });
    }
    
  } catch (error) {
    log(`❌ Test failed: ${error.message}`, 'error');
    log(`Stack trace: ${error.stack}`, 'error');
    
    // Take screenshot on error
    const screenshotPath = `capture-test-error-${Date.now()}.png`;
    await page.screenshot({ 
      path: screenshotPath,
      fullPage: true 
    });
    log(`📸 Screenshot saved: ${screenshotPath}`, 'info');
    
    // Print recent console logs on error
    if (consoleLogs.length > 0) {
      log('Recent console logs:', 'error');
      consoleLogs.slice(-10).forEach(logEntry => {
        log(`  [${logEntry.type}] ${logEntry.text}`, 'dim');
      });
    }
    
    throw error;
  } finally {
    await browser.close();
    log('🏁 Test completed', 'step');
  }
}

// Run the test
testCaptureFeature().catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});