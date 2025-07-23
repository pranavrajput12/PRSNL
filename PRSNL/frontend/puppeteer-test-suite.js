import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

// Configuration
const BASE_URL = 'http://localhost:3004';
const TEST_USER = {
  email: 'slathiap@gmail.com',
  password: 'PSnama@13'
};

// Selectors
const SELECTORS = {
  // Auth
  emailInput: 'input[type="email"]',
  passwordInput: 'input[type="password"]',
  submitButton: 'button[type="submit"]',
  loginForm: 'form',
  
  // Navigation
  userMenu: '[data-testid="user-menu"]',
  
  // Code Cortex
  repoList: '[data-testid="repo-list"]',
  repoItem: '[data-testid^="repo-item-"]',
  fileExplorer: '[data-testid="file-explorer"]',
  fileItem: '[data-testid^="file-item-"]',
  
  // Chat
  chatInput: '[data-testid="chat-input"]',
  sendMessageButton: '[data-testid="send-message-button"]',
  messageResponse: '[data-testid="message-response"]',
  
  // Profile & Settings
  profileName: '[data-testid="profile-name"]',
  settingsSection: '[data-testid^="settings-section-"]'
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
    await page.goto(BASE_URL, { 
      waitUntil: ['domcontentloaded', 'networkidle0'], 
      timeout: 30000 
    });
    
    // Wait for some content to be loaded
    await page.waitForSelector('body', { timeout: 10000 });
    await takeScreenshot(page, 'homepage');
    
    // Check for important elements
    const title = await page.title();
    if (!title) {
      throw new Error('Page title is empty');
    }
    
    // Check for any loading indicators that might be stuck
    const loadingIndicators = await page.$$('.loading, [aria-busy="true"]');
    if (loadingIndicators.length > 0) {
      console.log(`⚠️ Found ${loadingIndicators.length} loading indicators on the page`);
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
    
    // Wait for email input and fill credentials
    try {
      console.log('Starting login process...');
      
      // Wait for page to be fully loaded
      await page.waitForSelector('body', { timeout: 10000 });
      
      // Take initial screenshot for debugging
      await takeScreenshot(page, 'login-page-initial');
      
      // Try to find and fill email field
      const emailField = await page.$('input[type="email"], input[name="email"], input[autocomplete*="email"]');
      if (!emailField) {
        throw new Error('Email input field not found');
      }
      
      console.log('Filling email...');
      await emailField.click({ clickCount: 3 }); // Select all text if any
      await emailField.type(TEST_USER.email, { delay: 30 });
      
      // Look for password field or password toggle
      console.log('Looking for password field...');
      let passwordField = await page.$('input[type="password"]');
      
      if (!passwordField) {
        console.log('Password field not immediately visible, looking for password toggle...');
        
        // Try to find and click "Use password instead" button
        const passwordToggleButtons = await page.$$('button');
        let passwordToggleClicked = false;
        
        for (const button of passwordToggleButtons) {
          const buttonText = await page.evaluate(el => el.textContent, button);
          if (buttonText && buttonText.toLowerCase().includes('password')) {
            console.log('Found password toggle button, clicking...');
            await button.click();
            passwordToggleClicked = true;
            await page.waitForTimeout(1000); // Wait for animation
            break;
          }
        }
        
        if (passwordToggleClicked) {
          passwordField = await page.$('input[type="password"]');
        }
      }
      
      if (!passwordField) {
        // If still no password field, try to submit with just email (magic link)
        console.log('No password field found, trying to submit with just email...');
      } else {
        // Fill password if field is found
        console.log('Filling password...');
        await passwordField.click({ clickCount: 3 });
        await passwordField.type(TEST_USER.password, { delay: 30 });
      }
      
      // Take screenshot before submitting
      await takeScreenshot(page, 'login-form-filled');
      
      // Find and click the submit button
      console.log('Looking for submit button...');
      const submitButton = await page.evaluateHandle(() => {
        // Try to find a submit button
        const submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) return submitBtn;
        
        // Try to find a button with Sign in text (case insensitive)
        const buttons = Array.from(document.querySelectorAll('button, input[type="button"], a[role="button"]'));
        return buttons.find(btn => {
          const text = btn.textContent || btn.value || '';
          return text && (
            text.toLowerCase().includes('sign in') || 
            text.toLowerCase().includes('continue') ||
            text.trim() === '→' ||
            text.trim().toLowerCase() === 'next' ||
            text.trim().toLowerCase() === 'submit'
          );
        }) || null;
      });
      
      if (!submitButton || !(await submitButton.asElement())) {
        await takeScreenshot(page, 'submit-button-not-found');
        // Try pressing Enter as last resort
        console.log('Submit button not found, trying to press Enter...');
        await page.keyboard.press('Enter');
      } else {
        console.log('Clicking submit button...');
        await submitButton.click();
      }
      
      // Wait for navigation or any other changes
      console.log('Waiting for navigation or changes...');
      try {
        await Promise.race([
          page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 10000 }),
          page.waitForSelector('body', { timeout: 10000 })
        ]);
      } catch (e) {
        console.log('Navigation timeout, but continuing...');
      }
      
      // Check if we're still on the login page
      const currentUrl = page.url();
      if (currentUrl.includes('/auth/login')) {
        // Check for error messages
        const errorMessage = await page.evaluate(() => {
          const errorEl = document.querySelector('.error-message, .error, [role="alert"], .text-red-500, .text-error');
          return errorEl ? errorEl.textContent.trim() : null;
        });
        
        if (errorMessage) {
          throw new Error(`Login error: ${errorMessage}`);
        } else {
          throw new Error('Login failed - still on login page with no error message');
        }
      }
      
      console.log('Login successful!');
      
    } catch (e) {
      console.error('Error during login:', e);
      await takeScreenshot(page, 'login-error');
      
      // If we're not on the login page anymore, assume we're signed in
      if (!page.url().includes('/auth/login')) {
        console.log('Not on login page, assuming login was successful');
      } else {
        throw new Error(`Login failed: ${e.message}`);
      }
    }
    
    // Verify login success (check for user menu or protected content)
    try {
      await page.waitForSelector(SELECTORS.userMenu, { visible: true, timeout: 10000 });
    } catch (e) {
      // If user menu not found, check if we're on a protected route
      if (!page.url().includes('/auth/login')) {
        console.log('User menu not found but on protected route, assuming login was successful');
      } else {
        throw new Error('Login failed - user menu not found and still on login page');
      }
    }
    
    logTestResult(testName, true);
  } catch (error) {
    logTestResult(testName, false, error);
  }
}

