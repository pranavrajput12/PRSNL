import Foundation
import Security

/// Manages secure storage of sensitive data like API keys
class KeychainService {
    static let shared = KeychainService()
    
    // Replace "ABC12DEF34" with your actual Apple Developer Team ID
    // Find your Team ID in the Apple Developer Portal or in Xcode:
    // Xcode → Project Settings → Signing & Capabilities → Team
    // For free account, comment out accessGroup
    // private let accessGroup = "ABC12DEF34.ai.prsnl.shared"
    private let accessGroup: String? = nil
    
    private init() {}
    
    enum KeychainKey: String {
        case apiKey
        case serverURL
    }
    
    /// Store a string value in the keychain
    /// - Parameters:
    ///   - value: The string to store
    ///   - key: The key to associate with the stored value
    /// - Returns: True if the operation was successful
    @discardableResult
    func set(_ value: String, for key: KeychainKey) -> Bool {
        // Convert the string to data
        guard let data = value.data(using: .utf8) else {
            return false
        }
        
        // Create query dictionary
        var query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
        ]
        
        // Add access group for sharing between app and extension
        #if !targetEnvironment(simulator)
        query[kSecAttrAccessGroup as String] = accessGroup
        #endif
        
        // Delete any existing value for this key
        SecItemDelete(query as CFDictionary)
        
        // Add the new value
        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }
    
    /// Retrieve a string value from the keychain
    /// - Parameter key: The key associated with the value to retrieve
    /// - Returns: The stored string, or nil if no value exists
    func get(_ key: KeychainKey) -> String? {
        // Create query dictionary
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        // Execute the query
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        // Check if the operation was successful
        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return value
    }
    
    /// Remove a value from the keychain
    /// - Parameter key: The key associated with the value to remove
    /// - Returns: True if the operation was successful
    @discardableResult
    func delete(_ key: KeychainKey) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue
        ]
        
        let status = SecItemDelete(query as CFDictionary)
        return status == errSecSuccess
    }
}
