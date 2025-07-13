#!/usr/bin/env node
/**
 * Comprehensive Frontend Testing Suite
 * Tests all aspects of the frontend while backend is starting
 */

const http = require('http');
const https = require('https');
const url = require('url');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:3004';

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  gray: '\x1b[90m',
};

// Test categories
const TESTS = {
  navigation: [
    { name: 'Main navigation loads', path: '/', selector: 'nav' },
    { name: 'Sidebar navigation exists', path: '/', selector: '.sidebar, [data-sidebar]' },
  ],

  features: [
    {
      name: 'Capture form exists',
      path: '/capture',
      selector: 'form, .capture-form, [data-capture]',
    },
    { name: 'Timeline has content area', path: '/timeline', selector: '.timeline, .content, main' },
    { name: 'Videos page structure', path: '/videos', selector: '.videos, .content, main' },
    { name: 'Insights dashboard', path: '/insights', selector: '.insights, .content, main' },
    { name: 'Chat interface', path: '/chat', selector: '.chat, .content, main' },
    { name: 'Import page forms', path: '/import', selector: '.import, form, .content' },
    { name: 'AI page interface', path: '/ai', selector: '.ai, .content, main' },
  ],

  routing: [
    { name: 'Code Cortex main', path: '/code-cortex', expectedStatus: 200 },
    { name: 'Code Cortex docs', path: '/code-cortex/docs', expectedStatus: 200 },
    { name: 'Code Cortex links', path: '/code-cortex/links', expectedStatus: 200 },
    { name: 'Code Cortex projects', path: '/code-cortex/projects', expectedStatus: 200 },
    { name: 'Code Cortex synapses', path: '/code-cortex/synapses', expectedStatus: 200 },
  ],

  assets: [
    { name: 'CSS loads correctly', path: '/', checkAsset: true, assetPattern: /\.css$/ },
    { name: 'JavaScript loads', path: '/', checkAsset: true, assetPattern: /\.js$/ },
  ],

  errors: [
    { name: '404 page handles properly', path: '/totally-fake-route-12345', expectedStatus: 404 },
    { name: 'Invalid item ID', path: '/items/fake-id-12345', expectedStatus: [404, 500] },
  ],
};

// Test file structure
const FILE_TESTS = [
  { path: 'src/routes/+layout.svelte', description: 'Main layout exists' },
  { path: 'src/routes/+page.svelte', description: 'Homepage exists' },
  { path: 'src/app.css', description: 'Global styles exist' },
  { path: 'src/lib/api.ts', description: 'API client exists' },
  { path: 'package.json', description: 'Package.json exists' },
  { path: 'svelte.config.js', description: 'Svelte config exists' },
  { path: 'vite.config.ts', description: 'Vite config exists' },
];

// Helper to make HTTP request
async function makeRequest(testUrl) {
  return new Promise((resolve) => {
    const parsedUrl = url.parse(testUrl);
    const client = parsedUrl.protocol === 'https:' ? https : http;

    const req = client.get(testUrl, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: data,
          error: null,
        });
      });
    });

    req.on('error', (error) => {
      resolve({
        status: null,
        headers: {},
        body: '',
        error: error.message,
      });
    });

    req.setTimeout(10000, () => {
      req.destroy();
      resolve({
        status: null,
        headers: {},
        body: '',
        error: 'Request timeout',
      });
    });
  });
}

// Test page content
async function testPageContent(test) {
  const testUrl = `${BASE_URL}${test.path}`;
  const response = await makeRequest(testUrl);

  if (response.error) {
    return { success: false, message: response.error };
  }

  // Check status if specified
  if (test.expectedStatus) {
    const expected = Array.isArray(test.expectedStatus)
      ? test.expectedStatus
      : [test.expectedStatus];
    if (!expected.includes(response.status)) {
      return {
        success: false,
        message: `Expected ${expected.join(' or ')}, got ${response.status}`,
      };
    }
  } else if (response.status !== 200) {
    return { success: false, message: `HTTP ${response.status}` };
  }

  // Check for selector if specified
  if (test.selector) {
    const selectors = test.selector.split(', ');
    const found = selectors.some((sel) => response.body.includes(sel));
    if (!found) {
      return { success: false, message: `Selector "${test.selector}" not found` };
    }
  }

  // Check for assets
  if (test.checkAsset) {
    const hasAsset = test.assetPattern.test(response.body);
    if (!hasAsset) {
      return { success: false, message: 'Required assets not found' };
    }
  }

  return { success: true };
}

