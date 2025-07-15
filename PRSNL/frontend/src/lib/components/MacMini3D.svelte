<script lang="ts">
  export let onClick = () => {};
  export let tooltip = "Control Center - System Dashboard";
  
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
    // Add click animation class temporarily
    const element = document.querySelector('.mac-mini-container');
    element?.classList.add('clicked');
    setTimeout(() => {
      element?.classList.remove('clicked');
      onClick();
    }, 200);
  }
</script>

<div 
  class="mac-mini-container {isHovered ? 'hovered' : ''}"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- Mac Mini Body -->
  <div class="mac-mini-body">
    <!-- Top Surface -->
    <div class="mac-mini-top">
      <div class="apple-logo"></div>
      <div class="status-indicator"></div>
    </div>
    
    <!-- Front Face -->
    <div class="mac-mini-front">
      <!-- Ports -->
      <div class="port-section">
        <div class="port usb-port"></div>
        <div class="port usb-port"></div>
        <div class="port audio-port"></div>
      </div>
    </div>
    
    <!-- Side Faces -->
    <div class="mac-mini-side left"></div>
    <div class="mac-mini-side right">
      <!-- Side Ports -->
      <div class="side-ports">
        <div class="port thunderbolt"></div>
        <div class="port thunderbolt"></div>
        <div class="port hdmi"></div>
        <div class="port ethernet"></div>
        <div class="port power"></div>
      </div>
    </div>
    
    <!-- Back Face -->
    <div class="mac-mini-back">
      <div class="vent-pattern">
        {#each Array(12) as _, i}
          <div class="vent-line" style="animation-delay: {i * 50}ms"></div>
        {/each}
      </div>
    </div>
    
    <!-- Bottom -->
    <div class="mac-mini-bottom">
      <div class="rubber-foot"></div>
      <div class="rubber-foot"></div>
      <div class="rubber-foot"></div>
      <div class="rubber-foot"></div>
    </div>
  </div>
  
  <!-- Electrical Effects -->
  <div class="electrical-field {isHovered ? 'active' : ''}">
    <div class="electrical-ring ring-1"></div>
    <div class="electrical-ring ring-2"></div>
    <div class="electrical-ring ring-3"></div>
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
  .mac-mini-container {
    position: relative;
    width: 80px;
    height: 80px;
    cursor: pointer;
    transform-style: preserve-3d;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .mac-mini-container:hover {
    transform: rotateY(15deg) rotateX(10deg) translateY(-5px);
  }
  
  .mac-mini-container.clicked {
    transform: scale(0.95) rotateY(15deg) rotateX(10deg);
    transition: all 0.2s ease;
  }
  
  .mac-mini-body {
    position: relative;
    width: 60px;
    height: 20px;
    margin: 30px auto;
    transform-style: preserve-3d;
    animation: gentle-float 4s ease-in-out infinite;
  }
  
  @keyframes gentle-float {
    0%, 100% { transform: translateY(0px) rotateY(0deg); }
    50% { transform: translateY(-3px) rotateY(5deg); }
  }
  
  .mac-mini-top {
    position: absolute;
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #e8e8e8, #d0d0d0, #c0c0c0);
    border-radius: 8px;
    transform: rotateX(90deg) translateZ(10px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px;
    box-shadow: 
      inset 2px 2px 4px rgba(255,255,255,0.7),
      inset -2px -2px 4px rgba(0,0,0,0.1);
  }
  
  .apple-logo {
    width: 12px;
    height: 12px;
    background: linear-gradient(45deg, #333, #666);
    border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
    position: relative;
  }
  
  .apple-logo::before {
    content: '';
    position: absolute;
    top: -2px;
    right: 2px;
    width: 3px;
    height: 6px;
    background: #333;
    border-radius: 0 2px 0 0;
    transform: rotate(20deg);
  }
  
  .status-indicator {
    width: 4px;
    height: 4px;
    background: #00ff64;
    border-radius: 50%;
    box-shadow: 0 0 8px #00ff64;
    animation: status-pulse 2s ease-in-out infinite;
  }
  
  @keyframes status-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.2); }
  }
  
  .mac-mini-front {
    position: absolute;
    width: 60px;
    height: 20px;
    background: linear-gradient(135deg, #f0f0f0, #d8d8d8, #c8c8c8);
    border-radius: 0 0 8px 8px;
    transform: translateZ(30px);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 
      0 2px 8px rgba(0,0,0,0.2),
      inset 0 1px 2px rgba(255,255,255,0.8);
  }
  
  .port-section {
    display: flex;
    gap: 4px;
    align-items: center;
  }
  
  .port {
    border-radius: 1px;
    border: 1px solid #999;
    background: #333;
  }
  
  .usb-port {
    width: 6px;
    height: 3px;
  }
  
  .audio-port {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #222;
  }
  
  .mac-mini-side {
    position: absolute;
    width: 60px;
    height: 20px;
    background: linear-gradient(90deg, #d8d8d8, #c8c8c8, #b8b8b8);
  }
  
  .mac-mini-side.left {
    transform: rotateY(-90deg) translateZ(30px);
    border-radius: 8px 0 0 8px;
  }
  
  .mac-mini-side.right {
    transform: rotateY(90deg) translateZ(30px);
    border-radius: 0 8px 8px 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .side-ports {
    display: flex;
    flex-direction: column;
    gap: 1px;
    align-items: center;
  }
  
  .thunderbolt {
    width: 8px;
    height: 2px;
    background: #333;
    border-radius: 1px;
  }
  
  .hdmi {
    width: 6px;
    height: 2px;
    background: #333;
    border-radius: 0;
  }
  
  .ethernet {
    width: 6px;
    height: 3px;
    background: #333;
    border-radius: 1px;
  }
  
  .power {
    width: 4px;
    height: 4px;
    background: #333;
    border-radius: 50%;
  }
  
  .mac-mini-back {
    position: absolute;
    width: 60px;
    height: 20px;
    background: linear-gradient(135deg, #d0d0d0, #c0c0c0, #b0b0b0);
    transform: rotateY(180deg) translateZ(30px);
    border-radius: 8px 8px 0 0;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .vent-pattern {
    display: flex;
    gap: 1px;
    align-items: center;
  }
  
  .vent-line {
    width: 1px;
    height: 12px;
    background: linear-gradient(to bottom, #999, #777, #999);
    animation: vent-flow 3s ease-in-out infinite;
  }
  
  @keyframes vent-flow {
    0%, 100% { opacity: 0.4; transform: scaleY(1); }
    50% { opacity: 0.8; transform: scaleY(1.2); }
  }
  
  .mac-mini-bottom {
    position: absolute;
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #c0c0c0, #b0b0b0, #a0a0a0);
    border-radius: 8px;
    transform: rotateX(-90deg) translateZ(-10px);
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 20px;
    padding: 10px;
  }
  
  .rubber-foot {
    width: 8px;
    height: 8px;
    background: #333;
    border-radius: 50%;
    justify-self: center;
    align-self: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  }
  
  .electrical-field {
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
  
  .electrical-field.active {
    opacity: 1;
  }
  
  .electrical-ring {
    position: absolute;
    border-radius: 50%;
    border: 1px solid #00ff64;
    animation: electrical-pulse 2s ease-in-out infinite;
  }
  
  .ring-1 {
    top: 10%;
    left: 10%;
    width: 80%;
    height: 80%;
    animation-delay: 0s;
  }
  
  .ring-2 {
    top: 5%;
    left: 5%;
    width: 90%;
    height: 90%;
    animation-delay: 0.3s;
  }
  
  .ring-3 {
    top: 0%;
    left: 0%;
    width: 100%;
    height: 100%;
    animation-delay: 0.6s;
  }
  
  @keyframes electrical-pulse {
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
  
  .mac-mini-container.hovered .mac-mini-body {
    animation: gentle-float 2s ease-in-out infinite, hover-glow 2s ease-in-out infinite;
  }
  
  @keyframes hover-glow {
    0%, 100% {
      filter: drop-shadow(0 0 10px rgba(0, 255, 100, 0.3));
    }
    50% {
      filter: drop-shadow(0 0 20px rgba(0, 255, 100, 0.6));
    }
  }
</style>