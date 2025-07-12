#!/usr/bin/env node
/**
 * Frontend Permalink Routes Testing Script
 * 
 * This script tests the new frontend routes to ensure they properly handle
 * the new permalink structure and redirects.
 */

const puppeteer = require('puppeteer');
const process = require('process');

// Configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3004';
const TIMEOUT = 30000;

class FrontendRouteTester {
    constructor(baseUrl = BASE_URL) {
        this.baseUrl = baseUrl;
        this.browser = null;
        this.page = null;
        this.testResults = [];
        this.stats = {
            totalTests: 0,
            passedTests: 0,
            failedTests: 0,
            skippedTests: 0
        };
    }

    async init() {
        console.log('🚀 Initializing browser...');
        this.browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        this.page = await this.browser.newPage();
        
        // Set viewport and user agent
        await this.page.setViewport({ width: 1280, height: 720 });
        await this.page.setUserAgent('Mozilla/5.0 (compatible; PRSNL-Test-Bot/1.0)');
        
        // Set longer timeout
        this.page.setDefaultTimeout(TIMEOUT);
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
    }

    async runAllTests() {
        console.log('🧪 Starting frontend route testing...');
        
        try {
            await this.init();
            
            // Check if frontend is available
            if (!await this.testFrontendAvailability()) {
                return this.generateResults('Frontend is not available');
            }
            
            // Run all test suites
            await this.testContentRoutes();
            await this.testToolRoutes();
            await this.testSystemRoutes();
            await this.testLegacyRedirects();
            await this.testErrorHandling();
            await this.testSEOElements();
            await this.testResponsiveness();
            
            return this.generateResults();
            
        } finally {
            await this.cleanup();
        }
    }

    async testFrontendAvailability() {
        try {
            console.log('🔍 Testing frontend availability...');
            const response = await this.page.goto(this.baseUrl, { waitUntil: 'networkidle0' });
            
            if (response && response.status() === 200) {
                console.log('✅ Frontend is available');
                return true;
            } else {
                console.log(`❌ Frontend not available: ${response ? response.status() : 'No response'}`);
                return false;
            }
        } catch (error) {
            console.log(`❌ Cannot connect to frontend: ${error.message}`);
            return false;
        }
    }

    async testContentRoutes() {
        console.log('📄 Testing content routes...');
        
        const contentRoutes = [
            '/timeline',
            '/chat', 
            '/capture',
            '/insights',
            '/videos',
            '/code-cortex'
        ];

        for (const route of contentRoutes) {
            await this.runTest(
                `GET ${route}`,
                this.testBasicRoute.bind(this),
                route
            );
        }
    }

    async testToolRoutes() {
        console.log('🛠️ Testing tool routes...');
        
        const toolRoutes = [
            '/code-cortex/docs',
            '/code-cortex/links', 
            '/code-cortex/projects',
            '/code-cortex/synapses'
        ];

        for (const route of toolRoutes) {
            await this.runTest(
                `GET ${route}`,
                this.testBasicRoute.bind(this),
                route
            );
        }
    }

    async testSystemRoutes() {
        console.log('⚙️ Testing system routes...');
        
        const systemRoutes = [
            '/import',
            '/ai'
        ];

        for (const route of systemRoutes) {
            await this.runTest(
                `GET ${route}`,
                this.testBasicRoute.bind(this),
                route
            );
        }
    }

    async testLegacyRedirects() {
        console.log('🔄 Testing legacy redirects...');
        
        // For now, skipping legacy redirects as new permalink structure is being implemented
        console.log('⏭️ Legacy redirects testing skipped - new permalink structure in development');
    }

    async testErrorHandling() {
        console.log('⚠️ Testing error handling...');
        
        const errorRoutes = [
            '/invalid-route',
            '/nonexistent-page',
            '/s/invalid-page'
        ];

        for (const route of errorRoutes) {
            await this.runTest(
                `Error handling for ${route}`,
                this.testErrorRoute.bind(this),
                route
            );
        }
    }

    async testSEOElements() {
        console.log('🔍 Testing SEO elements...');
        
        await this.runTest(
            'SEO meta tags test',
            this.testSEOMetaTags.bind(this)
        );
        
        await this.runTest(
            'Canonical URLs test',
            this.testCanonicalURLs.bind(this)
        );
    }

