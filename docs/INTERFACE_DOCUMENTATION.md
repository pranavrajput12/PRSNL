# INTERFACE_DOCUMENTATION.md

## PRSNL User Interface Documentation

### Overview
PRSNL features a multi-component user interface spanning web application, browser extension, desktop overlay, and API interfaces. This document provides comprehensive UI/UX documentation with design patterns, interactions, and accessibility guidelines.

## Design System

### 1. Color Palette (Manchester United Red Theme)
```css
:root {
  /* Primary Colors */
  --color-primary: #dc143c;           /* Manchester United Red */
  --color-primary-dark: #b91c3c;     /* Darker red */
  --color-primary-light: #ef4f71;    /* Lighter red */
  
  /* Neutral Colors */
  --color-background: #ffffff;        /* Pure white */
  --color-surface: #f8fafc;          /* Light gray */
  --color-text: #1e293b;             /* Dark gray */
  --color-text-muted: #64748b;       /* Medium gray */
  --color-border: #e2e8f0;           /* Light border */
  
  /* Status Colors */
  --color-success: #10b981;          /* Green */
  --color-warning: #f59e0b;          /* Amber */
  --color-error: #ef4444;            /* Red error */
  --color-info: #3b82f6;             /* Blue */
}
```

### 2. Typography System
```css
/* Font Families */
--font-display: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
--font-sans: 'Mulish', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;

/* Font Scale */
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.25rem;      /* 20px */
--text-2xl: 1.5rem;      /* 24px */
--text-3xl: 1.875rem;    /* 30px */

/* Font Weights */
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 3. Spacing System
```css
/* Spacing Scale (8px base unit) */
--space-1: 0.25rem;      /* 4px */
--space-2: 0.5rem;       /* 8px */
--space-3: 0.75rem;      /* 12px */
--space-4: 1rem;         /* 16px */
--space-5: 1.25rem;      /* 20px */
--space-6: 1.5rem;       /* 24px */
--space-8: 2rem;         /* 32px */
--space-10: 2.5rem;      /* 40px */
--space-12: 3rem;        /* 48px */
--space-16: 4rem;        /* 64px */
```

### 4. Border Radius System
```css
--radius-sm: 0.125rem;   /* 2px */
--radius-md: 0.375rem;   /* 6px */
--radius-lg: 0.5rem;     /* 8px */
--radius-xl: 0.75rem;    /* 12px */
--radius-full: 9999px;   /* Full rounded */
```

### 5. Shadow System
```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
```

## Component Library

### 1. Button Components

#### Primary Button
```svelte
<!-- Primary Button -->
<button class="btn btn-primary">
  <Icon name="plus" />
  Add Item
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-lg);
    font-family: var(--font-sans);
    font-weight: var(--font-medium);
    font-size: var(--text-sm);
    transition: all 0.2s ease;
    border: none;
    cursor: pointer;
  }
  
  .btn-primary {
    background-color: var(--color-primary);
    color: white;
  }
  
  .btn-primary:hover {
    background-color: var(--color-primary-dark);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }
</style>
```

#### Secondary Button
```svelte
<button class="btn btn-secondary">Cancel</button>

<style>
  .btn-secondary {
    background-color: transparent;
    color: var(--color-text);
    border: 1px solid var(--color-border);
  }
  
  .btn-secondary:hover {
    background-color: var(--color-surface);
    border-color: var(--color-primary);
  }
</style>
```

### 2. Input Components

#### Text Input
```svelte
<div class="input-group">
  <label for="search" class="input-label">Search</label>
  <input 
    type="text" 
    id="search"
    class="input-field"
    placeholder="Search your knowledge..."
    bind:value={searchQuery}
  />
</div>

<style>
  .input-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }
  
  .input-label {
    font-family: var(--font-sans);
    font-weight: var(--font-medium);
    font-size: var(--text-sm);
    color: var(--color-text);
  }
  
  .input-field {
    padding: var(--space-3) var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    font-family: var(--font-sans);
    font-size: var(--text-base);
    transition: all 0.2s ease;
  }
  
  .input-field:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgb(220 20 60 / 0.1);
  }
