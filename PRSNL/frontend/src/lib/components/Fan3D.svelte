<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

  let canvas: HTMLCanvasElement;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let renderer: THREE.WebGLRenderer;
  let fanModel: THREE.Group;
  let fanBlades: THREE.Object3D[] = [];
  let fanFrame: THREE.Object3D[] = [];
  let bladesGroup: THREE.Group;
  let frameGroup: THREE.Group;
  let animationId: number;
  let isHovered = false;
  let rotationSpeed = 0.1;

  onMount(async () => {
    initThreeJS();
    await loadFanModel();
    animate();
  });

  onDestroy(() => {
    cleanup();
  });

  function cleanup() {
    // Cancel animation frame
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = 0;
    }

    // Dispose of geometries and materials
    if (scene) {
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          if (object.geometry) {
            object.geometry.dispose();
          }
          if (object.material) {
            if (Array.isArray(object.material)) {
              object.material.forEach((material) => material.dispose());
            } else {
              object.material.dispose();
            }
          }
        }
      });
      scene.clear();
    }

    // Dispose of renderer and force context loss
    if (renderer) {
      renderer.dispose();
      renderer.forceContextLoss();
      const gl = renderer.getContext();
      if (gl && gl.getExtension('WEBGL_lose_context')) {
        gl.getExtension('WEBGL_lose_context').loseContext();
      }
    }

    // Clear references
    scene = null;
    camera = null;
    renderer = null;
    fanModel = null;
    fanBlades = [];
    fanFrame = [];
    bladesGroup = null;
    frameGroup = null;
  }

  function initThreeJS() {
    // Scene setup
    scene = new THREE.Scene();
    scene.background = null; // Transparent background

    // Camera setup
    camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    camera.position.set(0, 0, 5);

    // Renderer setup
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(600, 600); // Doubled from 300x300
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Lighting setup for motherboard aesthetic
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 5, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 1024;
    directionalLight.shadow.mapSize.height = 1024;
    scene.add(directionalLight);

    // Add some colored lighting for motherboard effect
    const blueLight = new THREE.PointLight(0x0088ff, 0.3, 10);
    blueLight.position.set(-3, 2, 3);
    scene.add(blueLight);

    const greenLight = new THREE.PointLight(0x4ecdc4, 0.2, 10);
    greenLight.position.set(3, -2, 3);
    scene.add(greenLight);
  }

  async function loadFanModel() {
    const loader = new GLTFLoader();

    try {
      const gltf = await loader.loadAsync('/models/fan.glb');
      fanModel = gltf.scene;

      // Debug: Print model structure
      console.log('Fan model loaded. Structure:');
      fanModel.traverse((child, index) => {
        if (child instanceof THREE.Mesh) {
          console.log(
            `Mesh ${index}: ${child.name}, vertices: ${child.geometry.attributes.position.count}`
          );
        }
      });

      // Center and scale the model
      const box = new THREE.Box3().setFromObject(fanModel);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());

      // Center the model
      fanModel.position.sub(center);

      // Scale to fit nicely (doubled size)
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 6 / maxDim; // Doubled from 3 to 6
      fanModel.scale.setScalar(scale);

      // Clear any existing groups
      if (bladesGroup) scene.remove(bladesGroup);
      if (frameGroup) scene.remove(frameGroup);

      // Create fresh groups for frame and blades
      bladesGroup = new THREE.Group();
      frameGroup = new THREE.Group();

      // Clear arrays
      fanBlades.length = 0;
      fanFrame.length = 0;

      // Collect all meshes with their info
      const allMeshes: { mesh: THREE.Mesh; vertices: number; name: string }[] = [];

      fanModel.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.castShadow = true;
          child.receiveShadow = true;

          // Enhance materials
          if (child.material) {
            child.material.metalness = 0.7;
            child.material.roughness = 0.3;
          }

          allMeshes.push({
            mesh: child,
            vertices: child.geometry.attributes.position.count,
            name: child.name || 'unnamed',
          });
        }
      });

      console.log('All meshes found:');
      allMeshes.forEach((item, index) => {
        console.log(`${index}: "${item.name}" - ${item.vertices} vertices`);
      });

      // Smart detection: Find the mesh with most vertices (likely the frame)
      // and smaller meshes around the perimeter (likely blades)
      allMeshes.sort((a, b) => b.vertices - a.vertices);

      const largestMesh = allMeshes[0];
      console.log(`Largest mesh: "${largestMesh.name}" with ${largestMesh.vertices} vertices`);

      allMeshes.forEach((item, index) => {
        // Remove from original parent
        if (item.mesh.parent) {
          item.mesh.parent.remove(item.mesh);
        }

        // FLIPPED ASSIGNMENT:
        // Object_4 (65532 vertices) = Blades (rotating)
        // Object_5 & Object_7 = Frame (static)
        if (item.name === 'Object_4') {
          bladesGroup.add(item.mesh);
          console.log(`Added to BLADES (rotating): "${item.name}" - ${item.vertices} vertices`);
        } else {
          frameGroup.add(item.mesh);
          console.log(`Added to FRAME (static): "${item.name}" - ${item.vertices} vertices`);
        }
      });

      // Add groups to scene
      scene.add(frameGroup);
      scene.add(bladesGroup);

      // Store references for animation
      fanFrame.push(frameGroup);
      fanBlades.push(bladesGroup);

      // Force a render to update
      renderer.render(scene, camera);

      console.log(
        `Frame: ${frameGroup.children.length} parts, Blades: ${bladesGroup.children.length} parts`
      );
    } catch (error) {
      console.error('Error loading fan model:', error);
    }
  }

  function animate() {
    animationId = requestAnimationFrame(animate);

    // Rotate only the fan blades if not hovered
    if (!isHovered && fanBlades.length > 0) {
      fanBlades.forEach((blade) => {
        if (blade.rotation) {
          blade.rotation.z += rotationSpeed;
        }
      });
    }

    renderer.render(scene, camera);
  }

  function handleMouseEnter() {
    isHovered = true;
  }

  function handleMouseLeave() {
    isHovered = false;
  }

  function handleResize() {
    if (renderer && camera) {
      const size = Math.min(600, window.innerWidth * 0.9); // Doubled base size
      renderer.setSize(size, size);
      camera.aspect = 1;
      camera.updateProjectionMatrix();
    }
  }

  // Handle window resize
  onMount(() => {
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  });
</script>

