import * as THREE from './vendor/three.module.js';
import { GLTFLoader } from './vendor/GLTFLoader.js';

// State management
let currentTab = null;
let selectedText = '';
let tags = [];
let isCapturing = false;

// 3D Scene
let scene, camera, renderer, macModel;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  // Get current tab info
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tab;
  
  // Display tab info
  displayTabInfo(tab);
  
  // Check for selected text
  chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (response) => {
    if (response && response.selection) {
      selectedText = response.selection;
      displaySelection(selectedText);
    }
  });
  
  // Set up event listeners
  setupEventListeners();
  
  // Auto-detect content type
  autoDetectContentType(tab.url);

  // Initialize 3D scene
  init3D();
});

// Display tab information
function displayTabInfo(tab) {
  const favicon = document.getElementById('favicon-container');
  const title = document.getElementById('page-title');
  const url = document.getElementById('page-url');
  
  // Set favicon
  const faviconUrl = `https://www.google.com/s2/favicons?domain=${new URL(tab.url).hostname}&sz=32`;
  if (favicon) {
    favicon.innerHTML = `<img src="${faviconUrl}" alt="Site favicon" />`;
  }
  
  // Set title and URL
  if (title) {
    title.textContent = tab.title;
  }
  if (url) {
    url.textContent = tab.url;
  }
}

// Display selected text
function displaySelection(text) {
  const container = document.getElementById('selection-container');
  const textElement = document.getElementById('selection-text');
  
  if (text && text.trim() && container && textElement) {
    container.style.display = 'block';
    textElement.textContent = text.substring(0, 200) + (text.length > 200 ? '...' : '');
  }
}

// Auto-detect content type based on URL
function autoDetectContentType(url) {
  const contentTypeSelect = document.getElementById('content-type');
  if (!contentTypeSelect) return;

  if (url.includes('github.com')) {
    contentTypeSelect.value = 'development';
    toggleDevelopmentFields(true);
  } else if (url.includes('youtube.com') || url.includes('youtu.be')) {
    contentTypeSelect.value = 'video';
  } else if (url.includes('medium.com') || url.includes('dev.to')) {
    contentTypeSelect.value = 'article';
  }
}

// Toggle development fields visibility
function toggleDevelopmentFields(show) {
  const devFields = document.getElementById('development-fields');
  if (devFields) {
    devFields.style.display = show ? 'block' : 'none';
  }
}

// Set up all event listeners
function setupEventListeners() {
  const contentTypeSelect = document.getElementById('content-type');
  if (contentTypeSelect) {
    contentTypeSelect.addEventListener('change', (e) => {
      toggleDevelopmentFields(e.target.value === 'development');
    });
  }

  const tagInput = document.getElementById('tag-input');
  if (tagInput) {
    tagInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.target.value.trim()) {
        e.preventDefault();
        addTag(e.target.value.trim());
        e.target.value = '';
      }
    });
  }

  const captureBtn = document.getElementById('capture-btn');
  if (captureBtn) {
    captureBtn.addEventListener('click', handleCapture);
  }

  const cancelBtn = document.getElementById('cancel-btn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      window.close();
    });
  }

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleCapture();
    }
    if (e.key === 'Escape') {
      window.close();
    }
  });
}

// Add a tag
function addTag(tagText) {
  if (tags.includes(tagText.toLowerCase())) return;
  
  tags.push(tagText.toLowerCase());
  renderTags();
}

// Remove a tag
function removeTag(tagText) {
  tags = tags.filter(t => t !== tagText);
  renderTags();
}

// Render tags
function renderTags() {
  const container = document.getElementById('tags-container');
  if (!container) return;

  container.innerHTML = tags.map(tag => `
    <span class="tag">
      ${tag}
      <button class="tag-remove" data-tag="${tag}">×</button>
    </span>
  `).join('');
  
  // Add remove listeners
  container.querySelectorAll('.tag-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      removeTag(e.target.dataset.tag);
    });
  });
}

// Handle capture
async function handleCapture() {
  if (isCapturing) return;
  
  isCapturing = true;
  const captureBtn = document.getElementById('capture-btn');
  const btnText = captureBtn.querySelector('.btn-text');
  const btnLoader = captureBtn.querySelector('.btn-loader');
  
  // Show loading state
  btnText.style.display = 'none';
  btnLoader.style.display = 'inline-block';
  captureBtn.disabled = true;
  
  try {
    // Gather form data
    const captureData = {
      url: currentTab.url,
      title: currentTab.title,
      content: selectedText || null,
      highlight: selectedText || null,
      tags: tags,
      enable_summarization: document.getElementById('enable-summarization').checked,
      content_type: document.getElementById('content-type').value
    };
    
    // Add development fields if applicable
    if (captureData.content_type === 'development') {
      const progLang = document.getElementById('programming-language').value;
      const projCat = document.getElementById('project-category').value;
      const diffLevel = document.getElementById('difficulty-level').value;
      const careerRelated = document.getElementById('career-related').checked;
      
      if (progLang) captureData.programming_language = progLang;
      if (projCat) captureData.project_category = projCat;
      if (diffLevel) captureData.difficulty_level = parseInt(diffLevel);
      captureData.is_career_related = careerRelated;
    }
    
    // Send to backend
    chrome.runtime.sendMessage({ action: 'capture', data: captureData }, (response) => {
      if (response.success) {
        showStatus('Content captured successfully!', 'success');
        setTimeout(() => {
          window.close();
        }, 1500);
      } else {
        showStatus(response.error || 'Failed to capture content', 'error');
      }
    });

  } catch (error) {
    console.error('Capture error:', error);
    showStatus(error.message || 'Failed to capture content', 'error');
  } finally {
    // Reset button state
    btnText.style.display = 'inline-block';
    btnLoader.style.display = 'none';
    captureBtn.disabled = false;
    isCapturing = false;
  }
}

// Show status message
function showStatus(message, type) {
  const statusEl = document.getElementById('status-message');
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.style.display = 'block';
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    statusEl.style.display = 'none';
  }, 5000);
}

// Initialize 3D scene
function init3D() {
  const canvas = document.getElementById('mac-3d-canvas');
  if (!canvas) return;

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
  renderer = new THREE.WebGLRenderer({ 
    canvas: canvas,
    alpha: true,
    antialias: true 
  });
  renderer.setSize(40, 40);

  const loader = new GLTFLoader();
  loader.load('./models/mac-classic.glb', (gltf) => {
    macModel = gltf.scene;
    macModel.scale.set(0.5, 0.5, 0.5);
    scene.add(macModel);
  }, undefined, (error) => {
    console.error('An error happened while loading the model:', error);
  });

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(5, 10, 7.5);
  scene.add(directionalLight);

  camera.position.z = 5;

  animate();
}

// Animation loop
function animate() {
  requestAnimationFrame(animate);

  if (macModel) {
    macModel.rotation.y += 0.01;
  }

  if (isCapturing) {
    const scale = 1 + Math.sin(Date.now() * 0.005) * 0.1;
    if(macModel) macModel.scale.set(scale, scale, scale);
  }

  renderer.render(scene, camera);
}