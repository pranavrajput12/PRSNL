// Audio Manager for Gamified Visualizations
export class AudioManager {
  private audioContext: AudioContext | null = null;
  private sounds: Map<string, AudioBuffer> = new Map();
  private musicGainNode: GainNode | null = null;
  private effectsGainNode: GainNode | null = null;
  private currentMusic: AudioBufferSourceNode | null = null;
  private enabled: boolean = true;

  constructor() {
    // Only initialize in browser environment
    if (typeof window !== 'undefined' && window.AudioContext) {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Create gain nodes for volume control
      this.musicGainNode = this.audioContext.createGain();
      this.musicGainNode.gain.value = 0.3; // Background music volume
      this.musicGainNode.connect(this.audioContext.destination);
      
      this.effectsGainNode = this.audioContext.createGain();
      this.effectsGainNode.gain.value = 0.5; // Sound effects volume
      this.effectsGainNode.connect(this.audioContext.destination);
    }
  }

  // Initialize audio context on user interaction
  async init() {
    if (!this.audioContext) {
      // Try to initialize if we're now in browser
      if (typeof window !== 'undefined' && window.AudioContext) {
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        
        // Create gain nodes for volume control
        this.musicGainNode = this.audioContext.createGain();
        this.musicGainNode.gain.value = 0.3;
        this.musicGainNode.connect(this.audioContext.destination);
        
        this.effectsGainNode = this.audioContext.createGain();
        this.effectsGainNode.gain.value = 0.5;
        this.effectsGainNode.connect(this.audioContext.destination);
      } else {
        return;
      }
    }
    
    if (this.audioContext && this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }
  }

  // Create synthetic sounds
  createSyntheticSounds() {
    // Whoosh sound for galaxy
    this.createWhoosh('whoosh');
    
    // Bubble sound for DNA
    this.createBubble('bubble');
    
    // Level up sound for avatar
    this.createLevelUp('levelup');
    
    // Engine sound for racing
    this.createEngine('engine');
    
    // Nature sounds for terrarium
    this.createChirp('chirp');
  }

  private createWhoosh(name: string) {
    if (!this.audioContext) return;
    const duration = 0.5;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(1, duration * sampleRate, sampleRate);
    const data = buffer.getChannelData(0);
    
    for (let i = 0; i < data.length; i++) {
      const t = i / sampleRate;
      const envelope = Math.sin(Math.PI * t / duration);
      data[i] = (Math.random() - 0.5) * envelope * 0.3;
    }
    
    this.sounds.set(name, buffer);
  }

  private createBubble(name: string) {
    if (!this.audioContext) return;
    const duration = 0.3;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(1, duration * sampleRate, sampleRate);
    const data = buffer.getChannelData(0);
    
    for (let i = 0; i < data.length; i++) {
      const t = i / sampleRate;
      const frequency = 200 + Math.sin(t * 10) * 100;
      const envelope = Math.exp(-t * 5);
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope * 0.3;
    }
    
    this.sounds.set(name, buffer);
  }

  private createLevelUp(name: string) {
    if (!this.audioContext) return;
    const duration = 0.8;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(1, duration * sampleRate, sampleRate);
    const data = buffer.getChannelData(0);
    
    for (let i = 0; i < data.length; i++) {
      const t = i / sampleRate;
      const frequency = 440 * Math.pow(2, t * 2); // Rising pitch
      const envelope = Math.exp(-t * 2);
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope * 0.3;
    }
    
    this.sounds.set(name, buffer);
  }

  private createEngine(name: string) {
    if (!this.audioContext) return;
    const duration = 2;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(1, duration * sampleRate, sampleRate);
    const data = buffer.getChannelData(0);
    
    for (let i = 0; i < data.length; i++) {
      const t = i / sampleRate;
      const frequency = 60 + Math.sin(t * 2) * 20;
      const noise = (Math.random() - 0.5) * 0.1;
      data[i] = (Math.sin(2 * Math.PI * frequency * t) + noise) * 0.2;
    }
    
    this.sounds.set(name, buffer);
  }

  private createChirp(name: string) {
    if (!this.audioContext) return;
    const duration = 0.2;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(1, duration * sampleRate, sampleRate);
    const data = buffer.getChannelData(0);
    
    for (let i = 0; i < data.length; i++) {
      const t = i / sampleRate;
      const frequency = 2000 + Math.sin(t * 50) * 500;
      const envelope = Math.exp(-t * 10);
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope * 0.2;
    }
    
    this.sounds.set(name, buffer);
  }

  // Play a sound effect
  playSound(soundName: string, volume: number = 1) {
    if (!this.enabled || !this.audioContext || !this.effectsGainNode) return;
    
    const buffer = this.sounds.get(soundName);
    if (!buffer) return;
    
    const source = this.audioContext.createBufferSource();
    source.buffer = buffer;
    
    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = volume;
    
    source.connect(gainNode);
    gainNode.connect(this.effectsGainNode);
    
    source.start();
  }

  // Create and play background music
  playBackgroundMusic(type: 'space' | 'lab' | 'rpg' | 'racing' | 'nature') {
    if (!this.enabled || !this.audioContext || !this.musicGainNode) return;
    
    // Stop current music
    if (this.currentMusic) {
      this.currentMusic.stop();
    }
    
    // Create procedural background music based on type
    const duration = 30; // 30 second loop
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(2, duration * sampleRate, sampleRate);
    
    // Generate different music styles
    switch (type) {
      case 'space':
        this.generateSpaceMusic(buffer);
        break;
      case 'lab':
        this.generateLabMusic(buffer);
        break;
      case 'rpg':
        this.generateRPGMusic(buffer);
        break;
      case 'racing':
        this.generateRacingMusic(buffer);
        break;
      case 'nature':
        this.generateNatureMusic(buffer);
        break;
    }
    
    const source = this.audioContext.createBufferSource();
    source.buffer = buffer;
    source.loop = true;
    source.connect(this.musicGainNode);
    source.start();
    
    this.currentMusic = source;
  }

