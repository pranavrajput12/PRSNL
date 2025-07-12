<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from './Icon.svelte';

  let mounted = false;
  let scanlineAnimation = true;

  onMount(() => {
    mounted = true;
  });
</script>

<div class="mac-crt-monitor">
  <!-- Mac Classic Housing -->
  <div class="mac-housing">
    <!-- Screen Bezel -->
    <div class="screen-bezel">
      <!-- CRT Screen -->
      <div class="crt-screen">
        <!-- Scanlines overlay -->
        {#if scanlineAnimation}
          <div class="scanlines"></div>
        {/if}

        <!-- Screen Content -->
        <div class="screen-content">
          <!-- NEURAL MOTHERBOARD CONSOLE -->
          <div class="motherboard-console">
            <div class="console-header">
              <div class="console-brand">NEURAL-OS MAINFRAME</div>
              <div class="console-indicators">
                <div class="indicator">
                  <div class="indicator-light"></div>
                  <span>PWR</span>
                </div>
                <div class="indicator">
                  <div class="indicator-light red"></div>
                  <span>AI</span>
                </div>
                <div class="indicator">
                  <div class="indicator-light orange"></div>
                  <span>NET</span>
                </div>
              </div>
            </div>

            <div class="console-content">
              <!-- CREATIVE BRAIN NEURAL NETWORK ANIMATION -->
              <div class="neural-brain-animation">
                <!-- Brain Hemispheres -->
                <div class="brain-hemisphere brain-left"></div>
                <div class="brain-hemisphere brain-right"></div>

                <!-- Neural Network -->
                <div class="neural-network">
                  <!-- Neurons -->
                  {#each Array(10) as _, i}
                    <div class="neuron neuron-{i + 1}"></div>
                  {/each}

                  <!-- Synapses -->
                  {#each Array(5) as _, i}
                    <div class="synapse synapse-{i + 1}"></div>
                  {/each}
                </div>

                <!-- Memory Bubbles -->
                <div class="memory-bubbles">
                  {#each Array(3) as _, i}
                    <div class="memory-bubble bubble-{i + 1}"></div>
                  {/each}
                </div>

                <!-- Data Packets -->
                <div class="data-packets">
                  {#each Array(4) as _, i}
                    <div class="data-packet packet-{i + 1}"></div>
                  {/each}
                </div>
              </div>

              <div class="neural-header-section">
                <div class="system-badge">
                  <Icon name="sparkles" size="small" />
                  <span>AI-Powered Knowledge Vault</span>
                </div>

                <h1 class="motherboard-title">
                  Your Second Brain,<br />Supercharged
                </h1>

                <p class="neural-description">
                  Capture anything with a single keystroke. Search everything instantly.<br />
                  Never lose a brilliant idea again.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Screen reflection -->
        <div class="screen-reflection"></div>
      </div>
    </div>

    <!-- Mac Classic Base -->
    <div class="mac-base">
      <div class="ventilation-grilles">
        {#each Array(12) as _, i}
          <div class="grille-line"></div>
        {/each}
      </div>
    </div>

    <!-- Apple Logo -->
    <div class="apple-logo"></div>
  </div>
</div>

<style>
  .mac-crt-monitor {
    position: relative;
    max-width: 600px;
    margin: 0 auto;
    perspective: 1000px;
  }

  .mac-housing {
    position: relative;
    background: linear-gradient(135deg, #f5f5dc 0%, #e8e8dc 50%, #d0d0c0 100%);
    border-radius: 20px 20px 0 0;
    box-shadow:
      0 20px 60px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.3),
      inset 0 -1px 0 rgba(0, 0, 0, 0.1);
    padding: 40px 40px 20px 40px;
    transform: rotateX(-5deg) rotateY(2deg);
    transition: transform 0.3s ease;
  }

  .mac-housing:hover {
    transform: rotateX(-3deg) rotateY(1deg) scale(1.02);
  }

  .screen-bezel {
    background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
    border-radius: 15px;
    padding: 25px;
    box-shadow:
      inset 0 5px 15px rgba(0, 0, 0, 0.8),
      inset 0 -2px 5px rgba(255, 255, 255, 0.1);
  }

  .crt-screen {
    position: relative;
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    border-radius: 10px;
    min-height: 400px;
    overflow: hidden;
    box-shadow:
      inset 0 0 50px rgba(78, 205, 196, 0.1),
      inset 0 0 100px rgba(0, 0, 0, 0.8);
  }

  .scanlines {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(78, 205, 196, 0.03) 2px,
      rgba(78, 205, 196, 0.03) 4px
    );
    pointer-events: none;
    z-index: 3;
    animation: scanlineFlicker 0.1s infinite linear;
  }

  @keyframes scanlineFlicker {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.98;
    }
    100% {
      opacity: 1;
    }
  }

  .screen-content {
    position: relative;
    z-index: 2;
    padding: 30px;
    height: 100%;
    color: var(--synapse-teal);
    font-family: 'Monaco', 'Menlo', monospace;
  }

  .screen-reflection {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.1) 0%,
      transparent 30%,
      transparent 70%,
      rgba(255, 255, 255, 0.05) 100%
    );
    pointer-events: none;
    z-index: 4;
  }

  .mac-base {
    background: linear-gradient(135deg, #e8e8dc 0%, #d0d0c0 100%);
    height: 60px;
    border-radius: 0 0 25px 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow:
      0 10px 30px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }

  .ventilation-grilles {
    display: flex;
    gap: 3px;
    opacity: 0.6;
  }

  .grille-line {
    width: 2px;
    height: 20px;
    background: linear-gradient(180deg, #999 0%, #666 100%);
    border-radius: 1px;
  }

  .apple-logo {
    position: absolute;
    top: 15px;
    left: 50%;
    transform: translateX(-50%);
    width: 20px;
    height: 24px;
    background: #999;
    border-radius: 50% 0 50% 50%;
    transform: translateX(-50%) rotate(-45deg);
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.3);
  }

  /* Motherboard Console Styles (adapted for CRT) */
  .motherboard-console {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .console-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(78, 205, 196, 0.3);
  }

  .console-brand {
    font-size: 1rem;
    font-weight: 700;
    color: var(--synapse-teal);
    text-shadow: 0 0 10px var(--synapse-teal);
    font-family: 'Monaco', monospace;
    letter-spacing: 2px;
  }

  .console-indicators {
    display: flex;
    gap: 15px;
  }

  .indicator {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.7rem;
    color: var(--synapse-teal);
  }

  .indicator-light {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--synapse-teal);
    box-shadow: 0 0 8px var(--synapse-teal);
    animation: pulse 2s infinite;
  }

  .indicator-light.red {
    background: #ff0000;
    box-shadow: 0 0 8px #ff0000;
  }

  .indicator-light.orange {
    background: #ff8800;
    box-shadow: 0 0 8px #ff8800;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.6;
    }
  }

  .console-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .neural-brain-animation {
    position: relative;
    height: 80px;
    margin-bottom: 20px;
    overflow: hidden;
  }

  .brain-hemisphere {
    position: absolute;
    width: 40px;
    height: 60px;
    background: rgba(78, 205, 196, 0.2);
    border: 2px solid var(--synapse-teal);
    border-radius: 20px 0 0 20px;
    top: 10px;
  }

  .brain-left {
    left: 50%;
    transform: translateX(-45px);
  }

  .brain-right {
    left: 50%;
    transform: translateX(5px) scaleX(-1);
  }

  .neural-network {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .neuron {
    position: absolute;
    width: 6px;
    height: 6px;
    background: var(--synapse-teal);
    border-radius: 50%;
    animation: neuronPulse 3s infinite;
  }

  .neuron-1 {
    top: 20%;
    left: 20%;
    animation-delay: 0s;
  }
  .neuron-2 {
    top: 40%;
    left: 35%;
    animation-delay: 0.3s;
  }
  .neuron-3 {
    top: 60%;
    left: 25%;
    animation-delay: 0.6s;
  }
  .neuron-4 {
    top: 30%;
    left: 65%;
    animation-delay: 0.9s;
  }
  .neuron-5 {
    top: 50%;
    left: 75%;
    animation-delay: 1.2s;
  }
  .neuron-6 {
    top: 70%;
    left: 60%;
    animation-delay: 1.5s;
  }
  .neuron-7 {
    top: 15%;
    left: 80%;
    animation-delay: 1.8s;
  }
  .neuron-8 {
    top: 45%;
    left: 10%;
    animation-delay: 2.1s;
  }
  .neuron-9 {
    top: 25%;
    left: 45%;
    animation-delay: 2.4s;
  }
  .neuron-10 {
    top: 55%;
    left: 40%;
    animation-delay: 2.7s;
  }

  @keyframes neuronPulse {
    0%,
    100% {
      transform: scale(1);
      box-shadow: 0 0 5px var(--synapse-teal);
    }
    50% {
      transform: scale(1.5);
      box-shadow: 0 0 15px var(--synapse-teal);
    }
  }

  .system-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--synapse-teal);
    font-size: 0.8rem;
    margin-bottom: 10px;
    opacity: 0.8;
  }

  .motherboard-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--synapse-teal);
    text-shadow: 0 0 15px var(--synapse-teal);
    margin: 15px 0;
    line-height: 1.2;
    font-family: 'Monaco', monospace;
  }

  .neural-description {
    color: rgba(78, 205, 196, 0.8);
    font-size: 0.9rem;
    line-height: 1.4;
    margin-top: 15px;
    text-shadow: 0 0 5px rgba(78, 205, 196, 0.3);
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .mac-crt-monitor {
      max-width: 500px;
    }

    .mac-housing {
      padding: 30px 30px 15px 30px;
    }

    .screen-bezel {
      padding: 20px;
    }

    .crt-screen {
      min-height: 300px;
    }

    .screen-content {
      padding: 20px;
    }

    .motherboard-title {
      font-size: 1.4rem;
    }

    .neural-description {
      font-size: 0.8rem;
    }
  }

  @media (max-width: 480px) {
    .mac-crt-monitor {
      max-width: 400px;
    }

    .mac-housing {
      padding: 20px 20px 10px 20px;
    }

    .screen-bezel {
      padding: 15px;
    }

    .crt-screen {
      min-height: 250px;
    }

    .screen-content {
      padding: 15px;
    }

    .motherboard-title {
      font-size: 1.2rem;
    }

    .console-brand {
      font-size: 0.8rem;
    }
  }
</style>
