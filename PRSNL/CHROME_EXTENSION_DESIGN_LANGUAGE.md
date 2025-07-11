# PRSNL Chrome Extension Design Language Guide

## 🎨 Design Concept: "Neural Chip Module"

The Chrome extension represents a **Neural Processing Unit (NPU)** - a specialized chip that plugs into the browser's motherboard to capture and process web content. Think of it as a dedicated AI accelerator card that seamlessly integrates with the PRSNL mainframe.

## 🖼️ Visual Identity

### Core Concept
- **Theme**: Futuristic circuit board with neural pathways
- **Component Type**: Mini GPU/NPU chip with heat dissipation design
- **Animation**: Rotating Mac Classic 3D model as the "processing core"
- **Color Scheme**: Dark with electric blue/purple accents matching the main app

### Design Elements

#### 1. **3D Mac Model Integration**
```html
<!-- Mini rotating Mac in the corner of popup -->
<div class="mac-processor">
  <canvas id="mac-3d-canvas"></canvas>
  <div class="processing-indicator">
    <div class="pulse-ring"></div>
  </div>
</div>
```

**File Reference**: `/Users/pronav/Personal Knowledge Base/PRSNL/frontend/static/models/mac-classic.glb`

#### 2. **Logo and Branding**
**File Reference**: `/Users/pronav/Personal Knowledge Base/PRSNL/frontend/static/thug-brain-logo.png`
- Use as watermark or subtle background element
- Apply circuit-trace overlay effect

#### 3. **Circuit Board Background Pattern**
Create a subtle PCB trace pattern using CSS:
```css
.popup-container {
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(74, 158, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(220, 20, 60, 0.05) 0%, transparent 50%),
    url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M10,50 L30,50 L35,45 L65,45 L70,50 L90,50" stroke="%23333" stroke-width="0.5" fill="none" opacity="0.3"/></svg>');
  background-size: 100% 100%, 100% 100%, 50px 50px;
}
```

## 🎯 UI Components Design

### 1. **Popup Window - "Neural Chip Interface"**
```
┌─────────────────────────────────────┐
│  ┌─────┐  PRSNL NEURAL CAPTURE      │
│  │ Mac │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓         │
│  │ 3D  │  Processing Unit v4.1      │
│  └─────┘                            │
├─────────────────────────────────────┤
│  ╔═══════════════════════════════╗  │
│  ║   CONTENT ANALYSIS MODULE     ║  │
│  ╠═══════════════════════════════╣  │
│  ║ Type: [====Auto-Detect====] ▼ ║  │
│  ║ ┌───────────────────────────┐ ║  │
│  ║ │ 🧠 Neural Processing: ON  │ ║  │
│  ║ └───────────────────────────┘ ║  │
│  ╚═══════════════════════════════╝  │
│                                     │
│  [█████ CAPTURE DATA █████]         │
│  [     CANCEL PROCESS    ]          │
└─────────────────────────────────────┘
```

### 2. **Color Palette**
```css
:root {
  /* Primary Neural Colors */
  --neural-dark: #0a0a0a;
  --neural-surface: #1a1a1a;
  --neural-border: #333;
  
  /* Circuit Trace Colors */
  --trace-primary: #4a9eff;
  --trace-secondary: #dc143c;
  --trace-gold: #ffd700;
  
  /* Processing States */
  --processing-active: #00ff00;
  --processing-idle: #666;
  --processing-error: #ff0040;
  
  /* Text Hierarchy */
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0a0;
  --text-muted: #666;
  
  /* Glow Effects */
  --glow-blue: 0 0 20px rgba(74, 158, 255, 0.5);
  --glow-red: 0 0 20px rgba(220, 20, 60, 0.3);
  --glow-processing: 0 0 30px rgba(0, 255, 0, 0.4);
}
```

### 3. **Typography**
```css
/* Import futuristic fonts */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@200;300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* Font System */
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
--font-display: 'Space Grotesk', -apple-system, sans-serif;
```

## 🔧 Component Styling

### 1. **Heat Sink Design for Headers**
```css
.extension-header {
  background: linear-gradient(180deg, #2a2a2a 0%, #1a1a1a 100%);
  border-bottom: 2px solid var(--trace-primary);
  position: relative;
  overflow: hidden;
}

.extension-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 200%;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--trace-primary) 50%, 
    transparent 100%);
  animation: scan 3s linear infinite;
}

@keyframes scan {
  to { left: 100%; }
}
```

### 2. **Chip-Style Buttons**
```css
.chip-button {
  background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
  border: 1px solid var(--neural-border);
  border-radius: 4px;
  padding: 12px 24px;
  font-family: var(--font-mono);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chip-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, 
    transparent 30%, 
    rgba(74, 158, 255, 0.1) 50%, 
    transparent 70%);
  transform: translateX(-100%);
  transition: transform 0.6s;
}

.chip-button:hover::before {
  transform: translateX(100%);
}

.chip-button:hover {
  border-color: var(--trace-primary);
  box-shadow: var(--glow-blue);
  transform: translateY(-2px);
}
```

