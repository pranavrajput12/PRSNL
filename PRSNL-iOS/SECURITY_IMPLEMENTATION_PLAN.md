# PRSNL iOS: Security Implementation Plan

This document outlines the comprehensive security strategy for the PRSNL iOS app, focusing on protecting user data through secure authentication, encryption, and proper data handling practices.

## 1. Authentication Security

### 1.1 Secure Authentication Flow

```swift
// IMPLEMENT: Enhanced authentication with proper error handling
class AuthenticationService {
    // Singleton instance
    static let shared = AuthenticationService()
    
    // Authentication state
    @Published private(set) var authState: AuthState = .unknown
    private let keychainService = KeychainService()
    
    // Token management
    private var authToken: String? {
        didSet {
            if let token = authToken {
                try? keychainService.save(key: KeychainKeys.authToken, data: token)
            } else {
                try? keychainService.delete(key: KeychainKeys.authToken)
            }
        }
    }
    
    // Refresh token management
    private var refreshToken: String? {
        didSet {
            if let token = refreshToken {
                try? keychainService.save(key: KeychainKeys.refreshToken, data: token)
            } else {
                try? keychainService.delete(key: KeychainKeys.refreshToken)
            }
        }
    }
    
    // Initialize from keychain
    init() {
        do {
            self.authToken = try keychainService.retrieve(key: KeychainKeys.authToken)
            self.refreshToken = try keychainService.retrieve(key: KeychainKeys.refreshToken)
            self.authState = authToken != nil ? .authenticated : .unauthenticated
        } catch {
            self.authToken = nil
            self.refreshToken = nil
            self.authState = .unauthenticated
        }
    }
    
    // Login with credentials
    func login(email: String, password: String) async throws {
        do {
            // 1. Validate input
            guard isValidEmail(email) else { throw AuthError.invalidEmail }
            guard isValidPassword(password) else { throw AuthError.invalidPassword }
            
            // 2. Perform login request
            let response = try await APIClient.shared.login(email: email, password: password)
            
            // 3. Store tokens securely
            self.authToken = response.token
            self.refreshToken = response.refreshToken
            
            // 4. Update auth state
            self.authState = .authenticated
            
            // 5. Configure API client with new token
            APIClient.shared.setAuthToken(response.token)
            
        } catch {
            // Handle specific error cases
            if let apiError = error as? APIError {
                switch apiError {
                case .unauthorized:
                    throw AuthError.invalidCredentials
                case .networkError:
                    throw AuthError.networkError
                default:
                    throw AuthError.serverError
                }
            } else {
                throw AuthError.unknown(error)
            }
        }
    }
    
    // Token refresh logic
    func refreshAuthToken() async throws {
        guard let refreshToken = self.refreshToken else {
            throw AuthError.notAuthenticated
        }
        
        do {
            let response = try await APIClient.shared.refreshToken(refreshToken: refreshToken)
            self.authToken = response.token
            
            // Update API client with new token
            APIClient.shared.setAuthToken(response.token)
            
        } catch {
            // If refresh fails, logout
            if let apiError = error as? APIError, apiError == .unauthorized {
                await logout()
            }
            throw error
        }
    }
    
    // Secure logout
    func logout() async {
        // 1. Attempt to notify server (but don't wait for response)
        Task {
            try? await APIClient.shared.logout()
        }
        
        // 2. Clear tokens immediately
        self.authToken = nil
        self.refreshToken = nil
        
        // 3. Update auth state
        self.authState = .unauthenticated
        
        // 4. Reset API client
        APIClient.shared.clearAuthToken()
        
        // 5. Clear sensitive data
        CoreDataManager.shared.clearSensitiveData()
    }
    
    // Input validation
    private func isValidEmail(_ email: String) -> Bool {
        let emailRegEx = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPred = NSPredicate(format:"SELF MATCHES %@", emailRegEx)
        return emailPred.evaluate(with: email)
    }
    
    private func isValidPassword(_ password: String) -> Bool {
        return password.count >= 8
    }
}

// Auth state enum
enum AuthState {
    case unknown
    case authenticated
    case unauthenticated
}

// Authentication errors
enum AuthError: Error, LocalizedError {
    case invalidEmail
    case invalidPassword
    case invalidCredentials
    case notAuthenticated
    case networkError
    case serverError
    case unknown(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidEmail:
            return "Invalid email format"
        case .invalidPassword:
            return "Password must be at least 8 characters"
        case .invalidCredentials:
            return "Incorrect email or password"
        case .notAuthenticated:
            return "You are not logged in"
        case .networkError:
            return "Network connection error"
        case .serverError:
            return "Server error, please try again later"
        case .unknown(let error):
            return "Unknown error: \(error.localizedDescription)"
        }
    }
}
```

### 1.2 Biometric Authentication

