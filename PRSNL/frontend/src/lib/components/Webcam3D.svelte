<script lang="ts">
  export let onClick = () => {};
  export let tooltip = "Recording Studio - Capture Content";
  
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
    const element = document.querySelector('.webcam-container');
    element?.classList.add('clicked');
    setTimeout(() => {
      element?.classList.remove('clicked');
      onClick();
    }, 200);
  }
</script>

<div 
  class="webcam-container {isHovered ? 'hovered' : ''}"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- Webcam Mount/Base -->
  <div class="webcam-mount">
    <div class="mount-base"></div>
    <div class="mount-arm"></div>
    <div class="mount-joint"></div>
  </div>
  
  <!-- Main Webcam Body -->
  <div class="webcam-body">
    <!-- Front Face -->
    <div class="webcam-front">
      <!-- Camera Lens -->
      <div class="camera-lens">
        <div class="lens-outer-ring"></div>
        <div class="lens-inner-ring"></div>
        <div class="lens-center">
          <div class="lens-reflection"></div>
        </div>
      </div>
      
      <!-- Microphone -->
      <div class="microphone-array">
        <div class="mic-hole"></div>
        <div class="mic-hole"></div>
        <div class="mic-hole"></div>
      </div>
      
      <!-- Status LED -->
      <div class="status-led {isHovered ? 'recording' : ''}"></div>
      
      <!-- Brand Text -->
      <div class="brand-text">HD</div>
    </div>
    
    <!-- Top Surface -->
    <div class="webcam-top">
      <div class="cooling-vents">
        {#each Array(8) as _, i}
          <div class="vent-slit" style="animation-delay: {i * 100}ms"></div>
        {/each}
      </div>
    </div>
    
    <!-- Side Faces -->
    <div class="webcam-side left">
      <div class="adjustment-dial"></div>
    </div>
    <div class="webcam-side right">
      <div class="usb-port"></div>
    </div>
    
    <!-- Bottom -->
    <div class="webcam-bottom">
      <div class="serial-number">CAM-3D-2024</div>
    </div>
  </div>
  
  <!-- Recording Light Effect -->
  <div class="recording-effect {isHovered ? 'active' : ''}">
    <div class="light-beam"></div>
    <div class="recording-particles">
      {#each Array(6) as _, i}
        <div class="particle" style="animation-delay: {i * 200}ms"></div>
      {/each}
    </div>
  </div>
  
  <!-- Electrical Field -->
  <div class="electrical-field {isHovered ? 'active' : ''}">
    <div class="data-stream stream-1"></div>
    <div class="data-stream stream-2"></div>
    <div class="data-stream stream-3"></div>
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
  .webcam-container {
    position: relative;
    width: 80px;
    height: 80px;
    cursor: pointer;
    transform-style: preserve-3d;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .webcam-container:hover {
    transform: rotateY(-20deg) rotateX(-10deg) translateY(-8px);
  }
  
  .webcam-container.clicked {
    transform: scale(0.95) rotateY(-20deg) rotateX(-10deg);
    transition: all 0.2s ease;
  }
  
  .webcam-mount {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 40px;
    height: 25px;
    transform-style: preserve-3d;
  }
  
  .mount-base {
    position: absolute;
    bottom: 0;
    width: 40px;
    height: 8px;
    background: linear-gradient(135deg, #2c2c2c, #1a1a1a);
    border-radius: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  }
  
  .mount-arm {
    position: absolute;
    bottom: 6px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 15px;
    background: linear-gradient(90deg, #333, #222, #333);
    border-radius: 3px;
  }
  
  .mount-joint {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 12px;
    height: 6px;
    background: #444;
    border-radius: 6px;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.5);
  }
  
  .webcam-body {
    position: absolute;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    width: 50px;
    height: 35px;
    transform-style: preserve-3d;
    animation: gentle-bob 3s ease-in-out infinite;
  }
  
  @keyframes gentle-bob {
    0%, 100% { transform: translateX(-50%) translateY(0px) rotateZ(0deg); }
    50% { transform: translateX(-50%) translateY(-2px) rotateZ(1deg); }
  }
  
  .webcam-front {
    position: absolute;
    width: 50px;
    height: 35px;
    background: linear-gradient(135deg, #1a1a1a, #333, #1a1a1a);
    border-radius: 12px;
    transform: translateZ(15px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 
      0 4px 16px rgba(0,0,0,0.3),
      inset 0 1px 2px rgba(255,255,255,0.1);
    border: 1px solid #444;
  }
  
  .camera-lens {
    position: relative;
    width: 20px;
    height: 20px;
    margin-bottom: 4px;
  }
  
  .lens-outer-ring {
    position: absolute;
    width: 20px;
    height: 20px;
    background: linear-gradient(45deg, #666, #333, #666);
    border-radius: 50%;
    box-shadow: 
      0 2px 8px rgba(0,0,0,0.5),
      inset 0 1px 2px rgba(255,255,255,0.2);
  }
  
  .lens-inner-ring {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 16px;
    height: 16px;
    background: linear-gradient(45deg, #222, #111);
    border-radius: 50%;
    box-shadow: inset 0 1px 4px rgba(0,0,0,0.8);
  }
  
  .lens-center {
    position: absolute;
    top: 4px;
    left: 4px;
    width: 12px;
    height: 12px;
    background: radial-gradient(circle, #0a0a0a, #000);
    border-radius: 50%;
    overflow: hidden;
  }
  
  .lens-reflection {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 4px;
    height: 4px;
    background: linear-gradient(45deg, rgba(255,255,255,0.3), transparent);
    border-radius: 50%;
    animation: lens-glint 4s ease-in-out infinite;
  }
  
  @keyframes lens-glint {
    0%, 90%, 100% { opacity: 0.3; }
    95% { opacity: 0.8; }
  }
  
  .microphone-array {
    display: flex;
    gap: 2px;
    margin-bottom: 2px;
  }
  
  .mic-hole {
    width: 2px;
    height: 2px;
    background: #000;
    border-radius: 50%;
    box-shadow: inset 0 1px 1px rgba(0,0,0,0.8);
  }
  
  .status-led {
    width: 3px;
    height: 3px;
    background: #666;
    border-radius: 50%;
    margin-bottom: 2px;
    transition: all 0.3s ease;
  }
  
  .status-led.recording {
    background: #ff4444;
    box-shadow: 0 0 8px #ff4444;
    animation: recording-blink 1s ease-in-out infinite;
  }
  
  @keyframes recording-blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  
  .brand-text {
    font-size: 6px;
    color: #888;
    font-weight: bold;
    text-shadow: 0 1px 1px rgba(0,0,0,0.8);
  }
  
  .webcam-top {
    position: absolute;
    width: 50px;
    height: 25px;
    background: linear-gradient(90deg, #333, #222, #333);
    border-radius: 12px 12px 0 0;
    transform: rotateX(90deg) translateZ(17.5px);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .cooling-vents {
    display: flex;
    gap: 1px;
  }
  
  .vent-slit {
    width: 1px;
    height: 8px;
    background: linear-gradient(to bottom, #111, #000, #111);
    animation: thermal-flow 3s ease-in-out infinite;
  }
  
  @keyframes thermal-flow {
    0%, 100% { opacity: 0.3; transform: scaleY(1); }
    50% { opacity: 0.7; transform: scaleY(1.1); }
  }
  
  .webcam-side {
    position: absolute;
    width: 25px;
    height: 35px;
    background: linear-gradient(0deg, #222, #333, #222);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .webcam-side.left {
    transform: rotateY(-90deg) translateZ(25px);
    border-radius: 12px 0 0 12px;
  }
  
  .webcam-side.right {
    transform: rotateY(90deg) translateZ(25px);
    border-radius: 0 12px 12px 0;
  }
  
  .adjustment-dial {
    width: 8px;
    height: 8px;
    background: radial-gradient(circle, #555, #333);
    border-radius: 50%;
    border: 1px solid #666;
    position: relative;
  }
  
  .adjustment-dial::before {
    content: '';
    position: absolute;
    top: 1px;
    left: 50%;
    transform: translateX(-50%);
    width: 1px;
    height: 3px;
    background: #888;
  }
  
  .usb-port {
    width: 6px;
    height: 2px;
    background: #000;
    border: 1px solid #555;
    border-radius: 1px;
  }
  
  .webcam-bottom {
    position: absolute;
    width: 50px;
    height: 25px;
    background: linear-gradient(90deg, #1a1a1a, #111, #1a1a1a);
    border-radius: 0 0 12px 12px;
    transform: rotateX(-90deg) translateZ(-17.5px);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .serial-number {
    font-size: 4px;
    color: #666;
    transform: rotateZ(180deg);
  }
  
  .recording-effect {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .recording-effect.active {
    opacity: 1;
  }
  
  .light-beam {
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 2px;
    height: 40px;
    background: linear-gradient(to bottom, 
      rgba(255, 68, 68, 0.8),
      rgba(255, 68, 68, 0.3),
      transparent
    );
    animation: beam-pulse 2s ease-in-out infinite;
  }
  
  @keyframes beam-pulse {
    0%, 100% { opacity: 0.3; transform: translateX(-50%) scaleY(1); }
    50% { opacity: 0.8; transform: translateX(-50%) scaleY(1.2); }
  }
  
  .recording-particles {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60px;
    height: 60px;
  }
  
  .particle {
    position: absolute;
    width: 3px;
    height: 3px;
    background: #ff4444;
    border-radius: 50%;
    animation: particle-orbit 3s linear infinite;
  }
  
  .particle:nth-child(1) { transform: rotate(0deg) translateX(25px); }
  .particle:nth-child(2) { transform: rotate(60deg) translateX(25px); }
  .particle:nth-child(3) { transform: rotate(120deg) translateX(25px); }
  .particle:nth-child(4) { transform: rotate(180deg) translateX(25px); }
  .particle:nth-child(5) { transform: rotate(240deg) translateX(25px); }
  .particle:nth-child(6) { transform: rotate(300deg) translateX(25px); }
  
  @keyframes particle-orbit {
    from { transform: rotate(0deg) translateX(25px) rotate(0deg); }
    to { transform: rotate(360deg) translateX(25px) rotate(-360deg); }
  }
  
  .electrical-field {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80px;
    height: 80px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .electrical-field.active {
    opacity: 1;
  }
  
  .data-stream {
    position: absolute;
    width: 2px;
    height: 20px;
    background: linear-gradient(to top, 
      transparent,
      #00ff64,
      transparent
    );
    animation: data-flow 2s ease-in-out infinite;
  }
  
  .stream-1 {
    top: 0;
    left: 20px;
    animation-delay: 0s;
  }
  
  .stream-2 {
    top: 0;
    right: 20px;
    animation-delay: 0.3s;
  }
  
  .stream-3 {
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    animation-delay: 0.6s;
  }
  
  @keyframes data-flow {
    0% {
      opacity: 0;
      transform: translateY(20px);
    }
    50% {
      opacity: 1;
      transform: translateY(0);
    }
    100% {
      opacity: 0;
      transform: translateY(-20px);
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
  
  .webcam-container.hovered .webcam-body {
    animation: gentle-bob 1.5s ease-in-out infinite, hover-glow 2s ease-in-out infinite;
  }
  
  @keyframes hover-glow {
    0%, 100% {
      filter: drop-shadow(0 0 10px rgba(255, 68, 68, 0.3));
    }
    50% {
      filter: drop-shadow(0 0 20px rgba(255, 68, 68, 0.6));
    }
  }
</style>