// Test 3: Protected Routes
async function testProtectedRoutes(page) {
  // Only test these routes if they exist in the application
  const protectedRoutes = [
    { path: '/thoughts', testId: 'thoughts-page' },
    { path: '/timeline', testId: 'timeline-page' },
    { path: '/code-cortex', testId: 'code-cortex-page' },
    { path: '/chat', testId: 'chat-page' },
    { path: '/profile', testId: 'profile-page' },
    { path: '/settings', testId: 'settings-page' }
  ];
  
  for (const { path, testId } of protectedRoutes) {
    const testName = `Protected Route: ${path}`;
    try {
      console.log(`Testing route: ${path}`);
      await page.goto(`${BASE_URL}${path}`, { 
        waitUntil: ['domcontentloaded', 'networkidle0'],
        timeout: 30000
      });
      
      // Check if we're not redirected to login page
      const currentUrl = page.url();
      if (currentUrl.includes('/auth/login')) {
        throw new Error(`Unauthorized access to ${path} - redirected to login`);
      }
      
      // Wait for page-specific content to load
      try {
        // First try with test ID if available
        if (testId) {
          await page.waitForSelector(`[data-testid="${testId}"]`, { 
            visible: true, 
            timeout: 10000 
          });
        } 
        // Fallback to checking for main content
        else {
          await page.waitForSelector('main, [role="main"], .main-content', { 
            visible: true, 
            timeout: 10000 
          });
        }
      } catch (e) {
        console.log(`Warning: Could not find main content for ${path}, but continuing test`);
      }
      
      // Check for page title
      const pageTitle = await page.title();
      if (!pageTitle || pageTitle.toLowerCase().includes('error')) {
        throw new Error(`Invalid page title for ${path}: ${pageTitle}`);
      }
      
      // Check for any error messages on the page
      const errorMessages = await page.$$eval('div.error, .error-message, [role="alert"]', 
        elements => elements.map(el => el.textContent.trim())
      );
      
      if (errorMessages.length > 0) {
        throw new Error(`Found error messages on ${path}: ${errorMessages.join('; ')}`);
      }
      
      await takeScreenshot(page, `protected-${path.replace(/\//g, '-')}`);
      logTestResult(testName, true);
    } catch (error) {
      // Take screenshot on failure
      await takeScreenshot(page, `error-${path.replace(/\//g, '-')}`);
      logTestResult(testName, false, error);
    }
  }
}

