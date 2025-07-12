<script lang="ts" type="module">
  import { onMount } from 'svelte';
  import { spring } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import Fan3D from './Fan3D.svelte';

  export let items = [];
  export let onDateClick = (date: Date, items: any[]) => {};

  let currentDate = new Date();
  let currentMonth = currentDate.getMonth();
  let currentYear = currentDate.getFullYear();
  let hoveredDay = null;

  // Spring animations for smooth transitions
  const rotateX = spring(0, { stiffness: 0.1, damping: 0.9 });
  const rotateY = spring(0, { stiffness: 0.1, damping: 0.9 });

  // Get days in month
  function getDaysInMonth(year: number, month: number) {
    return new Date(year, month + 1, 0).getDate();
  }

  // Get first day of month (0 = Sunday, 6 = Saturday)
  function getFirstDayOfMonth(year: number, month: number) {
    return new Date(year, month, 1).getDay();
  }

  // Get calendar days for current month only
  function getCalendarDays() {
    const daysInMonth = getDaysInMonth(currentYear, currentMonth);
    const firstDay = getFirstDayOfMonth(currentYear, currentMonth);
    const days = [];

    // Add empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }

    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }

    return days;
  }

  // Count items for a specific date
  function getItemsForDate(day: number) {
    if (!day) return [];

    const date = new Date(currentYear, currentMonth, day);
    const dateStr = date.toDateString();

    return items.filter((item) => {
      const itemDate = new Date(item.createdAt);
      return itemDate.toDateString() === dateStr;
    });
  }

  // Handle mouse movement for 3D effect
  function handleMouseMove(event: MouseEvent) {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;

    // Calculate rotation based on mouse position
    const rotationX = (y - 0.5) * -15; // Smooth rotation
    const rotationY = (x - 0.5) * 15;

    rotateX.set(rotationX);
    rotateY.set(rotationY);
  }

  function handleMouseLeave() {
    rotateX.set(0);
    rotateY.set(0);
  }

  // Handle day click
  function handleDayClick(day: number) {
    if (!day) return;

    const date = new Date(currentYear, currentMonth, day);
    const dayItems = getItemsForDate(day);
    onDateClick(date, dayItems);
  }

  // Format month/year display
  function getMonthYearDisplay() {
    const monthNames = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];
    return `${monthNames[currentMonth]} ${currentYear}`;
  }

  // Auto-update current month
  onMount(() => {
    const now = new Date();
    currentMonth = now.getMonth();
    currentYear = now.getFullYear();
  });

  $: calendarDays = getCalendarDays();
  $: monthYearDisplay = getMonthYearDisplay();
</script>

