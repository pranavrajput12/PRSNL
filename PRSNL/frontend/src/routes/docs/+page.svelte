<script>
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';

  let mounted = false;

  onMount(() => {
    mounted = true;
  });
</script>

<svelte:head>
  <title>Documentation - PRSNL Neural Interface Guide</title>
  <meta
    name="description"
    content="Understanding PRSNL's neural interface terminology and brain-computer design language"
  />
</svelte:head>

<div class="docs-container">
  <div class="neural-motherboard-bg">
    <div class="pcb-traces"></div>
    <div class="circuit-nodes">
      <div class="node node-1"></div>
      <div class="node node-2"></div>
      <div class="node node-3"></div>
      <div class="node node-4"></div>
    </div>
  </div>

  <div class="docs-content">
    <div class="docs-header">
      <div class="neural-pulse-indicator">
        <Icon name="brain" size="large" color="#DC143C" />
        <div class="pulse-ring"></div>
      </div>
      <h1>PRSNL Neural Interface Guide</h1>
      <p class="docs-subtitle">Understanding the brain-computer terminology and design language</p>
    </div>

    <div class="documentation-grid">
      <div class="doc-section neural-terminology">
        <div class="section-header">
          <Icon name="brain" size="medium" color="#DC143C" />
          <h2>Neural Terminology</h2>
        </div>

        <div class="term-explanations">
          <div class="term-card">
            <div class="term-icon">
              <Icon name="memory" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="term-content">
              <h3>Memory Traces</h3>
              <p class="term-definition">
                Each saved item in PRSNL is called a "Memory Trace" - representing how our brain
                stores information as neural pathways.
              </p>
              <p class="term-simple">In simple terms: Your saved links, notes, and content</p>
            </div>
          </div>

          <div class="term-card">
            <div class="term-icon">
              <Icon name="network" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="term-content">
              <h3>Trace Network</h3>
              <p class="term-definition">
                Your complete collection of Memory Traces forms your "Trace Network" - like how
                memories connect in your brain.
              </p>
              <p class="term-simple">In simple terms: Your entire personal knowledge base</p>
            </div>
          </div>

          <div class="term-card">
            <div class="term-icon">
              <Icon name="search" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="term-content">
              <h3>Neural Interface Scanner</h3>
              <p class="term-definition">
                The search system that uses three brain-inspired modes to find information in your
                Trace Network.
              </p>
              <p class="term-simple">In simple terms: Smart search with different search styles</p>
            </div>
          </div>

          <div class="term-card">
            <div class="term-icon">
              <Icon name="cpu" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="term-content">
              <h3>Neural Processors</h3>
              <p class="term-definition">
                The main feature cards designed like CPU processors - each handles different aspects
                of your knowledge management.
              </p>
              <p class="term-simple">
                In simple terms: Main feature buttons (Ingest, Cognitive Map, etc.)
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="doc-section search-modes">
        <div class="section-header">
          <Icon name="brain-circuit" size="medium" color="#DC143C" />
          <h2>Search Modes</h2>
        </div>

        <div class="mode-explanations">
          <div class="mode-card prefrontal">
            <div class="mode-region">
              <div class="region-activity prefrontal-activity"></div>
              <span class="region-label">Prefrontal</span>
            </div>
            <div class="mode-content">
              <h3>Logical Processing</h3>
              <p class="mode-description">
                Searches for exact keywords and phrases in your Memory Traces.
              </p>
              <p class="mode-simple">Best for: Finding specific terms, titles, or exact phrases</p>
            </div>
          </div>

          <div class="mode-card hippocampus">
            <div class="mode-region">
              <div class="region-activity hippocampus-activity"></div>
              <span class="region-label">Hippocampus</span>
            </div>
            <div class="mode-content">
              <h3>Memory & Associations</h3>
              <p class="mode-description">
                Understands meaning and finds related content even with different words.
              </p>
              <p class="mode-simple">
                Best for: Finding related topics, concepts, or similar ideas
              </p>
            </div>
          </div>

          <div class="mode-card amygdala">
            <div class="mode-region">
              <div class="region-activity amygdala-activity"></div>
              <span class="region-label">Amygdala</span>
            </div>
            <div class="mode-content">
              <h3>Intuitive Connections</h3>
              <p class="mode-description">
                Combines both logical and associative search for comprehensive results.
              </p>
              <p class="mode-simple">
                Best for: Broad exploration and discovering unexpected connections
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="doc-section navigation-menu">
        <div class="section-header">
          <Icon name="navigation" size="medium" color="#DC143C" />
          <h2>Navigation Menu</h2>
        </div>

        <div class="navigation-explanations">
          <div class="nav-card">
            <div class="nav-icon">
              <Icon name="brain" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="nav-content">
              <h3>Neural Nest</h3>
              <p class="nav-definition">
                The main dashboard and command center for your entire knowledge network.
              </p>
              <p class="nav-simple">In simple terms: Your home page with overview and search</p>
            </div>
          </div>

          <div class="nav-card">
            <div class="nav-icon">
              <Icon name="ingest" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="nav-content">
              <h3>Ingest</h3>
              <p class="nav-definition">
                Data intake processor for capturing and storing new Memory Traces from various
                sources.
              </p>
              <p class="nav-simple">In simple terms: Add new content (links, notes, files)</p>
            </div>
          </div>

          <div class="nav-card">
            <div class="nav-icon">
              <Icon name="thought-stream" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="nav-content">
              <h3>Thought Stream</h3>
              <p class="nav-definition">
                Temporal flow visualization of your Memory Traces organized by time and context.
              </p>
              <p class="nav-simple">In simple terms: Timeline view of your saved content</p>
            </div>
          </div>

          <div class="nav-card">
            <div class="nav-icon">
              <Icon name="cognitive-map" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="nav-content">
              <h3>Cognitive Map</h3>
              <p class="nav-definition">
                Pattern recognition system that reveals connections and insights within your Trace
                Network.
              </p>
              <p class="nav-simple">In simple terms: Analytics and insights about your knowledge</p>
            </div>
          </div>

          <div class="nav-card">
            <div class="nav-icon">
              <Icon name="mind-palace" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="nav-content">
              <h3>Mind Palace</h3>
              <p class="nav-definition">
                AI-powered conversation interface for interactive dialogue with your knowledge
                network.
              </p>
              <p class="nav-simple">In simple terms: Chat with your knowledge using AI</p>
            </div>
          </div>

          <div class="nav-card">
            <div class="nav-icon">
              <Icon name="visual-cortex" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="nav-content">
              <h3>Visual Cortex</h3>
              <p class="nav-definition">
                Specialized processor for visual Memory Traces including videos, images, and media
                content.
              </p>
              <p class="nav-simple">In simple terms: View and manage your videos and images</p>
            </div>
          </div>

          <div class="nav-card">
            <div class="nav-icon">
              <Icon name="knowledge-sync" size="small" color="var(--synapse-teal)" />
            </div>
            <div class="nav-content">
              <h3>Knowledge Sync</h3>
              <p class="nav-definition">
                Batch processing system for importing large datasets into your Trace Network.
              </p>
              <p class="nav-simple">
                In simple terms: Import lots of data at once (bookmarks, files, etc.)
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="doc-section getting-started">
        <div class="section-header">
          <Icon name="rocket" size="medium" color="#DC143C" />
          <h2>Getting Started</h2>
        </div>

        <div class="getting-started-steps">
          <div class="step-card">
            <div class="step-number">1</div>
            <div class="step-content">
              <h3>Start Capturing</h3>
              <p>
                Use the <strong>INGEST</strong> processor to add your first Memory Traces - links, notes,
                or any content you want to remember.
              </p>
            </div>
          </div>

          <div class="step-card">
            <div class="step-number">2</div>
            <div class="step-content">
              <h3>Explore Your Network</h3>
              <p>
                Use the <strong>Neural Interface Scanner</strong> to search through your growing Trace
                Network using different brain-inspired search modes.
              </p>
            </div>
          </div>

          <div class="step-card">
            <div class="step-number">3</div>
            <div class="step-content">
              <h3>Visualize Connections</h3>
              <p>
                Use the <strong>COGNITIVE MAP</strong> processor to see how your Memory Traces connect
                and relate to each other.
              </p>
            </div>
          </div>

          <div class="step-card">
            <div class="step-number">4</div>
            <div class="step-content">
              <h3>Organize & Chat</h3>
              <p>
                Use the <strong>MIND PALACE</strong> processor to organize your traces and have AI-powered
                conversations with your knowledge.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .docs-container {
    min-height: 100vh;
    position: relative;
    background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
    overflow-x: hidden;
  }

  .neural-motherboard-bg {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    opacity: 0.1;
    pointer-events: none;
  }

  .pcb-traces {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      repeating-linear-gradient(0deg, transparent, transparent 40px, var(--synapse-teal) 40px, var(--synapse-teal) 42px),
      repeating-linear-gradient(90deg, transparent, transparent 40px, var(--synapse-teal) 40px, var(--synapse-teal) 42px);
  }

  .circuit-nodes {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .node {
    position: absolute;
    width: 20px;
    height: 20px;
    background: radial-gradient(circle, #dc143c, #b91c3c);
    border-radius: 50%;
    border: 2px solid #dc143c;
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
    animation: node-pulse 3s ease-in-out infinite;
  }

  .node-1 {
    top: 20%;
    left: 15%;
    animation-delay: 0s;
  }
  .node-2 {
    top: 60%;
    left: 80%;
    animation-delay: 1s;
  }
  .node-3 {
    top: 30%;
    left: 70%;
    animation-delay: 2s;
  }
  .node-4 {
    top: 80%;
    left: 25%;
    animation-delay: 1.5s;
  }

  @keyframes node-pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 0.6;
    }
    50% {
      transform: scale(1.3);
      opacity: 0.9;
    }
  }

  .docs-content {
    position: relative;
    z-index: 10;
    max-width: 1200px;
    margin: 0 auto;
    padding: 4rem 2rem;
  }

  .docs-header {
    text-align: center;
    margin-bottom: 4rem;
  }

  .neural-pulse-indicator {
    position: relative;
    display: inline-block;
    margin-bottom: 2rem;
  }

  .pulse-ring {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60px;
    height: 60px;
    border: 2px solid #dc143c;
    border-radius: 50%;
    opacity: 0.6;
    animation: pulse-expand 2s ease-in-out infinite;
  }

  @keyframes pulse-expand {
    0%,
    100% {
      transform: translate(-50%, -50%) scale(1);
      opacity: 0.6;
    }
    50% {
      transform: translate(-50%, -50%) scale(1.5);
      opacity: 0.2;
    }
  }

  .docs-header h1 {
    color: #dc143c;
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0 0 1rem 0;
    text-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
  }

  .docs-subtitle {
    color: var(--text-muted);
    font-size: 1.2rem;
    margin: 0;
    opacity: 0.8;
  }

  .documentation-grid {
    display: grid;
    gap: 3rem;
  }

  .doc-section {
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.9), rgba(42, 42, 42, 0.9));
    border: 1px solid rgba(220, 20, 60, 0.2);
    border-radius: 16px;
    padding: 2rem;
    backdrop-filter: blur(10px);
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(220, 20, 60, 0.2);
  }

  .section-header h2 {
    color: var(--text-primary);
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
  }

  .term-explanations,
  .mode-explanations,
  .navigation-explanations {
    display: grid;
    gap: 1.5rem;
  }

  .term-card,
  .mode-card,
  .nav-card {
    display: flex;
    gap: 1rem;
    padding: 1.5rem;
    background: rgba(26, 26, 26, 0.5);
    border: 1px solid rgba(220, 20, 60, 0.1);
    border-radius: 12px;
    transition: all 0.3s ease;
  }

  .term-card:hover,
  .mode-card:hover,
  .nav-card:hover {
    border-color: rgba(220, 20, 60, 0.3);
    transform: translateY(-2px);
  }

  .term-icon,
  .nav-icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    background: radial-gradient(circle, rgba(78, 205, 196, 0.1), rgba(78, 205, 196, 0.05));
    border: 1px solid rgba(78, 205, 196, 0.3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .term-content h3,
  .nav-content h3 {
    color: var(--text-primary);
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
  }

  .term-definition,
  .nav-definition {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0 0 0.5rem 0;
    line-height: 1.4;
  }

  .term-simple,
  .nav-simple {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin: 0;
    font-style: italic;
  }

  .mode-card {
    align-items: center;
  }

  .mode-region {
    position: relative;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    border: 2px solid #dc143c;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
  }

  .region-activity {
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    animation: region-pulse 2s ease-in-out infinite;
  }

  .prefrontal-activity {
    background: radial-gradient(circle, rgba(0, 150, 255, 0.3), transparent 70%);
  }

  .hippocampus-activity {
    background: radial-gradient(circle, rgba(78, 205, 196, 0.3), transparent 70%);
  }

  .amygdala-activity {
    background: radial-gradient(circle, rgba(255, 100, 0, 0.3), transparent 70%);
  }

  @keyframes region-pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 0.6;
    }
    50% {
      transform: scale(1.2);
      opacity: 0.9;
    }
  }

  .region-label {
    position: relative;
    z-index: 2;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-primary);
    text-align: center;
  }

  .mode-content h3 {
    color: var(--text-primary);
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
  }

  .mode-description {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0 0 0.5rem 0;
    line-height: 1.4;
  }

  .mode-simple {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin: 0;
    font-weight: 600;
  }

  .getting-started-steps {
    display: grid;
    gap: 1.5rem;
  }

  .step-card {
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    padding: 1.5rem;
    background: rgba(26, 26, 26, 0.5);
    border: 1px solid rgba(220, 20, 60, 0.1);
    border-radius: 12px;
    transition: all 0.3s ease;
  }

  .step-card:hover {
    border-color: rgba(220, 20, 60, 0.3);
    transform: translateY(-2px);
  }

  .step-number {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    background: radial-gradient(circle, #dc143c, #b91c3c);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    color: white;
    font-size: 1.2rem;
    box-shadow: 0 0 15px rgba(220, 20, 60, 0.4);
  }

  .step-content h3 {
    color: var(--text-primary);
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
  }

  .step-content p {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
    line-height: 1.4;
  }

  .step-content strong {
    color: #dc143c;
    font-weight: 700;
  }

  @media (max-width: 768px) {
    .docs-content {
      padding: 2rem 1rem;
    }

    .docs-header h1 {
      font-size: 2rem;
    }

    .term-card,
    .mode-card,
    .step-card {
      flex-direction: column;
      text-align: center;
    }

    .mode-card {
      align-items: center;
    }

    .step-card {
      align-items: center;
    }
  }
</style>