```swift
// IMPLEMENT: Face ID / Touch ID Authentication
class BiometricAuthService {
    enum BiometricType {
        case none
        case touchID
        case faceID
    }
    
    enum BiometricError: Error, LocalizedError {
        case notAvailable
        case notEnrolled
        case cancelled
        case failed
        case unknown
        
        var errorDescription: String? {
            switch self {
            case .notAvailable:
                return "Biometric authentication is not available on this device"
            case .notEnrolled:
                return "No biometric authentication methods are enrolled"
            case .cancelled:
                return "Authentication was cancelled"
            case .failed:
                return "Authentication failed"
            case .unknown:
                return "An unknown error occurred"
            }
        }
    }
    
    static let shared = BiometricAuthService()
    
    private let context = LAContext()
    
    // Get available biometric type
    var biometricType: BiometricType {
        var error: NSError?
        
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            return .none
        }
        
        switch context.biometryType {
        case .touchID:
            return .touchID
        case .faceID:
            return .faceID
        default:
            return .none
        }
    }
    
    // Authenticate with biometrics
    func authenticate() async throws {
        // Check if biometrics are available
        guard biometricType != .none else {
            throw BiometricError.notAvailable
        }
        
        do {
            // Attempt authentication
            let success = try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics,
                localizedReason: "Log in to your PRSNL account"
            )
            
            guard success else {
                throw BiometricError.failed
            }
            
            // If successful, get tokens from keychain and authenticate
            if let token = try? KeychainService().retrieve(key: KeychainKeys.authToken),
               let refreshToken = try? KeychainService().retrieve(key: KeychainKeys.refreshToken) {
                
                // Set tokens in auth service
                await MainActor.run {
                    AuthenticationService.shared.authState = .authenticated
                    APIClient.shared.setAuthToken(token)
                }
            } else {
                throw AuthError.notAuthenticated
            }
            
        } catch let authError as LAError {
            switch authError.code {
            case .biometryNotAvailable:
                throw BiometricError.notAvailable
            case .biometryNotEnrolled:
                throw BiometricError.notEnrolled
            case .userCancel:
                throw BiometricError.cancelled
            default:
                throw BiometricError.unknown
            }
        }
    }
    
    // Check if biometric login is enabled in user preferences
    var isBiometricLoginEnabled: Bool {
        get {
            UserDefaults.standard.bool(forKey: "biometricLoginEnabled")
        }
        set {
            UserDefaults.standard.set(newValue, forKey: "biometricLoginEnabled")
        }
    }
}
```

## 2. Data Encryption

### 2.1 Keychain Integration

```swift
// ENHANCE: KeychainService with additional security measures
class KeychainService {
    enum KeychainError: Error {
        case saveFailure(OSStatus)
        case readFailure(OSStatus)
        case deleteFailure(OSStatus)
        case itemNotFound
        case unexpectedData
    }
    
    // Save data to keychain
    func save(key: String, data: String) throws {
        guard let encodedData = data.data(using: .utf8) else {
            throw KeychainError.unexpectedData
        }
        
        // Create query dictionary
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: encodedData,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        ]
        
        // Delete existing item
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        
        if status != errSecSuccess {
            throw KeychainError.saveFailure(status)
        }
    }
    
    // Retrieve data from keychain
    func retrieve(key: String) throws -> String {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var dataTypeRef: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &dataTypeRef)
        
        if status == errSecItemNotFound {
            throw KeychainError.itemNotFound
        } else if status != errSecSuccess {
            throw KeychainError.readFailure(status)
        }
        
        guard let data = dataTypeRef as? Data,
              let result = String(data: data, encoding: .utf8) else {
            throw KeychainError.unexpectedData
        }
        
        return result
    }
    
    // Delete data from keychain
    func delete(key: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        
        let status = SecItemDelete(query as CFDictionary)
        
        if status != errSecSuccess && status != errSecItemNotFound {
            throw KeychainError.deleteFailure(status)
        }
    }
    
    // Clear all app-related keychain items
    func clearAll() {
        // Remove all keychain items for app
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword
        ]
        
        _ = SecItemDelete(query as CFDictionary)
    }
}

// Keychain keys enum
enum KeychainKeys {
    static let authToken = "com.prsnl.authToken"
    static let refreshToken = "com.prsnl.refreshToken"
    static let userId = "com.prsnl.userId"
    static let encryptionKey = "com.prsnl.encryptionKey"
}
```

### 2.2 Sensitive Data Encryption