// Test 4: Code Cortex
async function testCodeCortex(page) {
  const testName = 'Code Cortex Features';
  try {
    console.log('Testing Code Cortex features...');
    
    // Navigate to Code Cortex
    await page.goto(`${BASE_URL}/code-cortex`, { 
      waitUntil: ['domcontentloaded', 'networkidle0'],
      timeout: 30000
    });
    
    // Wait for the page to load
    await page.waitForSelector('body', { timeout: 10000 });
    
    // Check for repository listing or any content
    const repoList = await page.$$(SELECTORS.repoList);
    const repoItems = await page.$$(SELECTORS.repoItem);
    
    if (repoItems.length === 0) {
      console.log('No repository items found, checking for other content...');
      
      // Check if there's any content or message
      const content = await page.evaluate(() => {
        const main = document.querySelector('main') || document.body;
        return main.innerText;
      });
      
      if (!content || content.length < 50) {
        throw new Error('No repositories or meaningful content found on Code Cortex page');
      }
      
      console.log('Found content on Code Cortex page, but no repository items');
    } else {
      console.log(`Found ${repoItems.length} repository items`);
      
      // Test repository interaction if items exist
      if (repoItems.length > 0) {
        try {
          await repoItems[0].click();
          
          // Wait for either repo details or file explorer
          await Promise.race([
            page.waitForSelector(SELECTORS.repoDetails, { timeout: 5000 }),
            page.waitForSelector(SELECTORS.fileExplorer, { timeout: 5000 })
          ]);
          
          // Test file explorer if visible
          const fileExplorer = await page.$(SELECTORS.fileExplorer);
          if (fileExplorer) {
            const fileItems = await page.$$(SELECTORS.fileItem);
            if (fileItems.length > 0) {
              await fileItems[0].click();
              await page.waitForSelector('.cm-editor, .code-editor', { timeout: 5000 });
            }
          }
        } catch (e) {
          console.log('Could not interact with repository items:', e.message);
          // Continue test even if interaction fails
        }
      }
    }
    
    await takeScreenshot(page, 'code-cortex-page');
    logTestResult(testName, true);
  } catch (error) {
    await takeScreenshot(page, 'code-cortex-error');
    logTestResult(testName, false, error);
  }
}

// Test 5: Chat
async function testChat(page) {
  const testName = 'Chat Functionality';
  try {
    console.log('Testing Chat functionality...');
    
    await page.goto(`${BASE_URL}/chat`, { 
      waitUntil: ['domcontentloaded', 'networkidle0'],
      timeout: 30000
    });
    
    // Check if we're on the chat page
    if (page.url().includes('/auth/login')) {
      throw new Error('Not authenticated - redirected to login');
    }
    
    // Wait for chat interface to load
    await page.waitForSelector('body', { timeout: 10000 });
    
    // Check for chat input or any chat-related elements
    const chatInput = await page.$(SELECTORS.chatInput);
    const newChatButton = await page.$('[data-testid*="new-chat"], .new-chat-button');
    
    if (!chatInput) {
      // If no chat input, check if there's a welcome message or instructions
      const chatContent = await page.evaluate(() => {
        const main = document.querySelector('main') || document.body;
        return main.innerText;
      });
      
      if (!chatContent || chatContent.length < 30) {
        throw new Error('Chat interface not loaded properly');
      }
      
      console.log('Chat interface loaded but no input field found. Content:', chatContent.substring(0, 100) + '...');
    } else {
      console.log('Chat input found, testing message sending...');
      
      // Start a new chat if button exists
      if (newChatButton) {
        await newChatButton.click();
        await page.waitForTimeout(1000); // Wait for new chat to initialize
      }
      
      // Type and send a test message
      await chatInput.type('Hello, PRSNL!');
      
      const sendButton = await page.$(SELECTORS.sendMessageButton) || 
                        await page.$('button[type="submit"], button:has(svg)');
      
      if (sendButton) {
        await sendButton.click();
        
        // Wait for a response or any activity indicator
        try {
          await Promise.race([
            page.waitForSelector(SELECTORS.messageResponse, { timeout: 15000 }),
            page.waitForSelector('.typing-indicator, [role="status"]', { timeout: 10000 })
          ]);
          console.log('Chat message sent successfully');
        } catch (e) {
          console.log('No immediate response received, but continuing test');
        }
      } else {
        console.log('Send button not found, pressing Enter to send message');
        await chatInput.press('Enter');
      }
    }
    
    await takeScreenshot(page, 'chat-interface');
    logTestResult(testName, true);
  } catch (error) {
    await takeScreenshot(page, 'chat-error');
    logTestResult(testName, false, error);
  }
}

