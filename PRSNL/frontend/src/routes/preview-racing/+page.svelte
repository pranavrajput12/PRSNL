<script lang="ts" type="module">
  import RacingDashboard from '$lib/components/previews/RacingDashboard.svelte';
  import Icon from '$lib/components/Icon.svelte';
</script>

<svelte:head>
  <title>Metabolic Racing Dashboard - PRSNL Preview</title>
</svelte:head>

<div class="preview-page">
  <header class="preview-header">
    <a href="/insights" class="back-button">
      <Icon name="arrow-left" />
      Back to Insights
    </a>
    <h1>Metabolic Racing Dashboard Preview</h1>
    <div class="preview-badge">PREVIEW MODE</div>
  </header>

  <div class="preview-content">
    <RacingDashboard />
  </div>

  <div class="preview-info">
    <h2>🏎️ Metabolic Racing Dashboard</h2>
    <p>
      Experience your learning velocity through an F1-inspired racing dashboard. Track your mental
      performance like a high-speed race.
    </p>
    <ul>
      <li>🏁 Monitor your learning speed in real-time</li>
      <li>⛽ Track mental fuel levels and efficiency</li>
      <li>📊 Compare daily lap times and performance</li>
      <li>🚀 Activate turbo mode during intense learning</li>
    </ul>
  </div>
</div>

<style>
  .preview-page {
    width: 100%;
    height: 100vh;
    background: #000;
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
    border-bottom: 1px solid #dc143c;
  }

  .back-button {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #dc143c;
    text-decoration: none;
    font-family: 'Space Grotesk';
    transition: all 0.3s ease;
  }

  .back-button:hover {
    color: #00ff64;
    transform: translateX(-5px);
  }

  .preview-header h1 {
    font-family: 'Space Grotesk';
    font-size: 24px;
    color: white;
    margin: 0;
  }

  .preview-badge {
    background: #dc143c;
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
    top: 80px;
    right: 20px;
    background: rgba(0, 0, 0, 0.9);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #dc143c;
    color: white;
    font-family: 'Space Grotesk';
    max-width: 400px;
    backdrop-filter: blur(10px);
  }

  .preview-info h2 {
    margin: 0 0 10px 0;
    color: #dc143c;
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
