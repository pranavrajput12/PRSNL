// DOM Elements
const searchInput = document.getElementById('search-input');
const resultsContainer = document.getElementById('results-container');
const statusMessage = document.getElementById('status-message');

// Debounce function to limit API calls
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}

// Focus search input when window appears
window.api.onFocusSearch(() => {
  searchInput.focus();
  searchInput.select();
});

// Handle search input
const performSearch = debounce(async (query) => {
  if (!query || query.trim() === '') {
    resultsContainer.innerHTML = '';
    statusMessage.textContent = 'Type to search...';
    return;
  }

  try {
    statusMessage.textContent = 'Searching...';
    const data = await window.api.search(query);
    
    if (data.error) {
      statusMessage.textContent = `Error: ${data.error}`;
      return;
    }
    
    if (data.results.length === 0) {
      resultsContainer.innerHTML = '';
      statusMessage.textContent = 'No results found';
      return;
    }
    
    // Display results
    statusMessage.textContent = `${data.results.length} results found`;
    renderResults(data.results);
  } catch (error) {
    console.error('Search error:', error);
    statusMessage.textContent = `Error: ${error.message}`;
  }
}, 300);

// Render search results
function renderResults(results) {
  resultsContainer.innerHTML = '';
  
  results.forEach((result, index) => {
    const resultElement = document.createElement('div');
    resultElement.className = 'result-item';
    resultElement.setAttribute('data-index', index);
    resultElement.setAttribute('tabindex', index + 1);
    
    // Highlight the first result
    if (index === 0) {
      resultElement.classList.add('selected');
    }
    
    // Create title element
    const titleElement = document.createElement('div');
    titleElement.className = 'result-title';
    titleElement.textContent = result.title || 'Untitled';
    
    // Create description element
    const descElement = document.createElement('div');
    descElement.className = 'result-description';
    descElement.textContent = result.description || result.excerpt || '';
    
    // Add elements to result item
    resultElement.appendChild(titleElement);
    resultElement.appendChild(descElement);
    
    // Add click handler
    resultElement.addEventListener('click', () => {
      openResult(result);
    });
    
    resultsContainer.appendChild(resultElement);
  });
}

// Handle opening a result
function openResult(result) {
  console.log('Opening result:', result);
  // Here you would typically open the result in the main app
  // For now, we'll just hide the overlay
  window.api.hideWindow();
}

// Event listeners
searchInput.addEventListener('input', (e) => {
  performSearch(e.target.value);
});

// Keyboard navigation
let selectedIndex = 0;

document.addEventListener('keydown', (e) => {
  const results = document.querySelectorAll('.result-item');
  
  switch (e.key) {
    case 'Escape':
      window.api.hideWindow();
      break;
      
    case 'ArrowDown':
      e.preventDefault();
      if (results.length > 0) {
        selectedIndex = (selectedIndex + 1) % results.length;
        updateSelectedResult(results);
      }
      break;
      
    case 'ArrowUp':
      e.preventDefault();
      if (results.length > 0) {
        selectedIndex = (selectedIndex - 1 + results.length) % results.length;
        updateSelectedResult(results);
      }
      break;
      
    case 'Enter':
      e.preventDefault();
      const selectedResult = document.querySelector('.result-item.selected');
      if (selectedResult) {
        selectedResult.click();
      }
      break;
  }
});

// Update the selected result
function updateSelectedResult(results) {
  results.forEach((result, index) => {
    if (index === selectedIndex) {
      result.classList.add('selected');
      result.scrollIntoView({ block: 'nearest' });
    } else {
      result.classList.remove('selected');
    }
  });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  searchInput.focus();
});
