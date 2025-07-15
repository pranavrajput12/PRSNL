import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

// Create screenshot and results directories
const screenshotsDir = './codemirror-test-screenshots';
const resultsDir = './codemirror-test-results';
if (!fs.existsSync(screenshotsDir)) fs.mkdirSync(screenshotsDir, { recursive: true });
if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });

console.log('🧪 Starting CodeMirror features test...');

// List of features to test on the Code Mirror page
const features = [
  { name: 'Main CodeMirror Page', selector: '.codemirror-page' },
  { name: 'Repository Listing', selector: '.repos-grid' },
  { name: 'Repository Search', selector: 'input.repo-search' },
  { name: 'Timeline Sections', selector: '.intelligence-sections' },
  { name: 'Tab Navigation', selector: '.tab-btn' }
];

async function runTests() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({ 
    headless: false,
    defaultViewport: { width: 1280, height: 800 }
  });
  
  try {
    const page = await browser.newPage();
    console.log('Browser launched successfully');
    
    // Capture console logs
    page.on('console', msg => console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`));
    
    // Navigate to Code Mirror page
    console.log('Navigating to CodeMirror page...');
    await page.goto('http://localhost:3004/code-cortex/codemirror', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    console.log('✅ Page loaded successfully');
    
    // Take full page screenshot
    await page.screenshot({
      path: path.join(screenshotsDir, 'codemirror-page.png'),
      fullPage: true
    });
    console.log('📸 Full page screenshot captured');
    
    // Test each feature
    const results = [];
    for (const feature of features) {
      console.log(`\nTesting feature: ${feature.name}`);
      
      try {
        const element = await page.$(feature.selector);
        if (element) {
          console.log(`✅ Found ${feature.name}`);
          
          // Take screenshot of the element
          await element.screenshot({
            path: path.join(screenshotsDir, `${feature.name.toLowerCase().replace(/\\s+/g, '-')}.png`)
          });
          
          // Perform feature-specific tests
          switch (feature.name) {
            case 'Repository Search':
              console.log('Testing search functionality...');
              await page.type(feature.selector, 'test');
              await page.waitForTimeout(1000);
              await page.screenshot({
                path: path.join(screenshotsDir, 'search-results.png'),
                fullPage: true
              });
              console.log('✅ Search test completed');
              break;
              
            case 'Tab Navigation':
              console.log('Testing tab navigation...');
              const tabs = await page.$$('.tab-btn');
              if (tabs.length > 1) {
                await tabs[1].click();
                await page.waitForTimeout(500);
                await page.screenshot({
                  path: path.join(screenshotsDir, 'tab-navigation.png'),
                  fullPage: true
                });
                console.log('✅ Tab navigation test completed');
              } else {
                console.log('⚠️ Not enough tabs to test navigation');
              }
              break;
          }
          
          results.push({
            feature: feature.name,
            status: 'pass',
            screenshot: `${feature.name.toLowerCase().replace(/\\s+/g, '-')}.png`
          });
        } else {
          console.log(`❌ Could not find element for ${feature.name} with selector ${feature.selector}`);
          results.push({
            feature: feature.name,
            status: 'fail',
            error: 'Element not found'
          });
        }
      } catch (error) {
        console.error(`❌ Error testing ${feature.name}:`, error);
        results.push({
          feature: feature.name,
          status: 'error',
          error: error.message
        });
      }
    }
    
    // Save test results
    fs.writeFileSync(
      path.join(resultsDir, `results-${new Date().toISOString().replace(/:/g, '-')}.json`),
      JSON.stringify(results, null, 2)
    );
    
    // Print summary
    const passed = results.filter(r => r.status === 'pass').length;
    console.log(`\n📊 Test Summary: ${passed}/${results.length} features passed`);
    
    return results;
  } catch (mainError) {
    console.error('❌ Main test error:', mainError);
  } finally {
    await browser.close();
    console.log('🔒 Browser closed');
  }
}

// Execute the tests
runTests()
  .then(() => console.log('🎉 Testing completed'))
  .catch(err => console.error('💥 Fatal error:', err));
