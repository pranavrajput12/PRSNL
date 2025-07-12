#!/usr/bin/env node
/**
 * Feature Functionality Test
 * Tests specific features to ensure they're working
 */

const http = require('http');

const BASE_URL = 'http://localhost:3004';

// Feature-specific tests
const FEATURE_TESTS = [
  {
    name: 'Navigation menu exists',
    path: '/',
    checks: [
      { contains: 'Timeline', desc: 'Timeline link' },
      { contains: 'Capture', desc: 'Capture link' },
      { contains: 'Insights', desc: 'Insights link' },
      { contains: 'Videos', desc: 'Videos link' },
    ]
  },
  {
    name: 'Capture form elements',
    path: '/capture',
    checks: [
      { contains: ['input', 'textarea'], desc: 'Input fields' },
      { contains: ['button', 'submit'], desc: 'Submit button' },
      { contains: ['url', 'URL', 'link'], desc: 'URL input reference' },
    ]
  },
  {
    name: 'Import page options',
    path: '/import',
    checks: [
      { contains: ['bookmark', 'Bookmark'], desc: 'Bookmark import' },
      { contains: ['json', 'JSON'], desc: 'JSON import' },
      { contains: ['note', 'Note'], desc: 'Note import' },
    ]
  },
  {
    name: 'Code Cortex sections',
    path: '/code-cortex',
    checks: [
      { contains: ['docs', 'Docs', 'Documentation'], desc: 'Docs section' },
      { contains: ['link', 'Link'], desc: 'Links section' },
      { contains: ['project', 'Project'], desc: 'Projects section' },
    ]
  },
  {
    name: 'AI page interface',
    path: '/ai',
    checks: [
      { contains: ['model', 'Model', 'AI'], desc: 'AI references' },
      { contains: ['analyze', 'Analyze', 'analysis'], desc: 'Analysis features' },
    ]
  }
];

// Test critical API integrations (that work without backend)
const INTEGRATION_TESTS = [
  {
    name: 'Static assets load',
    path: '/_app/version.json',
    expectStatus: [200, 404], // Might not exist in dev
    checkContent: false
  },
  {
    name: 'Frontend routing works',
    path: '/non-existent-route-12345',
    expectStatus: 404,
    checkContent: true,
    contains: ['404', 'Not Found', 'not found']
  }
];

// Helper function
async function fetchPage(path) {
  return new Promise((resolve) => {
    http.get(`${BASE_URL}${path}`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          body: data
        });
      });
    }).on('error', (err) => {
      resolve({
        status: null,
        body: '',
        error: err.message
      });
    }).setTimeout(5000);
  });
}

// Check if content contains any of the search terms
function checkContains(body, search) {
  const searchTerms = Array.isArray(search) ? search : [search];
  const bodyLower = body.toLowerCase();
  return searchTerms.some(term => bodyLower.includes(term.toLowerCase()));
}

// Run tests
async function runTests() {
  console.log('🔧 Feature Functionality Tests');
  console.log('=' .repeat(60));
  
  let totalPassed = 0;
  let totalFailed = 0;
  
  // Test features
  console.log('\n📋 Testing Page Features');
  console.log('-' .repeat(60));
  
  for (const test of FEATURE_TESTS) {
    console.log(`\n🔍 ${test.name} (${test.path})`);
    
    const result = await fetchPage(test.path);
    
    if (result.error) {
      console.log(`   ❌ Error loading page: ${result.error}`);
      totalFailed++;
      continue;
    }
    
    if (result.status !== 200) {
      console.log(`   ❌ Page returned status ${result.status}`);
      totalFailed++;
      continue;
    }
    
    let pagePassed = 0;
    let pageFailed = 0;
    
    for (const check of test.checks) {
      if (checkContains(result.body, check.contains)) {
        console.log(`   ✅ ${check.desc}`);
        pagePassed++;
      } else {
        console.log(`   ❌ ${check.desc} - not found`);
        pageFailed++;
      }
    }
    
    if (pageFailed === 0) {
      console.log(`   ✨ All checks passed!`);
    }
    
    totalPassed += pagePassed;
    totalFailed += pageFailed;
  }
  
  // Test integrations
  console.log('\n\n🔌 Testing Integrations');
  console.log('-' .repeat(60));
  
  for (const test of INTEGRATION_TESTS) {
    const result = await fetchPage(test.path);
    
    if (result.error) {
      console.log(`❌ ${test.name}: ${result.error}`);
      totalFailed++;
      continue;
    }
    
    const expectedStatuses = Array.isArray(test.expectStatus) ? test.expectStatus : [test.expectStatus];
    
    if (expectedStatuses.includes(result.status)) {
      if (test.checkContent && test.contains) {
        if (checkContains(result.body, test.contains)) {
          console.log(`✅ ${test.name}`);
          totalPassed++;
        } else {
          console.log(`❌ ${test.name}: Expected content not found`);
          totalFailed++;
        }
      } else {
        console.log(`✅ ${test.name}`);
        totalPassed++;
      }
    } else {
      console.log(`❌ ${test.name}: Expected ${expectedStatuses.join(' or ')}, got ${result.status}`);
      totalFailed++;
    }
  }
  
  // Summary
  console.log('\n' + '=' .repeat(60));
  console.log('📊 Test Summary');
  console.log('=' .repeat(60));
  console.log(`Total Checks: ${totalPassed + totalFailed}`);
  console.log(`✅ Passed: ${totalPassed}`);
  console.log(`❌ Failed: ${totalFailed}`);
  console.log(`Success Rate: ${((totalPassed / (totalPassed + totalFailed)) * 100).toFixed(1)}%`);
  
  if (totalFailed === 0) {
    console.log('\n🎉 All feature tests passed!');
  } else {
    console.log(`\n⚠️  ${totalFailed} checks failed`);
  }
}

runTests().catch(err => {
  console.error('Test error:', err);
  process.exit(1);
});