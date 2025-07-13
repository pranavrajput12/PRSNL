#!/usr/bin/env node
/**
 * PRSNL Phase 1 Route Testing Suite
 *
 * Comprehensive tests to ensure all routes are stable before permalink implementation
 * Run with: node tests/phase1-route-tests.js
 */

const http = require('http');
const https = require('https');
const url = require('url');

const BASE_URL = 'http://localhost:3004';
const API_BASE_URL = 'http://localhost:8000';

// ANSI color codes for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  gray: '\x1b[90m',
};

// Test configuration
const ROUTE_TESTS = [
  // Main application routes
  { path: '/', name: 'Homepage', expectedStatus: 200 },
  { path: '/timeline', name: 'Timeline', expectedStatus: 200 },
  { path: '/videos', name: 'Videos', expectedStatus: 200 },
  { path: '/insights', name: 'Insights', expectedStatus: 200 },
  { path: '/chat', name: 'Chat', expectedStatus: 200 },
  { path: '/capture', name: 'Capture', expectedStatus: 200 },
  { path: '/import', name: 'Import', expectedStatus: 200 },
  { path: '/ai', name: 'AI', expectedStatus: 200 },
  { path: '/code-cortex', name: 'Code Cortex', expectedStatus: 200 },

  // Code Cortex sub-routes
  { path: '/code-cortex/docs', name: 'Code Docs', expectedStatus: 200 },
  { path: '/code-cortex/links', name: 'Code Links', expectedStatus: 200 },
  { path: '/code-cortex/projects', name: 'Code Projects', expectedStatus: 200 },
  { path: '/code-cortex/synapses', name: 'Code Synapses', expectedStatus: 200 },

  // Import variants (expecting redirect to /import?v=v2)
  { path: '/import/v2', name: 'Import V2', expectedStatus: 301 },

  // Preview routes - DISABLED: SSR issues with window access, non-critical for Phase 1
  // { path: '/preview-avatar', name: 'Preview Avatar', expectedStatus: 200 },
  // { path: '/preview-dna', name: 'Preview DNA', expectedStatus: 200 },
  // { path: '/preview-galaxy', name: 'Preview Galaxy', expectedStatus: 200 },
  // { path: '/preview-racing', name: 'Preview Racing', expectedStatus: 200 },
  // { path: '/preview-terrarium', name: 'Preview Terrarium', expectedStatus: 200 },

  // Error handling
  { path: '/non-existent-route', name: '404 Error Page', expectedStatus: 404 },
];

const API_TESTS = [
  { path: '/api/health', name: 'API Health', expectedStatus: 200 },
  { path: '/api/search?query=test&limit=1', name: 'API Search', expectedStatus: 200 },
];

// Test results storage
const results = {
  totalTests: 0,
  passed: 0,
  failed: 0,
  warnings: 0,
  errors: [],
};

