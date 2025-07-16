<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';

  export let particleCount = 80;
  export let connectionDistance = 150;
  export let particleSpeed = 0.5;
  export let mouseInfluence = true;
  export let colorScheme = {
    particles: '#8b5cf6', // purple
    connections: '#ec4899', // pink
    mouseGlow: '#10b981' // green
  };

  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let particles: Particle[] = [];
  let mousePosition = { x: 0, y: 0 };
  let animationId: number;

  class Particle {
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    pulsePhase: number;

    constructor(width: number, height: number) {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.vx = (Math.random() - 0.5) * particleSpeed;
      this.vy = (Math.random() - 0.5) * particleSpeed;
      this.radius = Math.random() * 2 + 1;
      this.pulsePhase = Math.random() * Math.PI * 2;
    }

    update(width: number, height: number) {
      // Add slight floating motion
      this.x += this.vx;
      this.y += this.vy;
      this.pulsePhase += 0.02;

      // Bounce off edges smoothly
      if (this.x <= 0 || this.x >= width) this.vx *= -1;
      if (this.y <= 0 || this.y >= height) this.vy *= -1;

      // Keep particles in bounds
      this.x = Math.max(0, Math.min(width, this.x));
      this.y = Math.max(0, Math.min(height, this.y));
    }

    draw(ctx: CanvasRenderingContext2D) {
      const pulseFactor = 1 + Math.sin(this.pulsePhase) * 0.2;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius * pulseFactor, 0, Math.PI * 2);
      ctx.fillStyle = colorScheme.particles + '88'; // Add transparency
      ctx.fill();
      
      // Add glow effect
      const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.radius * pulseFactor * 3);
      gradient.addColorStop(0, colorScheme.particles + '44');
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.fill();
    }
  }

  function initCanvas() {
    if (!canvas || !browser) return;
    
    ctx = canvas.getContext('2d')!;
    resizeCanvas();
    initParticles();
    animate();
  }

  function resizeCanvas() {
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function initParticles() {
    particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle(canvas.width, canvas.height));
    }
  }

  function drawConnections() {
    ctx.strokeStyle = colorScheme.connections + '22';
    ctx.lineWidth = 1;

    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < connectionDistance) {
          const opacity = (1 - distance / connectionDistance) * 0.5;
          ctx.strokeStyle = colorScheme.connections + Math.floor(opacity * 255).toString(16).padStart(2, '0');
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }

      // Mouse connections
      if (mouseInfluence && mousePosition.x > 0) {
        const dx = particles[i].x - mousePosition.x;
        const dy = particles[i].y - mousePosition.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < connectionDistance * 1.5) {
          const opacity = (1 - distance / (connectionDistance * 1.5)) * 0.7;
          ctx.strokeStyle = colorScheme.mouseGlow + Math.floor(opacity * 255).toString(16).padStart(2, '0');
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(mousePosition.x, mousePosition.y);
          ctx.stroke();

          // Attract particles slightly to mouse
          particles[i].vx += dx * 0.00001;
          particles[i].vy += dy * 0.00001;
        }
      }
    }
  }

  function animate() {
    if (!ctx || !canvas) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update and draw particles
    particles.forEach(particle => {
      particle.update(canvas.width, canvas.height);
    });

    // Draw connections first (behind particles)
    drawConnections();

    // Draw particles
    particles.forEach(particle => {
      particle.draw(ctx);
    });

    animationId = requestAnimationFrame(animate);
  }

  function handleMouseMove(e: MouseEvent) {
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    mousePosition = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }

  function handleMouseLeave() {
    mousePosition = { x: -1000, y: -1000 };
  }

  onMount(() => {
    if (browser) {
      initCanvas();
      window.addEventListener('resize', resizeCanvas);
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseleave', handleMouseLeave);
    }
  });

  onDestroy(() => {
    if (browser && animationId) {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
    }
  });
</script>

<canvas
  bind:this={canvas}
  class="neural-canvas"
/>

<style>
  .neural-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 1;
  }
</style>