</style>
```

### 3. Card Components

#### Content Card
```svelte
<div class="card">
  <div class="card-header">
    <h3 class="card-title">{item.title}</h3>
    <span class="card-date">{formatDate(item.created_at)}</span>
  </div>
  
  <div class="card-content">
    <p class="card-summary">{item.summary}</p>
    
    <div class="card-tags">
      {#each item.tags as tag}
        <span class="tag">{tag}</span>
      {/each}
    </div>
  </div>
  
  <div class="card-footer">
    <a href={item.url} class="card-link" target="_blank">
      <Icon name="external-link" />
      View Source
    </a>
  </div>
</div>

<style>
  .card {
    background: white;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    padding: var(--space-6);
    transition: all 0.2s ease;
  }
  
  .card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--color-primary);
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--space-4);
  }
  
  .card-title {
    font-family: var(--font-display);
    font-weight: var(--font-semibold);
    font-size: var(--text-lg);
    color: var(--color-text);
    margin: 0;
  }
  
  .card-date {
    font-size: var(--text-sm);
    color: var(--color-text-muted);
  }
  
  .tag {
    display: inline-block;
    background-color: rgb(220 20 60 / 0.1);
    color: var(--color-primary);
    padding: var(--space-1) var(--space-3);
    border-radius: var(--radius-full);
    font-size: var(--text-xs);
    font-weight: var(--font-medium);
  }
</style>
```

### 4. Icon System

#### Icon Component
```svelte
<!-- Icon.svelte -->
<script>
  export let name;
  export let size = 20;
  export let color = 'currentColor';
</script>

<svg 
  width={size} 
  height={size} 
  fill={color}
  class="icon"
  aria-hidden="true"
>
  {#if name === 'search'}
    <path d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  {:else if name === 'plus'}
    <path d="M12 4.5v15m7.5-7.5h-15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  {:else if name === 'external-link'}
    <path d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  {:else if name === 'timeline'}
    <path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  {:else if name === 'settings'}
    <path d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" stroke="currentColor" stroke-width="1.5" fill="none"/>
    <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" stroke="currentColor" stroke-width="1.5" fill="none"/>
  {/if}
</svg>

<style>
  .icon {
    display: inline-block;
    flex-shrink: 0;
  }
</style>
```

## Page Layouts and Navigation

### 1. Main Layout (Web Application)

#### Layout Structure
```svelte
<!-- +layout.svelte -->
<div class="app">
  <header class="app-header">
    <div class="header-content">
      <div class="logo">
        <Icon name="logo" size="32" />
        <h1>PRSNL</h1>
      </div>
      
      <nav class="main-nav">
        <a href="/" class="nav-link" class:active={$page.url.pathname === '/'}>
          <Icon name="home" />
          Home
        </a>
        <a href="/search" class="nav-link" class:active={$page.url.pathname === '/search'}>
          <Icon name="search" />
          Search
        </a>
        <a href="/timeline" class="nav-link" class:active={$page.url.pathname === '/timeline'}>
          <Icon name="timeline" />
          Timeline
        </a>
        <a href="/settings" class="nav-link" class:active={$page.url.pathname === '/settings'}>
          <Icon name="settings" />
          Settings
        </a>
      </nav>
      
      <div class="header-actions">
        <button class="btn btn-primary" on:click={openCaptureModal}>
          <Icon name="plus" />
          Quick Capture
        </button>
      </div>
    </div>
  </header>
  
  <main class="app-main">
    <slot />
  </main>
  
  <footer class="app-footer">
    <p>&copy; 2025 PRSNL. Local-first knowledge management.</p>
  </footer>
</div>

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  .app-header {
    background: white;
    border-bottom: 1px solid var(--color-border);
    padding: var(--space-4) 0;
  }
  
  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--space-6);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }
  
  .logo h1 {
    font-family: var(--font-display);
    font-weight: var(--font-bold);
    font-size: var(--text-2xl);
    color: var(--color-primary);
    margin: 0;
  }
  
  .main-nav {
    display: flex;
    gap: var(--space-6);
  }
  
  .nav-link {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-lg);
    text-decoration: none;
    color: var(--color-text-muted);
    font-weight: var(--font-medium);
    transition: all 0.2s ease;
  }
  
  .nav-link:hover,
  .nav-link.active {
    color: var(--color-primary);
    background-color: rgb(220 20 60 / 0.1);
  }
  
  .app-main {
    flex: 1;
    padding: var(--space-8) 0;
  }
