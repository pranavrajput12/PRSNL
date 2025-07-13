import puppeteer from 'puppeteer';

console.log('🧪 Starting simple test...');

(async () => {
  try {
    console.log('📱 Launching browser...');
    const browser = await puppeteer.launch({
      headless: false,
      defaultViewport: { width: 1920, height: 1080 },
    });

    console.log('📄 Creating new page...');
    const page = await browser.newPage();

    console.log('🌐 Navigating to homepage...');
    await page.goto('http://localhost:3004/', {
      waitUntil: 'networkidle2',
      timeout: 15000,
    });

    console.log('✅ Page loaded successfully!');
    const title = await page.title();
    console.log(`📋 Page title: ${title}`);

    const url = await page.url();
    console.log(`📍 Current URL: ${url}`);

    console.log('📸 Taking screenshot...');
    await page.screenshot({ path: './debug-screenshot.png', fullPage: true });
    console.log('Screenshot saved as debug-screenshot.png');

    console.log('🔒 Closing browser...');
    await browser.close();

    console.log('🎉 Test completed successfully!');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Stack:', error.stack);
  }
})();
