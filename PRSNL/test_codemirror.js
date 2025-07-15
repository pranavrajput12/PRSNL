#!/usr/bin/env node

/**
 * CodeMirror Feature Testing Script
 * Uses Browserless for automated testing as requested by user
 * Tests all navigation paths and functionality
 */

const puppeteer = require('puppeteer-core');

const BROWSERLESS_URL = 'ws://localhost:3000';
const FRONTEND_URL = 'http://localhost:3004';
const BACKEND_URL = 'http://localhost:8000';

class CodeMirrorTester {
  constructor() {
    this.browser = null;
    this.page = null;
    this.results = [];
  }

  async connect() {
    console.log('🔌 Connecting to Browserless...');
    try {
      this.browser = await puppeteer.connect({
        browserWSEndpoint: BROWSERLESS_URL,
        defaultViewport: { width: 1920, height: 1080 }
      });
      this.page = await this.browser.newPage();
      console.log('✅ Connected to Browserless successfully');
      return true;
    } catch (error) {
      console.log('❌ Failed to connect to Browserless:', error.message);
      console.log('💡 Make sure Browserless is running: docker-compose up -d browserless');
      return false;
    }
  }

  async testApiEndpoints() {
    console.log('\n🧪 Testing API Endpoints...');
    
    const endpoints = [
      { name: 'Health Check', url: `${BACKEND_URL}/health` },
      { name: 'CodeMirror Timeline', url: `${BACKEND_URL}/api/codemirror/timeline` },
      { name: 'Analysis by Slug', url: `${BACKEND_URL}/api/codemirror/analysis/pranavrajput12-prsnl-standard-20250714-1845` },
      { name: 'GitHub Repos', url: `${BACKEND_URL}/api/github/repos` }
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await fetch(endpoint.url, {
          headers: { 'X-PRSNL-Integration': 'test' }
        });
        
        if (response.ok) {
          console.log(`✅ ${endpoint.name}: ${response.status}`);
          this.results.push({ test: endpoint.name, status: 'PASS', details: `Status: ${response.status}` });
        } else {
          console.log(`❌ ${endpoint.name}: ${response.status} ${response.statusText}`);
          this.results.push({ test: endpoint.name, status: 'FAIL', details: `Status: ${response.status}` });
        }
      } catch (error) {
        console.log(`❌ ${endpoint.name}: ${error.message}`);
        this.results.push({ test: endpoint.name, status: 'ERROR', details: error.message });
      }
    }
  }

  async testFrontendPages() {
    console.log('\n🌐 Testing Frontend Pages...');
    
    if (!this.page) {
      console.log('❌ No browser page available');
      return;
    }

    const pages = [
      { name: 'CodeMirror Home', url: `${FRONTEND_URL}/code-cortex/codemirror` },
      { name: 'Analysis Page', url: `${FRONTEND_URL}/code-cortex/codemirror/analysis/pranavrajput12-prsnl-standard-20250714-1845` },
      { name: 'Code Cortex Home', url: `${FRONTEND_URL}/code-cortex` }
    ];

    for (const pageTest of pages) {
      try {
        console.log(`🔄 Testing ${pageTest.name}...`);
        
        await this.page.goto(pageTest.url, { 
          waitUntil: 'networkidle2', 
          timeout: 10000 
        });
        
        // Check for basic page elements
        const title = await this.page.title();
        const hasError = await this.page.$('.error, .crash, [data-error]');
        
        if (hasError) {
          console.log(`❌ ${pageTest.name}: Error detected on page`);
          this.results.push({ test: pageTest.name, status: 'FAIL', details: 'Error detected on page' });
        } else {
          console.log(`✅ ${pageTest.name}: Loaded successfully (${title})`);
          this.results.push({ test: pageTest.name, status: 'PASS', details: `Title: ${title}` });
        }
        
        // Take screenshot for debugging
        await this.page.screenshot({ 
          path: `./test_screenshots/${pageTest.name.replace(/[^a-zA-Z0-9]/g, '_')}.png`,
          fullPage: false 
        });
        
      } catch (error) {
        console.log(`❌ ${pageTest.name}: ${error.message}`);
        this.results.push({ test: pageTest.name, status: 'ERROR', details: error.message });
      }
    }
  }

  async testGitHubRepoCards() {
    console.log('\n🃏 Testing GitHub Repository Cards...');
    
    if (!this.page) {
      console.log('❌ No browser page available');
      return;
    }

    try {
      await this.page.goto(`${FRONTEND_URL}/code-cortex/codemirror`, { 
        waitUntil: 'networkidle2' 
      });
      
      // Wait for repo cards to load
      await this.page.waitForSelector('.repos-grid', { timeout: 5000 });
      
      // Check if GitHubRepoCardV2 components are present
      const repoCards = await this.page.$$('.repo-card');
      const hasViewButtons = await this.page.$$('.action-btn.secondary.small');
      const hasAnalyzeButtons = await this.page.$$('.action-btn.primary.small');
      
      console.log(`📊 Found ${repoCards.length} repository cards`);
      console.log(`👁️ Found ${hasViewButtons.length} View buttons`);
      console.log(`🚀 Found ${hasAnalyzeButtons.length} Analyze buttons`);
      
      if (repoCards.length > 0 && hasViewButtons.length > 0 && hasAnalyzeButtons.length > 0) {
        console.log('✅ Repository cards are displaying correctly with action buttons');
        this.results.push({ test: 'Repository Cards', status: 'PASS', details: `${repoCards.length} cards with buttons` });
      } else {
        console.log('❌ Repository cards or buttons are missing');
        this.results.push({ test: 'Repository Cards', status: 'FAIL', details: 'Missing cards or buttons' });
      }
      
    } catch (error) {
      console.log(`❌ Repository Cards Test: ${error.message}`);
      this.results.push({ test: 'Repository Cards', status: 'ERROR', details: error.message });
    }
  }

  async testIntelligenceSections() {
    console.log('\n🧠 Testing Intelligence Sections...');
    
    if (!this.page) {
      console.log('❌ No browser page available');
      return;
    }

    try {
      await this.page.goto(`${FRONTEND_URL}/code-cortex/codemirror`, { 
        waitUntil: 'networkidle2' 
      });
      
      // Test the three intelligence tabs
      const tabs = ['insights', 'issues', 'history'];
      
      for (const tab of tabs) {
        try {
          const tabSelector = `.tab-btn[onclick*="${tab}"]`;
          await this.page.waitForSelector(tabSelector, { timeout: 3000 });
          await this.page.click(tabSelector);
          
          // Wait for content to switch
          await this.page.waitForTimeout(500);
          
          console.log(`✅ ${tab.charAt(0).toUpperCase() + tab.slice(1)} tab is clickable`);
          this.results.push({ test: `${tab} Tab`, status: 'PASS', details: 'Tab navigation works' });
          
        } catch (error) {
          console.log(`❌ ${tab} tab: ${error.message}`);
          this.results.push({ test: `${tab} Tab`, status: 'FAIL', details: error.message });
        }
      }
      
    } catch (error) {
      console.log(`❌ Intelligence Sections Test: ${error.message}`);
      this.results.push({ test: 'Intelligence Sections', status: 'ERROR', details: error.message });
    }
  }

  async generateReport() {
    console.log('\n📊 Test Results Summary');
    console.log('========================');
    
    let passed = 0;
    let failed = 0;
    let errors = 0;
    
    this.results.forEach(result => {
      const icon = result.status === 'PASS' ? '✅' : result.status === 'FAIL' ? '❌' : '⚠️';
      console.log(`${icon} ${result.test}: ${result.status} - ${result.details}`);
      
      if (result.status === 'PASS') passed++;
      else if (result.status === 'FAIL') failed++;
      else errors++;
    });
    
    console.log('\n📈 Summary:');
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`⚠️ Errors: ${errors}`);
    console.log(`📋 Total: ${this.results.length}`);
    
    const successRate = ((passed / this.results.length) * 100).toFixed(1);
    console.log(`🎯 Success Rate: ${successRate}%`);
    
    return {
      passed,
      failed,
      errors,
      total: this.results.length,
      successRate: parseFloat(successRate),
      results: this.results
    };
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.disconnect();
      console.log('🔌 Disconnected from Browserless');
    }
  }

  async runAllTests() {
    console.log('🚀 Starting CodeMirror Feature Tests');
    console.log('====================================');
    
    // Create screenshots directory
    const fs = require('fs');
    const screenshotDir = './test_screenshots';
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
    
    // Test API endpoints first (doesn't require browser)
    await this.testApiEndpoints();
    
    // Connect to Browserless
    const connected = await this.connect();
    
    if (connected) {
      // Run browser-based tests
      await this.testFrontendPages();
      await this.testGitHubRepoCards();
      await this.testIntelligenceSections();
      await this.cleanup();
    } else {
      console.log('⚠️ Skipping browser tests - Browserless not available');
    }
    
    return await this.generateReport();
  }
}

// Main execution
async function main() {
  const tester = new CodeMirrorTester();
  
  try {
    const report = await tester.runAllTests();
    
    // Exit with appropriate code
    process.exit(report.failed === 0 && report.errors === 0 ? 0 : 1);
    
  } catch (error) {
    console.error('💥 Fatal error during testing:', error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Test interrupted by user');
  process.exit(1);
});

if (require.main === module) {
  main();
}

module.exports = CodeMirrorTester;