  private generateSpaceMusic(buffer: AudioBuffer) {
    const leftChannel = buffer.getChannelData(0);
    const rightChannel = buffer.getChannelData(1);
    const sampleRate = buffer.sampleRate;
    
    for (let i = 0; i < leftChannel.length; i++) {
      const t = i / sampleRate;
      
      // Deep space ambience
      const pad1 = Math.sin(2 * Math.PI * 55 * t) * 0.1;
      const pad2 = Math.sin(2 * Math.PI * 82.5 * t) * 0.08;
      const pad3 = Math.sin(2 * Math.PI * 110 * t) * 0.06;
      
      // Slow modulation
      const lfo = Math.sin(2 * Math.PI * 0.1 * t);
      
      leftChannel[i] = (pad1 + pad2 + pad3) * (1 + lfo * 0.3);
      rightChannel[i] = (pad1 + pad2 + pad3) * (1 - lfo * 0.3);
    }
  }

  private generateLabMusic(buffer: AudioBuffer) {
    const leftChannel = buffer.getChannelData(0);
    const rightChannel = buffer.getChannelData(1);
    const sampleRate = buffer.sampleRate;
    
    for (let i = 0; i < leftChannel.length; i++) {
      const t = i / sampleRate;
      
      // Electronic beeps and bubbles
      const beep1 = Math.sin(2 * Math.PI * 440 * t) * (t % 2 < 0.1 ? 0.1 : 0);
      const beep2 = Math.sin(2 * Math.PI * 880 * t) * (t % 3 < 0.1 ? 0.08 : 0);
      const bubble = Math.sin(2 * Math.PI * (200 + Math.sin(t * 5) * 50) * t) * 0.05;
      
      leftChannel[i] = beep1 + beep2 + bubble;
      rightChannel[i] = beep1 + beep2 + bubble;
    }
  }

  private generateRPGMusic(buffer: AudioBuffer) {
    const leftChannel = buffer.getChannelData(0);
    const rightChannel = buffer.getChannelData(1);
    const sampleRate = buffer.sampleRate;
    
    for (let i = 0; i < leftChannel.length; i++) {
      const t = i / sampleRate;
      
      // Heroic melody
      const melody = Math.sin(2 * Math.PI * 293.66 * t) * 0.1; // D4
      const harmony = Math.sin(2 * Math.PI * 440 * t) * 0.08; // A4
      const bass = Math.sin(2 * Math.PI * 73.42 * t) * 0.12; // D2
      
      leftChannel[i] = melody + harmony + bass;
      rightChannel[i] = melody + harmony + bass;
    }
  }

  private generateRacingMusic(buffer: AudioBuffer) {
    const leftChannel = buffer.getChannelData(0);
    const rightChannel = buffer.getChannelData(1);
    const sampleRate = buffer.sampleRate;
    
    for (let i = 0; i < leftChannel.length; i++) {
      const t = i / sampleRate;
      
      // Fast-paced electronic beats
      const kick = Math.sin(2 * Math.PI * 60 * t) * (t % 0.5 < 0.1 ? 0.3 : 0);
      const hihat = (Math.random() - 0.5) * (t % 0.125 < 0.05 ? 0.1 : 0);
      const bass = Math.sin(2 * Math.PI * 110 * t) * 0.1;
      
      leftChannel[i] = kick + hihat + bass;
      rightChannel[i] = kick + hihat + bass;
    }
  }

  private generateNatureMusic(buffer: AudioBuffer) {
    const leftChannel = buffer.getChannelData(0);
    const rightChannel = buffer.getChannelData(1);
    const sampleRate = buffer.sampleRate;
    
    for (let i = 0; i < leftChannel.length; i++) {
      const t = i / sampleRate;
      
      // Peaceful nature sounds
      const wind = (Math.random() - 0.5) * 0.02;
      const wave1 = Math.sin(2 * Math.PI * 0.05 * t) * 0.05;
      const wave2 = Math.sin(2 * Math.PI * 0.07 * t) * 0.04;
      
      leftChannel[i] = wind + wave1 + wave2;
      rightChannel[i] = wind + wave1 + wave2;
    }
  }

  // Toggle audio on/off
  toggle() {
    this.enabled = !this.enabled;
    if (!this.enabled && this.currentMusic) {
      this.currentMusic.stop();
      this.currentMusic = null;
    }
  }

  // Set volume levels
  setMusicVolume(volume: number) {
    if (this.musicGainNode) {
      this.musicGainNode.gain.value = Math.max(0, Math.min(1, volume));
    }
  }

  setEffectsVolume(volume: number) {
    if (this.effectsGainNode) {
      this.effectsGainNode.gain.value = Math.max(0, Math.min(1, volume));
    }
  }

  // Cleanup
  destroy() {
    if (this.currentMusic) {
      this.currentMusic.stop();
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
  }
}

// Singleton instance - lazy initialization
let audioManagerInstance: AudioManager | null = null;

export const getAudioManager = (): AudioManager => {
  if (!audioManagerInstance && typeof window !== 'undefined') {
    audioManagerInstance = new AudioManager();
  }
  return audioManagerInstance || new AudioManager();
};