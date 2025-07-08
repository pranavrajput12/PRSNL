<script lang="ts">
  import { onMount } from 'svelte';
  import { spring } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  
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
    
    return items.filter(item => {
      const itemDate = new Date(item.createdAt);
      return itemDate.toDateString() === dateStr;
    });
  }
  
  // Get depth based on item count
  function getDepth(itemCount: number) {
    if (itemCount === 0) return 0;
    if (itemCount === 1) return 20;
    if (itemCount === 2) return 40;
    if (itemCount === 3) return 60;
    return Math.min(80, 20 * itemCount);
  }
  
  // Navigate months
  function previousMonth() {
    if (currentMonth === 0) {
      currentMonth = 11;
      currentYear--;
    } else {
      currentMonth--;
    }
  }
  
  function nextMonth() {
    if (currentMonth === 11) {
      currentMonth = 0;
      currentYear++;
    } else {
      currentMonth++;
    }
  }
  
  // Format month/year display
  function getMonthYearDisplay() {
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
    return `${monthNames[currentMonth]} ${currentYear}`;
  }
  
  // Handle mouse movement for 3D effect
  function handleMouseMove(event: MouseEvent) {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    
    $rotateY = (x - 0.5) * 20;
    $rotateX = (y - 0.5) * -20;
  }
  
  function handleMouseLeave() {
    $rotateX = 0;
    $rotateY = 0;
  }
  
  $: calendarDays = getCalendarDays();
</script>

