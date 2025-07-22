import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

// Configuration
const BASE_URL = 'http://localhost:3000';
const TEST_USER = {
  email: process.env.TEST_EMAIL || 'test@example.com',
  password: process.env.TEST_PASSWORD || 'testpassword123'
};

// Test results directory
const RESULTS_DIR = './test-results';
if (!fs.existsSync(RESULTS_DIR)) {
  fs.mkdirSync(RESULTS_DIR, { recursive: true });
}

// Test results
const testResults = {
  total: 0,
  passed: 0,
  failed: 0,
  details: []
};

// Helper function to log test results
function logTestResult(testName, passed, error = null) {
  testResults.total++;
  const result = { testName, passed, timestamp: new Date().toISOString() };
  
  if (passed) {
    testResults.passed++;
    console.log(`✅ ${testName}`);
  } else {
    testResults.failed++;
    console.error(`❌ ${testName}`, error || '');
    result.error = error?.message || 'Test failed';
  }
  
  testResults.details.push(result);
  return passed;
}

// Save test results to a file
function saveTestResults() {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const filename = path.join(RESULTS_DIR, `test-results-${timestamp}.json`);
  fs.writeFileSync(filename, JSON.stringify(testResults, null, 2));
  console.log(`\n📊 Test results saved to: ${filename}`);
  
  // Print summary
  console.log('\n=== TEST SUMMARY ===');
  console.log(`Total: ${testResults.total}`);
  console.log(`✅ Passed: ${testResults.passed}`);
  console.log(`❌ Failed: ${testResults.failed}`);
  console.log('==================');
}

