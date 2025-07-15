<script lang="ts">
  export let onClick = () => {};
  export let tooltip = 'Message Center - Conversations';

  let isHovered = false;
  let showTooltip = false;
  let tooltipTimeout: ReturnType<typeof setTimeout>;

  function handleMouseEnter() {
    isHovered = true;
    tooltipTimeout = setTimeout(() => {
      showTooltip = true;
    }, 300);
  }

  function handleMouseLeave() {
    isHovered = false;
    showTooltip = false;
    if (tooltipTimeout) {
      clearTimeout(tooltipTimeout);
    }
  }

  function handleClick() {
    const element = document.querySelector('.typewriter-container');
    element?.classList.add('clicked');
    setTimeout(() => {
      element?.classList.remove('clicked');
      onClick();
    }, 200);
  }
</script>

<div
  class="typewriter-container {isHovered ? 'hovered' : ''}"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- Typewriter Main Body -->
  <div class="typewriter-body">
    <!-- Base Platform -->
    <div class="typewriter-base">
      <div class="base-pattern">
        {#each Array(8) as _, i}
          <div class="base-line" style="animation-delay: {i * 100}ms"></div>
        {/each}
      </div>
      <div class="brand-badge">PRSNL</div>
    </div>

    <!-- Main Housing -->
    <div class="typewriter-housing">
      <!-- Paper Roller -->
      <div class="paper-roller">
        <div class="roller-shaft"></div>
        <div class="paper-sheet {isHovered ? 'typing' : ''}">
          <div class="paper-content">
            <div class="typed-text">Dear User,</div>
            <div class="typed-text">Welcome to</div>
            <div class="typed-text">PRSNL Chat...</div>
            <div class="cursor-blink {isHovered ? 'active' : ''}">_</div>
          </div>
        </div>
      </div>

      <!-- Keyboard Section -->
      <div class="keyboard-section">
        <div class="key-rows">
          <!-- Top row -->
          <div class="key-row">
            {#each Array(10) as _, i}
              <div class="typewriter-key" style="animation-delay: {i * 20}ms">
                <div class="key-cap"></div>
                <div class="key-letter">{String.fromCharCode(81 + i)}</div>
              </div>
            {/each}
          </div>

          <!-- Middle row -->
          <div class="key-row">
            {#each Array(9) as _, i}
              <div class="typewriter-key" style="animation-delay: {(i + 10) * 20}ms">
                <div class="key-cap"></div>
                <div class="key-letter">{String.fromCharCode(65 + i)}</div>
              </div>
            {/each}
          </div>

          <!-- Bottom row -->
          <div class="key-row">
            {#each Array(7) as _, i}
              <div class="typewriter-key" style="animation-delay: {(i + 19) * 20}ms">
                <div class="key-cap"></div>
                <div class="key-letter">{String.fromCharCode(90 + i)}</div>
              </div>
            {/each}
          </div>
        </div>

        <!-- Space bar -->
        <div class="space-bar">
          <div class="space-cap"></div>
        </div>
      </div>

      <!-- Type Bars -->
      <div class="type-bars {isHovered ? 'active' : ''}">
        {#each Array(5) as _, i}
          <div class="type-bar" style="animation-delay: {i * 50}ms"></div>
        {/each}
      </div>
    </div>

    <!-- Side Details -->
    <div class="typewriter-side left">
      <div class="carriage-return">
        <div class="return-lever"></div>
      </div>
      <div class="margin-settings">
        <div class="margin-tab"></div>
        <div class="margin-tab"></div>
      </div>
    </div>

    <div class="typewriter-side right">
      <div class="ribbon-housing">
        <div class="ribbon-spool"></div>
        <div class="ribbon-indicator {isHovered ? 'fresh' : 'used'}"></div>
      </div>
    </div>
  </div>

  <!-- Email/Message Effects -->
  <div class="message-effects {isHovered ? 'active' : ''}">
    <div class="floating-messages">
      {#each Array(6) as _, i}
        <div class="message-bubble" style="animation-delay: {i * 300}ms">
          <div class="message-icon">@</div>
        </div>
      {/each}
    </div>

    <div class="typing-particles">
      {#each Array(8) as _, i}
        <div class="particle" style="animation-delay: {i * 150}ms"></div>
      {/each}
    </div>
  </div>

  <!-- Communication Signals -->
  <div class="communication-signals {isHovered ? 'active' : ''}">
    <div class="signal-wave wave-1"></div>
    <div class="signal-wave wave-2"></div>
    <div class="signal-wave wave-3"></div>
    <div class="signal-wave wave-4"></div>
  </div>

  <!-- Tooltip -->
  {#if showTooltip}
    <div class="tooltip-bubble">
      <div class="tooltip-content">{tooltip}</div>
      <div class="tooltip-arrow"></div>
    </div>
  {/if}
</div>

<style>
  .typewriter-container {
    position: relative;
    width: 80px;
    height: 80px;
    cursor: pointer;
    transform-style: preserve-3d;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .typewriter-container:hover {
    transform: rotateY(-15deg) rotateX(20deg) translateY(-6px);
  }

  .typewriter-container.clicked {
    transform: scale(0.95) rotateY(-15deg) rotateX(20deg);
    transition: all 0.2s ease;
  }

  .typewriter-body {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 70px;
    height: 50px;
    transform-style: preserve-3d;
    animation: vintage-sway 5s ease-in-out infinite;
  }

  @keyframes vintage-sway {
    0%,
    100% {
      transform: translate(-50%, -50%) rotateY(0deg);
    }
    50% {
      transform: translate(-50%, -50%) rotateY(-3deg);
    }
  }

  .typewriter-base {
    position: absolute;
    width: 70px;
    height: 50px;
    background: linear-gradient(135deg, #2c1810, #1a0f08, #2c1810);
    border-radius: 4px;
    transform: rotateX(-90deg) translateZ(-12px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 2px 4px;
    box-shadow:
      0 3px 12px rgba(0, 0, 0, 0.6),
      inset 0 1px 2px rgba(255, 255, 255, 0.1);
  }

  .base-pattern {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .base-line {
    width: 15px;
    height: 0.5px;
    background: linear-gradient(90deg, transparent, #8b4513, transparent);
    animation: base-glow 4s ease-in-out infinite;
  }

  @keyframes base-glow {
    0%,
    100% {
      opacity: 0.3;
    }
    50% {
      opacity: 0.7;
    }
  }

  .brand-badge {
    font-size: 3px;
    color: #d2691e;
    font-weight: bold;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.8);
  }

  .typewriter-housing {
    position: absolute;
    width: 70px;
    height: 40px;
    background: linear-gradient(135deg, #4a4a4a, #2a2a2a, #4a4a4a);
    border-radius: 6px 6px 2px 2px;
    transform: translateZ(8px);
    display: grid;
    grid-template-areas:
      'roller roller'
      'keyboard keyboard'
      'bars bars';
    grid-template-rows: auto 1fr auto;
    padding: 2px;
    box-shadow:
      0 4px 16px rgba(0, 0, 0, 0.4),
      inset 0 1px 3px rgba(255, 255, 255, 0.2);
  }

  .paper-roller {
    grid-area: roller;
    position: relative;
    height: 12px;
    background: linear-gradient(90deg, #333, #555, #333);
    border-radius: 6px 6px 0 0;
    overflow: hidden;
  }

  .roller-shaft {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60px;
    height: 3px;
    background: linear-gradient(90deg, #666, #888, #666);
    border-radius: 1.5px;
  }

  .paper-sheet {
    position: absolute;
    top: -2px;
    left: 5px;
    width: 60px;
    height: 16px;
    background: linear-gradient(180deg, #f8f8f8, #e8e8e8);
    border-radius: 2px 2px 0 0;
    transform: rotateX(15deg);
    transition: transform 0.3s ease;
    overflow: hidden;
  }

  .paper-sheet.typing {
    transform: rotateX(15deg) translateY(-2px);
    animation: paper-vibrate 0.1s linear infinite;
  }

  @keyframes paper-vibrate {
    0%,
    100% {
      transform: rotateX(15deg) translateY(-2px) translateX(0);
    }
    50% {
      transform: rotateX(15deg) translateY(-2px) translateX(0.5px);
    }
  }

  .paper-content {
    padding: 2px 3px;
    font-family: monospace;
  }

  .typed-text {
    font-size: 2px;
    color: #333;
    line-height: 1.2;
    margin-bottom: 1px;
  }

  .cursor-blink {
    display: inline-block;
    font-size: 2px;
    color: #333;
    opacity: 0;
    transition: opacity 0.1s ease;
  }

  .cursor-blink.active {
    animation: cursor-flash 0.8s ease-in-out infinite;
  }

  @keyframes cursor-flash {
    0%,
    50% {
      opacity: 1;
    }
    51%,
    100% {
      opacity: 0;
    }
  }

  .keyboard-section {
    grid-area: keyboard;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1px;
  }

  .key-rows {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .key-row {
    display: flex;
    gap: 0.5px;
    justify-content: center;
  }

  .typewriter-key {
    position: relative;
    width: 2.5px;
    height: 2.5px;
    animation: key-gentle-press 6s ease-in-out infinite;
  }

  @keyframes key-gentle-press {
    0%,
    95%,
    100% {
      transform: translateZ(0);
    }
    97% {
      transform: translateZ(-0.5px);
    }
  }

  .key-cap {
    width: 2.5px;
    height: 2.5px;
    background: linear-gradient(45deg, #ddd, #bbb, #ddd);
    border-radius: 0.5px;
    box-shadow:
      0 1px 2px rgba(0, 0, 0, 0.3),
      inset 0 0.5px 1px rgba(255, 255, 255, 0.6);
  }

  .key-letter {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1px;
    color: #333;
    font-weight: bold;
  }

  .space-bar {
    margin-top: 1px;
    width: 20px;
    height: 2px;
  }

  .space-cap {
    width: 100%;
    height: 100%;
    background: linear-gradient(45deg, #ddd, #bbb, #ddd);
    border-radius: 1px;
    box-shadow:
      0 1px 2px rgba(0, 0, 0, 0.3),
      inset 0 0.5px 1px rgba(255, 255, 255, 0.6);
  }

  .type-bars {
    grid-area: bars;
    display: flex;
    justify-content: space-around;
    align-items: center;
    height: 6px;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .type-bars.active {
    opacity: 1;
  }

  .type-bar {
    width: 1px;
    height: 4px;
    background: linear-gradient(180deg, #666, #333);
    border-radius: 0.5px;
    animation: type-strike 0.2s ease-in-out infinite;
  }

  @keyframes type-strike {
    0% {
      transform: translateY(0) rotateX(0deg);
    }
    50% {
      transform: translateY(-1px) rotateX(-15deg);
    }
    100% {
      transform: translateY(0) rotateX(0deg);
    }
  }

  .typewriter-side {
    position: absolute;
    width: 8px;
    height: 40px;
    background: linear-gradient(90deg, #3a3a3a, #2a2a2a);
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    align-items: center;
    padding: 2px 0;
  }

  .typewriter-side.left {
    transform: rotateY(-90deg) translateZ(35px);
    border-radius: 6px 0 0 2px;
  }

  .typewriter-side.right {
    transform: rotateY(90deg) translateZ(35px);
    border-radius: 0 6px 2px 0;
  }

  .carriage-return {
    width: 6px;
    height: 8px;
    background: #444;
    border-radius: 1px;
    position: relative;
  }

  .return-lever {
    position: absolute;
    top: -2px;
    right: -1px;
    width: 2px;
    height: 6px;
    background: #555;
    border-radius: 1px;
    transform: rotate(-20deg);
  }

  .margin-settings {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .margin-tab {
    width: 4px;
    height: 1px;
    background: #666;
    border-radius: 0.5px;
  }

  .ribbon-housing {
    width: 6px;
    height: 12px;
    background: #333;
    border-radius: 1px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1px;
  }

  .ribbon-spool {
    width: 4px;
    height: 4px;
    background: radial-gradient(circle, #444, #222);
    border-radius: 50%;
  }

  .ribbon-indicator {
    width: 3px;
    height: 1px;
    border-radius: 0.5px;
    transition: background 0.3s ease;
  }

  .ribbon-indicator.used {
    background: #666;
  }

  .ribbon-indicator.fresh {
    background: #ff4444;
    box-shadow: 0 0 2px #ff4444;
  }

  .message-effects {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .message-effects.active {
    opacity: 1;
  }

  .floating-messages {
    position: absolute;
    top: 10%;
    left: 10%;
    width: 80%;
    height: 80%;
  }

  .message-bubble {
    position: absolute;
    width: 8px;
    height: 8px;
    background: rgba(30, 144, 255, 0.8);
    border-radius: 50% 50% 50% 0;
    animation: message-float 3s ease-in-out infinite;
  }

  .message-bubble:nth-child(1) {
    top: 10%;
    left: 20%;
    animation-delay: 0s;
  }
  .message-bubble:nth-child(2) {
    top: 30%;
    right: 15%;
    animation-delay: 0.5s;
  }
  .message-bubble:nth-child(3) {
    top: 50%;
    left: 10%;
    animation-delay: 1s;
  }
  .message-bubble:nth-child(4) {
    top: 70%;
    right: 20%;
    animation-delay: 1.5s;
  }
  .message-bubble:nth-child(5) {
    top: 20%;
    left: 60%;
    animation-delay: 2s;
  }
  .message-bubble:nth-child(6) {
    top: 80%;
    left: 40%;
    animation-delay: 2.5s;
  }

  @keyframes message-float {
    0% {
      opacity: 0;
      transform: translateY(20px) scale(0.5);
    }
    50% {
      opacity: 1;
      transform: translateY(-10px) scale(1);
    }
    100% {
      opacity: 0;
      transform: translateY(-40px) scale(0.8);
    }
  }

  .message-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 4px;
    color: white;
    font-weight: bold;
  }

  .typing-particles {
    position: absolute;
    top: 30%;
    left: 50%;
    transform: translateX(-50%);
    width: 60px;
    height: 30px;
  }

  .particle {
    position: absolute;
    width: 2px;
    height: 2px;
    background: #ffd700;
    border-radius: 50%;
    animation: particle-dance 2s ease-in-out infinite;
  }

  .particle:nth-child(1) {
    top: 20%;
    left: 10%;
  }
  .particle:nth-child(2) {
    top: 40%;
    left: 30%;
  }
  .particle:nth-child(3) {
    top: 60%;
    left: 20%;
  }
  .particle:nth-child(4) {
    top: 30%;
    left: 70%;
  }
  .particle:nth-child(5) {
    top: 70%;
    left: 60%;
  }
  .particle:nth-child(6) {
    top: 10%;
    left: 50%;
  }
  .particle:nth-child(7) {
    top: 80%;
    left: 40%;
  }
  .particle:nth-child(8) {
    top: 50%;
    left: 80%;
  }

  @keyframes particle-dance {
    0% {
      opacity: 0;
      transform: scale(0.5) translateY(0);
    }
    25% {
      opacity: 1;
      transform: scale(1) translateY(-5px);
    }
    75% {
      opacity: 1;
      transform: scale(1) translateY(5px);
    }
    100% {
      opacity: 0;
      transform: scale(0.5) translateY(0);
    }
  }

  .communication-signals {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90px;
    height: 90px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .communication-signals.active {
    opacity: 1;
  }

  .signal-wave {
    position: absolute;
    border: 1px solid #32cd32;
    border-radius: 50%;
    animation: signal-pulse 2s ease-in-out infinite;
  }

  .wave-1 {
    top: 20%;
    left: 20%;
    width: 60%;
    height: 60%;
    animation-delay: 0s;
  }

  .wave-2 {
    top: 15%;
    left: 15%;
    width: 70%;
    height: 70%;
    animation-delay: 0.3s;
  }

  .wave-3 {
    top: 10%;
    left: 10%;
    width: 80%;
    height: 80%;
    animation-delay: 0.6s;
  }

  .wave-4 {
    top: 5%;
    left: 5%;
    width: 90%;
    height: 90%;
    animation-delay: 0.9s;
  }

  @keyframes signal-pulse {
    0% {
      opacity: 0;
      transform: scale(0.8);
    }
    50% {
      opacity: 0.6;
      transform: scale(1.1);
    }
    100% {
      opacity: 0;
      transform: scale(1.3);
    }
  }

  .tooltip-bubble {
    position: absolute;
    bottom: 110%;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    color: #32cd32;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    box-shadow: 0 4px 16px rgba(50, 205, 50, 0.3);
    border: 1px solid #32cd32;
    animation: tooltip-appear 0.3s ease-out;
    z-index: 1000;
  }

  .tooltip-arrow {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid rgba(0, 0, 0, 0.9);
  }

  @keyframes tooltip-appear {
    0% {
      opacity: 0;
      transform: translateX(-50%) translateY(10px);
    }
    100% {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  .typewriter-container.hovered .typewriter-body {
    animation:
      vintage-sway 3s ease-in-out infinite,
      hover-glow 2s ease-in-out infinite;
  }

  @keyframes hover-glow {
    0%,
    100% {
      filter: drop-shadow(0 0 12px rgba(50, 205, 50, 0.4));
    }
    50% {
      filter: drop-shadow(0 0 24px rgba(50, 205, 50, 0.7));
    }
  }
</style>
