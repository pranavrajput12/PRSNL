<script>
  export let url = '';

  let domain = '';
  let favicon = '';
  let isLoading = false;
  let error = null;

  $: if (url) {
    parseUrl(url);
  }

  function parseUrl(urlString) {
    try {
      if (!urlString.startsWith('http://') && !urlString.startsWith('https://')) {
        urlString = 'https://' + urlString;
      }

      const urlObj = new URL(urlString);
      domain = urlObj.hostname;
      favicon = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
    } catch (err) {
      domain = '';
      favicon = '';
      error = 'Invalid URL';
    }
  }
</script>

{#if url && domain}
  <div class="url-preview" class:loading={isLoading}>
    <div class="favicon">
      <img src={favicon} alt={domain} on:error={() => (favicon = '/favicon-fallback.svg')} />
    </div>
    <div class="url-info">
      <div class="domain">{domain}</div>
      <div class="full-url">{url}</div>
    </div>
  </div>
{/if}

<style>
  .url-preview {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 1rem;
    transition: all 0.2s ease;
  }

  .url-preview:hover {
    border-color: var(--accent);
  }

  .favicon {
    width: 24px;
    height: 24px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .favicon img {
    max-width: 100%;
    max-height: 100%;
    border-radius: 4px;
  }

  .url-info {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .domain {
    font-weight: 500;
    color: var(--text-primary);
  }

  .full-url {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .loading {
    opacity: 0.7;
  }
</style>
