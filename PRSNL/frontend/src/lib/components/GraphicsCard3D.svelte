<script lang="ts">
  export let onClick = () => {};
  export let tooltip = 'AI Processor - Personal Assistant';

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
    const element = document.querySelector('.gpu-container');
    element?.classList.add('clicked');
    setTimeout(() => {
      element?.classList.remove('clicked');
      onClick();
    }, 200);
  }
</script>

<div
  class="gpu-container {isHovered ? 'hovered' : ''}"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- GPU Main Body -->
  <div class="gpu-body">
    <!-- GPU PCB (Top) -->
    <div class="gpu-pcb">
      <!-- GPU Chip -->
      <div class="gpu-chip">
        <div class="chip-core">
          <div class="core-pattern">
            {#each Array(9) as _, i}
              <div class="core-block" style="animation-delay: {i * 100}ms"></div>
            {/each}
          </div>
          <div class="chip-label">AI-GPT</div>
        </div>
        <div class="thermal-interface"></div>
      </div>

      <!-- Memory Modules -->
      <div class="memory-modules">
        {#each Array(6) as _, i}
          <div class="memory-chip" style="animation-delay: {i * 50}ms">
            <div class="mem-activity {isHovered ? 'active' : ''}"></div>
          </div>
        {/each}
      </div>

      <!-- Power Connectors -->
      <div class="power-section">
        <div class="power-connector">
          <div class="connector-pins">
            {#each Array(8) as _, i}
              <div class="power-pin" style="animation-delay: {i * 30}ms"></div>
            {/each}
          </div>
          <div class="connector-label">12V</div>
        </div>
      </div>

      <!-- Capacitors -->
      <div class="capacitor-array">
        {#each Array(4) as _, i}
          <div class="capacitor" style="animation-delay: {i * 200}ms"></div>
        {/each}
      </div>
    </div>

    <!-- Cooling Shroud -->
    <div class="cooling-shroud">
      <!-- Fan Housings -->
      <div class="fan-housing fan-1">
        <div class="fan-blades {isHovered ? 'spinning' : ''}">
          {#each Array(7) as _, i}
            <div class="fan-blade" style="transform: rotate({i * 51.4}deg)"></div>
          {/each}
        </div>
        <div class="fan-center"></div>
      </div>

      <div class="fan-housing fan-2">
        <div class="fan-blades {isHovered ? 'spinning' : ''}">
          {#each Array(7) as _, i}
            <div class="fan-blade" style="transform: rotate({i * 51.4}deg)"></div>
          {/each}
        </div>
        <div class="fan-center"></div>
      </div>

      <!-- Heat Sink Fins -->
      <div class="heatsink-fins">
        {#each Array(12) as _, i}
          <div class="heat-fin" style="animation-delay: {i * 50}ms"></div>
        {/each}
      </div>

      <!-- RGB Strip -->
      <div class="rgb-strip {isHovered ? 'active' : ''}">
        <div class="rgb-section rgb-red"></div>
        <div class="rgb-section rgb-green"></div>
        <div class="rgb-section rgb-blue"></div>
      </div>
    </div>

    <!-- I/O Bracket -->
    <div class="io-bracket">
      <!-- Display Ports -->
      <div class="port-section">
        <div class="display-port hdmi">HDMI</div>
        <div class="display-port dp">DP</div>
        <div class="display-port dp">DP</div>
        <div class="display-port usbc">USB-C</div>
      </div>

      <!-- Ventilation -->
      <div class="bracket-vents">
        {#each Array(16) as _, i}
          <div class="vent-hole" style="animation-delay: {i * 25}ms"></div>
        {/each}
      </div>
    </div>

    <!-- PCIe Bracket -->
    <div class="pcie-bracket">
      <div class="bracket-tabs">
        <div class="bracket-tab"></div>
        <div class="bracket-tab"></div>
      </div>
    </div>

    <!-- Bottom Side -->
    <div class="gpu-bottom">
      <div class="bottom-pcb">
        <div class="trace-patterns">
          <div class="trace-line trace-1"></div>
          <div class="trace-line trace-2"></div>
          <div class="trace-line trace-3"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Processing Effects -->
  <div class="processing-effects {isHovered ? 'active' : ''}">
    <div class="compute-rays">
      {#each Array(8) as _, i}
        <div
          class="compute-ray"
          style="transform: rotate({i * 45}deg); animation-delay: {i * 100}ms"
        ></div>
      {/each}
    </div>

    <div class="neural-network">
      <div class="neural-node node-1"></div>
      <div class="neural-node node-2"></div>
      <div class="neural-node node-3"></div>
      <div class="neural-connection conn-1"></div>
      <div class="neural-connection conn-2"></div>
      <div class="neural-connection conn-3"></div>
    </div>
  </div>

  <!-- Heat Visualization -->
  <div class="thermal-effects {isHovered ? 'active' : ''}">
    <div class="heat-wave wave-1"></div>
    <div class="heat-wave wave-2"></div>
    <div class="heat-wave wave-3"></div>
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
  .gpu-container {
    position: relative;
    width: 80px;
    height: 80px;
    cursor: pointer;
    transform-style: preserve-3d;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .gpu-container:hover {
    transform: rotateY(-20deg) rotateX(10deg) translateY(-8px);
  }

  .gpu-container.clicked {
    transform: scale(0.95) rotateY(-20deg) rotateX(10deg);
    transition: all 0.2s ease;
  }

  .gpu-body {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 70px;
    height: 45px;
    transform-style: preserve-3d;
    animation: processing-idle 5s ease-in-out infinite;
  }

  @keyframes processing-idle {
    0%,
    100% {
      transform: translate(-50%, -50%) rotateY(0deg);
    }
    50% {
      transform: translate(-50%, -50%) rotateY(-2deg);
    }
  }

  .gpu-pcb {
    position: absolute;
    width: 70px;
    height: 45px;
    background: linear-gradient(135deg, #1a1a2e, #16213e, #1a1a2e);
    border-radius: 4px;
    transform: rotateX(90deg) translateZ(8px);
    display: grid;
    grid-template-areas:
      'chip power'
      'memory memory'
      'caps caps';
    grid-template-columns: 2fr 1fr;
    grid-template-rows: auto 1fr auto;
    gap: 2px;
    padding: 3px;
    box-shadow:
      0 4px 16px rgba(0, 0, 0, 0.4),
      inset 0 1px 3px rgba(255, 255, 255, 0.1);
  }

  .gpu-chip {
    grid-area: chip;
    position: relative;
    background: linear-gradient(45deg, #2a2a2a, #3a3a3a, #2a2a2a);
    border-radius: 2px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  }

  .chip-core {
    position: relative;
    width: 20px;
    height: 15px;
    background: linear-gradient(45deg, #444, #666, #444);
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .core-pattern {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
    gap: 1px;
    width: 12px;
    height: 9px;
  }

  .core-block {
    background: #222;
    border-radius: 0.5px;
    animation: core-activity 3s ease-in-out infinite;
  }

  @keyframes core-activity {
    0%,
    100% {
      background: #222;
    }
    50% {
      background: #00ff64;
    }
  }

  .chip-label {
    position: absolute;
    bottom: 1px;
    font-size: 3px;
    color: #ccc;
    font-weight: bold;
  }

  .thermal-interface {
    position: absolute;
    top: -1px;
    left: 50%;
    transform: translateX(-50%);
    width: 22px;
    height: 17px;
    background: linear-gradient(45deg, #888, #aaa, #888);
    border-radius: 1px;
    opacity: 0.7;
  }

  .memory-modules {
    grid-area: memory;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(2, 1fr);
    gap: 1px;
  }

  .memory-chip {
    background: linear-gradient(45deg, #333, #444, #333);
    border-radius: 1px;
    position: relative;
    animation: memory-access 4s ease-in-out infinite;
  }

  @keyframes memory-access {
    0%,
    90%,
    100% {
      opacity: 0.7;
    }
    95% {
      opacity: 1;
    }
  }

  .mem-activity {
    position: absolute;
    top: 1px;
    right: 1px;
    width: 1px;
    height: 1px;
    background: #666;
    border-radius: 50%;
    transition: all 0.3s ease;
  }

  .mem-activity.active {
    background: #00ccff;
    box-shadow: 0 0 3px #00ccff;
    animation: mem-blink 0.3s ease-in-out infinite;
  }

  @keyframes mem-blink {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.3;
    }
  }

  .power-section {
    grid-area: power;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .power-connector {
    background: #222;
    border-radius: 2px;
    padding: 1px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1px;
  }

  .connector-pins {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(2, 1fr);
    gap: 0.5px;
  }

  .power-pin {
    width: 1px;
    height: 1px;
    background: #d4af37;
    border-radius: 0.2px;
    animation: power-flow 2s ease-in-out infinite;
  }

  @keyframes power-flow {
    0%,
    100% {
      opacity: 0.6;
    }
    50% {
      opacity: 1;
    }
  }

  .connector-label {
    font-size: 2px;
    color: #888;
    font-weight: bold;
  }

  .capacitor-array {
    grid-area: caps;
    display: flex;
    justify-content: space-around;
    align-items: center;
  }

  .capacitor {
    width: 3px;
    height: 6px;
    background: linear-gradient(180deg, #4a4a4a, #2a2a2a);
    border-radius: 1px 1px 0 0;
    position: relative;
    animation: capacitor-charge 3s ease-in-out infinite;
  }

  .capacitor::before {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 1px;
    height: 2px;
    background: #d4af37;
  }

  @keyframes capacitor-charge {
    0%,
    100% {
      filter: brightness(1);
    }
    50% {
      filter: brightness(1.2);
    }
  }

  .cooling-shroud {
    position: absolute;
    width: 70px;
    height: 45px;
    background: linear-gradient(135deg, #2c2c2c, #1a1a1a, #2c2c2c);
    border-radius: 4px;
    transform: translateZ(16px);
    display: grid;
    grid-template-areas:
      'fan1 fan2'
      'fins fins'
      'rgb rgb';
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 2fr 1fr auto;
    gap: 1px;
    padding: 2px;
    box-shadow:
      0 6px 20px rgba(0, 0, 0, 0.6),
      inset 0 1px 3px rgba(255, 255, 255, 0.1);
  }

  .fan-housing {
    position: relative;
    background: radial-gradient(circle, #333, #222);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .fan-1 {
    grid-area: fan1;
  }

  .fan-2 {
    grid-area: fan2;
  }

  .fan-blades {
    position: relative;
    width: 80%;
    height: 80%;
    transition: transform 0.3s ease;
  }

  .fan-blades.spinning {
    animation: fan-spin 0.8s linear infinite;
  }

  @keyframes fan-spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .fan-blade {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 8px;
    height: 2px;
    background: linear-gradient(90deg, #444, #666, #444);
    border-radius: 1px;
    transform-origin: 0 50%;
  }

  .fan-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 4px;
    height: 4px;
    background: radial-gradient(circle, #555, #333);
    border-radius: 50%;
    z-index: 1;
  }

  .heatsink-fins {
    grid-area: fins;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 2px;
  }

  .heat-fin {
    width: 1px;
    height: 8px;
    background: linear-gradient(180deg, #666, #444, #666);
    animation: thermal-activity 4s ease-in-out infinite;
  }

  @keyframes thermal-activity {
    0%,
    100% {
      opacity: 0.6;
      transform: scaleY(1);
    }
    50% {
      opacity: 1;
      transform: scaleY(1.1);
    }
  }

  .rgb-strip {
    grid-area: rgb;
    display: flex;
    height: 3px;
    border-radius: 1px;
    overflow: hidden;
    opacity: 0.5;
    transition: opacity 0.3s ease;
  }

  .rgb-strip.active {
    opacity: 1;
  }

  .rgb-section {
    flex: 1;
    height: 100%;
    animation: rgb-cycle 3s ease-in-out infinite;
  }

  .rgb-red {
    background: linear-gradient(90deg, #ff4444, #ff6666);
    animation-delay: 0s;
  }

  .rgb-green {
    background: linear-gradient(90deg, #44ff44, #66ff66);
    animation-delay: 1s;
  }

  .rgb-blue {
    background: linear-gradient(90deg, #4444ff, #6666ff);
    animation-delay: 2s;
  }

  @keyframes rgb-cycle {
    0%,
    100% {
      opacity: 0.3;
    }
    33% {
      opacity: 1;
    }
  }

  .io-bracket {
    position: absolute;
    width: 4px;
    height: 45px;
    background: linear-gradient(180deg, #333, #222, #333);
    transform: rotateY(90deg) translateZ(35px);
    border-radius: 0 2px 2px 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 2px 0;
  }

  .port-section {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .display-port {
    width: 3px;
    height: 2px;
    background: #000;
    border: 0.5px solid #555;
    border-radius: 0.5px;
    font-size: 1px;
    color: #888;
    display: flex;
    align-items: center;
    justify-content: center;
    transform: rotateZ(90deg);
  }

  .bracket-vents {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(8, 1fr);
    gap: 0.5px;
  }

  .vent-hole {
    width: 1px;
    height: 1px;
    background: #111;
    border-radius: 50%;
    animation: vent-flow 3s ease-in-out infinite;
  }

  @keyframes vent-flow {
    0%,
    100% {
      opacity: 0.3;
    }
    50% {
      opacity: 0.7;
    }
  }

  .pcie-bracket {
    position: absolute;
    width: 70px;
    height: 4px;
    background: linear-gradient(90deg, #333, #222, #333);
    transform: rotateY(180deg) translateZ(22.5px);
    border-radius: 2px 2px 0 0;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 2px;
  }

  .bracket-tabs {
    display: flex;
    gap: 1px;
  }

  .bracket-tab {
    width: 2px;
    height: 3px;
    background: #444;
    border-radius: 0.5px 0.5px 0 0;
  }

  .gpu-bottom {
    position: absolute;
    width: 70px;
    height: 45px;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border-radius: 4px;
    transform: rotateX(-90deg) translateZ(-8px);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .bottom-pcb {
    width: 90%;
    height: 90%;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
  }

  .trace-patterns {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .trace-line {
    height: 0.5px;
    background: linear-gradient(90deg, transparent, #00ff64, transparent);
    animation: trace-signal 3s ease-in-out infinite;
  }

  .trace-1 {
    width: 90%;
    animation-delay: 0s;
  }
  .trace-2 {
    width: 70%;
    animation-delay: 0.5s;
  }
  .trace-3 {
    width: 50%;
    animation-delay: 1s;
  }

  @keyframes trace-signal {
    0%,
    100% {
      opacity: 0.3;
    }
    50% {
      opacity: 0.8;
    }
  }

  .processing-effects {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .processing-effects.active {
    opacity: 1;
  }

  .compute-rays {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60px;
    height: 60px;
  }

  .compute-ray {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 2px;
    height: 20px;
    background: linear-gradient(to top, transparent, #00ccff, transparent);
    transform-origin: 0 0;
    animation: ray-pulse 2s ease-in-out infinite;
  }

  @keyframes ray-pulse {
    0% {
      opacity: 0;
      transform: translate(-50%, -50%) scale(0.8);
    }
    50% {
      opacity: 1;
      transform: translate(-50%, -50%) scale(1.2);
    }
    100% {
      opacity: 0;
      transform: translate(-50%, -50%) scale(1);
    }
  }

  .neural-network {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80px;
    height: 80px;
  }

  .neural-node {
    position: absolute;
    width: 4px;
    height: 4px;
    background: #00ccff;
    border-radius: 50%;
    animation: neural-pulse 2s ease-in-out infinite;
  }

  .node-1 {
    top: 20%;
    left: 20%;
    animation-delay: 0s;
  }

  .node-2 {
    top: 20%;
    right: 20%;
    animation-delay: 0.3s;
  }

  .node-3 {
    bottom: 20%;
    left: 50%;
    transform: translateX(-50%);
    animation-delay: 0.6s;
  }

  @keyframes neural-pulse {
    0%,
    100% {
      opacity: 0.5;
      transform: scale(1);
    }
    50% {
      opacity: 1;
      transform: scale(1.3);
    }
  }

  .neural-connection {
    position: absolute;
    height: 1px;
    background: linear-gradient(90deg, #00ccff, transparent, #00ccff);
    animation: neural-flow 3s ease-in-out infinite;
  }

  .conn-1 {
    top: 22%;
    left: 24%;
    width: 52%;
    animation-delay: 0s;
  }

  .conn-2 {
    top: 22%;
    right: 24%;
    width: 30%;
    transform: rotate(45deg);
    animation-delay: 0.5s;
  }

  .conn-3 {
    top: 22%;
    left: 24%;
    width: 30%;
    transform: rotate(-45deg);
    animation-delay: 1s;
  }

  @keyframes neural-flow {
    0%,
    100% {
      opacity: 0.3;
    }
    50% {
      opacity: 0.8;
    }
  }

  .thermal-effects {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .thermal-effects.active {
    opacity: 1;
  }

  .heat-wave {
    position: absolute;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255, 100, 100, 0.5), transparent);
    animation: heat-rise 4s ease-in-out infinite;
  }

  .wave-1 {
    top: 20%;
    animation-delay: 0s;
  }

  .wave-2 {
    top: 50%;
    animation-delay: 0.5s;
  }

  .wave-3 {
    top: 80%;
    animation-delay: 1s;
  }

  @keyframes heat-rise {
    0% {
      opacity: 0;
      transform: translateY(20px);
    }
    50% {
      opacity: 0.7;
      transform: translateY(-10px);
    }
    100% {
      opacity: 0;
      transform: translateY(-40px);
    }
  }

  .tooltip-bubble {
    position: absolute;
    bottom: 110%;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    color: #00ccff;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    box-shadow: 0 4px 16px rgba(0, 204, 255, 0.3);
    border: 1px solid #00ccff;
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

  .gpu-container.hovered .gpu-body {
    animation:
      processing-idle 2s ease-in-out infinite,
      hover-glow 2s ease-in-out infinite;
  }

  @keyframes hover-glow {
    0%,
    100% {
      filter: drop-shadow(0 0 15px rgba(0, 204, 255, 0.4));
    }
    50% {
      filter: drop-shadow(0 0 30px rgba(0, 204, 255, 0.7));
    }
  }
</style>