// Test file existence
function testFileExists(fileTest) {
  const fullPath = path.join(process.cwd(), fileTest.path);
  try {
    fs.accessSync(fullPath, fs.constants.F_OK);
    return { success: true };
  } catch (error) {
    return { success: false, message: 'File not found' };
  }
}

// Test JavaScript console errors
async function testConsoleErrors() {
  console.log(`\n${colors.blue}🔍 Checking for JavaScript errors${colors.reset}`);
  console.log(`${colors.gray}${'─'.repeat(50)}${colors.reset}\n`);

  // This would require a headless browser; for now, we'll check if pages load without throwing
  const criticalPages = ['/', '/capture', '/timeline', '/insights'];
  let passed = 0;
  let failed = 0;

  for (const pagePath of criticalPages) {
    const response = await makeRequest(`${BASE_URL}${pagePath}`);

    if (
      response.status === 200 &&
      !response.body.includes('Error:') &&
      !response.body.includes('error')
    ) {
      console.log(`${colors.green}✅ ${pagePath} - No obvious errors${colors.reset}`);
      passed++;
    } else {
      console.log(`${colors.red}❌ ${pagePath} - Potential errors detected${colors.reset}`);
      failed++;
    }
  }

  return { passed, failed };
}

// Main test runner
async function runTests() {
  console.log(`${colors.blue}🧪 Comprehensive Frontend Testing${colors.reset}`);
  console.log(`${colors.gray}${'='.repeat(50)}${colors.reset}\n`);

  // Check if frontend is running
  const healthCheck = await makeRequest(BASE_URL);
  if (healthCheck.error) {
    console.log(`${colors.red}❌ Frontend not accessible on ${BASE_URL}${colors.reset}`);
    return;
  }

  console.log(`${colors.green}✅ Frontend is running${colors.reset}\n`);

  let totalPassed = 0;
  let totalFailed = 0;

  // Test file structure
  console.log(`${colors.blue}📁 Testing File Structure${colors.reset}`);
  console.log(`${colors.gray}${'─'.repeat(50)}${colors.reset}\n`);

  for (const fileTest of FILE_TESTS) {
    const result = testFileExists(fileTest);
    if (result.success) {
      console.log(`${colors.green}✅ ${fileTest.description}${colors.reset}`);
      totalPassed++;
    } else {
      console.log(`${colors.red}❌ ${fileTest.description}: ${result.message}${colors.reset}`);
      totalFailed++;
    }
  }

  // Test each category
  for (const [category, tests] of Object.entries(TESTS)) {
    console.log(
      `\n${colors.blue}🔍 Testing ${category.charAt(0).toUpperCase() + category.slice(1)}${colors.reset}`
    );
    console.log(`${colors.gray}${'─'.repeat(50)}${colors.reset}\n`);

    for (const test of tests) {
      const result = await testPageContent(test);

      if (result.success) {
        console.log(`${colors.green}✅ ${test.name}${colors.reset}`);
        totalPassed++;
      } else {
        console.log(`${colors.red}❌ ${test.name}: ${result.message}${colors.reset}`);
        totalFailed++;
      }
    }
  }

  // Test for console errors
  const errorResults = await testConsoleErrors();
  totalPassed += errorResults.passed;
  totalFailed += errorResults.failed;

  // Summary
  console.log(`\n${colors.blue}📊 Test Summary${colors.reset}`);
  console.log(`${colors.gray}${'='.repeat(50)}${colors.reset}\n`);

  console.log(`Total Tests: ${totalPassed + totalFailed}`);
  console.log(`${colors.green}Passed: ${totalPassed}${colors.reset}`);
  console.log(`${colors.red}Failed: ${totalFailed}${colors.reset}`);

  const successRate =
    totalPassed + totalFailed > 0
      ? ((totalPassed / (totalPassed + totalFailed)) * 100).toFixed(1)
      : 0;

  console.log(`\nSuccess Rate: ${successRate}%`);

  if (totalFailed === 0) {
    console.log(`\n${colors.green}✅ All frontend tests passed!${colors.reset}`);
    console.log(`${colors.green}   Frontend is fully functional${colors.reset}`);
  } else {
    console.log(`\n${colors.yellow}⚠️  ${totalFailed} tests failed${colors.reset}`);
  }

  process.exit(totalFailed > 0 ? 1 : 0);
}

// Run tests
runTests().catch((error) => {
  console.error(`${colors.red}Test suite error: ${error.message}${colors.reset}`);
  process.exit(2);
});
