# PRSNL Widget Debugging Guide

This guide provides information on debugging and troubleshooting the PRSNL iOS widgets.

## Overview

The PRSNL widget system has been designed with comprehensive debugging and error handling features to help identify and resolve issues that may occur during widget operation. These features include:

- Enhanced error logging with rate limiting
- Battery state monitoring and adaptation
- Cache diagnostics and management
- Integration with the main app for cross-process debugging
- Fallback mechanisms for graceful error recovery

## Widget Error Logging

Widget errors are logged with detailed context information to help diagnose issues:

### Error Format

Each widget error includes:
- Error message with context
- Error type and domain
- Detailed error information (code, description, reason)
- Stack trace for Core Data errors
- Environmental diagnostics (battery status, cache state)

### Rate Limiting

Error logging implements rate limiting to prevent log spam:
- Similar errors are grouped by error domain and code
- Repeated errors of the same type within a 5-minute window are suppressed
- Each unique error type is logged in full detail on first occurrence

### Viewing Logs

Logs can be viewed in:
1. Xcode console during debugging
2. Main app via the WidgetRefreshService integration
3. Debug view in the Settings screen of the main app

## Cache Diagnostics

The widget cache system includes diagnostic capabilities to help understand caching behavior:

### Cache Status Methods

- `cacheManager.getCacheStatus()`: Returns a compact overview of cache state
- `cacheManager.getDetailedCacheInfo()`: Returns detailed information about cache entries, ages, and status

### Cache Statistics

You can monitor:
- Total number of cached items by type
- Age of oldest and newest cache entries
- Cache invalidation status
- Memory usage (entry count)

### Cache Debugging Example

```swift
// Get cache status overview
let cacheStatus = WidgetCacheManager.shared.getCacheStatus()
print("Widget cache status: \(cacheStatus)")

// Get detailed cache info for deeper debugging
let detailedInfo = WidgetCacheManager.shared.getDetailedCacheInfo()
print(detailedInfo)
```

## Battery Monitoring

Widgets adapt to device battery conditions to conserve power:

### Battery State Monitoring

- Monitors battery level and charging state
- Adapts to Low Power Mode
- Dynamically adjusts refresh intervals

### Battery Status Method

The `getBatteryStatusDescription()` method provides a human-readable description of current battery status:

```swift
let batteryStatus = BatteryMonitor.shared.getBatteryStatusDescription()
print("Current battery status: \(batteryStatus)")
```

## Integration with Main App

The `WidgetRefreshService` provides integration between widgets and the main app:

### Features

- Shared logging across widget extension and main app
- Widget refresh coordination
- Error reporting from widgets to main app
- Historical log storage and viewing

### Usage Example

```swift
// In the main app
import WidgetKit

// Refresh all widgets
WidgetRefreshService.shared.requestWidgetRefresh()

// View widget logs
let logs = WidgetRefreshService.shared.getFormattedWidgetLogs()
print(logs)
```

## Common Issues and Solutions

### Widget Not Updating

**Symptoms:**
- Widget shows stale data
- Widget displays "Unable to load" message

**Debugging Steps:**
1. Check if app group container is accessible
   ```swift
   let isAccessible = UserDefaults(suiteName: APP_GROUP_IDENTIFIER) != nil
   print("App group accessible: \(isAccessible)")
   ```

2. Verify cache invalidation is working
   ```swift
   let invalidated = WidgetCacheManager.shared.isCacheInvalidated()
   print("Cache invalidated: \(invalidated)")
   ```

3. Check Core Data access in widget context
   ```swift
   // Add temporary debug code to TimelineProvider
   let coreDataAccess = try? CoreDataManager.shared.backgroundContext.count(for: NSFetchRequest(entityName: "CDItem"))
   print("Core Data accessible: \(coreDataAccess != nil)")
   ```

### Battery Drain Issues

**Debugging Steps:**
1. Verify battery monitoring is working correctly
   ```swift
   print("Battery monitoring available: \(BatteryMonitor.shared.isMonitoringAvailable)")
   ```

2. Check refresh intervals being used
   ```swift
   let interval = BatteryMonitor.shared.getRefreshInterval()
   print("Current refresh interval: \(interval/60) minutes")
   ```

3. Inspect timeline entries to ensure proper spacing
   ```swift
   // In your TimelineProvider
   print("Timeline entries: \(entries.count)")
   entries.forEach { entry in
       print("Entry date: \(entry.date)")
   }
   ```

## Advanced Debugging

### Widget Timeline Analysis

To analyze widget timeline behavior:

```swift
// Add this to your TimelineProvider's getTimeline method
let timeline = Timeline(entries: entries, policy: .atEnd)
print("Timeline created with \(entries.count) entries")
print("First entry: \(entries.first?.date ?? Date())")
print("Last entry: \(entries.last?.date ?? Date())")
print("Policy: \(timeline.policy)")
```

### Memory Usage Tracking

Monitor widget memory usage (important for widgets):

```swift
func getMemoryUsage() -> UInt64 {
    var info = mach_task_basic_info()
    var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size)/4
    
    let kerr: kern_return_t = withUnsafeMutablePointer(to: &info) {
        $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
            task_info(mach_task_self_,
                     task_flavor_t(MACH_TASK_BASIC_INFO),
                     $0,
                     &count)
        }
    }
    
    if kerr == KERN_SUCCESS {
        return info.resident_size
    } else {
        return 0
    }
}

// Usage
let memoryUsage = getMemoryUsage()
print("Widget memory usage: \(Double(memoryUsage) / 1024.0 / 1024.0) MB")
```

## Best Practices

1. **Always check for nil values**: Use optional chaining and nil coalescing to handle potential nil values.

2. **Use fallback mechanisms**: Implement graceful degradation when data is unavailable.

3. **Minimize Core Data access**: Cache widget data when possible to reduce Core Data queries.

4. **Be battery conscious**: Adapt refresh rates based on battery state and user activity.

5. **Test on real devices**: Simulator behavior can differ from real devices, especially for widgets.

6. **Monitor widget logs**: Regularly check the widget logs in the main app to catch issues early.

## Resources

- [Apple WidgetKit Documentation](https://developer.apple.com/documentation/widgetkit)
- [WWDC - Widgets Code-Along](https://developer.apple.com/videos/play/wwdc2020/10034/)
- [Core Data and App Groups](https://developer.apple.com/documentation/coredata/setting_up_a_core_data_stack)