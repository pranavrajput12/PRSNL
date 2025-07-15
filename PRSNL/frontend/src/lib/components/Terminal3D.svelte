<script lang="ts">
  export let onClick = () => {};
  export let tooltip = "Code Intelligence - Code Cortex";
  
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
    const element = document.querySelector('.terminal-container');
    element?.classList.add('clicked');
    setTimeout(() => {
      element?.classList.remove('clicked');
      onClick();
    }, 200);
  }
</script>

<div 
  class="terminal-container {isHovered ? 'hovered' : ''}"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- Terminal Brain Chip Body -->
  <div class="terminal-body">
    <!-- Base PCB -->
    <div class="terminal-pcb">
      <!-- Neural Processing Unit -->
      <div class="neural-processor">
        <div class="processor-core">
          <div class="core-grid">
            {#each Array(16) as _, i}
              <div class="core-unit" style="animation-delay: {i * 100}ms"></div>
            {/each}
          </div>
          <div class="processor-label">NPU</div>
        </div>
        <div class="heat-spreader {isHovered ? 'active' : ''}"></div>
      </div>
      
      <!-- Terminal Screen -->
      <div class="terminal-screen">
        <div class="screen-bezel">
          <div class="screen-display {isHovered ? 'active' : ''}">
            <div class="terminal-lines">
              <div class="code-line">$ nano brain.py</div>
              <div class="code-line">import neural_net</div>
              <div class="code-line">class CodeBrain:</div>
              <div class="code-line">  def think():</div>
              <div class="code-line cursor-line">    return ai.magic()<span class="terminal-cursor {isHovered ? 'blinking' : ''}">█</span></div>
            </div>
          </div>
        </div>
        <div class="screen-mount"></div>
      </div>
      
      <!-- Memory Banks -->
      <div class="memory-banks">
        {#each Array(4) as _, i}
          <div class="memory-module mod-{i}" style="animation-delay: {i * 150}ms">
            <div class="memory-chips">
              {#each Array(8) as _, j}
                <div class="memory-chip" style="animation-delay: {(i * 8 + j) * 25}ms"></div>
              {/each}
            </div>
            <div class="memory-activity {isHovered ? 'active' : ''}"></div>
          </div>
        {/each}
      </div>
      
      <!-- Neural Pathways -->
      <div class="neural-pathways">
        <div class="pathway pathway-1"></div>
        <div class="pathway pathway-2"></div>
        <div class="pathway pathway-3"></div>
        <div class="pathway pathway-4"></div>
        <div class="pathway pathway-5"></div>
      </div>
      
      <!-- Connection Ports -->
      <div class="connection-ports">
        <div class="port usb-c">
          <div class="port-label">USB-C</div>
        </div>
        <div class="port neural-link">
          <div class="port-label">NEURAL</div>
          <div class="neural-indicator {isHovered ? 'connected' : 'standby'}"></div>
        </div>
        <div class="port debug">
          <div class="port-label">DEBUG</div>
        </div>
      </div>
    </div>
    
    <!-- Side Edges -->
    <div class="terminal-edge left">
      <div class="edge-vents">
        {#each Array(6) as _, i}
          <div class="vent-slot" style="animation-delay: {i * 80}ms"></div>
        {/each}
      </div>
    </div>
    
    <div class="terminal-edge right">
      <div class="brain-antenna">
        <div class="antenna-base"></div>
        <div class="antenna-rod"></div>
        <div class="antenna-tip {isHovered ? 'transmitting' : ''}"></div>
      </div>
    </div>
    
    <!-- Back Panel -->
    <div class="terminal-back">
      <div class="circuit-traces">
        <div class="trace trace-main"></div>
        <div class="trace trace-power"></div>
        <div class="trace trace-data"></div>
        <div class="trace trace-neural"></div>
      </div>
      <div class="chip-capacitors">
        {#each Array(6) as _, i}
          <div class="capacitor" style="animation-delay: {i * 120}ms"></div>
        {/each}
      </div>
    </div>
    
    <!-- Bottom PCB -->
    <div class="terminal-bottom">
      <div class="bottom-circuitry">
        <div class="circuit-grid">
          {#each Array(24) as _, i}
            <div class="circuit-point"></div>
          {/each}
        </div>
        <div class="brain-serial">BRAIN-{Math.floor(Math.random() * 9999)}</div>
      </div>
    </div>
  </div>
  
  <!-- Neural Network Visualization -->
  <div class="neural-network {isHovered ? 'active' : ''}">
    <div class="neural-nodes">
      <div class="node-layer input-layer">
        {#each Array(3) as _, i}
          <div class="neural-node" style="animation-delay: {i * 200}ms"></div>
        {/each}
      </div>
      <div class="node-layer hidden-layer">
        {#each Array(4) as _, i}
          <div class="neural-node" style="animation-delay: {(i + 3) * 200}ms"></div>
        {/each}
      </div>
      <div class="node-layer output-layer">
        {#each Array(2) as _, i}
          <div class="neural-node" style="animation-delay: {(i + 7) * 200}ms"></div>
        {/each}
      </div>
    </div>
    
    <div class="neural-connections">
      {#each Array(12) as _, i}
        <div class="connection" style="animation-delay: {i * 100}ms"></div>
      {/each}
    </div>
  </div>
  
  <!-- Code Particles -->
  <div class="code-particles {isHovered ? 'active' : ''}">
    {#each Array(8) as _, i}
      <div class="code-particle" style="animation-delay: {i * 250}ms">
        <div class="particle-text">{['{}', '()', '[]', '<>', '//', '==', '&&', '||'][i]}</div>
      </div>
    {/each}
  </div>
  
  <!-- Electromagnetic Field -->
  <div class="em-field {isHovered ? 'active' : ''}">
    <div class="field-ring ring-1"></div>
    <div class="field-ring ring-2"></div>
    <div class="field-ring ring-3"></div>
    <div class="field-pulses">
      {#each Array(6) as _, i}
        <div class="em-pulse" style="animation-delay: {i * 300}ms"></div>
      {/each}
    </div>
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
  .terminal-container {
    position: relative;
    width: 80px;
    height: 80px;
    cursor: pointer;
    transform-style: preserve-3d;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .terminal-container:hover {
    transform: rotateY(20deg) rotateX(-15deg) translateY(-8px);
  }
  
  .terminal-container.clicked {
    transform: scale(0.95) rotateY(20deg) rotateX(-15deg);
    transition: all 0.2s ease;
  }
  
  .terminal-body {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 65px;
    height: 45px;
    transform-style: preserve-3d;
    animation: neural-pulse 4s ease-in-out infinite;
  }
  
  @keyframes neural-pulse {
    0%, 100% { transform: translate(-50%, -50%) rotateY(0deg); }
    50% { transform: translate(-50%, -50%) rotateY(-5deg); }
  }
  
  .terminal-pcb {
    position: absolute;
    width: 65px;
    height: 45px;
    background: linear-gradient(135deg, #0a1a0a, #0f2f0f, #0a1a0a);
    border-radius: 4px;
    transform: rotateX(90deg) translateZ(6px);
    display: grid;
    grid-template-areas: 
      "processor screen"
      "memory memory"
      "pathways pathways"
      "ports ports";
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto 1fr auto;
    gap: 2px;
    padding: 3px;
    box-shadow: 
      0 4px 16px rgba(0,0,0,0.6),
      inset 0 1px 3px rgba(0,255,100,0.2);
  }
  
  .neural-processor {
    grid-area: processor;
    position: relative;
    background: linear-gradient(45deg, #1a1a2e, #16213e, #1a1a2e);
    border-radius: 3px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
  }
  
  .processor-core {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2px;
  }
  
  .core-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(4, 1fr);
    gap: 0.5px;
    width: 16px;
    height: 12px;
  }
  
  .core-unit {
    background: #333;
    border-radius: 0.5px;
    animation: core-processing 3s ease-in-out infinite;
  }
  
  @keyframes core-processing {
    0%, 100% { background: #333; }
    50% { background: #00ff64; }
  }
  
  .processor-label {
    font-size: 2px;
    color: #00ff64;
    font-weight: bold;
    margin-top: 1px;
  }
  
  .heat-spreader {
    position: absolute;
    top: -1px;
    left: -1px;
    right: -1px;
    bottom: -1px;
    background: linear-gradient(45deg, rgba(255,100,100,0.1), rgba(255,150,150,0.1));
    border-radius: 3px;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .heat-spreader.active {
    opacity: 1;
    animation: heat-glow 2s ease-in-out infinite;
  }
  
  @keyframes heat-glow {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.7; }
  }
  
  .terminal-screen {
    grid-area: screen;
    position: relative;
    background: #000;
    border-radius: 2px;
    overflow: hidden;
  }
  
  .screen-bezel {
    position: absolute;
    inset: 1px;
    background: #111;
    border-radius: 1px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .screen-display {
    width: 90%;
    height: 90%;
    background: #001100;
    border-radius: 1px;
    padding: 1px;
    overflow: hidden;
    opacity: 0.7;
    transition: opacity 0.3s ease;
  }
  
  .screen-display.active {
    opacity: 1;
    box-shadow: inset 0 0 4px #00ff64;
  }
  
  .terminal-lines {
    font-family: monospace;
    font-size: 1px;
    line-height: 1.2;
    color: #00ff64;
  }
  
  .code-line {
    margin-bottom: 0.5px;
    opacity: 0.8;
  }
  
  .cursor-line {
    opacity: 1;
  }
  
  .terminal-cursor {
    display: inline;
    opacity: 0;
    transition: opacity 0.1s ease;
  }
  
  .terminal-cursor.blinking {
    animation: cursor-blink 1s ease-in-out infinite;
  }
  
  @keyframes cursor-blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
  
  .screen-mount {
    position: absolute;
    bottom: -1px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 2px;
    background: #333;
    border-radius: 0 0 1px 1px;
  }
  
  .memory-banks {
    grid-area: memory;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
  }
  
  .memory-module {
    background: linear-gradient(45deg, #2a2a2a, #3a3a3a, #2a2a2a);
    border-radius: 1px;
    position: relative;
    animation: memory-cycle 5s ease-in-out infinite;
  }
  
  @keyframes memory-cycle {
    0%, 90%, 100% { opacity: 0.7; }
    95% { opacity: 1; }
  }
  
  .memory-chips {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(2, 1fr);
    gap: 0.2px;
    padding: 0.5px;
    width: 100%;
    height: 100%;
  }
  
  .memory-chip {
    background: #444;
    border-radius: 0.2px;
    animation: chip-access 4s ease-in-out infinite;
  }
  
  @keyframes chip-access {
    0%, 95%, 100% { background: #444; }
    97% { background: #00ccff; }
  }
  
  .memory-activity {
    position: absolute;
    top: 1px;
    right: 1px;
    width: 1px;
    height: 1px;
    background: #666;
    border-radius: 50%;
    transition: all 0.3s ease;
  }
  
  .memory-activity.active {
    background: #ff6600;
    box-shadow: 0 0 2px #ff6600;
    animation: activity-pulse 0.5s ease-in-out infinite;
  }
  
  @keyframes activity-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  
  .neural-pathways {
    grid-area: pathways;
    position: relative;
    overflow: hidden;
  }
  
  .pathway {
    position: absolute;
    height: 0.5px;
    background: linear-gradient(90deg, transparent, #00ff64, transparent);
    animation: neural-signal 3s ease-in-out infinite;
  }
  
  .pathway-1 { top: 20%; left: 0; width: 100%; animation-delay: 0s; }
  .pathway-2 { top: 40%; left: 0; width: 80%; animation-delay: 0.3s; }
  .pathway-3 { top: 60%; left: 0; width: 60%; animation-delay: 0.6s; }
  .pathway-4 { top: 80%; left: 0; width: 90%; animation-delay: 0.9s; }
  .pathway-5 { top: 30%; left: 0; width: 70%; animation-delay: 1.2s; }
  
  @keyframes neural-signal {
    0%, 100% { opacity: 0.2; }
    50% { opacity: 0.8; }
  }
  
  .connection-ports {
    grid-area: ports;
    display: flex;
    justify-content: space-around;
    align-items: center;
  }
  
  .port {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5px;
  }
  
  .port-label {
    font-size: 1px;
    color: #888;
    font-weight: bold;
  }
  
  .usb-c .port-label::after {
    content: '';
    display: block;
    width: 3px;
    height: 1px;
    background: #333;
    border-radius: 0.5px;
    margin-top: 0.5px;
  }
  
  .neural-link .port-label::after {
    content: '';
    display: block;
    width: 2px;
    height: 2px;
    background: radial-gradient(circle, #444, #222);
    border-radius: 50%;
    margin-top: 0.5px;
  }
  
  .debug .port-label::after {
    content: '';
    display: block;
    width: 2px;
    height: 1px;
    background: #333;
    margin-top: 0.5px;
  }
  
  .neural-indicator {
    width: 1px;
    height: 1px;
    border-radius: 50%;
    transition: all 0.3s ease;
  }
  
  .neural-indicator.standby {
    background: #666;
  }
  
  .neural-indicator.connected {
    background: #00ff64;
    box-shadow: 0 0 2px #00ff64;
    animation: neural-heartbeat 1s ease-in-out infinite;
  }
  
  @keyframes neural-heartbeat {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.3); }
  }
  
  .terminal-edge {
    position: absolute;
    width: 6px;
    height: 45px;
    background: linear-gradient(90deg, #1a1a1a, #2a2a2a);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .terminal-edge.left {
    transform: rotateY(-90deg) translateZ(32.5px);
    border-radius: 4px 0 0 4px;
  }
  
  .terminal-edge.right {
    transform: rotateY(90deg) translateZ(32.5px);
    border-radius: 0 4px 4px 0;
  }
  
  .edge-vents {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }
  
  .vent-slot {
    width: 4px;
    height: 1px;
    background: linear-gradient(90deg, #111, #000, #111);
    animation: thermal-vent 4s ease-in-out infinite;
  }
  
  @keyframes thermal-vent {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.7; }
  }
  
  .brain-antenna {
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
    justify-content: center;
  }
  
  .antenna-base {
    width: 3px;
    height: 3px;
    background: radial-gradient(circle, #555, #333);
    border-radius: 50%;
  }
  
  .antenna-rod {
    width: 1px;
    height: 8px;
    background: linear-gradient(180deg, #666, #444);
    margin: 1px 0;
  }
  
  .antenna-tip {
    width: 2px;
    height: 2px;
    background: #666;
    border-radius: 50%;
    transition: all 0.3s ease;
  }
  
  .antenna-tip.transmitting {
    background: #ff6600;
    box-shadow: 0 0 4px #ff6600;
    animation: transmission-pulse 0.8s ease-in-out infinite;
  }
  
  @keyframes transmission-pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.7; }
  }
  
  .terminal-back {
    position: absolute;
    width: 65px;
    height: 45px;
    background: linear-gradient(135deg, #0f1f0f, #0a1a0a);
    transform: rotateY(180deg) translateZ(6px);
    border-radius: 4px;
    overflow: hidden;
    padding: 2px;
  }
  
  .circuit-traces {
    position: relative;
    width: 100%;
    height: 70%;
  }
  
  .trace {
    position: absolute;
    height: 0.5px;
    background: linear-gradient(90deg, transparent, #00ff64, transparent);
    animation: trace-data 4s ease-in-out infinite;
  }
  
  .trace-main { top: 20%; left: 0; width: 100%; animation-delay: 0s; }
  .trace-power { top: 40%; left: 0; width: 80%; animation-delay: 0.5s; }
  .trace-data { top: 60%; left: 0; width: 90%; animation-delay: 1s; }
  .trace-neural { top: 80%; left: 0; width: 70%; animation-delay: 1.5s; }
  
  @keyframes trace-data {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.7; }
  }
  
  .chip-capacitors {
    display: flex;
    justify-content: space-around;
    align-items: end;
    height: 30%;
  }
  
  .capacitor {
    width: 2px;
    height: 4px;
    background: linear-gradient(180deg, #444, #222);
    border-radius: 1px 1px 0 0;
    animation: capacitor-charge 5s ease-in-out infinite;
  }
  
  @keyframes capacitor-charge {
    0%, 100% { filter: brightness(1); }
    50% { filter: brightness(1.3); }
  }
  
  .terminal-bottom {
    position: absolute;
    width: 65px;
    height: 45px;
    background: linear-gradient(135deg, #0a1505, #0f1f0f);
    border-radius: 4px;
    transform: rotateX(-90deg) translateZ(-6px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2px;
  }
  
  .bottom-circuitry {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
  }
  
  .circuit-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    grid-template-rows: repeat(3, 1fr);
    gap: 1px;
    width: 90%;
    height: 70%;
  }
  
  .circuit-point {
    width: 1px;
    height: 1px;
    background: #333;
    border-radius: 50%;
    opacity: 0.6;
  }
  
  .brain-serial {
    font-size: 2px;
    color: #666;
    font-family: monospace;
  }
  
  .neural-network {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .neural-network.active {
    opacity: 1;
  }
  
  .neural-nodes {
    position: absolute;
    top: 20%;
    left: 20%;
    width: 60%;
    height: 60%;
    display: flex;
    justify-content: space-between;
  }
  
  .node-layer {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    height: 100%;
  }
  
  .neural-node {
    width: 4px;
    height: 4px;
    background: #00ccff;
    border-radius: 50%;
    animation: node-activation 2s ease-in-out infinite;
  }
  
  @keyframes node-activation {
    0%, 100% {
      opacity: 0.5;
      transform: scale(1);
    }
    50% {
      opacity: 1;
      transform: scale(1.3);
    }
  }
  
  .neural-connections {
    position: absolute;
    top: 20%;
    left: 20%;
    width: 60%;
    height: 60%;
  }
  
  .connection {
    position: absolute;
    width: 15px;
    height: 1px;
    background: linear-gradient(90deg, #00ccff, transparent, #00ccff);
    animation: connection-pulse 3s ease-in-out infinite;
  }
  
  .connection:nth-child(1) { top: 10%; left: 15%; transform: rotate(15deg); }
  .connection:nth-child(2) { top: 25%; left: 10%; transform: rotate(-10deg); }
  .connection:nth-child(3) { top: 40%; left: 20%; transform: rotate(20deg); }
  .connection:nth-child(4) { top: 55%; left: 15%; transform: rotate(-15deg); }
  .connection:nth-child(5) { top: 70%; left: 25%; transform: rotate(10deg); }
  .connection:nth-child(6) { top: 85%; left: 20%; transform: rotate(-5deg); }
  .connection:nth-child(7) { top: 15%; right: 20%; transform: rotate(-25deg); }
  .connection:nth-child(8) { top: 30%; right: 15%; transform: rotate(25deg); }
  .connection:nth-child(9) { top: 45%; right: 25%; transform: rotate(-20deg); }
  .connection:nth-child(10) { top: 60%; right: 20%; transform: rotate(15deg); }
  .connection:nth-child(11) { top: 75%; right: 30%; transform: rotate(-10deg); }
  .connection:nth-child(12) { top: 90%; right: 25%; transform: rotate(5deg); }
  
  @keyframes connection-pulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.8; }
  }
  
  .code-particles {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .code-particles.active {
    opacity: 1;
  }
  
  .code-particle {
    position: absolute;
    animation: code-float 4s ease-in-out infinite;
  }
  
  .code-particle:nth-child(1) { top: 10%; left: 20%; animation-delay: 0s; }
  .code-particle:nth-child(2) { top: 30%; right: 15%; animation-delay: 0.5s; }
  .code-particle:nth-child(3) { top: 50%; left: 10%; animation-delay: 1s; }
  .code-particle:nth-child(4) { top: 70%; right: 20%; animation-delay: 1.5s; }
  .code-particle:nth-child(5) { top: 20%; left: 60%; animation-delay: 2s; }
  .code-particle:nth-child(6) { top: 80%; left: 40%; animation-delay: 2.5s; }
  .code-particle:nth-child(7) { top: 40%; right: 40%; animation-delay: 3s; }
  .code-particle:nth-child(8) { top: 60%; left: 80%; animation-delay: 3.5s; }
  
  @keyframes code-float {
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
  
  .particle-text {
    font-size: 6px;
    color: #00ff64;
    font-weight: bold;
    font-family: monospace;
    text-shadow: 0 0 4px #00ff64;
  }
  
  .em-field {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100px;
    height: 100px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .em-field.active {
    opacity: 1;
  }
  
  .field-ring {
    position: absolute;
    border: 1px solid #ff6600;
    border-radius: 50%;
    animation: em-expansion 3s ease-in-out infinite;
  }
  
  .ring-1 {
    top: 30%;
    left: 30%;
    width: 40%;
    height: 40%;
    animation-delay: 0s;
  }
  
  .ring-2 {
    top: 20%;
    left: 20%;
    width: 60%;
    height: 60%;
    animation-delay: 0.5s;
  }
  
  .ring-3 {
    top: 10%;
    left: 10%;
    width: 80%;
    height: 80%;
    animation-delay: 1s;
  }
  
  @keyframes em-expansion {
    0% {
      opacity: 0;
      transform: scale(0.8);
    }
    50% {
      opacity: 0.7;
      transform: scale(1.1);
    }
    100% {
      opacity: 0;
      transform: scale(1.3);
    }
  }
  
  .field-pulses {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80%;
    height: 80%;
  }
  
  .em-pulse {
    position: absolute;
    width: 3px;
    height: 3px;
    background: #ff6600;
    border-radius: 50%;
    animation: pulse-orbit 4s linear infinite;
  }
  
  .em-pulse:nth-child(1) { animation-delay: 0s; }
  .em-pulse:nth-child(2) { animation-delay: 0.7s; }
  .em-pulse:nth-child(3) { animation-delay: 1.4s; }
  .em-pulse:nth-child(4) { animation-delay: 2.1s; }
  .em-pulse:nth-child(5) { animation-delay: 2.8s; }
  .em-pulse:nth-child(6) { animation-delay: 3.5s; }
  
  @keyframes pulse-orbit {
    from {
      transform: rotate(0deg) translateX(35px) rotate(0deg);
    }
    to {
      transform: rotate(360deg) translateX(35px) rotate(-360deg);
    }
  }
  
  .tooltip-bubble {
    position: absolute;
    bottom: 110%;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    color: #ff6600;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    box-shadow: 0 4px 16px rgba(255, 102, 0, 0.3);
    border: 1px solid #ff6600;
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
  
  .terminal-container.hovered .terminal-body {
    animation: neural-pulse 2s ease-in-out infinite, hover-glow 2s ease-in-out infinite;
  }
  
  @keyframes hover-glow {
    0%, 100% {
      filter: drop-shadow(0 0 15px rgba(255, 102, 0, 0.4));
    }
    50% {
      filter: drop-shadow(0 0 30px rgba(255, 102, 0, 0.7));
    }
  }
</style>