### 3. **Neural Network Background Animation**
```css
.neural-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.05;
  pointer-events: none;
  background-image: 
    radial-gradient(circle at 25% 25%, var(--trace-primary) 0%, transparent 25%),
    radial-gradient(circle at 75% 75%, var(--trace-secondary) 0%, transparent 25%);
  background-size: 50px 50px;
  animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.05; }
  50% { opacity: 0.1; }
}
```

### 4. **PCB Trace Connectors**
```css
.trace-connector {
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--trace-gold) 10%, 
    var(--trace-gold) 90%, 
    transparent 100%);
  position: relative;
  margin: 20px 0;
}

.trace-connector::before,
.trace-connector::after {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--trace-gold);
  border-radius: 50%;
  top: 50%;
  transform: translateY(-50%);
  box-shadow: 0 0 10px var(--trace-gold);
}

.trace-connector::before { left: 8%; }
.trace-connector::after { right: 8%; }
```

## 🎮 Interactive Elements

### 1. **Processing Indicator**
```css
.processing-core {
  width: 60px;
  height: 60px;
  border: 2px solid var(--neural-border);
  border-radius: 8px;
  position: relative;
  background: radial-gradient(circle, #1a1a1a 0%, #0a0a0a 100%);
}

.processing-core.active {
  animation: processing 2s linear infinite;
}

@keyframes processing {
  0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.7); }
  50% { box-shadow: 0 0 20px 10px rgba(0, 255, 0, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0); }
}
```

### 2. **Data Flow Visualization**
```css
.data-flow {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--processing-active) 50%, 
    transparent 100%);
  transform: scaleX(0);
  transform-origin: left;
}

.data-flow.active {
  animation: dataTransfer 1.5s ease-in-out;
}

@keyframes dataTransfer {
  0% { transform: scaleX(0); }
  50% { transform: scaleX(1); }
  100% { transform: scaleX(0); transform-origin: right; }
}
```

## 📐 Layout Structure

### Extension Popup Layout (400x600px)
```
┌─────────────────────────────────────────┐
│  Header (80px)                          │
│  - Logo + 3D Mac Mini (40x40)          │
│  - Title + Status LED                  │
├─────────────────────────────────────────┤
│  Control Panel (200px)                  │
│  - Content Type Selector               │
│  - AI Processing Toggle                │
│  - Development Fields (collapsible)    │
├─────────────────────────────────────────┤
│  Data Input Module (150px)              │
│  - Tags Input                          │
│  - Selection Preview                   │
├─────────────────────────────────────────┤
│  Action Console (70px)                  │
│  - Primary Action (Capture)            │
│  - Secondary Action (Cancel)           │
└─────────────────────────────────────────┘
```

## 🚀 Animation Guidelines

### 1. **Micro-interactions**
- Hover effects: Scale + glow
- Click feedback: Ripple effect from click point
- Toggle switches: Smooth slide with color transition
- Loading states: Pulsing circuits

### 2. **3D Mac Animation**
```javascript
// Continuous rotation with mouse interaction
const rotationSpeed = 0.001;
macModel.rotation.y += rotationSpeed;

// Pulse effect on capture
if (isCapturing) {
  const scale = 1 + Math.sin(Date.now() * 0.005) * 0.1;
  macModel.scale.set(scale, scale, scale);
}
```

### 3. **Transitions**
```css
/* Smooth state transitions */
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
```

## 🔌 Implementation Notes

### Required Files from Main App:
1. **3D Model**: `/Users/pronav/Personal Knowledge Base/PRSNL/frontend/static/models/mac-classic.glb`
2. **Logo**: `/Users/pronav/Personal Knowledge Base/PRSNL/frontend/static/thug-brain-logo.png`
3. **Font Files**: Google Fonts (JetBrains Mono, Space Grotesk)

### Three.js Setup for Extension:
```javascript
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

// Minimal Three.js scene for extension
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ 
  canvas: document.getElementById('mac-3d-canvas'),
  alpha: true,
  antialias: true 
});
renderer.setSize(40, 40); // Small size for extension
```

### Performance Considerations:
- Use CSS animations instead of JS when possible
- Limit 3D model polygon count
- Implement lazy loading for heavy assets
- Use CSS containment for better performance

## 🎯 Design Principles

1. **Minimalist Complexity**: Simple interface with sophisticated details
2. **Functional Beauty**: Every visual element serves a purpose
3. **Consistent Language**: Matches main app's neural/electrical theme
4. **Performance First**: Smooth animations without sacrificing speed
5. **Accessibility**: High contrast, clear typography, keyboard navigation

---

This design language creates a cohesive experience that makes the Chrome extension feel like a natural extension of the PRSNL ecosystem - a specialized neural processing chip that plugs into your browser's motherboard.