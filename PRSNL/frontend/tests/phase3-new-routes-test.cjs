#!/usr/bin/env node
/**
 * Phase 3 Test - Verify new permalink routes work alongside existing routes
 */

const http = require('http');

const BASE_URL = 'http://localhost:3004';

// Test both old and new routes
const ROUTE_TESTS = [
  // Category routes (new)
  { path: '/c/dev', name: 'Category: Development', expectStatus: 200 },
  { path: '/c/learn', name: 'Category: Learning', expectStatus: 200 },
  { path: '/c/media', name: 'Category: Media', expectStatus: 200 },
  { path: '/c/ideas', name: 'Category: Ideas', expectStatus: 200 },

  // Tool routes (new)
  { path: '/p/timeline', name: 'Tool: Timeline', expectStatus: 200 },
  { path: '/p/insights', name: 'Tool: Insights', expectStatus: 200 },
  { path: '/p/chat', name: 'Tool: Chat', expectStatus: 200 },

  // Static pages (new)
  { path: '/s/docs', name: 'Static: Docs', expectStatus: 200 },
  { path: '/s/about', name: 'Static: About', expectStatus: 200 },
  { path: '/s/settings', name: 'Static: Settings', expectStatus: 200 },

  // Original routes (should still work)
  { path: '/', name: 'Homepage', expectStatus: 200 },
  { path: '/capture', name: 'Capture', expectStatus: 200 },
  { path: '/timeline', name: 'Timeline (original)', expectStatus: 200 },
  { path: '/videos', name: 'Videos', expectStatus: 200 },
  { path: '/insights', name: 'Insights (original)', expectStatus: 200 },
  { path: '/chat', name: 'Chat (original)', expectStatus: 200 },
  { path: '/code-cortex', name: 'Code Cortex', expectStatus: 200 },
  { path: '/import', name: 'Import', expectStatus: 200 },
  { path: '/docs', name: 'Docs (original)', expectStatus: 200 },
  { path: '/settings', name: 'Settings (original)', expectStatus: 200 },
];

// Category content routes (with slugs)
// Note: 404 is expected for non-existent content, which is correct behavior
const CONTENT_ROUTES = [
  { path: '/c/dev/test-slug', name: 'Dev content with slug', expectStatus: [200, 404] },
  { path: '/c/learn/tutorial-example', name: 'Learn content with slug', expectStatus: [200, 404] },
  { path: '/c/media/video-demo', name: 'Media content with slug', expectStatus: [200, 404] },
  { path: '/c/ideas/note-example', name: 'Ideas content with slug', expectStatus: [200, 404] },
];

async function fetchRoute(path) {
  return new Promise((resolve) => {
    http
      .get(`${BASE_URL}${path}`, (res) => {
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => {
          resolve({
            status: res.statusCode,
            path,
            hasContent: data.length > 0,
            contentSnippet: data.substring(0, 200),
          });
        });
      })
      .on('error', (err) => {
        resolve({
          status: null,
          path,
          error: err.message,
        });
      })
      .setTimeout(5000);
  });
}

async function runTests() {
  console.log('🚀 Phase 3: Testing New Permalink Routes');
  console.log('='.repeat(60));
  console.log();

  let passed = 0;
  let failed = 0;

  // Test main routes
  console.log('📋 Testing Main Routes (Old + New)');
  console.log('-'.repeat(60));

  for (const test of ROUTE_TESTS) {
    const result = await fetchRoute(test.path);

    if (result.error) {
      console.log(`❌ ${test.name} (${test.path}): ${result.error}`);
      failed++;
    } else if (result.status === test.expectStatus) {
      console.log(`✅ ${test.name} (${test.path}): ${result.status}`);
      passed++;
    } else {
      console.log(
        `❌ ${test.name} (${test.path}): Expected ${test.expectStatus}, got ${result.status}`
      );
      failed++;
    }
  }

  // Test content routes
  console.log('\n📄 Testing Content Routes (Category/Slug)');
  console.log('-'.repeat(60));

  for (const test of CONTENT_ROUTES) {
    const result = await fetchRoute(test.path);
    const expectedStatuses = Array.isArray(test.expectStatus)
      ? test.expectStatus
      : [test.expectStatus];

    if (result.error) {
      console.log(`❌ ${test.name} (${test.path}): ${result.error}`);
      failed++;
    } else if (expectedStatuses.includes(result.status)) {
      console.log(`✅ ${test.name} (${test.path}): ${result.status}`);
      passed++;
    } else {
      console.log(
        `❌ ${test.name} (${test.path}): Expected ${expectedStatuses.join(' or ')}, got ${result.status}`
      );
      failed++;
    }
  }

  // Test route coexistence
  console.log('\n🔄 Testing Route Coexistence');
  console.log('-'.repeat(60));

  const coexistenceTests = [
    { old: '/timeline', new: '/p/timeline', name: 'Timeline' },
    { old: '/insights', new: '/p/insights', name: 'Insights' },
    { old: '/chat', new: '/p/chat', name: 'Chat' },
    { old: '/docs', new: '/s/docs', name: 'Docs' },
  ];

  for (const test of coexistenceTests) {
    const [oldResult, newResult] = await Promise.all([fetchRoute(test.old), fetchRoute(test.new)]);

    if (oldResult.status === 200 && newResult.status === 200) {
      console.log(`✅ ${test.name}: Both routes working (old: ${test.old}, new: ${test.new})`);
      passed += 2;
    } else {
      console.log(
        `❌ ${test.name}: Route issue - Old: ${oldResult.status}, New: ${newResult.status}`
      );
      failed += 2;
    }
  }

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 Test Summary');
  console.log('='.repeat(60));
  console.log(`Total Tests: ${passed + failed}`);
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

  if (failed === 0) {
    console.log('\n🎉 Phase 3 Complete! All routes working correctly.');
    console.log('✨ New permalink routes are active alongside existing routes.');
  } else {
    console.log(`\n⚠️  ${failed} tests failed. Please check the routes.`);
  }

  process.exit(failed === 0 ? 0 : 1);
}

runTests().catch((err) => {
  console.error('Test error:', err);
  process.exit(1);
});