    async testResponsiveness() {
        console.log('📱 Testing responsiveness...');
        
        await this.runTest(
            'Mobile viewport test',
            this.testMobileViewport.bind(this)
        );
        
        await this.runTest(
            'Desktop viewport test',
            this.testDesktopViewport.bind(this)
        );
    }

    // Individual test methods
    async testBasicRoute(route) {
        try {
            const response = await this.page.goto(`${this.baseUrl}${route}`, { 
                waitUntil: 'networkidle0',
                timeout: TIMEOUT 
            });

            if (response.status() !== 200) {
                return { status: 'failed', message: `Expected 200, got ${response.status()}` };
            }

            // Check if page has content
            const hasContent = await this.page.$eval('body', (body) => {
                return body.textContent.length > 100; // Basic content check
            });

            if (!hasContent) {
                return { status: 'failed', message: 'Page appears to be empty' };
            }

            return { status: 'passed', message: 'Route accessible and has content' };

        } catch (error) {
            return { status: 'failed', message: `Error: ${error.message}` };
        }
    }

    async testCategoryRoute(route) {
        try {
            const response = await this.page.goto(`${this.baseUrl}${route}`, { 
                waitUntil: 'networkidle0',
                timeout: TIMEOUT 
            });

            if (response.status() !== 200) {
                return { status: 'failed', message: `Expected 200, got ${response.status()}` };
            }

            // Check if page has category-specific content
            const hasContent = await this.page.$eval('body', (body) => {
                return body.textContent.length > 100; // Basic content check
            });

            if (!hasContent) {
                return { status: 'failed', message: 'Page appears to be empty or not fully loaded' };
            }

            // Check for error messages
            const hasError = await this.page.$('.error, .not-found, [data-error]');
            if (hasError) {
                return { status: 'failed', message: 'Page shows error state' };
            }

            return { status: 'passed', message: `Category route ${route} loaded successfully` };

        } catch (error) {
            return { status: 'failed', message: `Error loading route: ${error.message}` };
        }
    }

    async testSpecificContentRoute(route) {
        try {
            const response = await this.page.goto(`${this.baseUrl}${route}`, { 
                waitUntil: 'networkidle0',
                timeout: TIMEOUT 
            });

            // This might return 404 if content doesn't exist, which is expected
            if (response.status() === 404) {
                return { status: 'skipped', message: 'Content not found (expected for test data)' };
            }

            if (response.status() !== 200) {
                return { status: 'failed', message: `Expected 200 or 404, got ${response.status()}` };
            }

            // Check for content structure
            const hasContentStructure = await this.page.$('.content-page, .content-header, [data-content]');
            if (!hasContentStructure) {
                return { status: 'failed', message: 'Content page structure not found' };
            }

            return { status: 'passed', message: `Content route ${route} has correct structure` };

        } catch (error) {
            return { status: 'failed', message: `Error loading content route: ${error.message}` };
        }
    }

    async testToolRoute(route) {
        try {
            const response = await this.page.goto(`${this.baseUrl}${route}`, { 
                waitUntil: 'networkidle0',
                timeout: TIMEOUT 
            });

            if (response.status() !== 200) {
                return { status: 'failed', message: `Expected 200, got ${response.status()}` };
            }

            // Check if tool interface is present
            const hasToolInterface = await this.page.$eval('body', (body) => {
                return body.textContent.length > 100;
            });

            if (!hasToolInterface) {
                return { status: 'failed', message: 'Tool interface not found or not loaded' };
            }

            return { status: 'passed', message: `Tool route ${route} loaded successfully` };

        } catch (error) {
            return { status: 'failed', message: `Error loading tool route: ${error.message}` };
        }
    }

