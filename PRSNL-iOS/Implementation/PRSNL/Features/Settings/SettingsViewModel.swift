import Foundation
import Combine

@MainActor
class SettingsViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var apiKey = ""
    @Published var serverURL = ""
    @Published var isTestingConnection = false
    @Published var connectionTestResult: ConnectionTestResult?
    @Published var showConnectionTestResult = false
    
    // Cache info
    @Published var cacheSize: String = "Calculating..."
    @Published var isCalculatingCacheSize = false
    @Published var isClearingCache = false
    
    // App info
    let appVersion: String
    let buildNumber: String
    
    // MARK: - Private Properties
    private let apiClient = APIClient.shared
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    init() {
        // Get app version info
        let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
        let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "Unknown"
        self.appVersion = version
        self.buildNumber = build
        
        // Load current settings
        loadSettings()
        
        // Calculate cache size on init
        Task {
            await calculateCacheSize()
        }
    }
    
    // MARK: - Public Methods
    
    /// Loads settings from Keychain
    func loadSettings() {
        apiKey = KeychainService.shared.get(.apiKey) ?? ""
        serverURL = KeychainService.shared.get(.serverURL) ?? "http://localhost:8000"
    }
    
    /// Saves settings to Keychain
    func saveSettings() {
        // Clean up server URL
        var cleanedURL = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Remove trailing slash if present
        if cleanedURL.hasSuffix("/") {
            cleanedURL = String(cleanedURL.dropLast())
        }
        
        // Save to Keychain
        _ = KeychainService.shared.set(apiKey.trimmingCharacters(in: .whitespacesAndNewlines), for: .apiKey)
        _ = KeychainService.shared.set(cleanedURL, for: .serverURL)
        
        // Update API client
        apiClient.setAPIKey(apiKey)
        apiClient.setServerURL(cleanedURL)
    }
    
    /// Tests the connection with current settings
    func testConnection() async {
        isTestingConnection = true
        connectionTestResult = nil
        
        // Save settings first
        saveSettings()
        
        do {
            // Try to fetch tags as a simple test
            let tags = try await apiClient.fetchTags()
            
            connectionTestResult = ConnectionTestResult(
                success: true,
                message: "Connected successfully! Found \(tags.count) tags.",
                serverInfo: "Server: \(serverURL)"
            )
        } catch let error as APIError {
            connectionTestResult = ConnectionTestResult(
                success: false,
                message: error.localizedDescription,
                serverInfo: "Server: \(serverURL)"
            )
        } catch {
            connectionTestResult = ConnectionTestResult(
                success: false,
                message: "Connection failed: \(error.localizedDescription)",
                serverInfo: "Server: \(serverURL)"
            )
        }
        
        isTestingConnection = false
        showConnectionTestResult = true
    }
    
    /// Calculates the current cache size
    func calculateCacheSize() async {
        isCalculatingCacheSize = true
        
        // Get caches directory
        let cacheURL = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        
        do {
            let size = try await calculateDirectorySize(at: cacheURL)
            let formatter = ByteCountFormatter()
            formatter.allowedUnits = [.useKB, .useMB, .useGB]
            formatter.countStyle = .file
            
            cacheSize = formatter.string(fromByteCount: Int64(size))
        } catch {
            cacheSize = "Unknown"
        }
        
        isCalculatingCacheSize = false
    }
    
    /// Clears the app cache
    func clearCache() async {
        isClearingCache = true
        
        // Clear URL cache
        URLCache.shared.removeAllCachedResponses()
        
        // Clear image cache if using URLCache
        URLCache.shared.diskCapacity = 0
        URLCache.shared.diskCapacity = 1024 * 1024 * 100 // Reset to 100MB
        
        // Clear any custom cache directories
        let cacheURL = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        
        do {
            let contents = try FileManager.default.contentsOfDirectory(
                at: cacheURL,
                includingPropertiesForKeys: nil,
                options: []
            )
            
            for file in contents {
                try FileManager.default.removeItem(at: file)
            }
        } catch {
            print("Failed to clear cache: \(error)")
        }
        
        isClearingCache = false
        
        // Recalculate cache size
        await calculateCacheSize()
    }
    
    /// Resets settings to defaults
    func resetToDefaults() {
        apiKey = ""
        serverURL = "http://localhost:8000"
        saveSettings()
    }
    
    /// Validates the server URL format
    func validateServerURL() -> Bool {
        let urlString = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
        
        guard !urlString.isEmpty,
              let url = URL(string: urlString),
              let scheme = url.scheme,
              (scheme == "http" || scheme == "https") else {
            return false
        }
        
        return true
    }
    
    // MARK: - Private Methods
    
    private func calculateDirectorySize(at url: URL) async throws -> UInt64 {
        var size: UInt64 = 0
        
        let contents = try FileManager.default.contentsOfDirectory(
            at: url,
            includingPropertiesForKeys: [.fileSizeKey, .isDirectoryKey],
            options: []
        )
        
        for item in contents {
            let resourceValues = try item.resourceValues(forKeys: [.fileSizeKey, .isDirectoryKey])
            
            if resourceValues.isDirectory == true {
                // Recursively calculate subdirectory size
                size += try await calculateDirectorySize(at: item)
            } else {
                size += UInt64(resourceValues.fileSize ?? 0)
            }
        }
        
        return size
    }
}

// MARK: - Supporting Types

struct ConnectionTestResult {
    let success: Bool
    let message: String
    let serverInfo: String
}