// Take a screenshot
async function takeScreenshot(page, name) {
  const screenshotPath = path.join(RESULTS_DIR, `${name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  return screenshotPath;
}

// Main test suite
async function runTests() {
  console.log('🚀 Starting PRSNL Puppeteer Test Suite');
  
  // Launch browser
  const browser = await puppeteer.launch({
    headless: false, // Set to true for CI/CD
    defaultViewport: { width: 1280, height: 800 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    // Test 1: Homepage Load
    await testHomepage(page);
    
    // Test 2: Authentication
    await testAuthentication(page);
    
    // Test 3: Protected Routes
    await testProtectedRoutes(page);
    
    // Test 4: Code Cortex
    await testCodeCortex(page);
    
    // Test 5: Chat
    await testChat(page);
    
    // Test 6: Profile & Settings
    await testProfileAndSettings(page);
    
  } catch (error) {
    console.error('❌ Test suite failed:', error);
    await takeScreenshot(page, 'test-failure');
    throw error;
  } finally {
    await browser.close();
    saveTestResults();
  }
}

// Test 1: Homepage
async function testHomepage(page) {
  const testName = 'Homepage Load';
  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: 30000 });
    await takeScreenshot(page, 'homepage');
    
    // Check for important elements
    const title = await page.title();
    if (!title.toLowerCase().includes('prsnl')) {
      throw new Error(`Unexpected page title: ${title}`);
    }
    
    logTestResult(testName, true);
  } catch (error) {
    logTestResult(testName, false, error);
  }
}

// Test 2: Authentication
async function testAuthentication(page) {
  const testName = 'User Authentication';
  try {
    // Navigate to login page
    await page.goto(`${BASE_URL}/auth/login`, { waitUntil: 'networkidle2' });
    
    // Fill login form
    await page.type('input[name="email"]', TEST_USER.email);
    await page.type('input[name="password"]', TEST_USER.password);
    await takeScreenshot(page, 'login-form-filled');
    
    // Submit form
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle2' }),
      page.click('button[type="submit"]')
    ]);
    
    // Verify login success (check for user menu or protected content)
    const userMenu = await page.$('[data-testid="user-menu"]');
    if (!userMenu) {
      throw new Error('Login failed - user menu not found');
    }
    
    logTestResult(testName, true);
  } catch (error) {
    logTestResult(testName, false, error);
  }
}

// Test 3: Protected Routes
async function testProtectedRoutes(page) {
  const protectedRoutes = [
    '/thoughts',
    '/timeline',
    '/code-cortex',
    '/chat',
    '/profile',
    '/settings'
  ];
  
  for (const route of protectedRoutes) {
    const testName = `Protected Route: ${route}`;
    try {
      await page.goto(`${BASE_URL}${route}`, { waitUntil: 'networkidle2' });
      
      // Check if we're not redirected to login page
      if (page.url().includes('/auth/login')) {
        throw new Error(`Unauthorized access to ${route}`);
      }
      
      // Check for page-specific content
      const pageTitle = await page.title();
      if (!pageTitle) {
        throw new Error(`Empty page title for ${route}`);
      }
      
      await takeScreenshot(page, `protected-${route.replace(/\//g, '-')}`);
      logTestResult(testName, true);
    } catch (error) {
      logTestResult(testName, false, error);
    }
  }
}

// Test 4: Code Cortex
async function testCodeCortex(page) {
  const testName = 'Code Cortex Features';
  try {
    // Navigate to Code Cortex
    await page.goto(`${BASE_URL}/code-cortex`, { waitUntil: 'networkidle2' });
    
    // Test repository listing
    const repoList = await page.$$('[data-testid="repo-list"]');
    if (repoList.length === 0) {
      throw new Error('No repositories found');
    }
    
    // Test repository interaction
    await page.click('[data-testid="repo-item-0"]');
    await page.waitForSelector('[data-testid="repo-details"]', { timeout: 5000 });
    
    // Test file explorer
    const fileExplorer = await page.$('[data-testid="file-explorer"]');
    if (!fileExplorer) {
      throw new Error('File explorer not found');
    }
    
    // Test code editor
    await page.click('[data-testid="file-item-0"]');
    await page.waitForSelector('.cm-editor', { timeout: 5000 });
    
    await takeScreenshot(page, 'code-cortex-editor');
    logTestResult(testName, true);
  } catch (error) {
    logTestResult(testName, false, error);
  }
}

// Test 5: Chat
async function testChat(page) {
  const testName = 'Chat Functionality';
  try {
    await page.goto(`${BASE_URL}/chat`, { waitUntil: 'networkidle2' });
    
    // Test new chat
    await page.click('[data-testid="new-chat-button"]');
    await page.waitForSelector('[data-testid="chat-input"]', { timeout: 5000 });
    
    // Send a message
    await page.type('[data-testid="chat-input"]', 'Hello, PRSNL!');
    await page.click('[data-testid="send-message-button"]');
    
    // Wait for response
    await page.waitForSelector('[data-testid="message-response"]', { timeout: 10000 });
    
    await takeScreenshot(page, 'chat-interaction');
    logTestResult(testName, true);
  } catch (error) {
    logTestResult(testName, false, error);
  }
}

// Test 6: Profile & Settings
async function testProfileAndSettings(page) {
  const testName = 'Profile & Settings';
  try {
    // Test profile page
    await page.goto(`${BASE_URL}/profile`, { waitUntil: 'networkidle2' });
    
    // Check profile info
    const profileName = await page.$eval('[data-testid="profile-name"]', el => el.textContent);
    if (!profileName) {
      throw new Error('Profile name not found');
    }
    
    // Test settings page
    await page.goto(`${BASE_URL}/settings`, { waitUntil: 'networkidle2' });
    
    // Check settings sections
    const settingsSections = await page.$$('[data-testid^="settings-section-"]');
    if (settingsSections.length === 0) {
      throw new Error('No settings sections found');
    }
    
    await takeScreenshot(page, 'settings-page');
    logTestResult(testName, true);
  } catch (error) {
    logTestResult(testName, false, error);
  }
}

// Run the test suite
runTests()
  .then(() => console.log('\n🎉 Test suite completed successfully!'))
  .catch((error) => console.error('\n❌ Test suite failed:', error))
  .finally(() => process.exit(testResults.failed > 0 ? 1 : 0));