```swift
// IMPLEMENT: Encryption service for sensitive data
class EncryptionService {
    static let shared = EncryptionService()
    
    private let keychainService = KeychainService()
    
    // Generate and store encryption key
    func generateEncryptionKey() throws -> Data {
        var keyData = Data(count: 32) // 256-bit key
        let result = keyData.withUnsafeMutableBytes { mutableBytes in
            SecRandomCopyBytes(kSecRandomDefault, 32, mutableBytes.baseAddress!)
        }
        
        guard result == errSecSuccess else {
            throw EncryptionError.keyGenerationFailed
        }
        
        // Store in keychain
        try keychainService.save(key: KeychainKeys.encryptionKey, data: keyData.base64EncodedString())
        
        return keyData
    }
    
    // Get encryption key from keychain
    func getEncryptionKey() throws -> Data {
        // Try to get existing key
        do {
            let keyString = try keychainService.retrieve(key: KeychainKeys.encryptionKey)
            guard let keyData = Data(base64Encoded: keyString) else {
                throw EncryptionError.invalidKey
            }
            return keyData
        } catch KeychainError.itemNotFound {
            // If no key exists, generate a new one
            return try generateEncryptionKey()
        }
    }
    
    // Encrypt data
    func encrypt(_ data: Data) throws -> Data {
        let key = try getEncryptionKey()
        
        // Generate random IV (initialization vector)
        var iv = Data(count: 16)
        let result = iv.withUnsafeMutableBytes { mutableBytes in
            SecRandomCopyBytes(kSecRandomDefault, 16, mutableBytes.baseAddress!)
        }
        
        guard result == errSecSuccess else {
            throw EncryptionError.ivGenerationFailed
        }
        
        // Create a cryptographic context
        let cryptoContext = try createCryptoContext(operation: CCOperation(kCCEncrypt), key: key, iv: iv)
        
        // Allocate buffer for encrypted data
        var cipherData = Data(count: data.count + kCCBlockSizeAES128)
        var dataOutMoved = 0
        
        let status = data.withUnsafeBytes { dataBytes in
            cipherData.withUnsafeMutableBytes { cipherBytes in
                CCCrypt(
                    CCOperation(kCCEncrypt),
                    CCAlgorithm(kCCAlgorithmAES),
                    CCOptions(kCCOptionPKCS7Padding),
                    key.withUnsafeBytes { $0.baseAddress },
                    key.count,
                    iv.withUnsafeBytes { $0.baseAddress },
                    dataBytes.baseAddress,
                    data.count,
                    cipherBytes.baseAddress,
                    cipherData.count,
                    &dataOutMoved
                )
            }
        }
        
        guard status == kCCSuccess else {
            throw EncryptionError.encryptionFailed(status)
        }
        
        // Truncate to actual size and prepend IV for decryption later
        cipherData.count = dataOutMoved
        var result = iv
        result.append(cipherData)
        
        return result
    }
    
    // Decrypt data
    func decrypt(_ data: Data) throws -> Data {
        let key = try getEncryptionKey()
        
        // Extract IV from the first 16 bytes
        let iv = data.prefix(16)
        let encryptedData = data.suffix(from: 16)
        
        // Create cryptographic context
        let cryptoContext = try createCryptoContext(operation: CCOperation(kCCDecrypt), key: key, iv: Data(iv))
        
        // Allocate buffer for decrypted data
        var decryptedData = Data(count: encryptedData.count + kCCBlockSizeAES128)
        var dataOutMoved = 0
        
        let status = encryptedData.withUnsafeBytes { encryptedBytes in
            decryptedData.withUnsafeMutableBytes { decryptedBytes in
                CCCrypt(
                    CCOperation(kCCDecrypt),
                    CCAlgorithm(kCCAlgorithmAES),
                    CCOptions(kCCOptionPKCS7Padding),
                    key.withUnsafeBytes { $0.baseAddress },
                    key.count,
                    iv.withUnsafeBytes { $0.baseAddress },
                    encryptedBytes.baseAddress,
                    encryptedData.count,
                    decryptedBytes.baseAddress,
                    decryptedData.count,
                    &dataOutMoved
                )
            }
        }
        
        guard status == kCCSuccess else {
            throw EncryptionError.decryptionFailed(status)
        }
        
        // Truncate to actual size
        decryptedData.count = dataOutMoved
        
        return decryptedData
    }
    
    // Helper to create crypto context
    private func createCryptoContext(operation: CCOperation, key: Data, iv: Data) throws -> CCCryptorRef? {
        var cryptorRef: CCCryptorRef?
        
        let status = key.withUnsafeBytes { keyBytes in
            iv.withUnsafeBytes { ivBytes in
                CCCryptorCreate(
                    operation,
                    CCAlgorithm(kCCAlgorithmAES),
                    CCOptions(kCCOptionPKCS7Padding),
                    keyBytes.baseAddress,
                    key.count,
                    ivBytes.baseAddress,
                    &cryptorRef
                )
            }
        }
        
        guard status == kCCSuccess else {
            throw EncryptionError.contextCreationFailed(status)
        }
        
        return cryptorRef
    }
}

// Encryption errors
enum EncryptionError: Error {
    case keyGenerationFailed
    case ivGenerationFailed
    case contextCreationFailed(Int32)
    case encryptionFailed(Int32)
    case decryptionFailed(Int32)
    case invalidKey
}
```

## 3. Secure Networking

### 3.1 Certificate Pinning