<div class="calendar-3d-container">
  <div class="calendar-header">
    <button class="month-nav" on:click={previousMonth}>
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M12 6L8 10L12 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
    <h3 class="month-year">{getMonthYearDisplay()}</h3>
    <button class="month-nav" on:click={nextMonth}>
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M8 6L12 10L8 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
  </div>
  
  <div class="calendar-weekdays">
    {#each ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as weekday}
      <div class="weekday">{weekday}</div>
    {/each}
  </div>
  
  <div 
    class="calendar-grid"
    on:mousemove={handleMouseMove}
    on:mouseleave={handleMouseLeave}
    style="transform: perspective(1000px) rotateX({$rotateX}deg) rotateY({$rotateY}deg)"
  >
    {#each calendarDays as day, i}
      {#if day}
        {@const dayItems = getItemsForDate(day)}
        {@const depth = getDepth(dayItems.length)}
        {@const isToday = day === currentDate.getDate() && 
                          currentMonth === currentDate.getMonth() && 
                          currentYear === currentDate.getFullYear()}
        
        <button
          class="calendar-day"
          class:has-items={dayItems.length > 0}
          class:is-today={isToday}
          class:is-hovered={hoveredDay === day}
          on:click={() => onDateClick(new Date(currentYear, currentMonth, day), dayItems)}
          on:mouseenter={() => hoveredDay = day}
          on:mouseleave={() => hoveredDay = null}
          style="
            transform: translateZ({hoveredDay === day ? depth * 1.5 + 20 : depth}px) 
                      {hoveredDay === day ? 'scale(1.1)' : 'scale(1)'};
            --depth: {depth}px;
            --hover-depth: {depth * 1.5 + 20}px;
            animation-delay: {i * 30}ms;
            --glow-color: {dayItems.length > 3 ? 'rgba(74, 158, 255, 0.5)' : 
                          dayItems.length > 0 ? 'rgba(139, 92, 246, 0.3)' : 
                          'transparent'};
          "
        >
          <span class="day-number">{day}</span>
          {#if dayItems.length > 0}
            <span class="item-count">{dayItems.length}</span>
          {/if}
          
          {#if hoveredDay === day && dayItems.length > 0}
            <div class="tooltip">
              <strong>{dayItems.length} item{dayItems.length !== 1 ? 's' : ''}</strong>
              <div class="tooltip-items">
                {#each dayItems.slice(0, 3) as item}
                  <div class="tooltip-item">{item.title}</div>
                {/each}
                {#if dayItems.length > 3}
                  <div class="tooltip-more">+{dayItems.length - 3} more</div>
                {/if}
              </div>
            </div>
          {/if}
        </button>
      {:else}
        <div class="calendar-day empty"></div>
      {/if}
    {/each}
  </div>
</div>

<style>
  .calendar-3d-container {
    padding: 3rem;
    background: linear-gradient(135deg, 
      rgba(255, 255, 255, 0.03) 0%,
      rgba(255, 255, 255, 0.01) 50%,
      rgba(255, 255, 255, 0.02) 100%
    );
    backdrop-filter: blur(40px) saturate(150%);
    border-radius: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 
      0 30px 60px -20px rgba(0, 0, 0, 0.8),
      0 10px 20px -5px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2),
      inset 0 -1px 0 rgba(0, 0, 0, 0.1);
    position: relative;
    overflow: visible;
    transform-style: preserve-3d;
    perspective: 2000px;
  }
  
  .calendar-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 2rem;
  }
  
  .month-nav {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .month-nav:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    transform: scale(1.1);
  }
  
  .month-year {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    min-width: 200px;
    text-align: center;
  }
  
  .calendar-weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .weekday {
    text-align: center;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-muted);
    padding: 0.5rem;
  }
  
  .calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.5rem;
    transform-style: preserve-3d;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .calendar-day {
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(145deg,
      rgba(255, 255, 255, 0.05),
      rgba(255, 255, 255, 0.02)
    );
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    cursor: pointer;
    position: relative;
    transform-style: preserve-3d;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) backwards;
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.2),
      0 1px 2px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
  
  .calendar-day::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(145deg,
      transparent 0%,
      rgba(255, 255, 255, 0.03) 50%,
      transparent 100%
    );
    border-radius: 1rem;
    opacity: 0;
    transition: opacity 0.3s;
  }
  
  .calendar-day.empty {
    cursor: default;
    background: transparent;
    border: none;
    box-shadow: none;
  }
  
  .calendar-day:not(.empty):hover {
    background: linear-gradient(145deg,
      rgba(255, 255, 255, 0.1),
      rgba(255, 255, 255, 0.05)
    );
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 
      0 10px 40px rgba(0, 0, 0, 0.3),
      0 2px 10px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }
  
  .calendar-day:not(.empty):hover::before {
    opacity: 1;
  }
  
  .calendar-day.has-items {
    background: linear-gradient(145deg, 
      rgba(74, 158, 255, 0.15), 
      rgba(139, 92, 246, 0.1)
    );
    border: 1px solid transparent;
    border-image: linear-gradient(145deg,
      rgba(74, 158, 255, 0.5),
      rgba(139, 92, 246, 0.5)
    ) 1;
    box-shadow: 
      0 4px 20px -2px rgba(74, 158, 255, 0.4),
      0 2px 10px -2px rgba(139, 92, 246, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2),
      inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  }
  
  .calendar-day.has-items::after {
    content: '';
    position: absolute;
    inset: -1px;
    background: linear-gradient(145deg,
      rgba(74, 158, 255, 0.3),
      rgba(139, 92, 246, 0.3)
    );
    border-radius: 1rem;
    opacity: 0;
    z-index: -1;
    filter: blur(10px);
    transition: opacity 0.3s;
  }
  
  .calendar-day.has-items:hover {
    background: linear-gradient(145deg, 
      rgba(74, 158, 255, 0.25), 
      rgba(139, 92, 246, 0.2)
    );
    box-shadow: 
      0 15px 50px -5px rgba(74, 158, 255, 0.5),
      0 5px 20px -2px rgba(139, 92, 246, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.3),
      inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  }
  
  .calendar-day.has-items:hover::after {
    opacity: 0.5;
  }
  
  .calendar-day.is-today {
    background: linear-gradient(145deg, 
      rgba(220, 20, 60, 0.9),
      rgba(220, 20, 60, 0.7)
    );
    border: 1px solid rgba(220, 20, 60, 0.8);
    color: white;
    box-shadow: 
      0 8px 30px -4px rgba(220, 20, 60, 0.6),
      0 4px 15px -2px rgba(220, 20, 60, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.3),
      inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  }
  
  .calendar-day.is-today::after {
    content: '';
    position: absolute;
    inset: -2px;
    background: radial-gradient(circle,
      rgba(220, 20, 60, 0.6),
      transparent
    );
    border-radius: 1rem;
    z-index: -1;
    filter: blur(15px);
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.1); }
  }
  
  .calendar-day.is-today .day-number {
    font-weight: 800;
    color: white;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }
  
  .day-number {
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .item-count {
    position: absolute;
    top: -0.25rem;
    right: -0.25rem;
    background: linear-gradient(135deg, var(--accent), rgba(74, 158, 255, 0.8));
    color: white;
    font-size: 0.7rem;
    font-weight: 800;
    padding: 0.25rem 0.5rem;
    border-radius: 100px;
    min-width: 1.5rem;
    text-align: center;
    box-shadow: 
      0 4px 12px -2px rgba(74, 158, 255, 0.5),
      0 2px 4px -1px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.4);
    transform: translateZ(10px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: popIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) backwards;
    animation-delay: calc(var(--animation-delay, 0) + 200ms);
  }
  
  .calendar-day:hover .item-count {
    transform: translateZ(20px) scale(1.2);
    box-shadow: 
      0 6px 20px -2px rgba(74, 158, 255, 0.7),
      0 3px 8px -1px rgba(0, 0, 0, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.5);
  }
  
  @keyframes popIn {
    from {
      transform: scale(0) translateZ(0);
      opacity: 0;
    }
    to {
      transform: scale(1) translateZ(10px);
      opacity: 1;
    }
  }
  
  .tooltip {
    position: absolute;
    bottom: calc(100% + 0.5rem);
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    padding: 0.75rem;
    min-width: 200px;
    z-index: 1000;
    pointer-events: none;
    animation: tooltipIn 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .tooltip strong {
    display: block;
    margin-bottom: 0.5rem;
    color: white;
    font-size: 0.875rem;
  }
  
  .tooltip-items {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .tooltip-item {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.8);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .tooltip-more {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.5);
    font-style: italic;
    margin-top: 0.25rem;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateZ(-50px) rotateX(30deg) scale(0.8);
      filter: blur(4px);
    }
    to {
      opacity: 1;
      transform: translateZ(var(--depth, 0)) rotateX(0) scale(1);
      filter: blur(0);
    }
  }
  
  /* Dynamic shadow based on depth */
  .calendar-day:not(.empty) {
    box-shadow: 
      0 calc(2px + var(--depth) * 0.1) calc(8px + var(--depth) * 0.3) rgba(0, 0, 0, 0.2),
      0 calc(1px + var(--depth) * 0.05) calc(2px + var(--depth) * 0.1) rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
  
  .calendar-day.has-items {
    box-shadow: 
      0 calc(4px + var(--depth) * 0.15) calc(20px + var(--depth) * 0.4) -2px var(--glow-color),
      0 calc(2px + var(--depth) * 0.1) calc(10px + var(--depth) * 0.2) -2px rgba(139, 92, 246, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2),
      inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  }
  
  @keyframes tooltipIn {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }
  
  @media (max-width: 768px) {
    .calendar-3d-container {
      padding: 1rem;
    }
    
    .month-year {
      font-size: 1.25rem;
    }
    
    .calendar-grid {
      gap: 0.25rem;
    }
    
    .day-number {
      font-size: 0.875rem;
    }
  }
</style>