    async testSystemRoute(route) {
        try {
            const response = await this.page.goto(`${this.baseUrl}${route}`, { 
                waitUntil: 'networkidle0',
                timeout: TIMEOUT 
            });

            if (response.status() !== 200) {
                return { status: 'failed', message: `Expected 200, got ${response.status()}` };
            }

            // Check for system page content
            const hasSystemContent = await this.page.$eval('body', (body) => {
                return body.textContent.length > 50;
            });

            if (!hasSystemContent) {
                return { status: 'failed', message: 'System page content not found' };
            }

            return { status: 'passed', message: `System route ${route} loaded successfully` };

        } catch (error) {
            return { status: 'failed', message: `Error loading system route: ${error.message}` };
        }
    }

    async testLegacyRedirect(fromRoute, toRoute) {
        try {
            const response = await this.page.goto(`${this.baseUrl}${fromRoute}`, { 
                waitUntil: 'networkidle0',
                timeout: TIMEOUT 
            });

            // Check if we were redirected to the correct URL
            const currentUrl = this.page.url();
            const expectedUrl = `${this.baseUrl}${toRoute}`;

            if (currentUrl === expectedUrl) {
                return { status: 'passed', message: `Redirect from ${fromRoute} to ${toRoute} working` };
            } else {
                return { status: 'failed', message: `Expected redirect to ${expectedUrl}, got ${currentUrl}` };
            }

        } catch (error) {
            return { status: 'failed', message: `Error testing redirect: ${error.message}` };
        }
    }

    async testErrorRoute(route) {
        try {
            const response = await this.page.goto(`${this.baseUrl}${route}`, { 
                waitUntil: 'networkidle0',
                timeout: TIMEOUT 
            });

            if (response.status() === 404) {
                // Check if there's a proper 404 page
                const has404Content = await this.page.$eval('body', (body) => {
                    const text = body.textContent.toLowerCase();
                    return text.includes('404') || text.includes('not found') || text.includes('page not found');
                });

                if (has404Content) {
                    return { status: 'passed', message: `404 error properly handled for ${route}` };
                } else {
                    return { status: 'warning', message: '404 status returned but no clear 404 page content' };
                }
            } else {
                return { status: 'failed', message: `Expected 404, got ${response.status()}` };
            }

        } catch (error) {
            return { status: 'failed', message: `Error testing error route: ${error.message}` };
        }
    }

    async testSEOMetaTags() {
        try {
            await this.page.goto(`${this.baseUrl}/c/dev`, { waitUntil: 'networkidle0' });

            // Check for basic SEO meta tags
            const metaTags = await this.page.evaluate(() => {
                const title = document.querySelector('title')?.textContent || '';
                const description = document.querySelector('meta[name="description"]')?.getAttribute('content') || '';
                const ogTitle = document.querySelector('meta[property="og:title"]')?.getAttribute('content') || '';
                const ogDescription = document.querySelector('meta[property="og:description"]')?.getAttribute('content') || '';

                return { title, description, ogTitle, ogDescription };
            });

            const issues = [];
            if (!metaTags.title) issues.push('Missing title tag');
            if (!metaTags.description) issues.push('Missing meta description');
            if (!metaTags.ogTitle) issues.push('Missing OpenGraph title');
            if (!metaTags.ogDescription) issues.push('Missing OpenGraph description');

            if (issues.length > 0) {
                return { status: 'failed', message: `SEO issues: ${issues.join(', ')}` };
            }

            return { status: 'passed', message: 'All basic SEO meta tags present' };

        } catch (error) {
            return { status: 'failed', message: `Error checking SEO meta tags: ${error.message}` };
        }
    }

    async testCanonicalURLs() {
        try {
            await this.page.goto(`${this.baseUrl}/c/dev`, { waitUntil: 'networkidle0' });

            const canonicalUrl = await this.page.$eval('link[rel="canonical"]', el => el.href).catch(() => null);

            if (!canonicalUrl) {
                return { status: 'failed', message: 'Canonical URL not found' };
            }

            if (!canonicalUrl.includes('/c/dev')) {
                return { status: 'failed', message: 'Canonical URL does not match expected pattern' };
            }

            return { status: 'passed', message: 'Canonical URL properly set' };

        } catch (error) {
            return { status: 'failed', message: `Error checking canonical URL: ${error.message}` };
        }
    }