```swift
// IMPLEMENT: Certificate pinning to prevent MITM attacks
class SecureURLSessionDelegate: NSObject, URLSessionDelegate {
    // Store expected public key hash
    private let trustedPublicKeyHash: String
    
    init(trustedPublicKeyHash: String) {
        self.trustedPublicKeyHash = trustedPublicKeyHash
        super.init()
    }
    
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        
        // Check if this is a server trust challenge
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let serverTrust = challenge.protectionSpace.serverTrust else {
            // If not a server trust challenge, reject
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Get certificate
        guard let serverCertificate = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Extract public key
        let serverPublicKey = SecCertificateCopyKey(serverCertificate)
        let serverPublicKeyData = SecKeyCopyExternalRepresentation(serverPublicKey!, nil)! as Data
        
        // Hash the public key
        let serverPublicKeyHash = serverPublicKeyData.sha256().hexString
        
        // Compare with trusted hash
        if serverPublicKeyHash == trustedPublicKeyHash {
            // Public key matches our pinned key, so accept the challenge
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
        } else {
            // Public key doesn't match, so reject the challenge
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }
}

// Extension to compute SHA-256 hash
extension Data {
    func sha256() -> Data {
        let hash = SHA256.hash(data: self)
        return Data(hash)
    }
    
    var hexString: String {
        return self.map { String(format: "%02hhx", $0) }.joined()
    }
}

// Configuring URLSession with certificate pinning
func configureSecureURLSession() -> URLSession {
    let config = URLSessionConfiguration.default
    
    // Production server public key hash
    let trustedPublicKeyHash = "a8c43dc92e1a41a3df2ea8f42e3c648bd5ef8e0797e8956ffafd5d9529ddf4b8"
    
    let delegate = SecureURLSessionDelegate(trustedPublicKeyHash: trustedPublicKeyHash)
    
    return URLSession(configuration: config, delegate: delegate, delegateQueue: nil)
}
```

### 3.2 HTTPS Enforcement

```swift
// IMPLEMENT: HTTPS enforcement in Info.plist
// Add to Info.plist:
/*
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>api.prsnl.com</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <false/>
            <key>NSIncludesSubdomains</key>
            <true/>
            <key>NSRequiresCertificateTransparency</key>
            <true/>
        </dict>
    </dict>
</dict>
*/
```

### 3.3 Secure API Client

```swift
// ENHANCE: API client with security improvements
class APIClient {
    static let shared = APIClient()
    
    private var baseURL: URL
    private var session: URLSession
    private var authToken: String?
    
    // Initialize with secure session
    init() {
        self.baseURL = URL(string: "https://api.prsnl.com")!
        self.session = configureSecureURLSession()
        
        // Try to load auth token from keychain
        do {
            self.authToken = try KeychainService().retrieve(key: KeychainKeys.authToken)
        } catch {
            self.authToken = nil
        }
    }
    
    // Set auth token
    func setAuthToken(_ token: String) {
        self.authToken = token
    }
    
    // Clear auth token
    func clearAuthToken() {
        self.authToken = nil
    }
    
    // Generic request method with retry logic for unauthorized
    func request<T: Decodable>(endpoint: String, method: String = "GET", body: Data? = nil) async throws -> T {
        var url = baseURL.appendingPathComponent(endpoint)
        
        // Create request
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add authorization if available
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        // Set request body if provided
        request.httpBody = body
        
        // Add app metadata headers
        request.setValue(Bundle.main.bundleIdentifier, forHTTPHeaderField: "X-App-Bundle-ID")
        if let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String {
            request.setValue(version, forHTTPHeaderField: "X-App-Version")
        }
        
        do {
            // Perform request
            let (data, response) = try await session.data(for: request)
            
            // Check HTTP status code
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200..<300:
                // Success, decode response
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                decoder.dateDecodingStrategy = .iso8601
                
                do {
                    return try decoder.decode(T.self, from: data)
                } catch {
                    throw APIError.decodingError(error)
                }
                
            case 401:
                // Unauthorized, try to refresh token and retry
                if endpoint != "auth/refresh" {
                    do {
                        try await AuthenticationService.shared.refreshAuthToken()
                        return try await request(endpoint: endpoint, method: method, body: body)
                    } catch {
                        throw APIError.unauthorized
                    }
                } else {
                    throw APIError.unauthorized
                }
                
            case 403:
                throw APIError.forbidden
                
            case 404:
                throw APIError.notFound
                
            case 500..<600:
                throw APIError.serverError
                
            default:
                throw APIError.httpError(httpResponse.statusCode)
            }
            
        } catch let urlError as URLError {
            switch urlError.code {
            case .notConnectedToInternet, .networkConnectionLost:
                throw APIError.networkError
            case .timedOut:
                throw APIError.timeout
            default:
                throw APIError.urlError(urlError)
            }
        } catch let apiError as APIError {
            throw apiError
        } catch {
            throw APIError.unknown(error)
        }
    }
}

// Enhanced API Errors
enum APIError: Error, Equatable {
    case invalidResponse
    case decodingError(Error)
    case unauthorized
    case forbidden
    case notFound
    case serverError
    case networkError
    case timeout
    case httpError(Int)
    case urlError(URLError)
    case unknown(Error)
    
    static func == (lhs: APIError, rhs: APIError) -> Bool {
        switch (lhs, rhs) {
        case (.invalidResponse, .invalidResponse),
             (.unauthorized, .unauthorized),
             (.forbidden, .forbidden),
             (.notFound, .notFound),
             (.serverError, .serverError),
             (.networkError, .networkError),
             (.timeout, .timeout):
            return true
        case (.httpError(let lhsCode), .httpError(let rhsCode)):
            return lhsCode == rhsCode
        case (.urlError(let lhsError), .urlError(let rhsError)):
            return lhsError.code == rhsError.code
        default:
            return false
        }
    }
}
```