<div
  class="fan-3d-embedded"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  role="button"
  tabindex="0"
>
  <!-- 3D Fan Canvas -->
  <canvas bind:this={canvas} class="fan-3d-canvas"></canvas>

  <!-- Motherboard Components Around Fan -->
  <div class="motherboard-components">
    <!-- RPM Digital Readout Chip -->
    <div class="mb-component rpm-chip">
      <div class="chip-body">
        <div class="chip-label">RPM</div>
        <div class="chip-display">{isHovered ? '0000' : '1800'}</div>
        <div class="chip-pins">
          {#each Array(8) as _, i}
            <div class="chip-pin"></div>
          {/each}
        </div>
      </div>
      <div class="component-trace rpm-trace"></div>
    </div>

    <!-- Temperature Sensor -->
    <div class="mb-component temp-sensor">
      <div class="sensor-body">
        <div class="sensor-label">TEMP</div>
        <div class="sensor-display">{isHovered ? '45°C' : '42°C'}</div>
        <div class="sensor-indicator {isHovered ? 'warning' : 'normal'}"></div>
      </div>
      <div class="component-trace temp-trace"></div>
    </div>

    <!-- Status LED Array -->
    <div class="mb-component status-leds">
      <div class="led-array">
        <div class="led-label">STATUS</div>
        <div class="led-indicators">
          <div class="status-led power {isHovered ? 'off' : 'on'}"></div>
          <div class="status-led activity {isHovered ? 'off' : 'blinking'}"></div>
          <div class="status-led error off"></div>
        </div>
        <div class="led-labels">
          <span>PWR</span>
          <span>ACT</span>
          <span>ERR</span>
        </div>
      </div>
      <div class="component-trace status-trace"></div>
    </div>

    <!-- Fan Wiring Harness -->
    <div class="mb-component wiring-harness">
      <div class="harness-connector">
        <div class="connector-label">FAN1</div>
        <div class="wire-bundle">
          <div class="wire red"></div>
          <div class="wire black"></div>
          <div class="wire yellow"></div>
          <div class="wire blue"></div>
        </div>
      </div>
      <div class="component-trace wire-trace"></div>
    </div>
  </div>
</div>

<style>
  .fan-3d-embedded {
    position: relative;
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    background: transparent;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .fan-3d-canvas {
    display: block;
    width: 600px;
    height: 600px;
    max-width: 100%;
    margin: 0 auto;
    background: transparent;
  }

  /* Motherboard Components Layout */
  .motherboard-components {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  .mb-component {
    position: absolute;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  /* RPM Digital Readout Chip */
  .rpm-chip {
    top: 20%;
    left: 10%;
  }

  .chip-body {
    position: relative;
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
    border: 2px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 80px;
    box-shadow:
      0 2px 8px rgba(0, 0, 0, 0.5),
      inset 0 1px 2px rgba(255, 255, 255, 0.1);
  }

  .chip-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-align: center;
    margin-bottom: 2px;
    font-family: monospace;
  }

  .chip-display {
    font-size: 1rem;
    font-weight: bold;
    color: var(--synapse-teal);
    text-align: center;
    font-family: monospace;
    text-shadow: 0 0 6px var(--synapse-teal);
  }

  .chip-pins {
    position: absolute;
    bottom: -6px;
    left: 8px;
    right: 8px;
    display: flex;
    justify-content: space-between;
  }

  .chip-pin {
    width: 3px;
    height: 6px;
    background: var(--text-muted);
    border-radius: 1px;
  }

  /* Temperature Sensor */
  .temp-sensor {
    top: 20%;
    right: 10%;
  }

  .sensor-body {
    background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
    border: 2px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  }

  .sensor-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    font-family: monospace;
  }

  .sensor-display {
    font-size: 0.9rem;
    font-weight: bold;
    color: var(--warning);
    font-family: monospace;
    text-shadow: 0 0 6px var(--warning);
  }

  .sensor-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    transition: all 0.3s ease;
  }

  .sensor-indicator.normal {
    background: var(--synapse-teal);
    box-shadow: 0 0 8px var(--synapse-teal);
  }

  .sensor-indicator.warning {
    background: var(--warning);
    box-shadow: 0 0 8px var(--warning);
  }

  /* Status LED Array */
  .status-leds {
    bottom: 20%;
    left: 10%;
  }

  .led-array {
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
    border: 2px solid var(--border);
    border-radius: 6px;
    padding: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  }

  .led-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-align: center;
    margin-bottom: 4px;
    font-family: monospace;
  }

  .led-indicators {
    display: flex;
    gap: 6px;
    margin-bottom: 4px;
  }

  .status-led {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    transition: all 0.3s ease;
  }

  .status-led.on {
    background: var(--synapse-teal);
    box-shadow: 0 0 8px var(--synapse-teal);
  }

  .status-led.blinking {
    background: var(--info);
    box-shadow: 0 0 8px var(--info);
    animation: blink 1s infinite;
  }

  .status-led.off {
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
  }

  @keyframes blink {
    0%,
    50% {
      opacity: 1;
    }
    51%,
    100% {
      opacity: 0.3;
    }
  }

  .led-labels {
    display: flex;
    gap: 4px;
    font-size: 0.6rem;
    color: var(--text-muted);
    font-family: monospace;
  }

  .led-labels span {
    width: 10px;
    text-align: center;
  }

  /* Wiring Harness */
  .wiring-harness {
    bottom: 20%;
    right: 10%;
  }

  .harness-connector {
    background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
    border: 2px solid var(--border);
    border-radius: 4px;
    padding: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  }

  .connector-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-align: center;
    margin-bottom: 4px;
    font-family: monospace;
  }

  .wire-bundle {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .wire {
    width: 40px;
    height: 2px;
    border-radius: 1px;
  }

  .wire.red {
    background: linear-gradient(90deg, var(--error) 0%, var(--brand-hover) 100%);
  }

  .wire.black {
    background: linear-gradient(90deg, var(--bg-tertiary) 0%, var(--bg-primary) 100%);
  }

  .wire.yellow {
    background: linear-gradient(90deg, var(--highlight) 0%, var(--warning) 100%);
  }

  .wire.blue {
    background: linear-gradient(90deg, var(--info) 0%, var(--info) 100%);
  }

  /* PCB Traces */
  .component-trace {
    width: 30px;
    height: 2px;
    background: linear-gradient(90deg, var(--synapse-teal) 0%, transparent 100%);
    border-radius: 1px;
    opacity: 0.05;
  }

  .rpm-trace {
    transform: rotate(45deg);
  }

  .temp-trace {
    transform: rotate(-45deg);
  }

  .status-trace {
    transform: rotate(135deg);
  }

  .wire-trace {
    transform: rotate(-135deg);
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .fan-3d-embedded {
      padding: 1rem;
    }

    .fan-3d-canvas {
      width: 400px;
      height: 400px;
    }

    .mb-component {
      scale: 0.8;
    }
  }

  @media (max-width: 480px) {
    .fan-3d-canvas {
      width: 300px;
      height: 300px;
    }

    .mb-component {
      scale: 0.7;
    }

    .chip-body,
    .sensor-body,
    .led-array,
    .harness-connector {
      padding: 4px 6px;
    }
  }
</style>