</style>
```

### 2. Homepage Layout

#### Dashboard View
```svelte
<!-- +page.svelte (Homepage) -->
<div class="page">
  <div class="page-header">
    <h1 class="page-title">Welcome to PRSNL</h1>
    <p class="page-subtitle">Your local-first knowledge management system</p>
  </div>
  
  <div class="dashboard">
    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{stats.totalItems}</div>
        <div class="stat-label">Total Items</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-value">{stats.totalTags}</div>
        <div class="stat-label">Unique Tags</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-value">{stats.thisWeek}</div>
        <div class="stat-label">This Week</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-value">{stats.avgPerDay}</div>
        <div class="stat-label">Avg/Day</div>
      </div>
    </div>
    
    <!-- Quick Actions -->
    <div class="quick-actions">
      <h2 class="section-title">Quick Actions</h2>
      <div class="action-grid">
        <button class="action-card" on:click={openQuickCapture}>
          <Icon name="plus" size="24" />
          <span>Quick Capture</span>
        </button>
        
        <button class="action-card" on:click={openSearch}>
          <Icon name="search" size="24" />
          <span>Search All</span>
        </button>
        
        <button class="action-card" on:click={viewTimeline}>
          <Icon name="timeline" size="24" />
          <span>View Timeline</span>
        </button>
        
        <button class="action-card" on:click={importFile}>
          <Icon name="upload" size="24" />
          <span>Import File</span>
        </button>
      </div>
    </div>
    
    <!-- Recent Items -->
    <div class="recent-items">
      <h2 class="section-title">Recent Items</h2>
      <div class="items-grid">
        {#each recentItems as item}
          <ItemCard {item} />
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  .dashboard {
    display: flex;
    flex-direction: column;
    gap: var(--space-8);
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-4);
  }
  
  .stat-card {
    background: white;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    padding: var(--space-6);
    text-align: center;
  }
  
  .stat-value {
    font-family: var(--font-display);
    font-weight: var(--font-bold);
    font-size: var(--text-3xl);
    color: var(--color-primary);
  }
  
  .action-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--space-4);
  }
  
  .action-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-6);
    background: white;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .action-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--color-primary);
  }
