<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import Icon from './Icon.svelte';

  export let mode: any;
  export let onComplete: () => void;

  // Prevent rendering if mode is not properly provided
  // This fixes the issue where component renders on non-chat pages without valid props
  $: isValidMode = mode && mode.id && typeof onComplete === 'function';

  let currentSlide = 0;

  const modeDetails = {
    general: {
      slides: [
        {
          title: 'General Mode',
          subtitle: 'Your balanced thinking companion',
          description:
            'General mode provides balanced, comprehensive responses that consider multiple perspectives.',
          features: [
            'Balanced analysis of your knowledge',
            'Comprehensive overviews',
            'Multi-perspective insights',
            'Ideal for everyday questions',
          ],
          icon: 'message-circle',
        },
        {
          title: 'How to use General Mode',
          subtitle: 'Perfect for everyday knowledge exploration',
          examples: [
            {
              query: 'What are my notes on productivity?',
              description: 'Get a balanced overview of all your productivity-related content',
            },
            {
              query: 'Summarize my learnings from last week',
              description: 'Receive a comprehensive summary of recent knowledge',
            },
            {
              query: 'Connect my ideas about AI and business',
              description: 'Find relationships between different topics in your knowledge base',
            },
          ],
          tip: 'Use General mode when you want well-rounded insights without a specific focus',
        },
      ],
    },
    research: {
      slides: [
        {
          title: 'Research Mode',
          subtitle: 'Deep dive into knowledge exploration',
          description:
            'Research mode helps you thoroughly analyze topics, find patterns, and discover connections across your knowledge base.',
          features: [
            'Deep pattern recognition',
            'Cross-topic connections',
            'Comprehensive analysis',
            'Source-backed insights',
          ],
          icon: 'search',
        },
        {
          title: 'How to use Research Mode',
          subtitle: 'For thorough investigation and discovery',
          examples: [
            {
              query: 'Analyze all my notes on machine learning',
              description:
                'Get comprehensive analysis with patterns, gaps, and connections to other topics',
            },
            {
              query: 'Find connections between my business and tech notes',
              description:
                'Discover how different topics in your knowledge base relate to each other',
            },
            {
              query: 'What patterns exist in my saved articles?',
              description: 'Identify trends and recurring themes across your content',
            },
          ],
          tip: 'Use Research mode when investigating topics deeply or finding hidden connections',
        },
      ],
    },
    learning: {
      slides: [
        {
          title: 'Learning Mode',
          subtitle: 'Optimize knowledge retention',
          description:
            'Learning mode helps you understand and retain information more effectively through educational techniques.',
          features: [
            'Simplified explanations',
            'Step-by-step breakdowns',
            'Memory aids and mnemonics',
            'Active recall suggestions',
          ],
          icon: 'graduation-cap',
        },
        {
          title: 'How to use Learning Mode',
          subtitle: 'Transform your knowledge into lasting understanding',
          examples: [
            {
              query: 'Help me understand my notes on quantum physics',
              description: 'Get simplified explanations with analogies and examples',
            },
            {
              query: 'Create flashcards from my study materials',
              description: 'Generate study aids from your saved content',
            },
            {
              query: 'Quiz me on my marketing knowledge',
              description: 'Test your understanding with questions based on your notes',
            },
          ],
          tip: 'Use Learning mode when studying new topics or reviewing for better retention',
        },
      ],
    },
    creative: {
      slides: [
        {
          title: 'Creative Mode',
          subtitle: 'Unlock innovative connections',
          description:
            'Creative mode generates novel ideas and unexpected connections between concepts in your knowledge base.',
          features: [
            'Innovative idea generation',
            'Unexpected connections',
            'Creative problem solving',
            'Lateral thinking approaches',
          ],
          icon: 'lightbulb',
        },
        {
          title: 'How to use Creative Mode',
          subtitle: 'Spark innovation from your knowledge',
          examples: [
            {
              query: 'Combine my cooking and tech notes in creative ways',
              description: 'Discover innovative connections between unrelated topics',
            },
            {
              query: 'Generate new business ideas from my interests',
              description: 'Create novel concepts by combining your various interests',
            },
            {
              query: 'What if scenarios based on my project notes',
              description: 'Explore creative possibilities and alternative approaches',
            },
          ],
          tip: 'Use Creative mode when brainstorming, problem-solving, or seeking inspiration',
        },
      ],
    },
  };

  $: slides = modeDetails[mode.id]?.slides || [];

  function nextSlide() {
    if (currentSlide < slides.length - 1) {
      currentSlide++;
    } else {
      onComplete();
    }
  }

  function previousSlide() {
    if (currentSlide > 0) {
      currentSlide--;
    }
  }

  function skip() {
    onComplete();
  }
</script>

