<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
  import { performanceAnalyzer } from '$lib/utils/performanceAnalyzer';
  
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
  
  // Performance monitoring
  let frameCount = 0;
  let lastFPSTime = 0;
  let currentFPS = 0;
  let memoryUsage = { used: 0, total: 0 };
  let renderTime = 0;
  let loadStartTime = 0;
  let webglInfo = { vendor: '', renderer: '', version: '' };
  let networkMetrics = { loadTime: 0, fileSize: 0 };
  
  onMount(async () => {
    console.log('🖥️ Mac3D: Component mounting...');
    const startTime = performance.now();
    
    initThreeJS();
    await loadMacModel();
    createScreenTexture();
    animate();
    
    const loadTime = performance.now() - startTime;
    console.log(`🖥️ Mac3D: Initialized in ${loadTime.toFixed(2)}ms`);
    
    // Monitor performance every 5 seconds
    setInterval(() => {
      monitorPerformance();
    }, 5000);
    
    // Generate performance report every 30 seconds
    setInterval(() => {
      console.log('🔍 Mac3D Deployment Analysis:\n' + performanceAnalyzer.generateReport());
    }, 30000);
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
              object.material.forEach(material => material.dispose());
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
      powerPreference: "high-performance"
    });
    renderer.setSize(600, 600);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    
    // Capture WebGL info for server deployment analysis
    const gl = renderer.getContext();
    webglInfo = {
      vendor: gl.getParameter(gl.VENDOR),
      renderer: gl.getParameter(gl.RENDERER),
      version: gl.getParameter(gl.VERSION)
    };
    
    console.log('🖥️ Mac3D WebGL Info:', webglInfo);
    
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
      transparent: true
    });
  }
  
  async function loadMacModel() {
    const loader = new GLTFLoader();
    loadStartTime = performance.now();
    
    try {
      // Track network performance for server deployment
      const startTime = performance.now();
      const gltf = await loader.loadAsync('/models/mac-classic.glb');
      const endTime = performance.now();
      
      networkMetrics.loadTime = endTime - startTime;
      
      // Estimate file size (rough approximation)
      if (gltf.scene) {
        let vertexCount = 0;
        gltf.scene.traverse((child) => {
          if (child instanceof THREE.Mesh && child.geometry) {
            vertexCount += child.geometry.attributes.position?.count || 0;
          }
        });
        networkMetrics.fileSize = Math.round(vertexCount * 0.1); // Rough estimate in KB
      }
      
      console.log(`🖥️ Mac3D Network Metrics:
        - Load Time: ${networkMetrics.loadTime.toFixed(2)}ms
        - Estimated Size: ${networkMetrics.fileSize}KB
        - Connection: ${navigator.connection?.effectiveType || 'Unknown'}
        - Downlink: ${navigator.connection?.downlink || 'Unknown'}Mbps
      `);
      
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
          if (child.material && child.name && 
              (child.name.toLowerCase().includes('screen') || 
               child.name.toLowerCase().includes('display') ||
               child.name.toLowerCase().includes('monitor') ||
               child.name.toLowerCase().includes('crt'))) {
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
        }
      });
      
      scene.add(macModel);
      console.log('Mac Classic model loaded');
    } catch (error) {
      console.error('Error loading Mac model:', error);
    }
  }
  
  function animate() {
    animationId = requestAnimationFrame(animate);
    
    // FPS monitoring
    frameCount++;
    const currentTime = performance.now();
    if (currentTime >= lastFPSTime + 1000) {
      currentFPS = Math.round((frameCount * 1000) / (currentTime - lastFPSTime));
      frameCount = 0;
      lastFPSTime = currentTime;
    }
    
    // Apply user drag rotation only
    if (macModel) {
      macModel.rotation.x = rotationX;
      macModel.rotation.y = rotationY;
    }
    
    renderer.render(scene, camera);
  }
  
  function monitorPerformance() {
    if (performance.memory) {
      memoryUsage = {
        used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
        total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024)
      };
    }
    
    // Calculate render time for performance analysis
    const renderStart = performance.now();
    if (renderer && scene && camera) {
      renderer.render(scene, camera);
    }
    renderTime = performance.now() - renderStart;
    
    // Server deployment metrics
    const connectionInfo = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    const isSlowConnection = connectionInfo?.effectiveType === '2g' || connectionInfo?.effectiveType === 'slow-2g';
    const batteryInfo = navigator.getBattery ? 'Available' : 'N/A';
    
    console.log(`🖥️ Mac3D Performance:
      - FPS: ${currentFPS} ${currentFPS < 30 ? '⚠️ LOW' : currentFPS < 50 ? '⚡ OK' : '✅ GOOD'}
      - Memory: ${memoryUsage.used}MB / ${memoryUsage.total}MB ${memoryUsage.used > 100 ? '⚠️ HIGH' : '✅ OK'}
      - Render Time: ${renderTime.toFixed(2)}ms ${renderTime > 16 ? '⚠️ SLOW' : '✅ FAST'}
      - WebGL Context: ${renderer?.getContext() ? '✅ Active' : '❌ Lost'}
      - Textures: ${renderer?.info?.memory?.textures || 'N/A'}
      - Geometries: ${renderer?.info?.memory?.geometries || 'N/A'}
      - Network: ${connectionInfo?.effectiveType || 'Unknown'} ${isSlowConnection ? '⚠️ SLOW' : '✅ OK'}
      - Load Time: ${networkMetrics.loadTime.toFixed(0)}ms
      - File Size: ~${networkMetrics.fileSize}KB
    `);
    
    // Feed data to performance analyzer
    performanceAnalyzer.addMetric({
      fps: currentFPS,
      memoryUsed: memoryUsage.used,
      memoryTotal: memoryUsage.total,
      renderTime: renderTime,
      loadTime: networkMetrics.loadTime,
      fileSize: networkMetrics.fileSize,
      networkType: connectionInfo?.effectiveType || 'unknown',
      isWebGLActive: !!renderer?.getContext()
    });
    
    // Alert if performance degrades (important for server deployment)
    if (currentFPS < 30 || memoryUsage.used > 100 || renderTime > 16) {
      console.warn('⚠️ Mac3D: Performance degradation detected! Consider optimizations for server deployment.');
    }
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

<div 
  class="mac-3d-container"
  role="button"
  tabindex="0"
>
  <!-- 3D Mac Canvas -->
  <canvas 
    bind:this={canvas} 
    class="mac-3d-canvas"
    on:mousedown={handleMouseDown}
  ></canvas>
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