</style>
```

### 3. Search Interface

#### Search Layout
```svelte
<!-- search/+page.svelte -->
<div class="search-page">
  <div class="search-header">
    <div class="search-input-container">
      <Icon name="search" />
      <input 
        type="text"
        class="search-input"
        placeholder="Search your knowledge..."
        bind:value={searchQuery}
        on:input={handleSearch}
      />
    </div>
    
    <div class="search-filters">
      <select bind:value={dateFilter} class="filter-select">
        <option value="">All Time</option>
        <option value="today">Today</option>
        <option value="week">This Week</option>
        <option value="month">This Month</option>
      </select>
      
      <select bind:value={typeFilter} class="filter-select">
        <option value="">All Types</option>
        <option value="article">Articles</option>
        <option value="note">Notes</option>
        <option value="document">Documents</option>
      </select>
    </div>
  </div>
  
  <div class="search-results">
    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Searching...</p>
      </div>
    {:else if searchResults.length === 0}
      <div class="empty-state">
        <Icon name="search" size="48" />
        <h3>No results found</h3>
        <p>Try adjusting your search terms or filters</p>
      </div>
    {:else}
      <div class="results-header">
        <span class="results-count">{searchResults.length} results</span>
        <div class="view-toggle">
          <button 
            class="view-btn"
            class:active={viewMode === 'grid'}
            on:click={() => viewMode = 'grid'}
          >
            <Icon name="grid" />
          </button>
          <button 
            class="view-btn"
            class:active={viewMode === 'list'}
            on:click={() => viewMode = 'list'}
          >
            <Icon name="list" />
          </button>
        </div>
      </div>
      
      <div class="results-container" class:list-view={viewMode === 'list'}>
        {#each searchResults as item}
          <SearchResultCard {item} {searchQuery} />
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .search-input-container {
    position: relative;
    flex: 1;
    display: flex;
    align-items: center;
  }
  
  .search-input {
    width: 100%;
    padding: var(--space-4) var(--space-4) var(--space-4) var(--space-12);
    border: 2px solid var(--color-border);
    border-radius: var(--radius-xl);
    font-size: var(--text-lg);
    font-family: var(--font-sans);
    transition: all 0.2s ease;
  }
  
  .search-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 4px rgb(220 20 60 / 0.1);
  }
  
  .search-input-container :global(.icon) {
    position: absolute;
    left: var(--space-4);
    color: var(--color-text-muted);
    z-index: 1;
  }
  
  .results-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: var(--space-6);
  }
  
  .results-container.list-view {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
</style>
```

## Browser Extension Interface

### 1. Extension Popup

#### Popup Layout
```html
<!-- popup.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="popup">
    <div class="popup-header">
      <div class="logo">
        <img src="icons/icon48.png" alt="PRSNL" class="logo-icon">
        <h1>PRSNL</h1>
      </div>
      <div class="status" id="status">
        <span class="status-dot"></span>
        <span class="status-text">Ready</span>
      </div>
    </div>
    
    <div class="popup-content">
      <div class="capture-section">
        <h2>Quick Capture</h2>
        
        <div class="capture-buttons">
          <button id="capture-page" class="btn btn-primary">
            <svg class="icon"><!-- Page icon --></svg>
            Capture Page
          </button>
          
          <button id="capture-selection" class="btn btn-secondary">
            <svg class="icon"><!-- Selection icon --></svg>
            Capture Selection
          </button>
        </div>
        
        <div class="tags-input">
          <input 
            type="text" 
            id="custom-tags" 
            placeholder="Add custom tags..."
            class="input-field"
          >
        </div>
      </div>
      
      <div class="recent-section">
        <h3>Recent Captures</h3>
        <div id="recent-list" class="recent-list">
          <!-- Populated by JavaScript -->
        </div>
      </div>
    </div>
    
    <div class="popup-footer">
      <button id="open-app" class="link-btn">
        <svg class="icon"><!-- External link icon --></svg>
        Open PRSNL App
      </button>
      
      <button id="open-options" class="link-btn">
        <svg class="icon"><!-- Settings icon --></svg>
        Settings
      </button>
    </div>
  </div>
  
  <script src="popup.js"></script>
</body>
</html>
```

#### Popup Styles
```css
/* styles.css */
:root {
  --color-primary: #dc143c;
  --color-primary-dark: #b91c3c;
  --color-background: #ffffff;
  --color-text: #1e293b;
  --color-text-muted: #64748b;
  --color-border: #e2e8f0;
  --color-success: #10b981;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --radius-lg: 0.5rem;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  width: 380px;
  height: 500px;
}

.popup {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-background);
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.logo-icon {
  width: 24px;
  height: 24px;
}

.logo h1 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-primary);
}

.status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-success);
}

.capture-buttons {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--color-primary-dark);
}