## 4. Data Retention and Privacy

### 4.1 Secure Storage Policy

```swift
// IMPLEMENT: Enhanced CoreDataManager with security features
extension CoreDataManager {
    // Clear all sensitive data (for logout or privacy requests)
    func clearSensitiveData() {
        let context = persistentContainer.newBackgroundContext()
        context.perform {
            // Delete sensitive entity types
            self.deleteAllEntities(of: CDItem.self, in: context)
            // Add other sensitive entities as needed
            
            try? context.save()
        }
    }
    
    // Helper to delete all entities of a specific type
    private func deleteAllEntities<T: NSManagedObject>(of type: T.Type, in context: NSManagedObjectContext) {
        let fetchRequest: NSFetchRequest<NSFetchRequestResult> = T.fetchRequest()
        let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
        deleteRequest.resultType = .resultTypeObjectIDs
        
        do {
            let result = try context.execute(deleteRequest) as? NSBatchDeleteResult
            if let objectIDs = result?.result as? [NSManagedObjectID] {
                let changes = [NSDeletedObjectsKey: objectIDs]
                NSManagedObjectContext.mergeChanges(fromRemoteContextSave: changes, into: [self.viewContext])
            }
        } catch {
            print("Error deleting entities: \(error)")
        }
    }
    
    // Selectively delete user content
    func deleteUserContent(olderThan date: Date) {
        let context = persistentContainer.newBackgroundContext()
        context.perform {
            let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
            fetchRequest.predicate = NSPredicate(format: "updatedAt < %@", date as NSDate)
            
            do {
                let items = try context.fetch(fetchRequest)
                for item in items {
                    context.delete(item)
                }
                try context.save()
            } catch {
                print("Error deleting old content: \(error)")
            }
        }
    }
    
    // Secure data fields that need encryption
    func encryptSensitiveFields() {
        let context = persistentContainer.newBackgroundContext()
        context.perform {
            do {
                // Get items with unencrypted sensitive content
                let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
                fetchRequest.predicate = NSPredicate(format: "isEncrypted == NO AND isPrivate == YES")
                
                let items = try context.fetch(fetchRequest)
                
                // Encrypt sensitive fields
                for item in items {
                    if let content = item.content, !content.isEmpty {
                        do {
                            let contentData = content.data(using: .utf8)!
                            let encryptedData = try EncryptionService.shared.encrypt(contentData)
                            item.content = encryptedData.base64EncodedString()
                            item.isEncrypted = true
                        } catch {
                            print("Encryption error: \(error)")
                        }
                    }
                }
                
                try context.save()
            } catch {
                print("Error encrypting content: \(error)")
            }
        }
    }
    
    // Decrypt sensitive fields when needed
    func decryptItemContent(_ item: CDItem) -> String? {
        guard item.isEncrypted, let content = item.content else {
            return item.content
        }
        
        do {
            guard let data = Data(base64Encoded: content) else {
                return nil
            }
            
            let decryptedData = try EncryptionService.shared.decrypt(data)
            return String(data: decryptedData, encoding: .utf8)
        } catch {
            print("Decryption error: \(error)")
            return nil
        }
    }
}
```

### 4.2 User Data Access Policy