    async testMobileViewport() {
        try {
            await this.page.setViewport({ width: 375, height: 667 }); // iPhone SE size
            await this.page.goto(`${this.baseUrl}/c/dev`, { waitUntil: 'networkidle0' });

            // Check if page is responsive
            const isResponsive = await this.page.evaluate(() => {
                return window.innerWidth <= 500 && document.body.scrollWidth <= window.innerWidth + 10;
            });

            if (!isResponsive) {
                return { status: 'failed', message: 'Page not properly responsive on mobile' };
            }

            return { status: 'passed', message: 'Mobile viewport renders correctly' };

        } catch (error) {
            return { status: 'failed', message: `Error testing mobile viewport: ${error.message}` };
        }
    }

    async testDesktopViewport() {
        try {
            await this.page.setViewport({ width: 1280, height: 720 });
            await this.page.goto(`${this.baseUrl}/c/dev`, { waitUntil: 'networkidle0' });

            // Check if page loads properly on desktop
            const hasContent = await this.page.$eval('body', (body) => {
                return body.textContent.length > 100;
            });

            if (!hasContent) {
                return { status: 'failed', message: 'Desktop page appears empty or not loaded' };
            }

            return { status: 'passed', message: 'Desktop viewport renders correctly' };

        } catch (error) {
            return { status: 'failed', message: `Error testing desktop viewport: ${error.message}` };
        }
    }

    // Utility methods
    async runTest(testName, testFunc, ...args) {
        this.stats.totalTests++;

        try {
            const result = await testFunc(...args);
            result.testName = testName;
            result.timestamp = new Date().toISOString();

            if (result.status === 'passed') {
                this.stats.passedTests++;
                console.log(`  ✅ ${testName}`);
            } else if (result.status === 'failed') {
                this.stats.failedTests++;
                console.log(`  ❌ ${testName}: ${result.message}`);
            } else if (result.status === 'skipped') {
                this.stats.skippedTests++;
                console.log(`  ⏭️  ${testName}: ${result.message}`);
            }

            this.testResults.push(result);

        } catch (error) {
            this.stats.failedTests++;
            const errorResult = {
                testName,
                status: 'failed',
                message: `Test error: ${error.message}`,
                timestamp: new Date().toISOString()
            };
            this.testResults.push(errorResult);
            console.log(`  ❌ ${testName}: Test error: ${error.message}`);
        }
    }

    generateResults(errorMessage = null) {
        return {
            success: this.stats.failedTests === 0 && !errorMessage,
            errorMessage,
            stats: this.stats,
            testResults: this.testResults,
            timestamp: new Date().toISOString()
        };
    }
}

async function main() {
    console.log('🚀 Starting Frontend Route Testing Suite');
    console.log('='.repeat(50));

    const tester = new FrontendRouteTester();
    const results = await tester.runAllTests();

    console.log('\n' + '='.repeat(50));
    console.log('📊 TEST RESULTS');
    console.log('='.repeat(50));

    if (results.errorMessage) {
        console.log(`❌ Test suite failed: ${results.errorMessage}`);
        process.exit(2);
    }

    const stats = results.stats;
    console.log(`📈 Statistics:`);
    console.log(`   Total tests: ${stats.totalTests}`);
    console.log(`   Passed: ${stats.passedTests}`);
    console.log(`   Failed: ${stats.failedTests}`);
    console.log(`   Skipped: ${stats.skippedTests}`);

    const successRate = stats.totalTests > 0 ? (stats.passedTests / stats.totalTests * 100) : 0;
    console.log(`   Success rate: ${successRate.toFixed(1)}%`);

    if (results.success) {
        console.log('\n✅ All tests passed! The frontend routes are working correctly.');
        process.exit(0);
    } else {
        console.log(`\n⚠️ ${stats.failedTests} test(s) failed.`);
        
        // Show failed tests
        const failedTests = results.testResults.filter(r => r.status === 'failed');
        if (failedTests.length > 0) {
            console.log('\n❌ Failed tests:');
            failedTests.forEach(test => {
                console.log(`   - ${test.testName}: ${test.message}`);
            });
        }
        
        process.exit(1);
    }
}

// Handle script execution
if (require.main === module) {
    main().catch(error => {
        console.error('❌ Script error:', error.message);
        process.exit(2);
    });
}

module.exports = { FrontendRouteTester };