{#if isValidMode}
  <div class="onboarding-overlay" transition:fade={{ duration: 300 }}>
    <div class="onboarding-container" transition:fly={{ y: 50, duration: 500 }}>
      <button class="skip-button" on:click={skip}>
        Skip
        <Icon name="x" size={16} />
      </button>

      {#if slides[currentSlide]}
        <div class="slide-content">
          {#if slides[currentSlide].icon}
            <div class="mode-icon-large" style="background: {mode.color}">
              <Icon name={slides[currentSlide].icon} size={48} color="white" />
            </div>
          {/if}

          <h2>{slides[currentSlide].title}</h2>
          <p class="subtitle">{slides[currentSlide].subtitle}</p>

          {#if slides[currentSlide].description}
            <p class="description">{slides[currentSlide].description}</p>
          {/if}

          {#if slides[currentSlide].features}
            <div class="features-grid">
              {#each slides[currentSlide].features as feature}
                <div class="feature-item">
                  <Icon name="check" size={16} color={mode.color} />
                  <span>{feature}</span>
                </div>
              {/each}
            </div>
          {/if}

          {#if slides[currentSlide].examples}
            <div class="examples-section">
              <h3>Example Uses:</h3>
              {#each slides[currentSlide].examples as example}
                <div class="example-card">
                  <div class="example-query">
                    <Icon name="message-square" size={16} />
                    "{example.query}"
                  </div>
                  <p class="example-description">{example.description}</p>
                </div>
              {/each}
            </div>
          {/if}

          {#if slides[currentSlide].tip}
            <div class="tip-box" style="border-color: {mode.color}">
              <Icon name="info" size={20} color={mode.color} />
              <p>{slides[currentSlide].tip}</p>
            </div>
          {/if}
        </div>
      {/if}

      <div class="navigation">
        <div class="dots">
          {#each slides as _, index}
            <button
              class="dot {currentSlide === index ? 'active' : ''}"
              style="background: {currentSlide === index ? mode.color : 'rgba(255, 255, 255, 0.3)'}"
              on:click={() => (currentSlide = index)}
            />
          {/each}
        </div>

        <div class="nav-buttons">
          {#if currentSlide > 0}
            <button class="nav-btn secondary" on:click={previousSlide}>
              <Icon name="arrow-left" size={16} />
              Previous
            </button>
          {/if}

          <button class="nav-btn primary" style="background: {mode.color}" on:click={nextSlide}>
            {currentSlide === slides.length - 1 ? 'Get Started' : 'Next'}
            <Icon name="arrow-right" size={16} />
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .onboarding-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    backdrop-filter: blur(20px);
    padding: 2rem;
  }

  .onboarding-container {
    background: #1a1a1a;
    border-radius: 2rem;
    padding: 3rem;
    max-width: 650px;
    width: 100%;
    max-height: 85vh;
    overflow-y: auto;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
    position: relative;
  }

  .skip-button {
    position: absolute;
    top: 1.5rem;
    right: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 2rem;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .skip-button:hover {
    background: rgba(255, 255, 255, 0.15);
    color: white;
  }

  .slide-content {
    text-align: center;
    animation: slideIn 0.5s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .mode-icon-large {
    width: 100px;
    height: 100px;
    margin: 0 auto 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  }

  h2 {
    font-size: 2.5rem;
    margin: 0 0 0.5rem;
    color: white;
    font-weight: 700;
  }

  .subtitle {
    font-size: 1.25rem;
    color: rgba(255, 255, 255, 0.8);
    margin: 0 0 1.5rem;
    font-weight: 500;
  }

  .description {
    font-size: 1.125rem;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.6;
    margin: 0 0 2rem;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
    text-align: left;
  }

  .feature-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .feature-item span {
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.95rem;
  }

  .examples-section {
    margin: 2rem 0;
    text-align: left;
  }

  .examples-section h3 {
    font-size: 1.25rem;
    color: white;
    margin: 0 0 1rem;
  }

  .example-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 1.25rem;
    margin-bottom: 1rem;
  }

  .example-query {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: white;
    font-weight: 600;
    margin-bottom: 0.5rem;
    font-style: italic;
  }

  .example-description {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.875rem;
    margin: 0;
    padding-left: 1.5rem;
  }

  .tip-box {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid;
    border-radius: 1rem;
    margin: 2rem 0;
    text-align: left;
  }

  .tip-box p {
    margin: 0;
    color: rgba(255, 255, 255, 0.9);
    line-height: 1.5;
  }

  .navigation {
    margin-top: 3rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
  }

  .dots {
    display: flex;
    gap: 0.5rem;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    border: none;
    cursor: pointer;
    transition: all 0.3s;
  }

  .dot.active {
    width: 24px;
    border-radius: 4px;
  }

  .nav-buttons {
    display: flex;
    gap: 1rem;
  }

  .nav-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 2rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .nav-btn.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .nav-btn.secondary:hover {
    background: rgba(255, 255, 255, 0.15);
  }

  .nav-btn.primary {
    color: white;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }

  .nav-btn.primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 30px rgba(0, 0, 0, 0.4);
  }

  /* Scrollbar */
  .onboarding-container::-webkit-scrollbar {
    width: 6px;
  }

  .onboarding-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
  }

  .onboarding-container::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
  }

  .onboarding-container::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  @media (max-width: 768px) {
    .onboarding-container {
      padding: 2rem;
    }

    h2 {
      font-size: 2rem;
    }

    .features-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