```swift
// IMPLEMENT: GDPR compliance features
class PrivacyManager {
    static let shared = PrivacyManager()
    
    // Export user data
    func exportUserData() async throws -> URL {
        // Create a temporary directory for export
        let tempDir = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        
        try FileManager.default.createDirectory(at: tempDir, withIntermediateDirectories: true)
        
        // Create JSON file for user data
        let jsonURL = tempDir.appendingPathComponent("user_data.json")
        
        // Get all user data from Core Data
        let userData = try await getUserDataAsJSON()
        
        // Write to file
        try userData.write(to: jsonURL, atomically: true, encoding: .utf8)
        
        // Create a ZIP archive
        let zipURL = tempDir.appendingPathComponent("user_data.zip")
        
        // Zip the directory
        // (In a real app, use a library like ZIPFoundation)
        
        return zipURL
    }
    
    // Delete all user data
    func deleteAllUserData() async throws {
        // Clear keychain
        KeychainService().clearAll()
        
        // Clear Core Data
        CoreDataManager.shared.clearSensitiveData()
        
        // Clear user defaults
        let domain = Bundle.main.bundleIdentifier!
        UserDefaults.standard.removePersistentDomain(forName: domain)
        
        // Log out
        await AuthenticationService.shared.logout()
        
        // Notify server of account deletion (would send API request)
    }
    
    // Get all user data as JSON
    private func getUserDataAsJSON() async throws -> String {
        let context = CoreDataManager.shared.viewContext
        
        // Fetch all user items
        let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
        
        let items = try context.fetch(fetchRequest)
        
        // Convert to dictionaries
        var itemDicts: [[String: Any]] = []
        
        for item in items {
            var dict: [String: Any] = [:]
            
            dict["id"] = item.id
            dict["title"] = item.title
            
            // Decrypt content if needed
            if item.isEncrypted, let content = item.content {
                dict["content"] = CoreDataManager.shared.decryptItemContent(item) ?? "[Encrypted Content]"
            } else {
                dict["content"] = item.content
            }
            
            dict["created_at"] = item.createdAt?.timeIntervalSince1970
            dict["updated_at"] = item.updatedAt?.timeIntervalSince1970
            
            itemDicts.append(dict)
        }
        
        // Get user profile
        let userData: [String: Any] = [
            "items": itemDicts,
            "profile": [:] // Add user profile data here
        ]
        
        // Convert to JSON
        let jsonData = try JSONSerialization.data(withJSONObject: userData, options: .prettyPrinted)
        return String(data: jsonData, encoding: .utf8)!
    }
}
```

## 5. Jailbreak Detection

```swift
// IMPLEMENT: Jailbreak detection
class SecurityChecker {
    static let shared = SecurityChecker()
    
    // Check if device is jailbroken
    var isDeviceJailbroken: Bool {
        #if targetEnvironment(simulator)
        // Always return false for simulator
        return false
        #else
        // Check for common jailbreak files
        let jailbreakFilepaths = [
            "/Applications/Cydia.app",
            "/Library/MobileSubstrate/MobileSubstrate.dylib",
            "/bin/bash",
            "/usr/sbin/sshd",
            "/etc/apt",
            "/usr/bin/ssh",
            "/private/var/lib/apt"
        ]
        
        for path in jailbreakFilepaths {
            if FileManager.default.fileExists(atPath: path) {
                return true
            }
        }
        
        // Check if app can write to private directories
        let stringToWrite = "JailbreakTest"
        do {
            try stringToWrite.write(toFile: "/private/jailbreaktest.txt", atomically: true, encoding: .utf8)
            // If succeeded, device is jailbroken
            try? FileManager.default.removeItem(atPath: "/private/jailbreaktest.txt")
            return true
        } catch {
            // Cannot write, which is expected on non-jailbroken devices
        }
        
        // Check for suspicious environment variables
        if ProcessInfo.processInfo.environment["DYLD_INSERT_LIBRARIES"] != nil {
            return true
        }
        
        // Check for suspicious symbolic links
        if let url = URL(string: "/Applications"), (try? url.checkResourceIsReachable()) ?? false {
            if let path = try? url.resolvingSymlinksInPath().path, path != "/Applications" {
                return true
            }
        }
        
        return false
        #endif
    }
    
    // Check for app integrity (detect tampering)
    func checkAppIntegrity() -> Bool {
        // This would implement code signing verification
        // For iOS apps from the App Store, this is generally
        // handled by the OS, but additional checks can be added
        
        return true
    }
    
    // Detect debugger
    var isDebuggerAttached: Bool {
        #if DEBUG
        // Allow debugging in debug builds
        return false
        #else
        var info = kinfo_proc()
        var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()]
        var size = MemoryLayout<kinfo_proc>.stride
        let junk = sysctl(&mib, UInt32(mib.count), &info, &size, nil, 0)
        
        if junk == 0 {
            return (info.kp_proc.p_flag & P_TRACED) != 0
        }
        
        return false
        #endif
    }
    
    // Take action based on security checks
    func enforceSecurityPolicy() {
        if isDeviceJailbroken {
            // Log security event
            Logger.security.warning("Jailbroken device detected")
            
            // Depending on policy, could:
            // 1. Show warning
            // 2. Limit functionality
            // 3. Exit app
            
            #if !DEBUG
            // In production, might want to restrict functionality
            NotificationCenter.default.post(name: .securityWarningDetected, object: nil)
            #endif
        }
        
        if isDebuggerAttached {
            Logger.security.warning("Debugger attached to app")
            
            #if !DEBUG
            // In production, might want to take action
            #endif
        }
    }
}

// Custom notification
extension Notification.Name {
    static let securityWarningDetected = Notification.Name("securityWarningDetected")
}
```

## 6. App Transport Security