<div class="calendar-section">
  <!-- Timeline DDR4 RAM - Below Calendar -->
  <div class="timeline-ram-area">
    <div class="timeline-ram-slot">
      <!-- RAM Port/Slot -->
      <div class="ram-port">
        <div class="port-pins">
          {#each Array(30) as _, i}
            <div class="port-pin" style="--index: {i}"></div>
          {/each}
        </div>
      </div>

      <div class="timeline-ddr4-ram" on:click={() => (window.location.href = '/timeline')}>
        <div class="ram-body">
          <div class="ram-label">Timeline DDR4</div>
          <div class="ram-notch"></div>
          <div class="ram-contacts">
            {#each Array(30) as _, i}
              <div class="ram-contact" style="--index: {i}"></div>
            {/each}
          </div>
        </div>
        <div class="ram-hover-text">Click to access timeline</div>
      </div>
    </div>
  </div>

  <div
    class="calendar-container"
    on:mousemove={handleMouseMove}
    on:mouseleave={handleMouseLeave}
    style="transform: rotateX({$rotateX}deg) rotateY({$rotateY}deg);"
    role="button"
    tabindex="0"
  >
    <!-- Wire Spiral Binding -->
    <div class="wire-spiral-binding">
      {#each Array(12) as _, i}
        <div class="wire-coil" style="--index: {i}"></div>
      {/each}
    </div>

    <!-- Calendar Grid -->
    <div class="calendar-grid">
      <!-- Day headers -->
      <div class="day-header">Sun</div>
      <div class="day-header">Mon</div>
      <div class="day-header">Tue</div>
      <div class="day-header">Wed</div>
      <div class="day-header">Thu</div>
      <div class="day-header">Fri</div>
      <div class="day-header">Sat</div>

      <!-- Calendar days -->
      {#each calendarDays as day}
        <div
          class="calendar-day {day ? 'active' : ''} {day === currentDate.getDate() &&
          currentMonth === currentDate.getMonth() &&
          currentYear === currentDate.getFullYear()
            ? 'today'
            : ''}"
          class:has-items={day && getItemsForDate(day).length > 0}
          on:click={() => handleDayClick(day)}
          on:mouseenter={() => (hoveredDay = day)}
          on:mouseleave={() => (hoveredDay = null)}
        >
          {#if day}
            <span class="day-number">{day}</span>
            {#if getItemsForDate(day).length > 0}
              <div class="item-indicator">
                <span class="item-count">{getItemsForDate(day).length}</span>
              </div>
            {/if}
          {/if}
        </div>
      {/each}
    </div>
  </div>
</div>

<!-- EPIC 3D FAN - Bottom Centerpiece with Stickers -->
<div class="epic-fan-section">
  <div class="fan-with-stickers-layout">
    <!-- Left Side - 3D Fan -->
    <div class="fan-container">
      <Fan3D />
    </div>

    <!-- Right Side - Hardware Stickers -->
    <div class="hardware-stickers">
      <!-- Intel-style Processor Sticker -->
      <div class="hardware-sticker intel-style">
        <div class="sticker-frame">
          <div class="hologram-layer"></div>
          <div class="sticker-content">
            <div class="brand-section">
              <div class="brand-logo">PRSNL</div>
              <div class="brand-tagline">Neural Core</div>
            </div>
            <div class="spec-section">
              <div class="spec-line">AI-Powered</div>
              <div class="spec-line">Knowledge Engine</div>
            </div>
            <div class="performance-badge">
              <span class="perf-number">∞</span>
              <span class="perf-unit">IQ</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Memory Specification Sticker -->
      <div class="hardware-sticker memory-style">
        <div class="sticker-frame">
          <div class="hologram-layer"></div>
          <div class="sticker-content">
            <div class="memory-brand">
              <div class="brand-name">TIMELINE</div>
              <div class="memory-type">DDR5</div>
            </div>
            <div class="memory-specs">
              <div class="spec-item">
                <span class="spec-value">∞GB</span>
                <span class="spec-label">CAPACITY</span>
              </div>
              <div class="spec-item">
                <span class="spec-value">∞MHz</span>
                <span class="spec-label">SPEED</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Graphics Certification Sticker -->
      <div class="hardware-sticker graphics-style">
        <div class="sticker-frame">
          <div class="hologram-layer"></div>
          <div class="sticker-content">
            <div class="graphics-brand">
              <div class="gpu-logo">INSIGHTS</div>
              <div class="gpu-series">RTX ∞</div>
            </div>
            <div class="certification-badge">
              <div class="cert-icon">✓</div>
              <div class="cert-text">AI READY</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Energy Efficiency Sticker -->
      <div class="hardware-sticker efficiency-style">
        <div class="sticker-frame">
          <div class="hologram-layer"></div>
          <div class="sticker-content">
            <div class="efficiency-rating">
              <div class="rating-badge">A+++</div>
              <div class="rating-label">EFFICIENCY</div>
            </div>
            <div class="eco-badge">
              <div class="eco-icon">🌱</div>
              <div class="eco-text">ECO NEURAL</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .calendar-section {
    margin: 2rem 0;
    position: relative;
  }

  .calendar-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .calendar-header h2 {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #fff 0%, #e0e0e0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* Timeline DDR4 RAM - Below Calendar */
  .timeline-ram-area {
    display: flex;
    justify-content: center;
    margin: 3rem 0;
  }

  .timeline-ram-slot {
    position: relative;
    width: 220px;
    height: 80px;
    background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow:
      inset 0 2px 8px rgba(0, 0, 0, 0.3),
      0 4px 16px rgba(0, 0, 0, 0.2);
    padding: 10px;
  }

  .ram-port {
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
    width: 190px;
    height: 15px;
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    border-radius: 3px;
    box-shadow:
      inset 0 3px 8px rgba(0, 0, 0, 0.9),
      inset 0 -1px 2px rgba(255, 255, 255, 0.05);
    z-index: 1;
  }

  .port-pins {
    position: absolute;
    bottom: 0;
    left: 8px;
    right: 8px;
    height: 6px;
    display: flex;
    gap: 1px;
  }

  .port-pin {
    flex: 1;
    height: 100%;
    background: linear-gradient(180deg, #333 0%, #111 100%);
    border-radius: 0 0 1px 1px;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
  }

  .timeline-ddr4-ram {
    position: absolute;
    bottom: 8px;
    left: 50%;
    transform: translateX(-50%);
    width: 180px;
    height: 45px;
    background: linear-gradient(135deg, #4a9eff 0%, #0066cc 100%);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow:
      0 4px 12px rgba(74, 158, 255, 0.3),
      inset 0 1px 3px rgba(255, 255, 255, 0.3);
    z-index: 2;
  }

  .timeline-ddr4-ram:hover {
    transform: translateX(-50%) translateY(-2px);
    box-shadow:
      0 8px 24px rgba(74, 158, 255, 0.4),
      inset 0 1px 3px rgba(255, 255, 255, 0.4);
  }

  .ram-body {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .ram-label {
    color: white;
    font-size: 0.9rem;
    font-weight: 700;
    text-align: center;
    z-index: 2;
    position: relative;
  }

  .ram-notch {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 20px;
    height: 8px;
    background: #1a1a1a;
    border-radius: 0 0 4px 4px;
  }

  .ram-contacts {
    position: absolute;
    bottom: 0;
    left: 8px;
    right: 8px;
    height: 4px;
    display: flex;
    gap: 1px;
  }

  .ram-contact {
    flex: 1;
    height: 100%;
    background: linear-gradient(180deg, #ffd700 0%, #ffb000 100%);
    border-radius: 0 0 1px 1px;
  }

  .ram-hover-text {
    position: absolute;
    top: -30px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    white-space: nowrap;
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
  }

  .timeline-ddr4-ram:hover .ram-hover-text {
    opacity: 1;
  }

  .calendar-container {
    position: relative;
    max-width: 800px;
    margin: 0 auto;
    padding: 3rem 2rem;
    background: transparent;
    backdrop-filter: blur(6px) saturate(150%);
    border-radius: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow:
      0 30px 60px -20px rgba(0, 0, 0, 0.8),
      0 10px 20px -5px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2),
      inset 0 -1px 0 rgba(0, 0, 0, 0.1),
      0 0 40px rgba(255, 255, 255, 0.1);
    overflow: visible;
    transform-style: preserve-3d;
    perspective: 2000px;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .calendar-container:hover {
    box-shadow:
      0 40px 80px -20px rgba(0, 0, 0, 0.9),
      0 15px 30px -5px rgba(0, 0, 0, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.25),
      inset 0 -1px 0 rgba(0, 0, 0, 0.15),
      0 0 60px rgba(255, 255, 255, 0.15);
  }

  /* Wire Spiral Binding */
  .wire-spiral-binding {
    position: absolute;
    top: -20px;
    left: 50%;
    transform: translateX(-50%);
    width: 80%;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 10;
  }

  .wire-coil {
    width: 20px;
    height: 40px;
    background: linear-gradient(180deg, #c0c0c0 0%, #808080 50%, #404040 100%);
    border-radius: 50%;
    position: relative;
    box-shadow:
      inset 2px 0 4px rgba(255, 255, 255, 0.3),
      inset -2px 0 4px rgba(0, 0, 0, 0.3),
      0 2px 8px rgba(0, 0, 0, 0.2);
  }

  .wire-coil::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    right: 2px;
    bottom: 2px;
    background: linear-gradient(180deg, #e0e0e0 0%, #a0a0a0 100%);
    border-radius: 50%;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 1px;
    background: transparent;
    border-radius: 1rem;
    padding: 1rem;
  }

  .day-header {
    padding: 1rem;
    text-align: center;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-secondary);
    background: transparent;
    border-radius: 0.5rem;
  }

  .calendar-day {
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    background: transparent;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 60px;
  }

  .calendar-day.active {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .calendar-day.active:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  }

  .calendar-day.today {
    background: rgba(74, 158, 255, 0.2);
    border: 1px solid rgba(74, 158, 255, 0.5);
    box-shadow: 0 0 20px rgba(74, 158, 255, 0.3);
  }

  .calendar-day.has-items {
    background: rgba(220, 20, 60, 0.1);
    border: 1px solid rgba(220, 20, 60, 0.3);
  }

  .calendar-day.has-items:hover {
    background: rgba(220, 20, 60, 0.2);
    box-shadow: 0 10px 30px rgba(220, 20, 60, 0.3);
  }

  .day-number {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-primary);
    z-index: 1;
  }

  .item-indicator {
    position: absolute;
    top: 4px;
    right: 4px;
    background: var(--man-united-red);
    color: white;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(220, 20, 60, 0.4);
  }

  .item-count {
    font-size: 0.7rem;
    font-weight: 700;
  }

  /* EPIC 3D FAN - Bottom Centerpiece with Stickers */
  .epic-fan-section {
    margin: 4rem 0;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
  }

  .fan-with-stickers-layout {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 4rem;
    align-items: center;
    max-width: 1200px;
    width: 100%;
  }

  .fan-container {
    display: flex;
    justify-content: center;
  }

  /* Hardware Stickers */
  .hardware-stickers {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    min-width: 250px;
  }

  .hardware-sticker {
    position: relative;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    transform-origin: center;
  }

  .hardware-sticker:hover {
    transform: scale(1.05) rotate(1deg);
    z-index: 10;
  }

  .sticker-frame {
    position: relative;
    border-radius: 8px;
    padding: 3px;
    background: linear-gradient(135deg, #e0e0e0 0%, #bbb 50%, #999 100%);
    box-shadow:
      0 6px 20px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.4),
      inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  }

  .hologram-layer {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 6px;
    background: linear-gradient(
      135deg,
      transparent 0%,
      rgba(255, 255, 255, 0.1) 25%,
      transparent 50%,
      rgba(0, 255, 255, 0.1) 75%,
      transparent 100%
    );
    animation: hologramShift 3s infinite;
    pointer-events: none;
  }

  @keyframes hologramShift {
    0%,
    100% {
      opacity: 0.3;
    }
    50% {
      opacity: 0.7;
    }
  }

  .sticker-content {
    background: linear-gradient(135deg, #f8f8f8 0%, #e8e8e8 100%);
    border-radius: 6px;
    padding: 12px 16px;
    position: relative;
    overflow: hidden;
  }

  /* Intel-style Processor Sticker */
  .intel-style .sticker-content {
    background: linear-gradient(135deg, #0071c5 0%, #005a9f 100%);
    color: white;
  }

  .intel-style .brand-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .intel-style .brand-logo {
    font-size: 1.2rem;
    font-weight: 900;
    letter-spacing: 1px;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  }

  .intel-style .brand-tagline {
    font-size: 0.7rem;
    opacity: 0.9;
    font-weight: 600;
  }

  .intel-style .spec-section {
    margin-bottom: 8px;
  }

  .intel-style .spec-line {
    font-size: 0.8rem;
    font-weight: 600;
    line-height: 1.1;
    opacity: 0.95;
  }

  .intel-style .performance-badge {
    display: flex;
    align-items: baseline;
    gap: 2px;
  }

  .intel-style .perf-number {
    font-size: 1.8rem;
    font-weight: 900;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .intel-style .perf-unit {
    font-size: 0.9rem;
    font-weight: 700;
    opacity: 0.9;
  }

  /* Memory Specification Sticker */
  .memory-style .sticker-content {
    background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
    color: white;
  }

  .memory-style .memory-brand {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .memory-style .brand-name {
    font-size: 1rem;
    font-weight: 900;
    letter-spacing: 1px;
  }

  .memory-style .memory-type {
    font-size: 1.1rem;
    font-weight: 900;
    background: rgba(255, 255, 255, 0.2);
    padding: 2px 6px;
    border-radius: 3px;
  }

  .memory-style .memory-specs {
    display: flex;
    gap: 12px;
  }

  .memory-style .spec-item {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .memory-style .spec-value {
    font-size: 0.9rem;
    font-weight: 900;
    line-height: 1;
  }

  .memory-style .spec-label {
    font-size: 0.6rem;
    font-weight: 600;
    opacity: 0.8;
  }

  /* Graphics Certification Sticker */
  .graphics-style .sticker-content {
    background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
    color: white;
  }

  .graphics-style .graphics-brand {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .graphics-style .gpu-logo {
    font-size: 1rem;
    font-weight: 900;
    letter-spacing: 0.5px;
  }

  .graphics-style .gpu-series {
    font-size: 1.1rem;
    font-weight: 900;
    background: rgba(255, 255, 255, 0.2);
    padding: 2px 6px;
    border-radius: 3px;
  }

  .graphics-style .certification-badge {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .graphics-style .cert-icon {
    font-size: 1.2rem;
    font-weight: 900;
    background: rgba(255, 255, 255, 0.9);
    color: #27ae60;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .graphics-style .cert-text {
    font-size: 0.8rem;
    font-weight: 700;
  }

  /* Energy Efficiency Sticker */
  .efficiency-style .sticker-content {
    background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
    color: white;
  }

  .efficiency-style .efficiency-rating {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .efficiency-style .rating-badge {
    font-size: 1.2rem;
    font-weight: 900;
    background: rgba(255, 255, 255, 0.9);
    color: #8e44ad;
    padding: 4px 8px;
    border-radius: 4px;
    text-shadow: none;
  }

  .efficiency-style .rating-label {
    font-size: 0.8rem;
    font-weight: 700;
    opacity: 0.9;
  }

  .efficiency-style .eco-badge {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .efficiency-style .eco-icon {
    font-size: 1.1rem;
  }

  .efficiency-style .eco-text {
    font-size: 0.8rem;
    font-weight: 700;
  }

  /* Responsive Design */
  @media (max-width: 1024px) {
    .fan-with-stickers-layout {
      gap: 2rem;
    }

    .hardware-stickers {
      min-width: 200px;
    }
  }

  @media (max-width: 768px) {
    .calendar-container {
      padding: 2rem 1rem;
    }

    .calendar-grid {
      gap: 2px;
    }

    .day-number {
      font-size: 1rem;
    }

    .calendar-day {
      min-height: 50px;
    }

    .fan-with-stickers-layout {
      grid-template-columns: 1fr;
      gap: 3rem;
      text-align: center;
    }

    .hardware-stickers {
      flex-direction: row;
      flex-wrap: wrap;
      justify-content: center;
      gap: 1rem;
      min-width: auto;
    }

    .hardware-sticker {
      flex: 0 0 calc(50% - 0.5rem);
      max-width: 180px;
    }
  }

  @media (max-width: 480px) {
    .calendar-container {
      padding: 1.5rem 0.5rem;
    }

    .day-number {
      font-size: 0.9rem;
    }

    .calendar-day {
      min-height: 40px;
    }

    .cpu-fan-massive {
      width: 200px;
      height: 200px;
    }

    .fan-frame {
      width: 180px;
      height: 180px;
    }

    .timeline-ram-area {
      margin: 2rem 0;
    }

    .timeline-ram-slot {
      width: 160px;
      height: 50px;
    }

    .timeline-ddr4-ram {
      width: 140px;
      height: 30px;
    }

    .ram-label {
      font-size: 0.8rem;
    }
  }
</style>