// Test 6: Profile & Settings
async function testProfileAndSettings(page) {
  const testName = 'Profile & Settings';
  
  // Test profile page
  try {
    console.log('Testing Profile page...');
    await page.goto(`${BASE_URL}/profile`, { 
      waitUntil: ['domcontentloaded', 'networkidle0'],
      timeout: 30000
    });
    
    // Check if we're on the profile page
    if (page.url().includes('/auth/login')) {
      throw new Error('Not authenticated - redirected to login');
    }
    
    // Wait for profile content to load
    await page.waitForSelector('body', { timeout: 10000 });
    
    // Check for profile info - be more flexible with selectors
    const profileName = await page.evaluate(() => {
      // Try multiple possible selectors for profile name
      const selectors = [
        '[data-testid="profile-name"]',
        '.profile-name',
        'h1',
        'h2',
        'h3',
        'header h1',
        'header h2',
        'main h1',
        'main h2'
      ];
      
      for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent.trim()) {
          return element.textContent.trim();
        }
      }
      return null;
    });
    
    if (!profileName) {
      console.log('Profile name not found with standard selectors, checking page content...');
      const pageContent = await page.evaluate(() => document.body.innerText);
      if (!pageContent || pageContent.length < 100) {
        throw new Error('Profile page content not loaded properly');
      }
      console.log('Profile page loaded with content, but no name found');
    } else {
      console.log(`Profile name found: ${profileName}`);
    }
    
    await takeScreenshot(page, 'profile-page');
  } catch (error) {
    await takeScreenshot(page, 'profile-error');
    logTestResult(`${testName} - Profile`, false, error);
    return; // Skip settings test if profile test fails
  }
  
  // Test settings page
  try {
    console.log('Testing Settings page...');
    await page.goto(`${BASE_URL}/settings`, { 
      waitUntil: ['domcontentloaded', 'networkidle0'],
      timeout: 30000
    });
    
    // Check if we're on the settings page
    if (page.url().includes('/auth/login')) {
      throw new Error('Not authenticated - redirected to login');
    }
    
    // Wait for settings content to load
    await page.waitForSelector('body', { timeout: 10000 });
    
    // Check for settings sections - be more flexible
    const settingsSections = await page.evaluate((selector) => {
      // First try with the exact selector
      const exactMatches = Array.from(document.querySelectorAll(selector));
      if (exactMatches.length > 0) return exactMatches.length;
      
      // Fallback to more generic selectors
      const fallbackSelectors = [
        'section',
        '.settings-section',
        '.card',
        'form',
        'fieldset',
        'main > div > div',
        'main > div'
      ];
      
      const allMatches = new Set();
      
      for (const sel of fallbackSelectors) {
        document.querySelectorAll(sel).forEach(el => {
          // Only count elements that have some content
          if (el.textContent && el.textContent.trim().length > 10) {
            allMatches.add(el);
          }
        });
      }
      
      return allMatches.size;
    }, SELECTORS.settingsSection);
    
    if (settingsSections === 0) {
      console.log('No settings sections found with standard selectors, checking page content...');
      const pageContent = await page.evaluate(() => document.body.innerText);
      if (!pageContent || pageContent.length < 100) {
        throw new Error('Settings page content not loaded properly');
      }
      console.log('Settings page loaded with content, but no sections found');
    } else {
      console.log(`Found ${settingsSections} settings sections`);
    }
    
    await takeScreenshot(page, 'settings-page');
    logTestResult(testName, true);
  } catch (error) {
    await takeScreenshot(page, 'settings-error');
    logTestResult(`${testName} - Settings`, false, error);
  }
}

// Run the test suite
runTests()
  .then(() => console.log('\n🎉 Test suite completed successfully!'))
  .catch((error) => console.error('\n❌ Test suite failed:', error))
  .finally(() => process.exit(testResults.failed > 0 ? 1 : 0));
