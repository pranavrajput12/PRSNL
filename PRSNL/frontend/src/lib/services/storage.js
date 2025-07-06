// Simple localStorage wrapper for PRSNL

// Save an item to localStorage
export function saveItem(key, value) {
  try {
    localStorage.setItem(`prsnl-${key}`, JSON.stringify(value));
    return true;
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
    return false;
  }
}

// Get an item from localStorage
export function getItem(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(`prsnl-${key}`);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Failed to get from localStorage:', error);
    return defaultValue;
  }
}

// Remove an item from localStorage
export function removeItem(key) {
  try {
    localStorage.removeItem(`prsnl-${key}`);
    return true;
  } catch (error) {
    console.error('Failed to remove from localStorage:', error);
    return false;
  }
}

// Clear all PRSNL data from localStorage
export function clearAll() {
  try {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('prsnl-')) {
        localStorage.removeItem(key);
      }
    });
    return true;
  } catch (error) {
    console.error('Failed to clear localStorage:', error);
    return false;
  }
}

// Check if localStorage is available
export function isAvailable() {
  try {
    const test = '__prsnl_test__';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
}
