import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

console.log('🧪 Starting CodeMirror features test...');

// Configuration
const CONFIG = {
  baseUrl: 'http://localhost:3004',
  browserlessUrl: 'wss://chrome.browserless.io',
  screenshotsDir: './codemirror-test-screenshots',
  resultsDir: './codemirror-test-results',
  waitTimeout: 10000,
  token: process.env.BROWSERLESS_TOKEN || '',
};

// Create directories if they don't exist
[CONFIG.screenshotsDir, CONFIG.resultsDir].forEach((dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Features to test
const features = [
  { name: 'Main CodeMirror Page', path: '/code-cortex/codemirror' },
  { name: 'Onboarding Wizard', path: '/code-cortex/codemirror', testId: 'onboarding-wizard' },
  { name: 'Repository Listing', path: '/code-cortex/codemirror', testId: 'repos-grid' },
  { name: 'Repository Search', path: '/code-cortex/codemirror', testId: 'repo-search' },
  {
    name: 'Analysis Type Selection',
    path: '/code-cortex/codemirror',
    testId: 'analysis-type-selector',
  },
  { name: 'Timeline View', path: '/code-cortex/codemirror', testId: 'intelligence-sections' },
  { name: 'Insights Tab', path: '/code-cortex/codemirror', testId: 'insights-section' },
  { name: 'Issues Tab', path: '/code-cortex/codemirror', testId: 'issues-section' },
  { name: 'History Tab', path: '/code-cortex/codemirror', testId: 'history-section' },
];

// Helper functions
const waitForSelector = async (page, selector, timeout = CONFIG.waitTimeout) => {
  try {
    return await page.waitForSelector(selector, { timeout });
  } catch (e) {
    return null;
  }
};

const takeScreenshot = async (page, name) => {
  const filename = `${name.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.png`;
  const filepath = path.join(CONFIG.screenshotsDir, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  return filepath;
};

const logResult = (feature, status, details = {}) => {
  console.log(`${status === 'pass' ? '✅' : '❌'} ${feature.name}: ${status.toUpperCase()}`);
  if (details.error) console.error(`   Error: ${details.error}`);
  if (details.screenshot) console.log(`   Screenshot: ${details.screenshot}`);
  return {
    feature: feature.name,
    status,
    timestamp: new Date().toISOString(),
    ...details,
  };
};

// Core test function
async function testCodeMirrorFeatures() {
  const results = [];
  const consoleMessages = [];
  let browser, page;

  try {
    console.log('🚀 Launching browser with browserless...');

    // Set up browser options
    const browserOptions = CONFIG.token
      ? { browserWSEndpoint: `${CONFIG.browserlessUrl}?token=${CONFIG.token}` }
      : { headless: 'new' }; // Fall back to local headless if no token

    browser = await puppeteer.launch(browserOptions);
    page = await browser.newPage();

    // Set up viewport and request interception
    await page.setViewport({ width: 1280, height: 800 });

    // Monitor console logs
    page.on('console', (msg) => {
      const text = `[${msg.type()}] ${msg.text()}`;
      consoleMessages.push(text);
      console.log(text);
    });

    // Network error monitoring
    const networkErrors = [];
    page.on('response', (response) => {
      if (response.status() >= 400) {
        const error = `${response.status()} ${response.statusText()} - ${response.url()}`;
        networkErrors.push(error);
        console.log(`[NETWORK ERROR] ${error}`);
      }
    });

    // Test each feature
    for (const feature of features) {
      console.log(`\n🔍 Testing: ${feature.name}`);

      try {
        // Navigate to the feature path
        const url = `${CONFIG.baseUrl}${feature.path}`;
        await page.goto(url, { waitUntil: 'networkidle2', timeout: CONFIG.waitTimeout });

        // Take initial screenshot
        const screenshot = await takeScreenshot(page, feature.name);

        // Test feature-specific functionality
        let featureFound = false;

        // For features that should have specific elements, check for them
        if (feature.testId) {
          // We'll use a class or a constructed selector based on testId
          const selector = feature.testId.startsWith('.') ? feature.testId : `.${feature.testId}`;
          featureFound = (await waitForSelector(page, selector)) !== null;

          if (featureFound) {
            // Perform feature-specific testing
            switch (feature.testId) {
              case 'onboarding-wizard':
                // Check if onboarding wizard exists (may not appear if already seen)
                const onboardingElement = await waitForSelector(page, '.onboarding-overlay');
                if (onboardingElement) {
                  // If the onboarding is visible, test navigation through slides
                  const nextButton = await waitForSelector(page, '.onboarding-nav-btn.next');
                  if (nextButton) {
                    await page.click('.onboarding-nav-btn.next');
                    await new Promise((resolve) => setTimeout(resolve, 500));
                    await takeScreenshot(page, `${feature.name}-next-slide`);
                  }
                } else {
                  console.log('   Onboarding wizard not shown (might have been seen already)');
                }
                break;

              case 'repo-search':
                // Test the repository search functionality
                const searchInput = await waitForSelector(page, 'input.repo-search');
                if (searchInput) {
                  await page.type('input.repo-search', 'test');
                  await new Promise((resolve) => setTimeout(resolve, 1000));
                  await takeScreenshot(page, `${feature.name}-search-results`);
                  // Clear the search
                  await page.click('input.repo-search', { clickCount: 3 });
                  await page.keyboard.press('Backspace');
                }
                break;

              case 'repos-grid':
                // Test clicking on a repository if available
                const repoCards = await page.$$('.repo-card');
                if (repoCards.length > 0) {
                  await repoCards[0].click();
                  await new Promise((resolve) => setTimeout(resolve, 500));
                  await takeScreenshot(page, `${feature.name}-repo-selected`);
                }
                break;

              case 'analysis-type-selector':
                // Try to open analysis selector if a repo is selected
                const startButton = await waitForSelector(page, '.action-btn.primary');
                if (startButton) {
                  await page.click('.action-btn.primary');
                  await new Promise((resolve) => setTimeout(resolve, 1000));
                  const selector = await waitForSelector(page, '.analysis-type-selector');
                  if (selector) {
                    await takeScreenshot(page, `${feature.name}-opened`);

                    // Try selecting a different analysis type
                    const depthOptions = await page.$$('.depth-option');
                    if (depthOptions.length > 1) {
                      await depthOptions[1].click();
                      await takeScreenshot(page, `${feature.name}-depth-selected`);
                    }

                    // Close the selector (click outside)
                    await page.mouse.click(50, 50);
                  }
                }
                break;

              case 'intelligence-sections':
                // Test tab switching in intelligence sections
                const tabs = await page.$$('.tab-btn');
                if (tabs.length > 1) {
                  // Click second tab
                  await tabs[1].click();
                  await new Promise((resolve) => setTimeout(resolve, 500));
                  await takeScreenshot(page, `${feature.name}-tab2`);

                  // Click third tab if available
                  if (tabs.length > 2) {
                    await tabs[2].click();
                    await new Promise((resolve) => setTimeout(resolve, 500));
                    await takeScreenshot(page, `${feature.name}-tab3`);
                  }
                }
                break;

              case 'insights-section':
              case 'issues-section':
              case 'history-section':
                // Test clicking on items in these sections if they exist
                const items = await page.$$(
                  feature.testId === 'insights-section'
                    ? '.insight-card'
                    : feature.testId === 'issues-section'
                      ? '.issue-card'
                      : '.history-item'
                );

                if (items.length > 0) {
                  // Just test hovering since clicking would navigate away
                  await items[0].hover();
                  await takeScreenshot(page, `${feature.name}-hover`);
                }
                break;
            }
          }
        }

        // Add result to our tracking
        results.push(
          logResult(feature, featureFound ? 'pass' : 'warn', {
            url,
            screenshot,
            message: featureFound ? 'Feature found and tested' : 'Feature element not found',
            consoleMessages: [...consoleMessages],
            networkErrors: [...networkErrors],
          })
        );

        // Clear message arrays for next feature
        consoleMessages.length = 0;
        networkErrors.length = 0;
      } catch (error) {
        results.push(
          logResult(feature, 'fail', {
            error: error.message,
            screenshot: await takeScreenshot(page, `${feature.name}-error`),
            consoleMessages: [...consoleMessages],
            networkErrors: [...networkErrors],
          })
        );

        // Clear message arrays for next feature
        consoleMessages.length = 0;
        networkErrors.length = 0;
      }
    }

    // Special test for CodeMirror repository detail page
    try {
      // Check if there's a repository we can navigate to
      const repoLinks = await page.$$('a[href^="/code-cortex/codemirror/repo/"]');

      if (repoLinks.length > 0) {
        console.log('\n🔍 Testing: Repository Detail Page');

        // Get the href attribute
        const href = await page.evaluate((element) => element.getAttribute('href'), repoLinks[0]);

        // Navigate to the repository detail page
        await page.goto(`${CONFIG.baseUrl}${href}`, {
          waitUntil: 'networkidle2',
          timeout: CONFIG.waitTimeout,
        });
        const repoDetailScreenshot = await takeScreenshot(page, 'repo-detail-page');

        results.push(
          logResult({ name: 'Repository Detail Page' }, 'pass', {
            url: `${CONFIG.baseUrl}${href}`,
            screenshot: repoDetailScreenshot,
            message: 'Successfully navigated to repository detail page',
          })
        );
      }
    } catch (error) {
      results.push(
        logResult({ name: 'Repository Detail Page' }, 'fail', {
          error: error.message,
          screenshot: await takeScreenshot(page, 'repo-detail-page-error'),
        })
      );
    }

    // Save test results
    const resultsFile = path.join(
      CONFIG.resultsDir,
      `codemirror-test-results-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
    );
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));

    // Generate summary
    const summary = {
      total: results.length,
      passed: results.filter((r) => r.status === 'pass').length,
      warned: results.filter((r) => r.status === 'warn').length,
      failed: results.filter((r) => r.status === 'fail').length,
      timestamp: new Date().toISOString(),
    };

    console.log('\n📊 Test Summary:');
    console.log(`✅ Passed: ${summary.passed}/${summary.total}`);
    console.log(`⚠️ Warnings: ${summary.warned}/${summary.total}`);
    console.log(`❌ Failed: ${summary.failed}/${summary.total}`);
    console.log(`📁 Results saved to: ${resultsFile}`);

    return { results, summary };
  } catch (error) {
    console.error('❌ Test suite error:', error.message);
    console.error(error);
    return { error: error.message };
  } finally {
    if (browser) {
      await browser.close();
      console.log('🔒 Browser closed');
    }
  }
}

// Run tests
(async () => {
  try {
    await testCodeMirrorFeatures();
    console.log('🎉 All tests completed!');
  } catch (error) {
    console.error('💥 Fatal error:', error);
    process.exit(1);
  }
})();
