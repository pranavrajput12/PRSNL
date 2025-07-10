<script lang="ts">
  import DNASequencer from '$lib/components/previews/DNASequencer.svelte';
  import Icon from '$lib/components/Icon.svelte';
</script>

<svelte:head>
  <title>Memory DNA Sequencer - PRSNL Preview</title>
</svelte:head>

<div class="preview-page">
  <header class="preview-header">
    <a href="/insights" class="back-button">
      <Icon name="arrow-left" />
      Back to Insights
    </a>
    <h1>Memory DNA Sequencer Preview</h1>
    <div class="preview-badge">PREVIEW MODE</div>
  </header>
  
  <div class="preview-content">
    <DNASequencer />
  </div>
  
  <div class="preview-info">
    <h2>🧬 Memory DNA Sequencer</h2>
    <p>Explore your knowledge evolution encoded in a living DNA helix. Each base pair represents different content types forming your intellectual genome.</p>
    <ul>
      <li>🔄 Rotate the helix to view different time periods</li>
      <li>🔬 Zoom in to examine individual base pairs</li>
      <li>⚡ Start sequencing to analyze your learning patterns</li>
      <li>🧪 Enable gene splicing to predict knowledge combinations</li>
    </ul>
  </div>
</div>

<style>
  .preview-page {
    width: 100%;
    height: 100vh;
    background: #001122;
    overflow: hidden;
  }
  
  .preview-header {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    z-index: 100;
    border-bottom: 1px solid #00ff64;
  }
  
  .back-button {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #00ff64;
    text-decoration: none;
    font-family: 'Space Grotesk';
    transition: all 0.3s ease;
  }
  
  .back-button:hover {
    color: #4a9eff;
    transform: translateX(-5px);
  }
  
  .preview-header h1 {
    font-family: 'Space Grotesk';
    font-size: 24px;
    color: white;
    margin: 0;
  }
  
  .preview-badge {
    background: #00ff64;
    color: #000;
    padding: 5px 15px;
    border-radius: 20px;
    font-family: 'Space Grotesk';
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
  }
  
  .preview-content {
    width: 100%;
    height: 100%;
  }
  
  .preview-info {
    position: absolute;
    bottom: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.9);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #00ff64;
    color: white;
    font-family: 'Space Grotesk';
    max-width: 400px;
    backdrop-filter: blur(10px);
  }
  
  .preview-info h2 {
    margin: 0 0 10px 0;
    color: #00ff64;
    font-size: 20px;
  }
  
  .preview-info p {
    margin: 0 0 15px 0;
    color: #ccc;
    line-height: 1.6;
  }
  
  .preview-info ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .preview-info li {
    padding: 5px 0;
    color: #999;
    font-size: 14px;
  }
</style>