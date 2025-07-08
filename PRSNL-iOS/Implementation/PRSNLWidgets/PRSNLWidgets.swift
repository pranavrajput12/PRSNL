import WidgetKit
import SwiftUI

@main
struct PRSNLWidgets: WidgetBundle {
    @WidgetBundleBuilder
    var body: some Widget {
        TimelineWidget()
        QuickActionsWidget()
        StatsWidget()
    }
}

// MARK: - Bundle Configuration

// Deep linking URL scheme
let APP_URL_SCHEME = "prsnl"

// MARK: - Widget Extensions

extension WidgetFamily {
    var maxItemCount: Int {
        switch self {
        case .systemSmall:
            return 2
        case .systemMedium:
            return 3
        case .systemLarge:
            return 5
        default:
            return 3
        }
    }
}

// MARK: - Widget Color Theme

struct WidgetColorTheme {
    // Accent colors
    static let primary = Color(red: 37/255, green: 99/255, blue: 235/255)
    static let secondary = Color(red: 96/255, green: 165/255, blue: 250/255)
    
    // Item type colors
    static let taskColor = Color(red: 59/255, green: 130/255, blue: 246/255)
    static let eventColor = Color(red: 239/255, green: 68/255, blue: 68/255)
    static let noteColor = Color(red: 168/255, green: 85/255, blue: 247/255)
    static let linkColor = Color(red: 20/255, green: 184/255, blue: 166/255)
    
    // Status colors
    static let successColor = Color(red: 34/255, green: 197/255, blue: 94/255)
    static let warningColor = Color(red: 245/255, green: 158/255, blue: 11/255)
    static let errorColor = Color(red: 239/255, green: 68/255, blue: 68/255)
    
    // Returns the appropriate color for a given item type
    static func colorForType(_ type: String) -> Color {
        switch type.lowercased() {
        case "task":
            return taskColor
        case "event":
            return eventColor
        case "note":
            return noteColor
        case "link":
            return linkColor
        default:
            return primary
        }
    }
}

// MARK: - Battery Management for Widgets

enum BatteryState {
    case normal
    case low
    case unknown
    
    static var current: BatteryState {
        #if os(iOS)
        // Enable battery monitoring if not already enabled
        if !UIDevice.current.isBatteryMonitoringEnabled {
            UIDevice.current.isBatteryMonitoringEnabled = true
        }
        
        // Check if battery monitoring is actually available
        if UIDevice.current.isBatteryMonitoringEnabled {
            switch UIDevice.current.batteryState {
            case .charging, .full:
                return .normal
            case .unplugged:
                // Check for valid battery level (-1.0 means unavailable)
                let level = UIDevice.current.batteryLevel
                if level >= 0 {
                    return level <= 0.2 ? .low : .normal
                } else {
                    return .unknown
                }
            case .unknown:
                return .unknown
            @unknown default:
                return .unknown
            }
        } else {
            // Battery monitoring is unavailable
            return .normal // Default to normal if monitoring is unavailable
        }
        #else
        return .normal
        #endif
    }
}

// Widget refresh intervals based on battery state
enum RefreshInterval {
    static func basedOnBatteryState() -> TimeInterval {
        switch BatteryState.current {
        case .normal:
            return 15 * 60 // 15 minutes
        case .low:
            return 60 * 60 // 1 hour
        case .unknown:
            return 15 * 60 // 15 minutes
        }
    }
}