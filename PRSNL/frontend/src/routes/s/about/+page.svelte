<script>
  import Icon from '$lib/components/Icon.svelte';
</script>

<svelte:head>
  <title>About PRSNL | Your Digital Brain</title>
  <meta name="description" content="PRSNL is a personal knowledge management system that acts as your digital brain, helping you capture, organize, and retrieve information efficiently." />
</svelte:head>

<div class="about-page">
  <div class="hero-section">
    <div class="hero-content">
      <h1>About PRSNL</h1>
      <p class="tagline">Your Personal Knowledge Neural System</p>
    </div>
  </div>

  <div class="content-section">
    <div class="section">
      <h2>What is PRSNL?</h2>
      <p>
        PRSNL (Personal Research & Synapse Neural Link) is a comprehensive personal knowledge 
        management system designed to act as your digital brain. It helps you capture, organize, 
        and retrieve information from various sources, creating meaningful connections between 
        your ideas and content.
      </p>
    </div>

    <div class="section">
      <h2>Key Features</h2>
      <div class="features-grid">
        <div class="feature-card">
          <Icon name="brain" size={32} />
          <h3>Neural Organization</h3>
          <p>Intelligent categorization and tagging system that mimics how your brain organizes information.</p>
        </div>
        <div class="feature-card">
          <Icon name="zap" size={32} />
          <h3>Instant Capture</h3>
          <p>Quickly save articles, videos, notes, and ideas from anywhere with our browser extension.</p>
        </div>
        <div class="feature-card">
          <Icon name="search" size={32} />
          <h3>Smart Search</h3>
          <p>AI-powered search that understands context and finds exactly what you're looking for.</p>
        </div>
        <div class="feature-card">
          <Icon name="trending-up" size={32} />
          <h3>Insights & Analytics</h3>
          <p>Discover patterns in your knowledge and get personalized learning recommendations.</p>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>How It Works</h2>
      <ol class="steps">
        <li>
          <strong>Capture</strong> - Save content from the web, upload files, or create notes directly
        </li>
        <li>
          <strong>Process</strong> - PRSNL automatically extracts key information and generates summaries
        </li>
        <li>
          <strong>Connect</strong> - AI analyzes your content to find relationships and build your knowledge graph
        </li>
        <li>
          <strong>Retrieve</strong> - Access your information through smart search, timeline, or visual interfaces
        </li>
      </ol>
    </div>

    <div class="section">
      <h2>Privacy & Security</h2>
      <p>
        Your knowledge is your own. PRSNL is designed with privacy-first principles:
      </p>
      <ul>
        <li>Self-hosted option available for complete data control</li>
        <li>End-to-end encryption for sensitive content</li>
        <li>No data sharing with third parties</li>
        <li>Regular security audits and updates</li>
      </ul>
    </div>

    <div class="section cta-section">
      <h2>Start Building Your Digital Brain</h2>
      <p>Join thousands of researchers, students, and knowledge workers who trust PRSNL to manage their digital knowledge.</p>
      <div class="cta-buttons">
        <a href="/p/capture" class="btn btn-primary">
          <Icon name="plus" />
          Start Capturing
        </a>
        <a href="/s/docs" class="btn btn-secondary">
          <Icon name="book" />
          Read Documentation
        </a>
      </div>
    </div>
  </div>
</div>

<style>
  .about-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  .hero-section {
    text-align: center;
    padding: 4rem 0;
    margin-bottom: 3rem;
    background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-secondary-light) 100%);
    border-radius: 1rem;
  }

  .hero-content h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: var(--color-primary);
  }

  .tagline {
    font-size: 1.5rem;
    color: var(--color-text-muted);
  }

  .content-section {
    display: flex;
    flex-direction: column;
    gap: 3rem;
  }

  .section {
    background: var(--color-surface);
    padding: 2rem;
    border-radius: 0.75rem;
  }

  .section h2 {
    margin-bottom: 1.5rem;
    color: var(--color-primary);
  }

  .section p {
    line-height: 1.8;
    color: var(--color-text-muted);
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
  }

  .feature-card {
    text-align: center;
    padding: 1.5rem;
    background: var(--color-background);
    border-radius: 0.5rem;
    transition: transform 0.2s;
  }

  .feature-card:hover {
    transform: translateY(-4px);
  }

  .feature-card h3 {
    margin: 1rem 0 0.5rem;
    color: var(--color-text);
  }

  .steps {
    list-style: none;
    counter-reset: step-counter;
    padding: 0;
  }

  .steps li {
    counter-increment: step-counter;
    padding: 1rem 0 1rem 3rem;
    position: relative;
  }

  .steps li::before {
    content: counter(step-counter);
    position: absolute;
    left: 0;
    top: 1rem;
    width: 2rem;
    height: 2rem;
    background: var(--color-primary);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
  }

  ul {
    list-style: none;
    padding: 0;
  }

  ul li {
    padding: 0.5rem 0 0.5rem 2rem;
    position: relative;
  }

  ul li::before {
    content: '✓';
    position: absolute;
    left: 0;
    color: var(--color-success);
    font-weight: bold;
  }

  .cta-section {
    background: var(--color-primary-light);
    text-align: center;
  }

  .cta-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 2rem;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 2rem;
    border-radius: 0.5rem;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
  }

  .btn-primary:hover {
    background: var(--color-primary-dark);
  }

  .btn-secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border: 2px solid var(--color-border);
  }

  .btn-secondary:hover {
    background: var(--color-background);
  }

  @media (max-width: 768px) {
    .hero-content h1 {
      font-size: 2rem;
    }

    .tagline {
      font-size: 1.2rem;
    }

    .features-grid {
      grid-template-columns: 1fr;
    }

    .cta-buttons {
      flex-direction: column;
    }
  }
</style>