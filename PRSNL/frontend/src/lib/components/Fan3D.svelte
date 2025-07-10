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
  let animationId: number;
  let isHovered = false;
  let rotationSpeed = 0.1;
  
  onMount(async () => {
    initThreeJS();
    await loadFanModel();
    animate();
  });
  
  onDestroy(() => {
    if (animationId) {
      cancelAnimationFrame(animationId);
    }
    if (renderer) {
      renderer.dispose();
    }
  });
  
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
      powerPreference: "high-performance"
    });
    renderer.setSize(300, 300);
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
    
    const greenLight = new THREE.PointLight(0x00ff00, 0.2, 10);
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
          console.log(`Mesh ${index}: ${child.name}, vertices: ${child.geometry.attributes.position.count}`);
        }
      });
      
      // Center and scale the model
      const box = new THREE.Box3().setFromObject(fanModel);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      
      // Center the model
      fanModel.position.sub(center);
      
      // Scale to fit nicely
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 3 / maxDim;
      fanModel.scale.setScalar(scale);
      
      // Create separate groups for frame and blades
      const bladesGroup = new THREE.Group();
      const frameGroup = new THREE.Group();
      
      // Analyze each mesh to determine if it's a blade or frame
      const meshes: { mesh: THREE.Mesh, vertices: number, name: string }[] = [];
      
      fanModel.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.castShadow = true;
          child.receiveShadow = true;
          
          // Enhance materials
          if (child.material) {
            child.material.metalness = 0.7;
            child.material.roughness = 0.3;
          }
          
          meshes.push({
            mesh: child,
            vertices: child.geometry.attributes.position.count,
            name: child.name
          });
        }
      });
      
      // Sort by vertex count - blades usually have fewer vertices than the frame
      meshes.sort((a, b) => a.vertices - b.vertices);
      
      console.log('Meshes sorted by vertex count:');
      meshes.forEach((item, index) => {
        console.log(`${index}: ${item.name} - ${item.vertices} vertices`);
      });
      
      // Typically, the frame is the largest mesh, blades are smaller
      const frameThreshold = meshes.length > 1 ? meshes[meshes.length - 1].vertices * 0.3 : 1000;
      
      meshes.forEach((item) => {
        const clonedMesh = item.mesh.clone();
        
        // If it has fewer vertices than threshold, it's likely a blade
        if (item.vertices < frameThreshold) {
          bladesGroup.add(clonedMesh);
          console.log(`Added to blades: ${item.name} (${item.vertices} vertices)`);
        } else {
          frameGroup.add(clonedMesh);
          console.log(`Added to frame: ${item.name} (${item.vertices} vertices)`);
        }
        
        // Hide original mesh
        item.mesh.visible = false;
      });
      
      // Add groups to scene
      scene.add(frameGroup);
      scene.add(bladesGroup);
      
      // Store references
      fanFrame.push(frameGroup);
      fanBlades.push(bladesGroup);
      
      console.log(`Frame group has ${frameGroup.children.length} parts`);
      console.log(`Blades group has ${bladesGroup.children.length} parts`);
      
      scene.add(fanModel);
    } catch (error) {
      console.error('Error loading fan model:', error);
    }
  }
  
  function animate() {
    animationId = requestAnimationFrame(animate);
    
    // Rotate only the fan blades if not hovered
    if (!isHovered && fanBlades.length > 0) {
      fanBlades.forEach(blade => {
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
      const size = Math.min(300, window.innerWidth * 0.8);
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
  class="fan-3d-container"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  role="button"
  tabindex="0"
>
  <canvas bind:this={canvas} class="fan-3d-canvas"></canvas>
  
  <!-- Performance Stats -->
  <div class="fan-stats">
    <div class="stat-item">
      <span class="stat-label">Status</span>
      <span class="stat-value status-{isHovered ? 'paused' : 'active'}">
        {isHovered ? 'Paused' : 'Active'}
      </span>
    </div>
    <div class="stat-item">
      <span class="stat-label">RPM</span>
      <span class="stat-value">{isHovered ? '0' : '1800'}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Temp</span>
      <span class="stat-value">{isHovered ? '45°C' : '42°C'}</span>
    </div>
  </div>
  
  <!-- Fan Wiring -->
  <div class="fan-wiring">
    <div class="wire red"></div>
    <div class="wire black"></div>
    <div class="wire yellow"></div>
    <div class="wire blue"></div>
  </div>
</div>

<style>
  .fan-3d-container {
    position: relative;
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
    padding: 2rem;
    background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%);
    border-radius: 2rem;
    box-shadow: 
      0 20px 40px rgba(0, 0, 0, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .fan-3d-container:hover {
    box-shadow: 
      0 25px 50px rgba(0, 0, 0, 0.6),
      inset 0 1px 0 rgba(255, 255, 255, 0.15);
    transform: translateY(-5px);
  }
  
  .fan-3d-canvas {
    display: block;
    width: 300px;
    height: 300px;
    max-width: 100%;
    margin: 0 auto;
    border-radius: 1rem;
  }
  
  .fan-stats {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 1.5rem;
    flex-wrap: wrap;
  }
  
  .stat-item {
    text-align: center;
  }
  
  .stat-label {
    display: block;
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
  }
  
  .stat-value {
    display: block;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  .status-active {
    color: #00ff00;
  }
  
  .status-paused {
    color: #ff6600;
  }
  
  .fan-wiring {
    position: absolute;
    bottom: 15px;
    right: 15px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  
  .wire {
    width: 50px;
    height: 3px;
    border-radius: 1.5px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  }
  
  .wire.red {
    background: linear-gradient(90deg, #ff0000 0%, #cc0000 100%);
  }
  
  .wire.black {
    background: linear-gradient(90deg, #333 0%, #000 100%);
  }
  
  .wire.yellow {
    background: linear-gradient(90deg, #ffff00 0%, #cccc00 100%);
  }
  
  .wire.blue {
    background: linear-gradient(90deg, #0000ff 0%, #0000cc 100%);
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .fan-3d-container {
      padding: 1.5rem;
    }
    
    .fan-3d-canvas {
      width: 250px;
      height: 250px;
    }
    
    .fan-stats {
      gap: 1rem;
      margin-top: 1rem;
    }
    
    .stat-value {
      font-size: 1rem;
    }
  }
  
  @media (max-width: 480px) {
    .fan-3d-container {
      padding: 1rem;
    }
    
    .fan-3d-canvas {
      width: 200px;
      height: 200px;
    }
    
    .fan-stats {
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .wire {
      width: 40px;
    }
  }
</style>