.btn-secondary {
  background-color: transparent;
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.recent-list {
  max-height: 200px;
  overflow-y: auto;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
}

.recent-item:hover {
  background-color: #f8fafc;
}
```

### 2. Extension Options Page

#### Options Layout
```html
<!-- options.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PRSNL Extension Settings</title>
  <link rel="stylesheet" href="options.css">
</head>
<body>
  <div class="options-page">
    <header class="page-header">
      <div class="logo">
        <img src="icons/icon48.png" alt="PRSNL">
        <h1>PRSNL Extension Settings</h1>
      </div>
    </header>
    
    <main class="page-content">
      <div class="settings-section">
        <h2>Connection Settings</h2>
        <div class="setting-item">
          <label for="api-url">API URL</label>
          <input type="url" id="api-url" class="input-field" value="http://localhost:8000">
          <p class="setting-description">URL of your PRSNL backend server</p>
        </div>
      </div>
      
      <div class="settings-section">
        <h2>Capture Settings</h2>
        
        <div class="setting-item">
          <label class="checkbox-label">
            <input type="checkbox" id="auto-tags" checked>
            <span class="checkbox-custom"></span>
            Auto-generate tags
          </label>
          <p class="setting-description">Automatically generate tags using AI</p>
        </div>
        
        <div class="setting-item">
          <label class="checkbox-label">
            <input type="checkbox" id="show-notifications" checked>
            <span class="checkbox-custom"></span>
            Show capture notifications
          </label>
        </div>
        
        <div class="setting-item">
          <label class="checkbox-label">
            <input type="checkbox" id="context-menu" checked>
            <span class="checkbox-custom"></span>
            Enable right-click context menu
          </label>
        </div>
      </div>
      
      <div class="settings-section">
        <h2>Keyboard Shortcuts</h2>
        <div class="shortcuts-list">
          <div class="shortcut-item">
            <span class="shortcut-label">Capture current page</span>
            <kbd class="shortcut-key">⌘+Shift+S</kbd>
          </div>
          <div class="shortcut-item">
            <span class="shortcut-label">Capture selection</span>
            <kbd class="shortcut-key">⌘+Shift+E</kbd>
          </div>
        </div>
        <p class="setting-description">
          Shortcuts can be customized in Chrome's extension settings
        </p>
      </div>
    </main>
    
    <footer class="page-footer">
      <button id="save-settings" class="btn btn-primary">Save Settings</button>
      <button id="reset-settings" class="btn btn-secondary">Reset to Defaults</button>
    </footer>
  </div>
  
  <script src="options.js"></script>
</body>
</html>
```

## Desktop Overlay Interface

### 1. Search Overlay

#### Overlay Layout
```html
<!-- index.html (Electron) -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PRSNL Quick Search</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="overlay">
    <div class="search-container">
      <div class="search-input-wrapper">
        <input 
          type="text" 
          id="search-input"
          class="search-input"
          placeholder="Search your knowledge..."
          autofocus
        >
        <div class="search-icon">
          <svg><!-- Search icon --></svg>
        </div>
      </div>
      
      <div class="results-container" id="results">
        <div class="empty-state">
          <p>Start typing to search your knowledge base...</p>
        </div>
      </div>
    </div>
    
    <div class="overlay-footer">
      <div class="shortcuts">
        <span class="shortcut">↵ Open</span>
        <span class="shortcut">⌘↵ Open in App</span>
        <span class="shortcut">Esc Close</span>
      </div>
    </div>
  </div>
  
  <script src="renderer.js"></script>
</body>
</html>
```

#### Overlay Styles
```css
/* styles.css (Electron overlay) */
body {
  margin: 0;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  background: rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(20px);
}

.overlay {
  max-width: 600px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  backdrop-filter: blur(40px);
}

.search-input {
  width: 100%;
  padding: 20px 60px 20px 20px;
  border: none;
  background: transparent;
  font-size: 18px;
  outline: none;
}

.results-container {
  max-height: 400px;
  overflow-y: auto;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.result-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: background-color 0.1s ease;
}

.result-item:hover,
.result-item.selected {
  background-color: rgba(220, 20, 60, 0.1);
}

.result-content {
  flex: 1;
}

.result-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.result-summary {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
}
```

## Responsive Design and Mobile

### 1. Breakpoint System
```css
/* Responsive breakpoints */
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}

/* Mobile-first responsive design */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: var(--space-4);
  }
  
  .main-nav {
    width: 100%;
    justify-content: center;
  }
  
  .dashboard {
    padding: var(--space-4);
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .action-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .action-grid {
    grid-template-columns: 1fr;
  }
  
  .card {
    padding: var(--space-4);
  }
}
```

### 2. Touch-Friendly Interactions
```css
/* Touch target sizing */
.btn,
.nav-link,
.action-card {
  min-height: 44px; /* iOS accessibility guideline */
  min-width: 44px;
}

/* Touch hover states */
@media (hover: none) and (pointer: coarse) {
  .card:hover {
    transform: none;
  }
  
  .card:active {
    transform: scale(0.98);
  }
}
```

## Accessibility Features

### 1. Keyboard Navigation
```svelte
<script>
  let currentFocus = 0;
  let items = [];
  
  function handleKeydown(event) {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        currentFocus = Math.min(currentFocus + 1, items.length - 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        currentFocus = Math.max(currentFocus - 1, 0);
        break;
      case 'Enter':
        event.preventDefault();
        selectItem(items[currentFocus]);
        break;
      case 'Escape':
        event.preventDefault();
        closeModal();
        break;
    }
  }
</script>

