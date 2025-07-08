# PRSNL iOS Authentication Guide

## Overview
PRSNL uses API key authentication (temporary solution - will migrate to JWT/OAuth in the future).

## API Key Configuration

### Getting an API Key
1. The API key is configured via environment variable `PRSNL_API_KEY` on the backend
2. For development, ask the backend admin for a test API key
3. For production, keys will be generated through the web interface (future feature)

### Storing the API Key Securely

```swift
import Security

class KeychainService {
    static let shared = KeychainService()
    
    enum KeychainKey: String {
        case apiKey = "ai.prsnl.apiKey"
        case serverURL = "ai.prsnl.serverURL"
    }
    
    func save(_ value: String, for key: KeychainKey) -> Bool {
        let data = value.data(using: .utf8)!
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        // Delete any existing item
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }
    
    func get(_ key: KeychainKey) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var dataTypeRef: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &dataTypeRef)
        
        guard status == errSecSuccess,
              let data = dataTypeRef as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return value
    }
    
    func delete(_ key: KeychainKey) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue
        ]
        
        let status = SecItemDelete(query as CFDictionary)
        return status == errSecSuccess
    }
}
```

## Authentication Headers

### Primary Method: X-API-Key Header
```swift
var request = URLRequest(url: url)
request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
```

### Fallback Method: Bearer Token
```swift
var request = URLRequest(url: url)
request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
```

## Protected vs Public Endpoints

### Protected Endpoints (Require API Key)
- `/api/admin`
- `/api/capture`
- `/api/items` (POST, PATCH, DELETE)
- `/api/tags` (modifications)
- `/api/telegram/webhook`

### Public Endpoints (No API Key Required)
- `/health`
- `/api/health`
- `/api/search` (GET)
- `/api/timeline` (GET)
- `/api/items/{id}` (GET)
- `/api/tags` (GET)
- `/media/*` (static files)

## Error Handling

### 401 Unauthorized Response
```json
{
    "detail": "Invalid or missing API key"
}
```

Headers will include: `WWW-Authenticate: Bearer`

### Swift Error Handling
```swift
extension APIClient {
    func handleAuthError(_ response: HTTPURLResponse) async throws {
        if response.statusCode == 401 {
            // Clear stored API key
            KeychainService.shared.delete(.apiKey)
            
            // Notify user to re-authenticate
            await MainActor.run {
                NotificationCenter.default.post(
                    name: .apiKeyInvalid,
                    object: nil
                )
            }
            
            throw APIError.unauthorized
        }
    }
}

extension Notification.Name {
    static let apiKeyInvalid = Notification.Name("PRSNLAPIKeyInvalid")
}
```

## Settings Screen Implementation

```swift
struct SettingsView: View {
    @State private var apiKey: String = ""
    @State private var serverURL: String = "http://localhost:8000"
    @State private var isSaving = false
    @State private var testResult: String?
    
    var body: some View {
        Form {
            Section("API Configuration") {
                SecureField("API Key", text: $apiKey)
                    .textContentType(.password)
                    .autocapitalization(.none)
                
                TextField("Server URL", text: $serverURL)
                    .textContentType(.URL)
                    .autocapitalization(.none)
                    .keyboardType(.URL)
                
                Button("Save & Test Connection") {
                    Task {
                        await saveAndTestConnection()
                    }
                }
                .disabled(apiKey.isEmpty || serverURL.isEmpty)
                
                if let result = testResult {
                    Label(result, systemImage: result.contains("Success") ? "checkmark.circle" : "xmark.circle")
                        .foregroundColor(result.contains("Success") ? .green : .red)
                }
            }
        }
        .navigationTitle("Settings")
        .onAppear {
            loadSettings()
        }
    }
    
    private func loadSettings() {
        apiKey = KeychainService.shared.get(.apiKey) ?? ""
        serverURL = KeychainService.shared.get(.serverURL) ?? "http://localhost:8000"
    }
    
    private func saveAndTestConnection() async {
        isSaving = true
        defer { isSaving = false }
        
        // Save to Keychain
        _ = KeychainService.shared.save(apiKey, for: .apiKey)
        _ = KeychainService.shared.save(serverURL, for: .serverURL)
        
        // Test connection
        do {
            let client = APIClient.shared
            client.updateConfiguration(baseURL: serverURL, apiKey: apiKey)
            
            // Test with a simple endpoint
            _ = try await client.fetchTags()
            
            await MainActor.run {
                testResult = "Success! Connected to PRSNL"
            }
        } catch {
            await MainActor.run {
                testResult = "Failed: \(error.localizedDescription)"
            }
        }
    }
}
```

## Best Practices

1. **Never hardcode API keys** - Always use Keychain
2. **Validate server URL** - Ensure it's a valid HTTP/HTTPS URL
3. **Test connection** - Verify API key works before saving
4. **Handle expiration** - Be prepared for key rotation
5. **Biometric protection** - Consider adding Face ID/Touch ID for accessing settings

## Future Migration to JWT

The backend team plans to migrate to JWT authentication. When this happens:
1. API keys will be exchanged for JWT tokens
2. Tokens will need to be refreshed periodically
3. The iOS app will need to handle token refresh logic

For now, the simple API key approach works well for the MVP.