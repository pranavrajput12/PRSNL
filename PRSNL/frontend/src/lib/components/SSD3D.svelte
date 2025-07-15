<script lang="ts">
  export let onClick = () => {};
  export let tooltip = 'Memory Bank - Timeline History';

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
    const element = document.querySelector('.ssd-container');
    element?.classList.add('clicked');
    setTimeout(() => {
      element?.classList.remove('clicked');
      onClick();
    }, 200);
  }
</script>

<div
  class="ssd-container {isHovered ? 'hovered' : ''}"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- SSD Main Body -->
  <div class="ssd-body">
    <!-- Top Surface -->
    <div class="ssd-top">
      <!-- Brand Label -->
      <div class="brand-area">
        <div class="brand-logo">PRSNL</div>
        <div class="capacity-label">1TB</div>
      </div>

      <!-- Controller Chip -->
      <div class="controller-chip">
        <div class="chip-pins">
          {#each Array(16) as _, i}
            <div class="chip-pin" style="animation-delay: {i * 50}ms"></div>
          {/each}
        </div>
        <div class="chip-surface">
          <div class="chip-text">CTRL</div>
        </div>
      </div>

      <!-- NAND Flash Chips -->
      <div class="flash-chips">
        {#each Array(4) as _, i}
          <div class="flash-chip chip-{i}" style="animation-delay: {i * 100}ms">
            <div class="chip-label">NAND</div>
            <div class="activity-indicator {isHovered ? 'active' : ''}"></div>
          </div>
        {/each}
      </div>

      <!-- Serial Number -->
      <div class="serial-area">
        <div class="serial-text">SN: TL-2024-{Math.floor(Math.random() * 1000)}</div>
        <div class="qr-code">
          <div class="qr-pattern">
            {#each Array(25) as _, i}
              <div class="qr-dot {Math.random() > 0.5 ? 'filled' : ''}"></div>
            {/each}
          </div>
        </div>
      </div>
    </div>

    <!-- Front Edge -->
    <div class="ssd-front">
      <!-- M.2 Connector -->
      <div class="m2-connector">
        <div class="connector-notch"></div>
        <div class="golden-contacts">
          {#each Array(12) as _, i}
            <div class="contact-pin" style="animation-delay: {i * 25}ms"></div>
          {/each}
        </div>
      </div>
    </div>

    <!-- Back Edge -->
    <div class="ssd-back">
      <div class="pcb-traces">
        <div class="trace trace-1"></div>
        <div class="trace trace-2"></div>
        <div class="trace trace-3"></div>
      </div>
    </div>

    <!-- Side Edges -->
    <div class="ssd-side left"></div>
    <div class="ssd-side right"></div>

    <!-- Bottom Surface -->
    <div class="ssd-bottom">
      <div class="bottom-pcb">
        <div class="pcb-grid">
          {#each Array(40) as _, i}
            <div class="pcb-dot"></div>
          {/each}
        </div>
      </div>
    </div>
  </div>

  <!-- Data Transfer Animation -->
  <div class="data-transfer {isHovered ? 'active' : ''}">
    <div class="data-stream stream-1"></div>
    <div class="data-stream stream-2"></div>
    <div class="data-stream stream-3"></div>
    <div class="transfer-particles">
      {#each Array(8) as _, i}
        <div class="data-particle" style="animation-delay: {i * 150}ms"></div>
      {/each}
    </div>
  </div>

  <!-- Electrical Field -->
  <div class="electrical-field {isHovered ? 'active' : ''}">
    <div class="field-line line-1"></div>
    <div class="field-line line-2"></div>
    <div class="field-line line-3"></div>
    <div class="field-line line-4"></div>
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
  .ssd-container {
    position: relative;
    width: 80px;
    height: 80px;
    cursor: pointer;
    transform-style: preserve-3d;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .ssd-container:hover {
    transform: rotateY(25deg) rotateX(-15deg) translateY(-5px);
  }

  .ssd-container.clicked {
    transform: scale(0.95) rotateY(25deg) rotateX(-15deg);
    transition: all 0.2s ease;
  }

  .ssd-body {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 65px;
    height: 20px;
    transform-style: preserve-3d;
    animation: gentle-pulse 4s ease-in-out infinite;
  }

  @keyframes gentle-pulse {
    0%,
    100% {
      transform: translate(-50%, -50%) rotateY(0deg);
    }
    50% {
      transform: translate(-50%, -50%) rotateY(3deg);
    }
  }

  .ssd-top {
    position: absolute;
    width: 65px;
    height: 20px;
    background: linear-gradient(135deg, #1a4c2e, #2d5a3d, #1a4c2e);
    border-radius: 2px;
    transform: rotateX(90deg) translateZ(2px);
    display: grid;
    grid-template-areas:
      'brand controller'
      'flash flash'
      'serial serial';
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto 1fr auto;
    gap: 1px;
    padding: 2px;
    box-shadow:
      0 2px 8px rgba(0, 0, 0, 0.3),
      inset 0 1px 2px rgba(255, 255, 255, 0.1);
  }

  .brand-area {
    grid-area: brand;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .brand-logo {
    font-size: 4px;
    font-weight: bold;
    color: #fff;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.8);
    background: linear-gradient(45deg, #00ff64, #00cc50);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .capacity-label {
    font-size: 3px;
    color: #ccc;
    margin-top: 1px;
  }

  .controller-chip {
    grid-area: controller;
    position: relative;
    width: 12px;
    height: 8px;
    justify-self: end;
  }

  .chip-pins {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-between;
    padding: 0 1px;
  }

  .chip-pin {
    width: 0.5px;
    height: 2px;
    background: #d4af37;
    animation: pin-pulse 3s ease-in-out infinite;
  }

  @keyframes pin-pulse {
    0%,
    100% {
      opacity: 0.7;
      transform: scaleY(1);
    }
    50% {
      opacity: 1;
      transform: scaleY(1.2);
    }
  }

  .chip-surface {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    background: linear-gradient(45deg, #333, #555, #333);
    border-radius: 1px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  }

  .chip-text {
    font-size: 2px;
    color: #ccc;
    font-weight: bold;
  }

  .flash-chips {
    grid-area: flash;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 1px;
  }

  .flash-chip {
    background: linear-gradient(45deg, #2a2a2a, #3a3a3a, #2a2a2a);
    border-radius: 1px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    animation: chip-activity 4s ease-in-out infinite;
  }

  @keyframes chip-activity {
    0%,
    100% {
      opacity: 0.8;
    }
    50% {
      opacity: 1;
    }
  }

  .chip-label {
    font-size: 1.5px;
    color: #999;
    font-weight: bold;
  }

  .activity-indicator {
    position: absolute;
    top: 1px;
    right: 1px;
    width: 1px;
    height: 1px;
    background: #666;
    border-radius: 50%;
    transition: all 0.3s ease;
  }

  .activity-indicator.active {
    background: #00ff64;
    box-shadow: 0 0 3px #00ff64;
    animation: activity-blink 0.5s ease-in-out infinite;
  }

  @keyframes activity-blink {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.3;
    }
  }

  .serial-area {
    grid-area: serial;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .serial-text {
    font-size: 2px;
    color: #888;
    font-family: monospace;
  }

  .qr-code {
    width: 6px;
    height: 6px;
  }

  .qr-pattern {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    grid-template-rows: repeat(5, 1fr);
    gap: 0.2px;
    width: 100%;
    height: 100%;
  }

  .qr-dot {
    background: transparent;
    border-radius: 0.2px;
  }

  .qr-dot.filled {
    background: #000;
  }

  .ssd-front {
    position: absolute;
    width: 65px;
    height: 4px;
    background: linear-gradient(135deg, #2d5a3d, #1a4c2e);
    transform: translateZ(2px);
    border-radius: 2px 2px 0 0;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    padding-bottom: 1px;
  }

  .m2-connector {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5px;
  }

  .connector-notch {
    width: 4px;
    height: 1px;
    background: #333;
    border-radius: 0.5px;
  }

  .golden-contacts {
    display: flex;
    gap: 0.5px;
  }

  .contact-pin {
    width: 1px;
    height: 2px;
    background: linear-gradient(to bottom, #ffd700, #daa520);
    animation: contact-shine 4s ease-in-out infinite;
  }

  @keyframes contact-shine {
    0%,
    90%,
    100% {
      opacity: 0.8;
    }
    95% {
      opacity: 1;
    }
  }

  .ssd-back {
    position: absolute;
    width: 65px;
    height: 4px;
    background: linear-gradient(135deg, #1a4c2e, #2d5a3d);
    transform: rotateY(180deg) translateZ(2px);
    border-radius: 0 0 2px 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .pcb-traces {
    display: flex;
    flex-direction: column;
    gap: 0.5px;
    width: 100%;
    align-items: center;
  }

  .trace {
    height: 0.5px;
    background: linear-gradient(90deg, transparent, #00ff64, transparent);
    animation: trace-flow 3s ease-in-out infinite;
  }

  .trace-1 {
    width: 80%;
    animation-delay: 0s;
  }
  .trace-2 {
    width: 60%;
    animation-delay: 0.5s;
  }
  .trace-3 {
    width: 40%;
    animation-delay: 1s;
  }

  @keyframes trace-flow {
    0%,
    100% {
      opacity: 0.3;
    }
    50% {
      opacity: 0.8;
    }
  }

  .ssd-side {
    position: absolute;
    width: 4px;
    height: 4px;
    background: linear-gradient(90deg, #1a4c2e, #2d5a3d);
  }

  .ssd-side.left {
    transform: rotateY(-90deg) translateZ(32.5px);
    border-radius: 2px 0 0 2px;
  }

  .ssd-side.right {
    transform: rotateY(90deg) translateZ(32.5px);
    border-radius: 0 2px 2px 0;
  }

  .ssd-bottom {
    position: absolute;
    width: 65px;
    height: 20px;
    background: linear-gradient(135deg, #0f3322, #1a4c2e);
    border-radius: 2px;
    transform: rotateX(-90deg) translateZ(-2px);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .bottom-pcb {
    width: 90%;
    height: 90%;
  }

  .pcb-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    grid-template-rows: repeat(5, 1fr);
    gap: 1px;
    width: 100%;
    height: 100%;
  }

  .pcb-dot {
    width: 1px;
    height: 1px;
    background: #333;
    border-radius: 50%;
    opacity: 0.5;
  }

  .data-transfer {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .data-transfer.active {
    opacity: 1;
  }

  .data-stream {
    position: absolute;
    width: 2px;
    height: 30px;
    background: linear-gradient(to top, transparent, #00ff64, #00ccff, transparent);
    animation: data-flow 2s ease-in-out infinite;
  }

  .stream-1 {
    left: 20%;
    bottom: 0;
    animation-delay: 0s;
  }

  .stream-2 {
    left: 50%;
    bottom: 0;
    animation-delay: 0.3s;
  }

  .stream-3 {
    left: 80%;
    bottom: 0;
    animation-delay: 0.6s;
  }

  @keyframes data-flow {
    0% {
      opacity: 0;
      transform: translateY(20px);
    }
    50% {
      opacity: 1;
      transform: translateY(-10px);
    }
    100% {
      opacity: 0;
      transform: translateY(-40px);
    }
  }

  .transfer-particles {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 70px;
    height: 70px;
  }

  .data-particle {
    position: absolute;
    width: 2px;
    height: 2px;
    background: #00ff64;
    border-radius: 50%;
    animation: particle-stream 3s linear infinite;
  }

  .data-particle:nth-child(1) {
    top: 10%;
    left: 10%;
    animation-delay: 0s;
  }
  .data-particle:nth-child(2) {
    top: 20%;
    left: 80%;
    animation-delay: 0.2s;
  }
  .data-particle:nth-child(3) {
    top: 50%;
    left: 5%;
    animation-delay: 0.4s;
  }
  .data-particle:nth-child(4) {
    top: 70%;
    left: 90%;
    animation-delay: 0.6s;
  }
  .data-particle:nth-child(5) {
    top: 30%;
    left: 60%;
    animation-delay: 0.8s;
  }
  .data-particle:nth-child(6) {
    top: 80%;
    left: 30%;
    animation-delay: 1s;
  }
  .data-particle:nth-child(7) {
    top: 15%;
    left: 40%;
    animation-delay: 1.2s;
  }
  .data-particle:nth-child(8) {
    top: 60%;
    left: 70%;
    animation-delay: 1.4s;
  }

  @keyframes particle-stream {
    0% {
      opacity: 0;
      transform: scale(0.5);
    }
    20% {
      opacity: 1;
      transform: scale(1);
    }
    80% {
      opacity: 1;
      transform: scale(1);
    }
    100% {
      opacity: 0;
      transform: scale(0.5);
    }
  }

  .electrical-field {
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

  .electrical-field.active {
    opacity: 1;
  }

  .field-line {
    position: absolute;
    background: linear-gradient(90deg, transparent, #00ff64, transparent);
    animation: field-pulse 3s ease-in-out infinite;
  }

  .line-1 {
    top: 20%;
    left: 0;
    width: 100%;
    height: 1px;
    animation-delay: 0s;
  }

  .line-2 {
    top: 50%;
    left: 0;
    width: 100%;
    height: 1px;
    animation-delay: 0.5s;
  }

  .line-3 {
    top: 0;
    left: 20%;
    width: 1px;
    height: 100%;
    animation-delay: 1s;
  }

  .line-4 {
    top: 0;
    left: 80%;
    width: 1px;
    height: 100%;
    animation-delay: 1.5s;
  }

  @keyframes field-pulse {
    0%,
    100% {
      opacity: 0.2;
      transform: scale(1);
    }
    50% {
      opacity: 0.8;
      transform: scale(1.1);
    }
  }

  .tooltip-bubble {
    position: absolute;
    bottom: 110%;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    color: #00ff64;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    box-shadow: 0 4px 16px rgba(0, 255, 100, 0.3);
    border: 1px solid #00ff64;
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

  .ssd-container.hovered .ssd-body {
    animation:
      gentle-pulse 2s ease-in-out infinite,
      hover-glow 2s ease-in-out infinite;
  }

  @keyframes hover-glow {
    0%,
    100% {
      filter: drop-shadow(0 0 12px rgba(0, 255, 100, 0.4));
    }
    50% {
      filter: drop-shadow(0 0 24px rgba(0, 255, 100, 0.7));
    }
  }
</style>
