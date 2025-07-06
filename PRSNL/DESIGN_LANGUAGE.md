# PRSNL Design Language

## Overview
PRSNL's design language emphasizes clarity, efficiency, and a modern aesthetic that reflects its AI-powered capabilities. The interface is designed to be intuitive for personal knowledge management while showcasing advanced features without overwhelming the user.

## Design Principles

### 1. Clarity First
- Clean, uncluttered interfaces
- Clear visual hierarchy
- Meaningful whitespace
- Intuitive navigation patterns

### 2. Content-Centric
- Content takes center stage
- Minimal chrome and UI elements
- Focus on readability and scanability
- Smart use of typography

### 3. Progressive Disclosure
- Show essential information first
- Advanced features accessible but not prominent
- Context-aware UI elements
- Layered information architecture

### 4. Intelligent Feedback
- Real-time status updates
- Clear loading states
- Informative error messages
- Progress indicators for long operations

## Color System

### Primary Colors
```css
--primary-blue: #2563EB;      /* Primary actions, links */
--primary-purple: #7C3AED;    /* AI/intelligent features */
--primary-green: #10B981;     /* Success states */
```

### Neutral Colors
```css
--gray-900: #111827;          /* Primary text */
--gray-800: #1F2937;          /* Secondary text */
--gray-700: #374151;          /* Tertiary text */
--gray-600: #4B5563;          /* Disabled text */
--gray-500: #6B7280;          /* Borders */
--gray-400: #9CA3AF;          /* Dividers */
--gray-300: #D1D5DB;          /* Light borders */
--gray-200: #E5E7EB;          /* Backgrounds */
--gray-100: #F3F4F6;          /* Light backgrounds */
--gray-50: #F9FAFB;           /* Subtle backgrounds */
```

### Semantic Colors
```css
--error: #EF4444;             /* Error states */
--warning: #F59E0B;           /* Warning states */
--info: #3B82F6;              /* Information */
--success: #10B981;           /* Success states */
```

### Dark Mode
```css
--dark-bg: #0F172A;           /* Main background */
--dark-surface: #1E293B;      /* Card/surface background */
--dark-border: #334155;       /* Borders */
--dark-text: #F1F5F9;         /* Primary text */
--dark-text-secondary: #CBD5E1; /* Secondary text */
```

## Typography

### Font Stack
```css
--font-sans: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-mono: 'JetBrains Mono', Consolas, 'Courier New', monospace;
```

### Type Scale
```css
--text-xs: 0.75rem;     /* 12px - Captions, labels */
--text-sm: 0.875rem;    /* 14px - Secondary text */
--text-base: 1rem;      /* 16px - Body text */
--text-lg: 1.125rem;    /* 18px - Emphasized text */
--text-xl: 1.25rem;     /* 20px - Small headings */
--text-2xl: 1.5rem;     /* 24px - Section headings */
--text-3xl: 1.875rem;   /* 30px - Page headings */
--text-4xl: 2.25rem;    /* 36px - Large headings */
```

### Font Weights
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

## Spacing System

### Base Unit
8px grid system for consistent spacing

```css
--space-1: 0.25rem;     /* 4px */
--space-2: 0.5rem;      /* 8px */
--space-3: 0.75rem;     /* 12px */
--space-4: 1rem;        /* 16px */
--space-5: 1.25rem;     /* 20px */
--space-6: 1.5rem;      /* 24px */
--space-8: 2rem;        /* 32px */
--space-10: 2.5rem;     /* 40px */
--space-12: 3rem;       /* 48px */
--space-16: 4rem;       /* 64px */
```

## Component Patterns

### Cards
```css
.card {
  background: var(--white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);
  transition: all var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
```

### Buttons
```css
/* Primary Button */
.btn-primary {
  background: var(--primary-blue);
  color: white;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-weight: var(--font-medium);
  transition: all var(--transition-fast);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: var(--primary-blue);
  border: 1px solid var(--gray-300);
}

/* Ghost Button */
.btn-ghost {
  background: transparent;
  color: var(--gray-700);
}
```

### Input Fields
```css
.input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  transition: all var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
```

## Layout Patterns

### Container Widths
```css
--container-sm: 640px;
--container-md: 768px;
--container-lg: 1024px;
--container-xl: 1280px;
--container-2xl: 1536px;
```

### Grid System
- 12-column grid for complex layouts
- CSS Grid for 2D layouts
- Flexbox for 1D layouts
- Responsive breakpoints:
  - Mobile: < 640px
  - Tablet: 640px - 1024px
  - Desktop: > 1024px

## Motion & Animation

### Timing Functions
```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### Durations
```css
--transition-fast: 150ms;
--transition-base: 250ms;
--transition-slow: 350ms;
--transition-slower: 500ms;
```

### Common Animations
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## Icons & Imagery

### Icon Style
- Outline style for UI icons (24x24px base)
- Consistent 2px stroke weight
- Rounded line caps and joins
- Phosphor Icons or Lucide as primary icon sets

### Image Treatment
- Rounded corners (8px default)
- Subtle shadows for elevation
- 16:9 aspect ratio for video thumbnails
- Lazy loading with blur-up effect

## Accessibility

### Focus States
- Visible focus indicators (3px offset)
- High contrast focus colors
- Keyboard navigation support
- Skip links for main content

### Color Contrast
- WCAG AA compliance minimum
- 4.5:1 for normal text
- 3:1 for large text
- 7:1 for enhanced accessibility mode

### Motion Preferences
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Dark Mode Implementation

### Automatic Theme Detection
```javascript
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
```

### Theme Variables
```css
[data-theme="dark"] {
  --bg-primary: var(--dark-bg);
  --bg-surface: var(--dark-surface);
  --text-primary: var(--dark-text);
  --text-secondary: var(--dark-text-secondary);
  --border-color: var(--dark-border);
}
```

## Component Library

### Timeline Item
- Card-based design with hover effects
- Clear visual hierarchy
- Metadata displayed subtly
- AI-generated tags with pill design
- Platform-specific icons

### Search Interface
- Prominent search bar
- Real-time suggestions
- Filter chips below search
- Results with highlighted matches
- Semantic similarity indicators

### Video Player
- Custom controls overlay
- Progress bar with preview
- Quality selector
- Playback speed controls
- Fullscreen support

### AI Features
- Purple accent for AI-powered elements
- Streaming text with typing indicator
- Progress bars for processing
- Confidence scores visualization
- Interactive AI insights

## Responsive Design

### Mobile First
- Base styles for mobile
- Progressive enhancement
- Touch-friendly tap targets (44x44px min)
- Swipe gestures for navigation
- Collapsed navigation menu

### Breakpoint Strategy
```css
/* Mobile */
@media (min-width: 640px) { }

/* Tablet */
@media (min-width: 768px) { }

/* Desktop */
@media (min-width: 1024px) { }

/* Large Desktop */
@media (min-width: 1280px) { }
```

## Performance Considerations

### CSS Optimization
- CSS custom properties for theming
- Minimal specificity
- Logical properties for RTL support
- CSS containment for layout performance

### Loading States
- Skeleton screens for content
- Progressive image loading
- Optimistic UI updates
- Debounced search inputs

## Future Enhancements

### Planned Features
- Customizable themes
- User preference persistence
- Advanced animation controls
- Accessibility preferences panel
- Component playground

### Design Tokens
- JSON-based design tokens
- Automated documentation
- Cross-platform consistency
- Version control for design system