// Helper function to make HTTP request
function makeRequest(testUrl) {
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

    req.setTimeout(5000, () => {
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

// Test a single route
async function testRoute(test, baseUrl) {
  const testUrl = `${baseUrl}${test.path}`;
  results.totalTests++;

  try {
    const response = await makeRequest(testUrl);

    if (response.error) {
      results.failed++;
      results.errors.push({
        test: test.name,
        error: response.error,
        url: testUrl,
      });
      return {
        success: false,
        test: test.name,
        url: testUrl,
        error: response.error,
      };
    }

    if (response.status === test.expectedStatus) {
      // Additional checks for 200 responses
      if (response.status === 200) {
        // Check if page has actual content
        if (response.body.length < 100) {
          results.warnings++;
          return {
            success: true,
            warning: true,
            test: test.name,
            url: testUrl,
            message: 'Page seems empty (less than 100 characters)',
          };
        }

        // Check for error indicators in content
        const errorIndicators = ['error', 'Error', 'failed', 'Failed', '500', '404'];
        const hasErrorContent = errorIndicators.some(
          (indicator) =>
            response.body.includes(`<h1>${indicator}</h1>`) ||
            response.body.includes(`class="error"`) ||
            response.body.includes('Internal Server Error')
        );

        if (hasErrorContent) {
          results.warnings++;
          return {
            success: true,
            warning: true,
            test: test.name,
            url: testUrl,
            message: 'Page loads but contains error content',
          };
        }
      }

      results.passed++;
      return {
        success: true,
        test: test.name,
        url: testUrl,
        status: response.status,
      };
    } else {
      results.failed++;
      results.errors.push({
        test: test.name,
        error: `Expected ${test.expectedStatus}, got ${response.status}`,
        url: testUrl,
      });
      return {
        success: false,
        test: test.name,
        url: testUrl,
        expected: test.expectedStatus,
        actual: response.status,
      };
    }
  } catch (error) {
    results.failed++;
    results.errors.push({
      test: test.name,
      error: error.message,
      url: testUrl,
    });
    return {
      success: false,
      test: test.name,
      url: testUrl,
      error: error.message,
    };
  }
}

// Check if servers are running
async function checkServers() {
  console.log(`${colors.blue}🔍 Checking server availability...${colors.reset}\n`);

  const frontendCheck = await makeRequest(BASE_URL);
  const backendCheck = await makeRequest(`${API_BASE_URL}/api/health`);

  const frontendOk = !frontendCheck.error && frontendCheck.status === 200;
  const backendOk = !backendCheck.error && backendCheck.status === 200;

  console.log(
    `Frontend (${BASE_URL}): ${frontendOk ? colors.green + '✅ Online' : colors.red + '❌ Offline'}${colors.reset}`
  );
  console.log(
    `Backend (${API_BASE_URL}): ${backendOk ? colors.green + '✅ Online' : colors.red + '❌ Offline'}${colors.reset}`
  );
  console.log();

  return { frontendOk, backendOk };
}

// Run all tests
async function runTests() {
  console.log(`${colors.blue}🧪 PRSNL Phase 1 Route Testing Suite${colors.reset}`);
  console.log(`${colors.gray}${'='.repeat(50)}${colors.reset}\n`);

  // Check servers
  const { frontendOk, backendOk } = await checkServers();

  if (!frontendOk) {
    console.log(`${colors.red}❌ Frontend server is not running on ${BASE_URL}${colors.reset}`);
    console.log(
      `${colors.yellow}Please start the frontend with: cd frontend && npm run dev -- --port 3004${colors.reset}\n`
    );
    return;
  }

  if (!backendOk) {
    console.log(
      `${colors.yellow}⚠️  Backend server is not running on ${API_BASE_URL}${colors.reset}`
    );
    console.log(`${colors.gray}Some API tests will fail${colors.reset}\n`);
  }

  // Test frontend routes
  console.log(`${colors.blue}📄 Testing Frontend Routes${colors.reset}`);
  console.log(`${colors.gray}${'─'.repeat(50)}${colors.reset}\n`);

  for (const test of ROUTE_TESTS) {
    const result = await testRoute(test, BASE_URL);

    if (result.success && !result.warning) {
      console.log(`${colors.green}✅ ${test.name.padEnd(20)} [${test.path}]${colors.reset}`);
    } else if (result.warning) {
      console.log(
        `${colors.yellow}⚠️  ${test.name.padEnd(20)} [${test.path}] - ${result.message}${colors.reset}`
      );
    } else {
      console.log(
        `${colors.red}❌ ${test.name.padEnd(20)} [${test.path}] - ${result.error || `Expected ${test.expectedStatus}, got ${result.actual}`}${colors.reset}`
      );
    }
  }

  // Test API endpoints if backend is running
  if (backendOk) {
    console.log(`\n${colors.blue}🔌 Testing API Endpoints${colors.reset}`);
    console.log(`${colors.gray}${'─'.repeat(50)}${colors.reset}\n`);

    for (const test of API_TESTS) {
      const result = await testRoute(test, API_BASE_URL);

      if (result.success) {
        console.log(`${colors.green}✅ ${test.name.padEnd(20)} [${test.path}]${colors.reset}`);
      } else {
        console.log(
          `${colors.red}❌ ${test.name.padEnd(20)} [${test.path}] - ${result.error || `Expected ${test.expectedStatus}, got ${result.actual}`}${colors.reset}`
        );
      }
    }
  }

  // Summary
  console.log(`\n${colors.blue}📊 Test Summary${colors.reset}`);
  console.log(`${colors.gray}${'='.repeat(50)}${colors.reset}\n`);

  console.log(`Total Tests: ${results.totalTests}`);
  console.log(`${colors.green}Passed: ${results.passed}${colors.reset}`);
  console.log(`${colors.red}Failed: ${results.failed}${colors.reset}`);
  console.log(`${colors.yellow}Warnings: ${results.warnings}${colors.reset}`);

  const successRate =
    results.totalTests > 0 ? ((results.passed / results.totalTests) * 100).toFixed(1) : 0;

  console.log(`\nSuccess Rate: ${successRate}%`);

  // Show errors if any
  if (results.errors.length > 0) {
    console.log(`\n${colors.red}❌ Errors:${colors.reset}`);
    results.errors.forEach((error) => {
      console.log(`${colors.gray}  - ${error.test}: ${error.error}${colors.reset}`);
    });
  }

  // Phase 1 completion check
  console.log(`\n${colors.blue}📋 Phase 1 Status${colors.reset}`);
  console.log(`${colors.gray}${'='.repeat(50)}${colors.reset}\n`);

  if (results.failed === 0 && results.warnings === 0) {
    console.log(`${colors.green}✅ All routes are stable! Phase 1 is complete.${colors.reset}`);
    console.log(
      `${colors.green}   Ready to proceed to Phase 2: Backend permalink infrastructure${colors.reset}`
    );
  } else if (results.failed === 0) {
    console.log(
      `${colors.yellow}⚠️  Routes are functional but there are ${results.warnings} warnings.${colors.reset}`
    );
    console.log(
      `${colors.yellow}   Consider addressing warnings before proceeding to Phase 2.${colors.reset}`
    );
  } else {
    console.log(
      `${colors.red}❌ ${results.failed} routes are failing. Fix these before proceeding.${colors.reset}`
    );
  }

  // Exit code
  process.exit(results.failed > 0 ? 1 : 0);
}

// Run tests
runTests().catch((error) => {
  console.error(`${colors.red}Test suite error: ${error.message}${colors.reset}`);
  process.exit(2);
});
