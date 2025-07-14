<script lang="ts">
  interface Props {
    onComplete: () => void;
  }
  
  let { onComplete }: Props = $props();
  
  let currentStep = $state(0);
  
  const steps = [
    {
      title: "Welcome to CodeMirror",
      content: "CodeMirror is your AI-powered repository intelligence assistant. It analyzes your code repositories to detect patterns, suggest improvements, and provide actionable insights.",
      icon: "🔍"
    },
    {
      title: "How It Works",
      content: "Connect your GitHub repositories and CodeMirror will analyze the structure, patterns, and architecture without ever storing your actual code. Only metadata and patterns are processed.",
      icon: "⚙️"
    },
    {
      title: "Privacy First",
      content: "Your code stays private. We only analyze repository structure, file patterns, and dependencies. No source code is ever stored or transmitted to our servers.",
      icon: "🔒"
    },
    {
      title: "CLI Integration",
      content: "Use our command-line tool to analyze repositories locally. Install with 'pip install prsnl-codemirror' and run 'prsnl-codemirror audit /path/to/repo' for offline analysis.",
      icon: "💻"
    },
    {
      title: "Ready to Start",
      content: "Connect your GitHub account to begin. You can always disconnect and delete your data at any time. Let's unlock the intelligence in your repositories!",
      icon: "🚀"
    }
  ];
  
  function nextStep() {
    if (currentStep < steps.length - 1) {
      currentStep++;
    } else {
      complete();
    }
  }
  
  function prevStep() {
    if (currentStep > 0) {
      currentStep--;
    }
  }
  
  function complete() {
    onComplete();
  }
  
  function skip() {
    onComplete();
  }
</script>

<div class="onboarding-overlay">
  <div class="onboarding-modal">
    <!-- Progress Bar -->
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-fill" style="width: {((currentStep + 1) / steps.length) * 100}%"></div>
      </div>
      <span class="progress-text">{currentStep + 1} of {steps.length}</span>
    </div>
    
    <!-- Step Content -->
    <div class="step-content">
      <div class="step-icon">{steps[currentStep].icon}</div>
      <h2>{steps[currentStep].title}</h2>
      <p>{steps[currentStep].content}</p>
    </div>
    
    <!-- Navigation -->
    <div class="navigation">
      <div class="nav-left">
        {#if currentStep > 0}
          <button class="btn-secondary" onclick={prevStep}>
            ← Previous
          </button>
        {/if}
      </div>
      
      <div class="nav-center">
        <div class="dots">
          {#each steps as _, index}
            <div class="dot {index === currentStep ? 'active' : ''} {index < currentStep ? 'completed' : ''}"></div>
          {/each}
        </div>
      </div>
      
      <div class="nav-right">
        <button class="btn-secondary" onclick={skip}>
          Skip
        </button>
        <button class="btn-primary" onclick={nextStep}>
          {currentStep === steps.length - 1 ? 'Get Started' : 'Next →'}
        </button>
      </div>
    </div>
  </div>
</div>

<style>
  .onboarding-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(5px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 2rem;
  }
  
  .onboarding-modal {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1.5rem;
    padding: 3rem;
    max-width: 600px;
    width: 100%;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
    color: white;
  }
  
  /* Progress Bar */
  .progress-container {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 3rem;
  }
  
  .progress-bar {
    flex: 1;
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #60a5fa, #a78bfa);
    border-radius: 2px;
    transition: width 0.3s ease;
  }
  
  .progress-text {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9rem;
    font-weight: 500;
    white-space: nowrap;
  }
  
  /* Step Content */
  .step-content {
    text-align: center;
    margin-bottom: 3rem;
    min-height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  
  .step-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
  }
  
  .step-content h2 {
    margin: 0 0 1.5rem 0;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .step-content p {
    margin: 0;
    font-size: 1.1rem;
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.8);
  }
  
  /* Navigation */
  .navigation {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .nav-left,
  .nav-right {
    display: flex;
    gap: 1rem;
  }
  
  .nav-center {
    flex: 1;
    display: flex;
    justify-content: center;
  }
  
  /* Dots */
  .dots {
    display: flex;
    gap: 0.5rem;
  }
  
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transition: all 0.3s ease;
  }
  
  .dot.active {
    background: #60a5fa;
    transform: scale(1.3);
  }
  
  .dot.completed {
    background: #22c55e;
  }
  
  /* Buttons */
  .btn-primary,
  .btn-secondary {
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    font-size: 0.95rem;
  }
  
  .btn-primary {
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    color: white;
  }
  
  .btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 25px rgba(96, 165, 250, 0.3);
  }
  
  .btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.15);
    color: white;
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .onboarding-overlay {
      padding: 1rem;
    }
    
    .onboarding-modal {
      padding: 2rem;
    }
    
    .step-content h2 {
      font-size: 1.5rem;
    }
    
    .step-content p {
      font-size: 1rem;
    }
    
    .navigation {
      flex-direction: column;
      gap: 1.5rem;
    }
    
    .nav-left,
    .nav-right {
      order: 2;
    }
    
    .nav-center {
      order: 1;
    }
  }
</style>