<div class="search-results" on:keydown={handleKeydown}>
  {#each items as item, index}
    <div 
      class="result-item"
      class:focused={index === currentFocus}
      tabindex="0"
      role="option"
    >
      {item.title}
    </div>
  {/each}
</div>
```

### 2. ARIA Labels and Semantics
```svelte
<div class="search-container" role="search">
  <label for="search-input" class="sr-only">Search your knowledge base</label>
  <input 
    id="search-input"
    type="text"
    aria-label="Search your knowledge base"
    aria-describedby="search-help"
    bind:value={searchQuery}
  >
  
  <div id="search-help" class="sr-only">
    Type to search through your saved content
  </div>
  
  <div 
    class="search-results"
    role="listbox"
    aria-label="Search results"
    aria-live="polite"
  >
    {#each results as result}
      <div 
        class="result-item"
        role="option"
        aria-selected={result === selectedResult}
      >
        {result.title}
      </div>
    {/each}
  </div>
</div>

<style>
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
</style>
```

### 3. Color Contrast and Themes
```css
/* High contrast mode support */
@media (prefers-contrast: high) {
  :root {
    --color-border: #000000;
    --color-text: #000000;
    --color-background: #ffffff;
  }
  
  .card {
    border-width: 2px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## Animation and Micro-interactions

### 1. Loading States
```svelte
<script>
  export let isLoading = false;
</script>

{#if isLoading}
  <div class="loading-container">
    <div class="spinner"></div>
    <p>Loading your content...</p>
  </div>
{/if}

<style>
  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--color-border);
    border-top: 3px solid var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8);
  }
</style>
```

### 2. Transition Effects
```css
/* Page transitions */
.page-transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-enter {
  opacity: 0;
  transform: translateY(20px);
}

.page-enter-active {
  opacity: 1;
  transform: translateY(0);
}

/* Card hover animations */
.card {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

/* Button press animations */
.btn {
  transition: all 0.1s ease;
}

.btn:active {
  transform: scale(0.95);
}
```

## Error States and Empty States

### 1. Error Handling UI
```svelte
<script>
  export let error = null;
  export let retry = () => {};
</script>

{#if error}
  <div class="error-state">
    <div class="error-icon">
      <Icon name="exclamation-triangle" size="48" />
    </div>
    <h3 class="error-title">Something went wrong</h3>
    <p class="error-message">{error.message}</p>
    <button class="btn btn-primary" on:click={retry}>
      Try Again
    </button>
  </div>
{/if}

<style>
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8);
    text-align: center;
  }
  
  .error-icon {
    color: var(--color-error);
  }
  
  .error-title {
    margin: 0;
    font-family: var(--font-display);
    font-weight: var(--font-semibold);
    color: var(--color-text);
  }
  
  .error-message {
    margin: 0;
    color: var(--color-text-muted);
    max-width: 400px;
  }
</style>
```

### 2. Empty States
```svelte
<script>
  export let type = 'search'; // 'search', 'timeline', 'general'
  export let action = () => {};
</script>

<div class="empty-state">
  {#if type === 'search'}
    <Icon name="search" size="64" />
    <h3>No results found</h3>
    <p>Try adjusting your search terms or check your spelling</p>
  {:else if type === 'timeline'}
    <Icon name="plus" size="64" />
    <h3>No items yet</h3>
    <p>Start capturing content to build your knowledge base</p>
    <button class="btn btn-primary" on:click={action}>
      Capture Your First Item
    </button>
  {:else}
    <Icon name="inbox" size="64" />
    <h3>Nothing here yet</h3>
    <p>This area will populate as you use PRSNL</p>
  {/if}
</div>

<style>
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-12);
    text-align: center;
  }
  
  .empty-state :global(.icon) {
    color: var(--color-text-muted);
    opacity: 0.5;
  }
  
  .empty-state h3 {
    margin: 0;
    font-family: var(--font-display);
    font-weight: var(--font-semibold);
    color: var(--color-text);
  }
  
  .empty-state p {
    margin: 0;
    color: var(--color-text-muted);
    max-width: 400px;
  }
</style>
```

This comprehensive interface documentation covers all major UI components, layouts, and interaction patterns used throughout PRSNL. The design system ensures consistency across all interfaces while maintaining the distinctive Manchester United red branding and professional appearance.