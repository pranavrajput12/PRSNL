<script lang="ts">
  import NeuralGalaxy from '$lib/components/previews/NeuralGalaxy.svelte';
  import Icon from '$lib/components/Icon.svelte';
</script>

<svelte:head>
  <title>Neural Galaxy Explorer - PRSNL Preview</title>
</svelte:head>

<div class="preview-page">
  <header class="preview-header">
    <a href="/insights" class="back-button">
      <Icon name="arrow-left" />
      Back to Insights
    </a>
    <h1>Neural Galaxy Explorer Preview</h1>
    <div class="preview-badge">PREVIEW MODE</div>
  </header>
  
  <div class="preview-content">
    <NeuralGalaxy />
  </div>
  
  <div class="preview-info">
    <h2>🌌 Neural Galaxy Explorer</h2>
    <p>Navigate through your knowledge constellation in 3D space. Each topic forms a solar system with orbiting content planets.</p>
    <ul>
      <li>🎮 Use the zoom slider to navigate from galaxy view to individual planets</li>
      <li>⏰ Travel through time to see how your knowledge evolved</li>
      <li>🎯 Click on systems to explore deeper</li>
      <li>🎵 Ambient space music creates an immersive experience</li>
    </ul>
  </div>
</div>

<style>
  .preview-page {
    width: 100%;
    height: 100vh;
    background: #0a0a0a;
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
    border-bottom: 1px solid #333;
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
    color: #DC143C;
    transform: translateX(-5px);
  }
  
  .preview-header h1 {
    font-family: 'Space Grotesk';
    font-size: 24px;
    color: white;
    margin: 0;
  }
  
  .preview-badge {
    background: #DC143C;
    color: white;
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
    border: 1px solid #333;
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