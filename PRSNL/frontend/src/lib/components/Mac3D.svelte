<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

  let canvas: HTMLCanvasElement;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let renderer: THREE.WebGLRenderer;
  let macModel: THREE.Group;
  let screenMaterial: THREE.MeshBasicMaterial;
  let screenTexture: THREE.CanvasTexture;
  let animationId: number;
  let isDragging = false;
  let previousMousePosition = { x: 0, y: 0 };
  let rotationX = 0;
  let rotationY = 0;

  onMount(async () => {
    initThreeJS();
    await loadMacModel();
    createScreenTexture();
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

    // Dispose of screen texture and material
    if (screenTexture) {
      screenTexture.dispose();
    }
    if (screenMaterial) {
      screenMaterial.dispose();
    }

    // Dispose of renderer
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
    macModel = null;
    screenMaterial = null;
    screenTexture = null;
  }

  function initThreeJS() {
    // Scene setup
    scene = new THREE.Scene();
    scene.background = null; // Transparent background

    // Camera setup
    camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
    camera.position.set(0, 0, 8);

    // Renderer setup
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(600, 600);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Lighting setup
    const ambientLight = new THREE.AmbientLight(0x404040, 0.8);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight.position.set(5, 5, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);

    // Add some warm lighting for Mac aesthetic
    const warmLight = new THREE.PointLight(0xffeecc, 0.3, 15);
    warmLight.position.set(-3, 3, 3);
    scene.add(warmLight);
  }

  function createScreenTexture() {
    // Create a canvas for the screen content
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    // Fill with classic Mac screen green
    ctx.fillStyle = '#00ff00';
    ctx.fillRect(0, 0, 1024, 1024);

    // Add scanlines effect
    ctx.strokeStyle = 'rgba(0, 200, 0, 0.3)';
    ctx.lineWidth = 2;
    for (let i = 0; i < 1024; i += 4) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(1024, i);
      ctx.stroke();
    }

    // Set text properties
    ctx.fillStyle = '#003300';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Main title
    ctx.font = 'bold 72px "Monaco", monospace';
    ctx.fillText('Your Second Brain,', 512, 350);
    ctx.fillText('Supercharged', 512, 450);

    // Tagline
    ctx.font = '48px "Monaco", monospace';
    ctx.fillText('Never lose a brilliant', 512, 580);
    ctx.fillText('idea again.', 512, 640);

    // Add some retro computer elements
    ctx.strokeStyle = '#003300';
    ctx.lineWidth = 3;
    ctx.strokeRect(50, 50, 924, 924);

    // Add blinking cursor
    ctx.fillRect(500, 700, 20, 40);

    // Create texture from canvas
    screenTexture = new THREE.CanvasTexture(canvas);
    screenTexture.needsUpdate = true;

    // Create screen material
    screenMaterial = new THREE.MeshBasicMaterial({
      map: screenTexture,
      transparent: true,
    });
  }

  async function loadMacModel() {
    const loader = new GLTFLoader();

    try {
      const gltf = await loader.loadAsync('/models/mac-classic.glb');
      macModel = gltf.scene;

      // Center and scale the model
      const box = new THREE.Box3().setFromObject(macModel);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());

      // Center the model
      macModel.position.sub(center);

      // Scale to fit nicely
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 5 / maxDim;
      macModel.scale.setScalar(scale);

      // Find and replace screen material
      let screenFound = false;
      macModel.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.castShadow = true;
          child.receiveShadow = true;

          // Look for screen mesh by name first
          if (
            child.material &&
            child.name &&
            (child.name.toLowerCase().includes('screen') ||
              child.name.toLowerCase().includes('display') ||
              child.name.toLowerCase().includes('monitor') ||
              child.name.toLowerCase().includes('crt'))
          ) {
            child.material = screenMaterial;
            screenFound = true;
          }
          // Look for very dark materials (black screen)
          else if (!screenFound && child.material && child.material.color) {
            const color = child.material.color;
            if (color.r < 0.2 && color.g < 0.2 && color.b < 0.2) {
              child.material = screenMaterial;
              screenFound = true;
            }
          }
          // Fallback: Apply to any mesh that looks like it could be a screen
          else if (!screenFound && child.material) {
            // Try applying to any flat, front-facing mesh
            if (child.geometry && child.geometry.attributes.position) {
              child.material = screenMaterial;
              screenFound = true;
            }
          }
        }
      });

      scene.add(macModel);
    } catch (error) {
      console.error('Error loading Mac model:', error);
    }
  }

  function animate() {
    animationId = requestAnimationFrame(animate);

    // Apply user drag rotation only
    if (macModel) {
      macModel.rotation.x = rotationX;
      macModel.rotation.y = rotationY;
    }

    renderer.render(scene, camera);
  }

  function updateRotation() {
    if (macModel) {
      macModel.rotation.x = rotationX;
      macModel.rotation.y = rotationY;
    }
  }

  function handleMouseDown(event: MouseEvent) {
    isDragging = true;
    previousMousePosition.x = event.clientX;
    previousMousePosition.y = event.clientY;
    canvas.style.cursor = 'grabbing';
  }

  function handleMouseMove(event: MouseEvent) {
    if (!isDragging) return;

    const deltaX = event.clientX - previousMousePosition.x;
    const deltaY = event.clientY - previousMousePosition.y;

    rotationY += deltaX * 0.01;
    rotationX += deltaY * 0.01;

    // Clamp rotation X to prevent flipping
    rotationX = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, rotationX));

    updateRotation();

    previousMousePosition.x = event.clientX;
    previousMousePosition.y = event.clientY;
  }

  function handleMouseUp() {
    isDragging = false;
    canvas.style.cursor = 'grab';
  }

  function handleResize() {
    if (renderer && camera) {
      const size = Math.min(600, window.innerWidth * 0.9);
      renderer.setSize(size, size);
      camera.aspect = 1;
      camera.updateProjectionMatrix();
    }
  }

  // Handle window resize
  onMount(() => {
    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  });
</script>

<div class="mac-3d-container" role="button" tabindex="0">
  <!-- 3D Mac Canvas -->
  <canvas bind:this={canvas} class="mac-3d-canvas" on:mousedown={handleMouseDown}></canvas>
</div>

<style>
  .mac-3d-container {
    position: relative;
    width: 100%;
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem;
    background: transparent;
    transition: all 0.3s ease;
  }

  .mac-3d-canvas {
    display: block;
    width: 600px;
    height: 600px;
    max-width: 100%;
    margin: 0 auto;
    background: transparent;
    cursor: grab;
    user-select: none;
  }

  .mac-3d-canvas:active {
    cursor: grabbing;
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .mac-3d-container {
      padding: 1rem;
    }

    .mac-3d-canvas {
      width: 400px;
      height: 400px;
    }
  }

  @media (max-width: 480px) {
    .mac-3d-canvas {
      width: 300px;
      height: 300px;
    }
  }
</style>
