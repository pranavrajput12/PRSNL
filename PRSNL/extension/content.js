// Enhanced content script with selection tracking and smart detection

let selectedText = '';

// Track text selection
document.addEventListener('selectionchange', () => {
  const selection = window.getSelection();
  selectedText = selection.toString().trim();
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSelection') {
    sendResponse({ selection: selectedText });
  } else if (request.action === 'getPageMetadata') {
    sendResponse({
      selection: selectedText,
      metadata: extractPageMetadata()
    });
  }
});

// Extract additional page metadata
function extractPageMetadata() {
  const metadata = {
    readTime: estimateReadTime(),
    mainContent: extractMainContent(),
    codeBlocks: findCodeBlocks(),
    images: findImages()
  };
  
  // GitHub-specific metadata
  if (window.location.hostname === 'github.com') {
    metadata.github = extractGitHubMetadata();
  }
  
  return metadata;
}

// Estimate reading time
function estimateReadTime() {
  const text = document.body.innerText;
  const wordsPerMinute = 200;
  const wordCount = text.trim().split(/\s+/).length;
  return Math.ceil(wordCount / wordsPerMinute);
}

// Extract main content using readability heuristics
function extractMainContent() {
  // Look for article, main, or content containers
  const contentSelectors = ['article', 'main', '[role="main"]', '.content', '#content'];
  
  for (const selector of contentSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      return element.innerText.substring(0, 1000);
    }
  }
  
  return document.body.innerText.substring(0, 1000);
}

// Find code blocks
function findCodeBlocks() {
  const codeBlocks = [];
  const blocks = document.querySelectorAll('pre code, .highlight, .code-block');
  
  blocks.forEach(block => {
    const language = block.className.match(/language-(\w+)/)?.[1] || 'unknown';
    codeBlocks.push({
      language,
      content: block.textContent.substring(0, 500)
    });
  });
  
  return codeBlocks;
}

// Find images
function findImages() {
  const images = [];
  const imgs = document.querySelectorAll('img');
  
  imgs.forEach(img => {
    if (img.width > 100 && img.height > 100) {
      images.push({
        src: img.src,
        alt: img.alt,
        width: img.width,
        height: img.height
      });
    }
  });
  
  return images.slice(0, 5); // Limit to 5 images
}

// Extract GitHub-specific metadata
function extractGitHubMetadata() {
  const metadata = {};
  
  // Repository info
  const repoLink = document.querySelector('[itemprop="name"] a');
  if (repoLink) {
    metadata.repository = repoLink.textContent.trim();
  }
  
  // Language
  const langElement = document.querySelector('[itemprop="programmingLanguage"]');
  if (langElement) {
    metadata.language = langElement.textContent.trim();
  }
  
  // Stars
  const starsElement = document.querySelector('[aria-label*="star"]');
  if (starsElement) {
    metadata.stars = starsElement.textContent.trim();
  }
  
  // README content
  const readme = document.querySelector('.markdown-body');
  if (readme) {
    metadata.hasReadme = true;
    metadata.readmePreview = readme.textContent.substring(0, 500);
  }
  
  return metadata;
}