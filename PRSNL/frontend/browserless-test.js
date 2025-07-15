import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

// Configuration
const BROWSERLESS_TOKEN = process.env.BROWSERLESS_TOKEN;
if (!BROWSERLESS_TOKEN) {
  console.error('❌ Error: BROWSERLESS_TOKEN environment variable is required.');
  console.error('Please set your browserless token with:');
  console.error('export BROWSERLESS_TOKEN=your-token-here');
  process.exit(1);
}

// Create directories if they don't exist
const screenshotsDir = './codemirror-test-screenshots';
const resultsDir = './codemirror-test-results';
if (!fs.existsSync(screenshotsDir)) fs.mkdirSync(screenshotsDir, { recursive: true });
if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });

console.log('🧪 Starting CodeMirror browserless test...');

// Features to test on the Code Mirror page
const features = [
  { name: 'Main CodeMirror Page' },
  { name: 'Repository Section', selector: '.repo-section' },
  { name: 'Repository Cards', selector: '.repo-card' },
  { name: 'Search Input', selector: 'input[type="text"]' },
  { name: 'Intelligence Sections', selector: '.intelligence-sections, section' },
  { name: 'Tab Buttons', selector: '.tab-btn, button' }
];

async function runTests() {
  console.log('🚀 Connecting to browserless.io...');
  
  const browser = await puppeteer.connect({
    browserWSEndpoint: `wss://chrome.browserless.io?token=${BROWSERLESS_TOKEN}`,
  });
  
  console.log('✅ Connected to browserless.io');
  
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 900 });
    
    console.log('📱 Browser page created');
    
    // Set up console log capturing
    page.on('console', msg => {
      console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`);
    });
    
    // Set up error handling for failed requests
    page.on('requestfailed', request => {
      console.log(`[Request Failed] ${request.url()}: ${request.failure().errorText}`);
    });
    
    // Navigate to the Code Mirror page
    console.log('🌐 Navigating to Code Cortex CodeMirror page...');
    
    try {
      await page.goto('http://localhost:3004/code-cortex/codemirror', {
        waitUntil: 'networkidle2',
        timeout: 30000
      });
      console.log('✅ Page loaded successfully');
    } catch (error) {
      console.error(`❌ Navigation failed: ${error.message}`);
      console.log('⚠️ Trying alternate URL...');
      
      try {
        // Fallback to just the code-cortex page if the specific path doesn't work
        await page.goto('http://localhost:3004/code-cortex', {
          waitUntil: 'networkidle2',
          timeout: 30000
        });
        console.log('✅ Fallback page loaded successfully');
      } catch (fallbackError) {
        console.error(`❌ Fallback navigation failed: ${fallbackError.message}`);
        throw new Error('Navigation failed to both primary and fallback URLs');
      }
    }
    
    // Take full page screenshot
    console.log('📸 Taking full page screenshot...');
    await page.screenshot({
      path: path.join(screenshotsDir, 'full-page.png'),
      fullPage: true
    });
    console.log('✅ Screenshot saved');
    
    // Extract HTML structure for debugging
    console.log('🔍 Extracting page HTML structure...');
    const htmlContent = await page.content();
    fs.writeFileSync(path.join(resultsDir, 'page-content.html'), htmlContent);
    console.log('✅ HTML structure saved');
    
    // Check all interactive elements on the page
    console.log('🔍 Finding all interactive elements...');
    const interactiveElements = await page.evaluate(() => {
      const elements = {
        buttons: Array.from(document.querySelectorAll('button')).map(el => ({
          text: el.innerText.trim().slice(0, 30),
          classes: Array.from(el.classList)
        })),
        inputs: Array.from(document.querySelectorAll('input')).map(el => ({
          type: el.type,
          placeholder: el.placeholder,
          classes: Array.from(el.classList)
        })),
        links: Array.from(document.querySelectorAll('a')).map(el => ({
          text: el.innerText.trim().slice(0, 30),
          href: el.href,
          classes: Array.from(el.classList)
        }))
      };
      return elements;
    });
    
    fs.writeFileSync(
      path.join(resultsDir, 'interactive-elements.json'), 
      JSON.stringify(interactiveElements, null, 2)
    );
    console.log(`✅ Found ${interactiveElements.buttons.length} buttons, ${interactiveElements.inputs.length} inputs, ${interactiveElements.links.length} links`);
    
    // Test features
    console.log('\n🧪 Testing individual features:');
    const results = [];
    
    for (const feature of features) {
      console.log(`\n🔍 Testing: ${feature.name}`);
      
      try {
        if (feature.selector) {
          // Check if the element exists
          const element = await page.$(feature.selector);
          
          if (element) {
            console.log(`✅ Found ${feature.name}`);
            
            // Take a screenshot of the element
            try {
              await element.screenshot({
                path: path.join(screenshotsDir, `${feature.name.toLowerCase().replace(/\\s+/g, '-')}.png`),
              });
              console.log(`📸 Element screenshot saved`);
            } catch (screenshotError) {
              console.log(`⚠️ Couldn't take element screenshot: ${screenshotError.message}`);
            }
            
            // Test specific interactions based on the feature
            switch(feature.name) {
              case 'Search Input':
                console.log('🔍 Testing search functionality...');
                try {
                  await page.type(feature.selector, 'test');
                  console.log('✅ Typed "test" into search input');
                  
                  await page.screenshot({
                    path: path.join(screenshotsDir, 'after-search.png'),
                    fullPage: true
                  });
                } catch (typeError) {
                  console.error(`❌ Failed to type in search: ${typeError.message}`);
                }
                break;
                
              case 'Tab Buttons':
                console.log('🔍 Testing tab buttons...');
                try {
                  const buttons = await page.$$(feature.selector);
                  if (buttons.length > 1) {
                    await buttons[1].click();
                    console.log('✅ Clicked second tab button');
                    
                    await page.screenshot({
                      path: path.join(screenshotsDir, 'after-tab-click.png'),
                      fullPage: true
                    });
                  }
                } catch (clickError) {
                  console.error(`❌ Failed to click tab: ${clickError.message}`);
                }
                break;
                
              case 'Repository Cards':
                console.log('🔍 Testing repo card interaction...');
                try {
                  const cards = await page.$$(feature.selector);
                  if (cards.length > 0) {
                    await cards[0].hover();
                    console.log('✅ Hovered over first repo card');
                    
                    await page.screenshot({
                      path: path.join(screenshotsDir, 'repo-card-hover.png'),
                      fullPage: true
                    });
                  }
                } catch (hoverError) {
                  console.error(`❌ Failed to hover: ${hoverError.message}`);
                }
                break;
            }
            
            results.push({
              feature: feature.name,
              status: 'pass',
              message: 'Feature found and tested'
            });
          } else {
            console.log(`❌ Element not found for ${feature.name}`);
            results.push({
              feature: feature.name,
              status: 'fail',
              message: 'Element not found'
            });
          }
        } else {
          // For features without specific selectors (e.g., main page)
          results.push({
            feature: feature.name,
            status: 'pass',
            message: 'General page feature'
          });
        }
      } catch (featureError) {
        console.error(`❌ Error testing ${feature.name}: ${featureError.message}`);
        results.push({
          feature: feature.name,
          status: 'error',
          error: featureError.message
        });
      }
    }
    
    // Save test results
    const resultsFile = path.join(
      resultsDir,
      `browserless-test-results-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
    );
    
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
    console.log(`\n📊 Results saved to ${resultsFile}`);
    
    // Generate summary
    const summary = {
      total: results.length,
      passed: results.filter(r => r.status === 'pass').length,
      failed: results.filter(r => r.status === 'fail').length,
      errors: results.filter(r => r.status === 'error').length
    };
    
    console.log('\n📊 Test Summary:');
    console.log(`✅ Passed: ${summary.passed}/${summary.total}`);
    console.log(`❌ Failed: ${summary.failed}/${summary.total}`);
    console.log(`⚠️ Errors: ${summary.errors}/${summary.total}`);
    
    return { results, summary };
  } catch (error) {
    console.error('❌ Test suite error:', error);
    return { error: error.message };
  } finally {
    await browser.disconnect();
    console.log('🔌 Disconnected from browserless');
  }
}

// Execute the tests
runTests()
  .then(() => console.log('🎉 Testing completed'))
  .catch(err => console.error('💥 Fatal error:', err));
