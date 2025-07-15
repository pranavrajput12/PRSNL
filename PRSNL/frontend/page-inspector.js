import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

// Create output directory
const outputDir = './page-inspection';
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

async function inspectPage() {
  console.log('🔍 Starting page inspection...');
  const browser = await puppeteer.launch({ 
    headless: false,
    defaultViewport: { width: 1280, height: 800 }
  });
  
  try {
    const page = await browser.newPage();
    console.log('Browser launched successfully');
    
    // Navigate to Code Mirror page
    console.log('Navigating to CodeMirror page...');
    await page.goto('http://localhost:3004/code-cortex/codemirror', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    console.log('✅ Page loaded successfully');
    
    // Take a screenshot
    await page.screenshot({
      path: path.join(outputDir, 'codemirror-page.png'),
      fullPage: true
    });
    console.log('📸 Screenshot captured');
    
    // Extract page HTML structure
    const pageHTML = await page.content();
    fs.writeFileSync(path.join(outputDir, 'page-structure.html'), pageHTML);
    console.log('📄 HTML structure saved');
    
    // Extract main element selectors
    const selectors = await page.evaluate(() => {
      const results = {};
      
      // Helper function to get a short description of an element
      function describeElement(el) {
        const tag = el.tagName.toLowerCase();
        const id = el.id ? `#${el.id}` : '';
        const classList = Array.from(el.classList).map(c => `.${c}`).join('');
        const text = el.textContent.trim().substring(0, 50);
        return {
          selector: id || classList || tag,
          text: text ? `"${text}${text.length > 49 ? '...' : ''}"` : ''
        };
      }
      
      // Find key elements
      const mainElements = [
        'main', 'header', 'section', 'nav',
        '.page-header', '.main-content', '.repo-section', 
        '.repo-grid', '.intelligence-sections'
      ];
      
      // Collect information about key elements
      mainElements.forEach(selector => {
        try {
          const elements = document.querySelectorAll(selector);
          if (elements.length > 0) {
            results[selector] = Array.from(elements).map(describeElement);
          }
        } catch (e) {
          results[selector] = { error: e.message };
        }
      });
      
      // Find interactive elements
      const interactiveElements = [
        'button', 'a', 'input', '.tab-btn', '.repo-card'
      ];
      
      // Count and sample interactive elements
      interactiveElements.forEach(selector => {
        try {
          const elements = document.querySelectorAll(selector);
          if (elements.length > 0) {
            const sample = Array.from(elements).slice(0, 5).map(describeElement);
            results[selector] = {
              count: elements.length,
              sample
            };
          }
        } catch (e) {
          results[selector] = { error: e.message };
        }
      });
      
      return results;
    });
    
    fs.writeFileSync(
      path.join(outputDir, 'selectors.json'),
      JSON.stringify(selectors, null, 2)
    );
    console.log('🔍 Selectors information saved');
    
    return { success: true };
  } catch (error) {
    console.error('❌ Error during page inspection:', error);
    return { success: false, error: error.message };
  } finally {
    await browser.close();
    console.log('🔒 Browser closed');
  }
}

// Execute the inspection
inspectPage()
  .then(result => {
    if (result.success) {
      console.log('✅ Page inspection completed successfully');
    } else {
      console.error('❌ Page inspection failed:', result.error);
    }
  })
  .catch(err => console.error('💥 Fatal error:', err));