```swift
// IMPLEMENT: Advanced ATS configuration in Info.plist
/*
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>api.prsnl.com</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <false/>
            <key>NSIncludesSubdomains</key>
            <true/>
            <key>NSExceptionRequiresForwardSecrecy</key>
            <true/>
            <key>NSExceptionMinimumTLSVersion</key>
            <string>TLSv1.3</string>
            <key>NSRequiresCertificateTransparency</key>
            <true/>
        </dict>
    </dict>
</dict>
*/
```

## 7. Background State Protection

```swift
// IMPLEMENT: Background state protection
class AppStateManager {
    static let shared = AppStateManager()
    
    init() {
        setupNotifications()
    }
    
    private func setupNotifications() {
        NotificationCenter.default.addObserver(self, 
                                               selector: #selector(appWillResignActive), 
                                               name: UIApplication.willResignActiveNotification, 
                                               object: nil)
        
        NotificationCenter.default.addObserver(self, 
                                               selector: #selector(appDidBecomeActive), 
                                               name: UIApplication.didBecomeActiveNotification, 
                                               object: nil)
        
        NotificationCenter.default.addObserver(self, 
                                               selector: #selector(appDidEnterBackground), 
                                               name: UIApplication.didEnterBackgroundNotification, 
                                               object: nil)
    }
    
    // App is about to go into background
    @objc private func appWillResignActive() {
        // Hide sensitive data from screenshots
        hideScreenContents(true)
    }
    
    // App returned to foreground
    @objc private func appDidBecomeActive() {
        // Show contents again
        hideScreenContents(false)
        
        // If needed, verify user identity again
        checkUserAuthenticationIfNeeded()
    }
    
    // App is now in background
    @objc private func appDidEnterBackground() {
        // Save any pending changes
        CoreDataManager.shared.saveContext()
        
        // Additional cleanup
    }
    
    // Hide sensitive UI during app switching
    private func hideScreenContents(_ hide: Bool) {
        guard let window = UIApplication.shared.windows.first else { return }
        
        // Privacy screen approach 1: Blur
        if hide {
            let blurEffect = UIBlurEffect(style: .regular)
            let blurView = UIVisualEffectView(effect: blurEffect)
            blurView.frame = window.bounds
            blurView.tag = 12345
            window.addSubview(blurView)
        } else {
            if let blurView = window.viewWithTag(12345) {
                blurView.removeFromSuperview()
            }
        }
    }
    
    // Check if authentication is needed when returning from background
    private func checkUserAuthenticationIfNeeded() {
        // Get time spent in background
        if let backgroundTime = UserDefaults.standard.object(forKey: "app_entered_background_time") as? Date {
            let timeInBackground = Date().timeIntervalSince(backgroundTime)
            
            // If in background for more than 5 minutes, require authentication again
            if timeInBackground > 5 * 60 {
                // Show authentication screen
                showAuthenticationScreen()
            }
        }
    }
    
    private func showAuthenticationScreen() {
        // In a real app, present a login/biometric verification screen
        if BiometricAuthService.shared.isBiometricLoginEnabled {
            Task {
                do {
                    try await BiometricAuthService.shared.authenticate()
                } catch {
                    // If biometric auth fails, show manual login screen
                    NotificationCenter.default.post(
                        name: NSNotification.Name("ShowLoginScreen"),
                        object: nil
                    )
                }
            }
        } else {
            // Show login screen
            NotificationCenter.default.post(
                name: NSNotification.Name("ShowLoginScreen"),
                object: nil
            )
        }
    }
}
```

## 8. Secure Coding Practices

### 8.1 Secure Input Validation

```swift
// IMPLEMENT: Secure input validation
class InputValidator {
    // Validate text input
    static func validate(text: String, type: ValidationType) -> Bool {
        switch type {
        case .email:
            return validateEmail(text)
        case .password:
            return validatePassword(text)
        case .name:
            return validateName(text)
        case .itemTitle:
            return validateItemTitle(text)
        case .itemContent:
            return validateItemContent(text)
        }
    }
    
    // Email validation
    private static func validateEmail(_ email: String) -> Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPredicate = NSPredicate(format: "SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: email)
    }
    
    // Password validation (minimum 8 characters, requires letter, number, and special char)
    private static func validatePassword(_ password: String) -> Bool {
        // Length check
        guard password.count >= 8 else {
            return false
        }
        
        // Contains at least one letter
        let letterRegex = ".*[A-Za-z]+.*"
        let letterPredicate = NSPredicate(format: "SELF MATCHES %@", letterRegex)
        guard letterPredicate.evaluate(with: password) else {
            return false
        }
        
        // Contains at least one digit
        let digitRegex = ".*[0-9]+.*"
        let digitPredicate = NSPredicate(format: "SELF MATCHES %@", digitRegex)
        guard digitPredicate.evaluate(with: password) else {
            return false
        }
        
        // Contains at least one special character
        let specialCharRegex = ".*[^A-Za-z0-9].*"
        let specialCharPredicate = NSPredicate(format: "SELF MATCHES %@", specialCharRegex)
        return specialCharPredicate.evaluate(with: password)
    }
    
    // Name validation
    private static func validateName(_ name: String) -> Bool {
        guard name.count >= 2, name.count <= 50 else {
            return false
        }
        
        // Only allow letters, spaces, and common name characters
        let nameRegex = "^[A-Za-z\\s'-]+$"
        let namePredicate = NSPredicate(format: "SELF MATCHES %@", nameRegex)
        return namePredicate.evaluate(with: name)
    }
    
    // Item title validation
    private static func validateItemTitle(_ title: String) -> Bool {
        // Basic validation for now - no empty titles and reasonable length
        guard !title.isEmpty, title.count <= 100 else {
            return false
        }
        
        return true
    }
    
    // Item content validation
    private static func validateItemContent(_ content: String) -> Bool {
        // Basic validation for content length
        guard content.count <= 10000 else {
            return false
        }
        
        return true
    }
}

// Validation types
enum ValidationType {
    case email
    case password
    case name
    case itemTitle
    case itemContent
}
```

