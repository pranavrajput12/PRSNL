<script lang="ts">
  import DOMPurify from 'dompurify';
  import { onMount } from 'svelte';
  
  export let content: string = '';
  export let allowedTags: string[] = [
    // Text formatting
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'mark', 'small', 'sub', 'sup',
    // Headings
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    // Lists
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    // Code
    'code', 'pre', 'kbd', 'samp', 'var',
    // Links and media (sanitized)
    'a', 'img',
    // Tables
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
    // Semantic elements
    'blockquote', 'cite', 'q', 'abbr', 'acronym', 'address', 'time',
    // Containers
    'div', 'span', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main',
    // Form elements (read-only)
    'input', 'button', 'select', 'option', 'textarea', 'label', 'fieldset', 'legend',
    // Details/summary
    'details', 'summary'
  ];
  export let allowedAttributes: Record<string, string[]> = {
    '*': ['class', 'id', 'title', 'style', 'data-*'],
    'a': ['href', 'target', 'rel', 'download'],
    'img': ['src', 'alt', 'width', 'height', 'loading', 'decoding'],
    'input': ['type', 'value', 'checked', 'disabled', 'readonly'],
    'button': ['type', 'disabled'],
    'select': ['disabled', 'multiple'],
    'option': ['value', 'selected', 'disabled'],
    'textarea': ['readonly', 'disabled', 'rows', 'cols'],
    'th': ['scope', 'colspan', 'rowspan'],
    'td': ['colspan', 'rowspan'],
    'details': ['open'],
    'time': ['datetime']
  };
  export let allowedSchemes: string[] = ['http', 'https', 'mailto', 'tel', 'ftp'];
  export let stripScripts: boolean = true;
  export let stripEventHandlers: boolean = true;
  
  let sanitizedHTML: string = '';
  let mounted: boolean = false;
  
  // Configure DOMPurify options
  $: if (mounted && content) {
    sanitizeContent();
  }
  
  onMount(() => {
    mounted = true;
    sanitizeContent();
  });
  
  function sanitizeContent() {
    if (!content) {
      sanitizedHTML = '';
      return;
    }
    
    try {
      // Configure DOMPurify
      const config = {
        ALLOWED_TAGS: allowedTags,
        ALLOWED_ATTR: Object.entries(allowedAttributes).reduce((acc, [tag, attrs]) => {
          if (tag === '*') {
            // Global attributes
            attrs.forEach(attr => {
              if (!acc.includes(attr)) acc.push(attr);
            });
          } else {
            // Tag-specific attributes
            attrs.forEach(attr => {
              if (!acc.includes(attr)) acc.push(attr);
            });
          }
          return acc;
        }, [] as string[]),
        ALLOWED_URI_REGEXP: new RegExp(`^(?:(?:${allowedSchemes.join('|')}):|[^a-z]|[a-z+.\\-]+(?:[^a-z+.\\-:]|$))`, 'i'),
        KEEP_CONTENT: true,
        RETURN_DOM: false,
        RETURN_DOM_FRAGMENT: false,
        RETURN_DOM_IMPORT: false,
        SANITIZE_DOM: true,
        FORCE_BODY: false,
        // Security options
        FORBID_TAGS: stripScripts ? ['script', 'object', 'embed', 'applet', 'iframe'] : [],
        FORBID_ATTR: stripEventHandlers ? ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur'] : [],
        // Additional security
        ALLOW_DATA_ATTR: true,
        ALLOW_UNKNOWN_PROTOCOLS: false,
        WHOLE_DOCUMENT: false,
        // Custom hooks for additional security
        SANITIZE_NAMED_PROPS: true
      };
      
      // Add custom hook to sanitize style attributes
      DOMPurify.addHook('afterSanitizeAttributes', function (node) {
        // Sanitize style attributes to prevent CSS injection
        if ('target' in node && node.tagName === 'A') {
          node.setAttribute('target', '_blank');
          node.setAttribute('rel', 'noopener noreferrer');
        }
        
        // Remove potentially dangerous style properties
        if (node.hasAttribute('style')) {
          const style = node.getAttribute('style') || '';
          const safeCSSProps = [
            'color', 'background-color', 'font-size', 'font-weight', 'font-family',
            'text-align', 'text-decoration', 'margin', 'padding', 'border',
            'width', 'height', 'display', 'float', 'clear', 'position',
            'top', 'left', 'right', 'bottom', 'z-index', 'opacity'
          ];
          
          const sanitizedStyle = style
            .split(';')
            .filter(prop => {
              const [property] = prop.split(':').map(p => p.trim().toLowerCase());
              return safeCSSProps.some(safe => property.startsWith(safe));
            })
            .join(';');
          
          if (sanitizedStyle !== style) {
            node.setAttribute('style', sanitizedStyle);
          }
        }
      });
      
      sanitizedHTML = DOMPurify.sanitize(content, config);
      
    } catch (error) {
      console.error('HTML sanitization failed:', error);
      // Fallback to plain text
      sanitizedHTML = content.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
  }
  
  // Cleanup DOMPurify hooks when component is destroyed
  import { onDestroy } from 'svelte';
  onDestroy(() => {
    try {
      DOMPurify.removeAllHooks();
    } catch (e) {
      // Ignore cleanup errors
    }
  });
</script>

<!-- 
  SafeHTML Component
  
  This component safely renders HTML content using DOMPurify to prevent XSS attacks.
  It should be used anywhere we need to render user-generated or external HTML content.
  
  Usage:
  <SafeHTML content={htmlString} />
  
  Advanced usage with custom configuration:
  <SafeHTML 
    content={htmlString}
    allowedTags={['p', 'strong', 'em']}
    allowedAttributes={{'*': ['class'], 'a': ['href']}}
  />
-->

<div class="safe-html-container">
  {@html sanitizedHTML}
</div>

<style>
  .safe-html-container {
    /* Inherit parent styles but provide safe defaults */
    color: inherit;
    font-family: inherit;
    line-height: inherit;
  }
  
  /* Ensure user content can't break layout */
  .safe-html-container :global(*) {
    max-width: 100%;
    box-sizing: border-box;
  }
  
  /* Security: Prevent content from escaping container */
  .safe-html-container :global(iframe),
  .safe-html-container :global(object),
  .safe-html-container :global(embed),
  .safe-html-container :global(applet) {
    display: none !important;
  }
  
  /* Security: Remove any remaining event handlers via CSS */
  .safe-html-container :global([onclick]),
  .safe-html-container :global([onmouseover]),
  .safe-html-container :global([onfocus]),
  .safe-html-container :global([onload]) {
    pointer-events: none !important;
  }
</style>