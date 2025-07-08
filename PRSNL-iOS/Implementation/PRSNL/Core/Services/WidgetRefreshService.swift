//
//  WidgetRefreshService.swift
//  PRSNL
//
//  Created on 7/7/2025.
//

import Foundation
import WidgetKit

/// Service responsible for coordinating widget refreshes and logging
class WidgetRefreshService {
    static let shared = WidgetRefreshService()
    
    // Max number of widget logs to store
    private let maxLogEntries = 100
    
    // Notification name for widget refresh requests
    private let widgetRefreshNotificationName = "com.prsnl.widget.refreshRequested"
    
    // Shared UserDefaults for app group
    private let sharedDefaults: UserDefaults?
    
    // Key for storing widget logs
    private let widgetLogsKey = "com.prsnl.widget.logs"
    
    private init() {
        // Initialize with app group container
        sharedDefaults = UserDefaults(suiteName: "group.ai.prsnl.shared")
    }
    
    /// Request a refresh of all widgets
    func requestWidgetRefresh() {
        // Update timestamp in shared container
        sharedDefaults?.set(Date().timeIntervalSince1970, 
                           forKey: "WidgetCacheInvalidationTimestamp")
        
        // Post local notification for in-process widgets
        NotificationCenter.default.post(
            name: Notification.Name(widgetRefreshNotificationName),
            object: nil
        )
        
        // Request WidgetKit to reload timelines
        WidgetCenter.shared.reloadAllTimelines()
        
        // Log the refresh
        logWidgetEvent("Manual widget refresh requested")
    }
    
    /// Log a widget error that can be viewed in the main app
    func logWidgetError(_ message: String, errorCode: Int = 0) {
        let logEntry = [
            "timestamp": Date().timeIntervalSince1970,
            "type": "error",
            "message": message,
            "errorCode": errorCode
        ] as [String: Any]
        
        appendLogEntry(logEntry)
    }
    
    /// Log a widget information event
    func logWidgetEvent(_ message: String) {
        let logEntry = [
            "timestamp": Date().timeIntervalSince1970,
            "type": "info",
            "message": message
        ] as [String: Any]
        
        appendLogEntry(logEntry)
    }
    
    /// Get all widget logs
    func getWidgetLogs() -> [[String: Any]] {
        return sharedDefaults?.array(forKey: widgetLogsKey) as? [[String: Any]] ?? []
    }
    
    /// Clear all widget logs
    func clearWidgetLogs() {
        sharedDefaults?.removeObject(forKey: widgetLogsKey)
    }
    
    // Helper to append a log entry to the persistent store
    private func appendLogEntry(_ entry: [String: Any]) {
        var logs = getWidgetLogs()
        
        // Add new entry
        logs.append(entry)
        
        // Keep only the most recent logs
        if logs.count > maxLogEntries {
            logs = Array(logs.suffix(maxLogEntries))
        }
        
        // Save back to UserDefaults
        sharedDefaults?.set(logs, forKey: widgetLogsKey)
    }
}

/// Convenience extension for formatting widget logs
extension WidgetRefreshService {
    /// Get formatted widget logs for display
    func getFormattedWidgetLogs() -> String {
        let logs = getWidgetLogs()
        
        if logs.isEmpty {
            return "No widget logs available."
        }
        
        var result = "=== Widget Logs (\(logs.count) entries) ===\n\n"
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        
        for log in logs.reversed() {
            let timestamp = log["timestamp"] as? TimeInterval ?? 0
            let date = Date(timeIntervalSince1970: timestamp)
            let formattedDate = dateFormatter.string(from: date)
            
            let type = log["type"] as? String ?? "unknown"
            let typeSymbol = type == "error" ? "🔴" : "🔵"
            
            let message = log["message"] as? String ?? "No message"
            
            result += "\(formattedDate) \(typeSymbol) \(message)\n"
            
            if type == "error", let errorCode = log["errorCode"] as? Int, errorCode != 0 {
                result += "   Error code: \(errorCode)\n"
            }
            
            result += "\n"
        }
        
        return result
    }
}