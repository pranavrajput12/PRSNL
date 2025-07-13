#!/usr/bin/env node
/**
 * Visual Page Test - Extracts key content from pages to verify rendering
 */

const http = require('http');
const url = require('url');

const BASE_URL = 'http://localhost:3004';

// Pages to test
const PAGES = [
  { path: '/', name: 'Homepage' },
  { path: '/capture', name: 'Capture' },
  { path: '/timeline', name: 'Timeline' },
  { path: '/videos', name: 'Videos' },
  { path: '/insights', name: 'Insights' },
  { path: '/chat', name: 'Chat' },
];

// Extract visible text from HTML
function extractVisibleText(html) {
  // Remove script and style tags
  let text = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  text = text.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');

  // Extract text from specific elements
  const h1Match = text.match(/<h1[^>]*>([^<]+)<\/h1>/);
  const h2Matches = text.match(/<h2[^>]*>([^<]+)<\/h2>/g) || [];
  const pMatches = text.match(/<p[^>]*>([^<]+)<\/p>/g) || [];

  return {
    title: h1Match ? h1Match[1].trim() : 'No title found',
    headings: h2Matches.slice(0, 3).map((h) => h.replace(/<[^>]+>/g, '').trim()),
    paragraphs: pMatches.slice(0, 3).map((p) => p.replace(/<[^>]+>/g, '').trim()),
    hasForm: html.includes('<form'),
    hasNavigation: html.includes('<nav') || html.includes('nav-'),
    hasButtons: html.includes('<button') || html.includes('btn-'),
  };
}

// Make request
async function fetchPage(pagePath) {
  return new Promise((resolve) => {
    const testUrl = `${BASE_URL}${pagePath}`;
    const parsedUrl = url.parse(testUrl);

    const req = http.get(testUrl, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          html: data,
        });
      });
    });

    req.on('error', (error) => {
      resolve({
        status: null,
        html: '',
        error: error.message,
      });
    });

    req.setTimeout(5000, () => {
      req.destroy();
      resolve({
        status: null,
        html: '',
        error: 'Timeout',
      });
    });
  });
}

// Main test
async function runVisualTests() {
  console.log('🎨 Visual Page Content Test');
  console.log('='.repeat(60));
  console.log();

  for (const page of PAGES) {
    console.log(`📄 Testing ${page.name} (${page.path})`);
    console.log('-'.repeat(40));

    const result = await fetchPage(page.path);

    if (result.error) {
      console.log(`❌ Error: ${result.error}`);
    } else if (result.status !== 200) {
      console.log(`❌ HTTP ${result.status}`);
    } else {
      const content = extractVisibleText(result.html);

      console.log(`✅ Page loaded successfully`);
      console.log(`   Title: "${content.title}"`);

      if (content.headings.length > 0) {
        console.log(`   Headings: ${content.headings.map((h) => `"${h}"`).join(', ')}`);
      }

      if (content.paragraphs.length > 0) {
        console.log(`   Content preview: "${content.paragraphs[0].substring(0, 60)}..."`);
      }

      console.log(
        `   Features: ${
          [
            content.hasForm && 'Forms',
            content.hasNavigation && 'Navigation',
            content.hasButtons && 'Buttons',
          ]
            .filter(Boolean)
            .join(', ') || 'None detected'
        }`
      );
    }

    console.log();
  }

  console.log('='.repeat(60));
  console.log('✅ Visual test complete');
}

runVisualTests().catch((error) => {
  console.error('Test error:', error);
  process.exit(1);
});