### 8.2 Secure Logging

```swift
// IMPLEMENT: Secure logging extension
extension Logger {
    // Define subsystems
    static let network = Logger(subsystem: Bundle.main.bundleIdentifier!, category: "network")
    static let security = Logger(subsystem: Bundle.main.bundleIdentifier!, category: "security")
    static let sync = Logger(subsystem: Bundle.main.bundleIdentifier!, category: "sync")
    static let database = Logger(subsystem: Bundle.main.bundleIdentifier!, category: "database")
    static let ui = Logger(subsystem: Bundle.main.bundleIdentifier!, category: "ui")
    
    // Sanitize sensitive data before logging
    func sanitizedLog(level: OSLogType, message: String, sensitive: [String] = [], file: String = #file, function: String = #function, line: Int = #line) {
        var sanitizedMessage = message
        
        // Redact sensitive information
        for item in sensitive {
            if !item.isEmpty {
                sanitizedMessage = sanitizedMessage.replacingOccurrences(of: item, with: "[REDACTED]")
            }
        }
        
        // Log the sanitized message
        switch level {
        case .debug:
            self.debug("\(sanitizedMessage, privacy: .public) [File: \(file), Function: \(function), Line: \(line)]")
        case .info:
            self.info("\(sanitizedMessage, privacy: .public)")
        case .error:
            self.error("\(sanitizedMessage, privacy: .public) [File: \(file), Function: \(function), Line: \(line)]")
        case .fault:
            self.fault("\(sanitizedMessage, privacy: .public) [File: \(file), Function: \(function), Line: \(line)]")
        default:
            self.log("\(sanitizedMessage, privacy: .public)")
        }
    }
}

// Usage examples:
// Logger.network.sanitizedLog(level: .debug, message: "Sending request to \(url) with token \(token)", sensitive: [token])
// Logger.security.sanitizedLog(level: .error, message: "Authentication failed for user \(email)", sensitive: [email])
```

## 9. Implementation Timeline

### Phase 1: Foundation (Week 1-2)
1. Implement KeychainService for secure credential storage
2. Set up secure URLSession with certificate pinning
3. Configure App Transport Security settings
4. Enhance the APIClient with security features

### Phase 2: Authentication (Week 3-4)
1. Implement AuthenticationService with proper token handling
2. Add BiometricAuthService for Face ID/Touch ID support
3. Create secure login/logout flows
4. Implement token refresh mechanisms

### Phase 3: Data Protection (Week 5-6)
1. Implement EncryptionService for sensitive data
2. Enhance CoreDataManager with security features
3. Add secure background state handling
4. Implement secure logging

### Phase 4: Advanced Security (Week 7-8)
1. Add jailbreak and debugger detection
2. Implement privacy features (data export/deletion)
3. Add input validation
4. Perform security testing and auditing

## 10. Security Testing Checklist

- [ ] Validate secure storage of credentials
- [ ] Test certificate pinning against MITM attacks
- [ ] Verify biometric authentication flows
- [ ] Test token refresh mechanisms
- [ ] Validate encryption/decryption of sensitive data
- [ ] Verify privacy features (data export/deletion)
- [ ] Test app behavior on jailbroken devices
- [ ] Validate app behavior during background transitions
- [ ] Test input validation with edge cases
- [ ] Verify logging doesn't contain sensitive information
- [ ] Validate secure network communications
- [ ] Perform penetration testing

## 11. Security Incident Response

In case of a security incident:

1. Identify and contain the vulnerability
2. Assess impact and severity
3. Notify affected users if necessary
4. Issue app updates to fix vulnerabilities
5. Document incident and preventive measures

## 12. Compliance Considerations

- Ensure GDPR compliance for EU users
- Follow Apple's App Store Review Guidelines for privacy
- Implement App Privacy details for App Store
- Consider CCPA requirements for California users
- Document all data collection in privacy policy