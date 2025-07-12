<script lang="ts" type="module">
  import Fan3D from './Fan3D.svelte';
  import MacCRT from './MacCRT.svelte';

  // Export props for sticker configuration
  export let showStickers = true;
</script>

<div class="marketing-layout">
  <div class="layout-container">
    <!-- Left Side - 3D Fan -->
    <div class="left-section">
      <div class="fan-container">
        <Fan3D />
      </div>
    </div>

    <!-- Center - Mac CRT Monitor -->
    <div class="center-section">
      <MacCRT />
    </div>

    <!-- Right Side - Tech Stickers -->
    <div class="right-section">
      {#if showStickers}
        <div class="stickers-container">
          <!-- Neural Cortex Inside Sticker -->
          <div class="tech-sticker neural-sticker">
            <div class="sticker-border">
              <div class="sticker-content">
                <div class="sticker-logo">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path
                      d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
                    />
                  </svg>
                </div>
                <div class="sticker-text">
                  <div class="brand-name">Neural Cortex</div>
                  <div class="brand-tagline">Inside</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Timeline DDR4 Ready Sticker -->
          <div class="tech-sticker ddr4-sticker">
            <div class="sticker-border">
              <div class="sticker-content">
                <div class="sticker-logo">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M4 4h16v2H4V4zm0 4h16v2H4V8zm0 4h16v2H4v-2zm0 4h16v2H4v-2z" />
                  </svg>
                </div>
                <div class="sticker-text">
                  <div class="brand-name">Timeline DDR4</div>
                  <div class="brand-tagline">Ready</div>
                </div>
              </div>
            </div>
          </div>

          <!-- AI Memory Certified Sticker -->
          <div class="tech-sticker memory-sticker">
            <div class="sticker-border">
              <div class="sticker-content">
                <div class="sticker-logo">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path
                      d="M9 11H7v6h2v-6zm4 0h-2v6h2v-6zm4 0h-2v6h2v-6zm2.5-5H19V4.5C19 3.12 17.88 2 16.5 2h-9C6.12 2 5 3.12 5 4.5V6H4.5C3.12 6 2 7.12 2 8.5v11C2 20.88 3.12 22 4.5 22h15c1.38 0 2.5-1.12 2.5-2.5v-11C22 7.12 20.88 6 19.5 6zM7 4.5c0-.28.22-.5.5-.5h9c.28 0 .5.22.5.5V6H7V4.5zm13 15c0 .28-.22.5-.5.5h-15c-.28 0-.5-.22-.5-.5v-11c0-.28.22-.5.5-.5h15c.28 0 .5.22.5.5v11z"
                    />
                  </svg>
                </div>
                <div class="sticker-text">
                  <div class="brand-name">AI Memory</div>
                  <div class="brand-tagline">Certified</div>
                </div>
              </div>
            </div>
          </div>

          <!-- PRSNL Powered Sticker -->
          <div class="tech-sticker prsnl-sticker">
            <div class="sticker-border">
              <div class="sticker-content">
                <div class="sticker-logo">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path
                      d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                    />
                  </svg>
                </div>
                <div class="sticker-text">
                  <div class="brand-name">PRSNL</div>
                  <div class="brand-tagline">Powered</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .marketing-layout {
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }

  .layout-container {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    gap: 3rem;
    align-items: center;
    min-height: 600px;
  }

  .left-section {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .fan-container {
    transform: scale(0.8);
    transition: transform 0.3s ease;
  }

  .fan-container:hover {
    transform: scale(0.85);
  }

  .center-section {
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2;
  }

  .right-section {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .stickers-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-height: 400px;
    justify-content: center;
  }

  .tech-sticker {
    position: relative;
    width: 180px;
    height: 60px;
    cursor: pointer;
    transition: all 0.3s ease;
    transform-origin: center;
  }

  .tech-sticker:hover {
    transform: scale(1.05) rotate(1deg);
    z-index: 10;
  }

  .sticker-border {
    width: 100%;
    height: 100%;
    border-radius: 8px;
    padding: 2px;
    background: linear-gradient(135deg, #333 0%, #666 50%, #999 100%);
    box-shadow:
      0 4px 12px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }

  .sticker-content {
    width: 100%;
    height: 100%;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 15px;
    font-family: 'Arial', sans-serif;
    font-weight: 700;
    position: relative;
    overflow: hidden;
  }

  .sticker-content::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
    pointer-events: none;
  }

  .sticker-logo {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .sticker-text {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .brand-name {
    font-size: 0.9rem;
    font-weight: 700;
    line-height: 1;
  }

  .brand-tagline {
    font-size: 0.7rem;
    font-weight: 500;
    opacity: 0.9;
    line-height: 1;
  }

  /* Neural Cortex Sticker - Intel Style */
  .neural-sticker .sticker-content {
    background: linear-gradient(135deg, #0071c5 0%, #005a9f 100%);
    color: white;
  }

  .neural-sticker .sticker-logo {
    color: #ffffff;
  }

  /* Timeline DDR4 Sticker - Memory Style */
  .ddr4-sticker .sticker-content {
    background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
    color: white;
  }

  .ddr4-sticker .sticker-logo {
    color: #ffffff;
  }

  /* AI Memory Sticker - Certification Style */
  .memory-sticker .sticker-content {
    background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
    color: white;
  }

  .memory-sticker .sticker-logo {
    color: #ffffff;
  }

  /* PRSNL Powered Sticker - Brand Style */
  .prsnl-sticker .sticker-content {
    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    color: white;
  }

  .prsnl-sticker .sticker-logo {
    color: #ffffff;
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .layout-container {
      grid-template-columns: 1fr 2fr 1fr;
      gap: 2rem;
    }

    .fan-container {
      transform: scale(0.7);
    }

    .tech-sticker {
      width: 160px;
      height: 55px;
    }

    .brand-name {
      font-size: 0.8rem;
    }

    .brand-tagline {
      font-size: 0.65rem;
    }
  }

  @media (max-width: 968px) {
    .layout-container {
      grid-template-columns: 1fr;
      gap: 3rem;
      text-align: center;
    }

    .stickers-container {
      flex-direction: row;
      flex-wrap: wrap;
      gap: 1rem;
      justify-content: center;
      max-height: none;
    }

    .fan-container {
      transform: scale(0.6);
    }

    .tech-sticker {
      width: 140px;
      height: 50px;
    }
  }

  @media (max-width: 768px) {
    .marketing-layout {
      padding: 1rem;
    }

    .layout-container {
      gap: 2rem;
    }

    .fan-container {
      transform: scale(0.5);
    }

    .stickers-container {
      gap: 0.8rem;
    }

    .tech-sticker {
      width: 120px;
      height: 45px;
    }

    .brand-name {
      font-size: 0.7rem;
    }

    .brand-tagline {
      font-size: 0.6rem;
    }
  }
</style>
